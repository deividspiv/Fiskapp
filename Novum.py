import flet as ft
from database import AppDB
from pagos import generar_enlace_pago
import asyncio
import datetime
import os
import time
from zoneinfo import ZoneInfo

# --- PALETA DE COLORES "RESPIRO" ---
COLOR_RESPIRO = "#a3968d"
COLOR_RESPIRO_DARK = "#8e8279"
COLOR_CREMA_BOTON = "#dfd0c1"
COLOR_BG_CLARO = "#f4f2f1"
COLOR_TEXTO_OSCURO = "#4a4a4a"
COLOR_TEXTO_BLANCO = "#FFFFFF"

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "3157525")


def main(page: ft.Page):
    # -------------------------------------------------------------------------
    # 1. CONFIGURACIÓN INICIAL Y SESIÓN
    # -------------------------------------------------------------------------
    page.title = "Novum Pilates"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = COLOR_BG_CLARO
    page.padding = 0

    session_keys = {
        "is_logged_in": False,
        "has_active_package": False,
        "user_phone": "",
        "user_name": "",
        "monto_pendiente": ""
    }
    for key, default_val in session_keys.items():
        if page.session.get(key) is None:
            page.session.set(key, default_val)

    # -------------------------------------------------------------------------
    # 2. HELPERS GLOBALES
    # -------------------------------------------------------------------------
    def cs_get(key, default=None):
        try:
            val = page.client_storage.get(key)
            return val if val is not None else default
        except Exception as ex:
            print(f"Error leyendo client_storage '{key}': {ex}")
            return default

    def cs_set(key, value):
        try:
            page.client_storage.set(key, value)
        except Exception as ex:
            print(f"Error guardando client_storage '{key}': {ex}")

    def cs_remove(key):
        try:
            page.client_storage.remove(key)
        except Exception as ex:
            print(f"Error eliminando client_storage '{key}': {ex}")

    def mostrar_snack(texto, color_bg):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(texto, color=COLOR_TEXTO_BLANCO),
            bgcolor=color_bg,
            open=True,
        )
        page.update()

    def obtener_ahora_mexico():
        try:
            return datetime.datetime.now(ZoneInfo("America/Mexico_City"))
        except Exception:
            return datetime.datetime.utcnow() - datetime.timedelta(hours=6)

    def limpiar_telefono(texto):
        if not texto: return ""
        return "".join(ch for ch in str(texto) if ch.isdigit())

    def add_overlay_once(control):
        if control not in page.overlay:
            page.overlay.append(control)

    def get_creditos_por_monto(monto):
        return {"100": 1, "650": 8, "800": 12, "1000": 30}.get(str(monto), 0)

    def sync_creditos_silencioso(telefono):
        if not telefono: return
        try:
            u_sync = AppDB.verificar_usuario(telefono)
            if u_sync and str(u_sync.get("active_package", "")).lower().strip() == "pagado":
                if int(u_sync.get("credits", 0) or 0) <= 0:
                    monto = page.session.get("monto_pendiente") or cs_get("monto_pendiente", "")
                    
                    if not monto and hasattr(AppDB, "obtener_ultimo_pago"):
                        ultimo_pago = AppDB.obtener_ultimo_pago(telefono)
                        if ultimo_pago:
                            monto = str(int(float(ultimo_pago.get("amount", 0))))

                    if monto:
                        nuevos_creditos = get_creditos_por_monto(monto)
                        if nuevos_creditos > 0:
                            AppDB.asignar_creditos(telefono, nuevos_creditos)
                        page.session.set("monto_pendiente", "")
                        cs_remove("monto_pendiente")
        except Exception as e:
            print("Error en sincronización silenciosa:", e)

    # -------------------------------------------------------------------------
    # 3. DIÁLOGOS GLOBALES
    # -------------------------------------------------------------------------
    admin_pwd_field = ft.TextField(
        label="Contraseña", password=True, can_reveal_password=True,
        border_radius=10, border_color=COLOR_RESPIRO, cursor_color=COLOR_RESPIRO
    )

    def cerrar_admin_dialogo(_=None):
        admin_dlg.open = False
        admin_pwd_field.error_text = None
        admin_pwd_field.value = ""
        page.update()

    def check_admin_pwd(e):
        if (admin_pwd_field.value or "").strip() == ADMIN_PASSWORD:
            cerrar_admin_dialogo()
            page.go("/admin")
        else:
            admin_pwd_field.error_text = "Contraseña incorrecta"
            page.update()

    admin_dlg = ft.AlertDialog(
        title=ft.Text("Acceso Administrativo", color=COLOR_RESPIRO),
        content=admin_pwd_field,
        actions_alignment=ft.MainAxisAlignment.END,
        actions=[
            ft.TextButton("Cancelar", on_click=cerrar_admin_dialogo),
            ft.ElevatedButton("Entrar", bgcolor=COLOR_RESPIRO, color=COLOR_TEXTO_BLANCO, on_click=check_admin_pwd),
        ]
    )
    add_overlay_once(admin_dlg)

    def RespiroPricingCard(title, price, savings_text, features_list, package_id):
        features_ui = [
            ft.Row(controls=[
                ft.Icon(ft.icons.CHECK_CIRCLE_ROUNDED, size=16, color=COLOR_RESPIRO),
                ft.Text(feat, size=13, weight=ft.FontWeight.W_500, color=COLOR_TEXTO_OSCURO)
            ], spacing=8) for feat in features_list
        ]
        return ft.Container(
            content=ft.Column(controls=[
                ft.Text(title, size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                ft.Text(price, size=34, weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO),
                ft.Text(savings_text, size=13, color=COLOR_RESPIRO_DARK),
                ft.Divider(height=30, color="#E5E5EA"),
                ft.Column(controls=features_ui, spacing=10),
                ft.Container(height=10),
                ft.ElevatedButton("Elegir paquete", color=COLOR_TEXTO_BLANCO, bgcolor=COLOR_RESPIRO, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)), on_click=lambda _: page.go(f"/pago/{package_id}")),
            ]),
            bgcolor=COLOR_TEXTO_BLANCO, padding=25, border_radius=20, border=ft.border.all(1, "#E5E5EA"), width=280,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color="#1A000000", offset=ft.Offset(0, 8))
        )

    # -------------------------------------------------------------------------
    # 4. CONSTRUCTORES DE VISTAS
    # -------------------------------------------------------------------------
    def build_login_view():
        return ft.View(
            route="/login", bgcolor=COLOR_RESPIRO, padding=0,
            controls=[
                ft.Container(
                    expand=True, padding=ft.padding.only(left=30, right=30, top=40, bottom=40),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(controls=[ft.Container(expand=True), ft.IconButton(icon=ft.icons.SETTINGS, icon_color="white70", on_click=lambda _: (setattr(admin_dlg, "open", True), page.update()))]),
                            ft.Container(height=0),
                            ft.Container(content=ft.Image(src="logo_respiros.png", width=280, fit=ft.ImageFit.CONTAIN), alignment=ft.alignment.center),
                            ft.Icon(ft.icons.SPA, size=100, color=COLOR_TEXTO_BLANCO),
                            ft.Text("Pilates/Yoga/Relax", size=36, color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.W_300),
                            ft.Container(expand=True),
                            ft.Text("Tu espacio de bienestar", size=17, color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.W_400),
                            ft.Text("Regístrate y agenda tu cita", color="white70"),
                            ft.Container(height=40),
                            ft.Container(
                                content=ft.Text("Iniciar Sesión", color="#6b5b50", weight=ft.FontWeight.BOLD, size=15),
                                alignment=ft.alignment.center, width=300, height=55, bgcolor=COLOR_CREMA_BOTON, border_radius=27,
                                shadow=ft.BoxShadow(blur_radius=10, color="#33000000", offset=ft.Offset(0, 4)),
                                on_click=lambda _: page.go("/formulario_ingreso")
                            ),
                            ft.Container(height=10),
                            ft.TextButton(content=ft.Text("¿Nuevo? Regístrate aquí", color="white", size=14, weight=ft.FontWeight.W_300), on_click=lambda _: page.go("/formulario_ingreso")),
                        ]
                    )
                )
            ]
        )

    def build_formulario_view():
        nombre_field = ft.TextField(label="Nombre completo", border_radius=10, prefix_icon=ft.icons.PERSON, border_color=COLOR_RESPIRO, cursor_color=COLOR_RESPIRO)
        celular_field = ft.TextField(label="Número celular (10 dígitos)", border_radius=10, prefix_icon=ft.icons.PHONE, keyboard_type=ft.KeyboardType.PHONE, border_color=COLOR_RESPIRO, cursor_color=COLOR_RESPIRO)
        btn_continuar = ft.ElevatedButton(content=ft.Text("Continuar", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.W_600), bgcolor=COLOR_RESPIRO, color=COLOR_TEXTO_BLANCO, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), width=300, height=50)

        def do_login(e):
            nombre, celular = (nombre_field.value or "").strip(), limpiar_telefono(celular_field.value)
            
            if not nombre or not celular:
                mostrar_snack("Completa nombre y número celular.", ft.colors.RED_500)
                return
                
            if len(celular) < 10:
                mostrar_snack("Ingresa un número válido de 10 dígitos.", ft.colors.ORANGE_600)
                return

            contenido_original = btn_continuar.content
            btn_continuar.content = ft.ProgressRing(width=20, height=20, color=COLOR_TEXTO_BLANCO, stroke_width=2)
            btn_continuar.disabled = True
            page.update()

            try:
                usuario = AppDB.verificar_usuario(celular)
                if not usuario:
                    AppDB.registrar_usuario(celular, nombre)
                    nombre_final = nombre
                else:
                    nombre_final = usuario.get("full_name", nombre)

                sync_creditos_silencioso(celular)
                usuario_actualizado = AppDB.verificar_usuario(celular)

                tiene_paquete_activo = False
                if usuario_actualizado and str(usuario_actualizado.get("active_package", "")).lower().strip() == "pagado" and int(usuario_actualizado.get("credits", 0) or 0) > 0:
                    tiene_paquete_activo = True

                page.session.set("user_phone", celular)
                page.session.set("user_name", nombre_final)
                page.session.set("has_active_package", tiene_paquete_activo)
                cs_set("user_phone", celular)
                cs_set("user_name", nombre_final)

                btn_continuar.content = contenido_original
                btn_continuar.disabled = False
                page.update()
                page.go("/servicios" if tiene_paquete_activo else "/paquetes")
            except Exception as ex:
                print(f"Error de conexión BD: {ex}")
                btn_continuar.content = contenido_original
                btn_continuar.disabled = False
                page.update()
                mostrar_snack("Error de conexión. Verifica tu internet.", ft.colors.RED_500)

        btn_continuar.on_click = do_login

        return ft.View(
            route="/formulario_ingreso", bgcolor=COLOR_TEXTO_BLANCO, padding=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(controls=[ft.IconButton(icon=ft.icons.ARROW_BACK_IOS_NEW, icon_color=COLOR_RESPIRO, on_click=lambda _: page.go("/login")), ft.Container(expand=True)]),
                ft.Container(height=20),
                ft.Icon(ft.icons.SPA, size=80, color=COLOR_RESPIRO),
                ft.Text("Tus Datos", size=32, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                ft.Text("Ingresa para ver tus reservaciones", size=16, color=COLOR_RESPIRO_DARK, text_align=ft.TextAlign.CENTER),
                ft.Container(height=30),
                nombre_field, celular_field,
                ft.Container(height=30),
                btn_continuar,
            ]
        )

    def build_paquetes_view():
        try:
            paquetes_db = AppDB.obtener_paquetes()
        except Exception as ex:
            print("Error cargando paquetes:", ex)
            paquetes_db = []

        lista_tarjetas = [ft.Container(width=10)]
        for pq in paquetes_db:
            creditos_texto = f"{pq['credits']} clases a elegir" if pq.get("credits") else "Clases ilimitadas"
            precio_entero = int(float(pq["price"]))
            lista_tarjetas.append(RespiroPricingCard(pq["name"], f"${precio_entero}", f"Vigencia: {pq['validity_days']} días", [creditos_texto, "Reserva desde la app"], str(precio_entero)))
        lista_tarjetas.append(ft.Container(width=10))

        return ft.View(
            route="/paquetes", bgcolor=COLOR_BG_CLARO, padding=0,
            controls=[
                ft.Container(
                    padding=20, content=ft.Column(controls=[
                        ft.Container(height=20),
                        ft.Text("Elige tu plan", size=34, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                        ft.Text("Selecciona el paquete que mejor se adapte a tu rutina.", size=16, color=COLOR_RESPIRO_DARK),
                    ])
                ),
                ft.Container(height=450, content=ft.ListView(controls=lista_tarjetas, horizontal=True, spacing=15)),
            ]
        )

    def build_pago_view(monto):
        page.session.set("monto_pendiente", monto)
        
        estado_ui = ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(width=40, height=40, color=COLOR_RESPIRO, stroke_width=4),
                    ft.Container(height=10),
                    ft.Text("Esperando confirmación del banco...", size=16, color=COLOR_RESPIRO_DARK),
                    ft.Container(height=10),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ), alignment=ft.alignment.center, visible=False
        )

        async def auto_check_payment():
            telefono_alumno = page.session.get("user_phone") or cs_get("user_phone", "")
            if not telefono_alumno: return
            for _ in range(60):
                if page.route != f"/pago/{monto}": break
                await asyncio.sleep(3)
                try:
                    u = AppDB.verificar_usuario(telefono_alumno)
                    if u and str(u.get("active_package", "")).lower().strip() == "pagado":
                        sync_creditos_silencioso(telefono_alumno)
                        page.session.set("monto_pendiente", "")
                        cs_remove("monto_pendiente")
                        page.go("/servicios")
                        return
                except Exception as ex:
                    print("Error verificando pago:", ex)

        def verificar_estado_pago_manual(e):
            telefono_alumno = page.session.get("user_phone") or cs_get("user_phone", "")
            if not telefono_alumno:
                mostrar_snack("No se encontró el usuario actual.", ft.colors.RED_500)
                return
            try:
                if hasattr(AppDB, "simular_webhook_banco"): AppDB.simular_webhook_banco(telefono_alumno)
                sync_creditos_silencioso(telefono_alumno)
                page.session.set("monto_pendiente", "")
                cs_remove("monto_pendiente")
                page.go("/servicios")
            except Exception as ex:
                print("Error en comprobación manual:", ex)
                mostrar_snack("No fue posible comprobar el pago.", ft.colors.RED_500)

        btn_comprobar = ft.ElevatedButton("Ya pagué (Comprobar)", color=COLOR_TEXTO_BLANCO, bgcolor=COLOR_RESPIRO, width=250, height=45, on_click=verificar_estado_pago_manual)
        estado_ui.content.controls.append(btn_comprobar)

        def contenido_btn_bbva_default():
            return ft.Row(controls=[ft.Icon(ft.icons.CREDIT_CARD, color=COLOR_TEXTO_BLANCO), ft.Text("Pagar en línea (BBVA)", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER)

        btn_bbva = ft.ElevatedButton(content=contenido_btn_bbva_default(), bgcolor="#004481", color=COLOR_TEXTO_BLANCO, height=52, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)))

        def restaurar_btn_bbva():
            btn_bbva.disabled = False
            btn_bbva.bgcolor = "#004481"
            btn_bbva.content = contenido_btn_bbva_default()

        def pagar_bbva(e):
            btn_bbva.content = ft.Row(controls=[ft.ProgressRing(width=20, height=20, color=COLOR_TEXTO_BLANCO, stroke_width=2), ft.Text("Conectando al banco...", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER)
            btn_bbva.disabled = True
            page.update()

            telefono, nombre = page.session.get("user_phone") or cs_get("user_phone", ""), page.session.get("user_name") or cs_get("user_name", "")
            if not telefono:
                restaurar_btn_bbva()
                page.update()
                mostrar_snack("Primero inicia sesión.", ft.colors.RED_500)
                return

            try:
                AppDB.crear_registro_pago(telefono, monto)
                page.session.set("monto_pendiente", str(monto))
                cs_set("monto_pendiente", str(monto))

                link = generar_enlace_pago(monto, f"Paquete Novum Pilates {monto}", nombre, telefono)
                if link:
                    btn_bbva.content = ft.Row(controls=[ft.Icon(ft.icons.LOCK_OUTLINE, color=COLOR_TEXTO_BLANCO), ft.Text("Redirigiendo a BBVA...", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER)
                    btn_bbva.bgcolor = ft.colors.GREEN_600
                    estado_ui.visible = True
                    page.update()
                    page.launch_url(link, web_window_name="_self")
                    page.run_task(auto_check_payment)
                else:
                    restaurar_btn_bbva()
                    page.update()
                    mostrar_snack("No se pudo generar el enlace de pago.", ft.colors.RED_500)
            except Exception as ex:
                print(f"Error en flujo de BBVA: {ex}")
                restaurar_btn_bbva()
                page.update()
                mostrar_snack("Error iniciando el pago.", ft.colors.RED_500)

        btn_bbva.on_click = pagar_bbva

        return ft.View(
            route=f"/pago/{monto}", bgcolor=COLOR_TEXTO_BLANCO, padding=20,
            controls=[
                ft.Row(controls=[ft.IconButton(icon=ft.icons.ARROW_BACK_IOS_NEW, icon_color=COLOR_RESPIRO, on_click=lambda _: page.go("/paquetes")), ft.Text("Checkout", size=24, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO)]),
                ft.Container(height=30),
                ft.Text(f"Total a pagar: ${monto}.00 MXN", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                ft.Container(height=40),
                ft.Text("Método de pago", size=14, weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO_DARK),
                ft.Container(height=10),
                btn_bbva,
                ft.Container(height=15),
                ft.Container(content=ft.Row(controls=[ft.Icon(ft.icons.MONEY, color=COLOR_TEXTO_OSCURO), ft.Text("Pagar en Recepción", color=COLOR_TEXTO_OSCURO, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER), bgcolor=COLOR_BG_CLARO, padding=15, border_radius=12, on_click=lambda _: mostrar_snack("Solicitud enviada. Paga en recepción.", COLOR_RESPIRO)),
                ft.Container(height=20),
                estado_ui,
            ]
        )

    def build_verificando_view():
        estado_texto = ft.Text("Aprobando automáticamente...", size=16, color=COLOR_RESPIRO_DARK)
        anillo_carga = ft.ProgressRing(width=60, height=60, color=COLOR_RESPIRO, stroke_width=4)
        
        estado_ui = ft.Container(
            content=ft.Column(
                controls=[
                    anillo_carga, 
                    ft.Container(height=20), 
                    estado_texto
                ], 
                alignment=ft.MainAxisAlignment.CENTER, 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center, 
            height=300
        )

        async def auto_check_payment_recovery():
            await asyncio.sleep(2) 
            telefono_alumno = page.session.get("user_phone") or cs_get("user_phone", "")
            
            if not telefono_alumno:
                anillo_carga.visible = False
                estado_texto.value = "No se pudo recuperar la sesión. Usa el botón manual."
                estado_texto.color = ft.colors.RED_500
                page.update()
                return

            intentos = 0
            base_route = page.route.split("?")[0]
            while intentos < 15:
                if base_route != "/pago/verificando": 
                    break
                    
                try:
                    u = AppDB.verificar_usuario(telefono_alumno)
                    if u and str(u.get("active_package", "")).lower().strip() == "pagado":
                        sync_creditos_silencioso(telefono_alumno)
                        page.session.set("monto_pendiente", "")
                        cs_remove("monto_pendiente")
                        page.go("/servicios")
                        return
                except Exception as ex:
                    print("Error verificando pago recovery:", ex)
                
                intentos += 1
                await asyncio.sleep(3)

            base_route = page.route.split("?")[0]
            if base_route == "/pago/verificando":
                anillo_carga.visible = False
                estado_texto.value = "El banco está tardando. Toca el botón de Bypass."
                estado_texto.color = ft.colors.ORANGE_600
                page.update()

        page.run_task(auto_check_payment_recovery)

        def verificar_estado_pago_manual_rec(e):
            telefono_alumno = page.session.get("user_phone") or cs_get("user_phone", "")
            if not telefono_alumno:
                mostrar_snack("No se encontró el usuario actual.", ft.colors.RED_500)
                return
            try:
                if hasattr(AppDB, "simular_webhook_banco"): 
                    AppDB.simular_webhook_banco(telefono_alumno)
                
                sync_creditos_silencioso(telefono_alumno)
                page.session.set("monto_pendiente", "")
                cs_remove("monto_pendiente")
                page.go("/servicios")
            except Exception as ex:
                print("Error en bypass de pago:", ex)
                mostrar_snack("No fue posible comprobar el pago.", ft.colors.RED_500)

        btn_accion = ft.ElevatedButton(
            "Comprobar Manualmente (Bypass)", 
            color=COLOR_TEXTO_BLANCO, 
            bgcolor=COLOR_RESPIRO, 
            width=300, 
            height=50, 
            on_click=verificar_estado_pago_manual_rec
        )

        return ft.View(
            route="/pago/verificando", bgcolor=COLOR_TEXTO_BLANCO, padding=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(height=50),
                ft.Text("Checkout Seguro", size=24, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                ft.Container(height=40), estado_ui, ft.Container(height=40), btn_accion,
            ]
        )

    def build_servicios_view():
        telefono_alumno = page.session.get("user_phone") or cs_get("user_phone", "")
        sync_creditos_silencioso(telefono_alumno)
        nombre_usuario = page.session.get("user_name") or cs_get("user_name", "")
        primer_nombre = nombre_usuario.split()[0] if nombre_usuario else "Alumno"
        inicial = primer_nombre[0].upper() if primer_nombre else "A"
        hoy = datetime.date.today()

        vista_estado = {"fecha_activa": hoy, "servicio_activo": "Pilates"}

        servicios_ui = ft.Row(spacing=10, scroll=ft.ScrollMode.HIDDEN)
        dias_ui = ft.Row(spacing=15, scroll=ft.ScrollMode.HIDDEN)
        horarios_ui = ft.Column(spacing=15)

        def recargar_pantalla():
            horarios_ui.controls.clear()
            horarios_ui.controls.append(ft.Container(content=ft.ProgressRing(color=COLOR_RESPIRO), alignment=ft.alignment.center, padding=40))
            page.update()

            try: mis_reservas = AppDB.obtener_reservas_usuario(telefono_alumno)
            except Exception as ex:
                print("Error obteniendo reservas:", ex)
                mis_reservas = []

            fechas_reservadas_limpias, clases_agendadas = [], []
            for r in mis_reservas:
                if r.get("estado", "").lower() == "futura":
                    clases_agendadas.append(r.get("class_id"))
                    f_raw = str(r.get("class_date") or r.get("fecha", "")).strip().split(" ")[0]
                    fechas_reservadas_limpias.append(f_raw)

            servicios_ui.controls.clear()
            for serv in ["Pilates", "Yoga", "Ejercicios Funcionales"]:
                es_activo = serv == vista_estado["servicio_activo"]
                servicios_ui.controls.append(
                    ft.Container(
                        content=ft.Text(serv, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_BLANCO if es_activo else COLOR_RESPIRO),
                        bgcolor=COLOR_RESPIRO if es_activo else COLOR_TEXTO_BLANCO, padding=ft.padding.symmetric(horizontal=20, vertical=10),
                        border_radius=20, border=ft.border.all(1, COLOR_RESPIRO) if not es_activo else None,
                        on_click=lambda e, s=serv: al_seleccionar_servicio(s)
                    )
                )

            dias_ui.controls.clear()
            nombres_dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
            for i in range(14):
                fecha_iter = hoy + datetime.timedelta(days=i)
                es_dia_seleccionado = fecha_iter == vista_estado["fecha_activa"]
                bg_color = COLOR_RESPIRO if es_dia_seleccionado else COLOR_TEXTO_BLANCO
                text_color = COLOR_TEXTO_BLANCO if es_dia_seleccionado else COLOR_TEXTO_OSCURO
                dia_str = fecha_iter.strftime("%Y-%m-%d")
                tiene_reserva_hoy = any(dia_str in f_res or f_res in dia_str for f_res in fechas_reservadas_limpias)

                col_dia = [
                    ft.Text(nombres_dias[fecha_iter.weekday()], size=14, color=text_color, weight=ft.FontWeight.W_500),
                    ft.Text(str(fecha_iter.day), size=20, color=text_color, weight=ft.FontWeight.BOLD),
                ]
                col_dia.append(ft.Icon(ft.icons.CHECK_CIRCLE, color=text_color, size=12) if tiene_reserva_hoy else ft.Container(height=12))

                dias_ui.controls.append(
                    ft.Container(
                        content=ft.Column(controls=col_dia, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                        bgcolor=bg_color, width=65, height=85, border_radius=15, border=ft.border.all(1, "#E5E5EA") if not es_dia_seleccionado else None,
                        on_click=lambda e, f=fecha_iter: al_seleccionar_dia(f)
                    )
                )

            horarios_ui.controls.clear()
            fecha_str = vista_estado["fecha_activa"].strftime("%Y-%m-%d")
            try: dia_bloqueado = AppDB.es_dia_bloqueado(fecha_str)
            except Exception: dia_bloqueado = False

            if dia_bloqueado:
                horarios_ui.controls.append(ft.Container(content=ft.Column(controls=[ft.Icon(ft.icons.NIGHTLIGHT_ROUND, size=50, color=COLOR_RESPIRO), ft.Text("Estudio Cerrado", size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), ft.Text("Tómate un descanso. Nos vemos pronto.", text_align=ft.TextAlign.CENTER, color=COLOR_RESPIRO_DARK)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), bgcolor=COLOR_TEXTO_BLANCO, padding=40, border_radius=15))
            else:
                try: clases_del_dia = AppDB.obtener_clases(vista_estado["servicio_activo"], fecha_str)
                except Exception: clases_del_dia = []

                dia_ya_reservado = any(fecha_str in f_res or f_res in fecha_str for f_res in fechas_reservadas_limpias)
                if not clases_del_dia:
                    horarios_ui.controls.append(ft.Text(f"No hay clases de {vista_estado['servicio_activo']} programadas.", color=COLOR_RESPIRO_DARK))

                ahora_mx = obtener_ahora_mexico().replace(tzinfo=None)

                for h in clases_del_dia:
                    cupo_actual = int(h.get("cupo", 0) or 0)
                    is_full = cupo_actual <= 0
                    ya_agendado = h.get("id") in clases_agendadas
                    
                    try:
                        dt_str = f"{fecha_str} {h.get('hora')}"
                        try:
                            dt_clase = datetime.datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
                        except ValueError:
                            dt_clase = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                        ya_paso = ahora_mx >= dt_clase
                    except Exception:
                        ya_paso = False

                    if ya_paso:
                        btn_color, btn_text, text_btn_color, accion_btn = "#E5E5EA", "Finalizada", COLOR_RESPIRO_DARK, None
                    elif ya_agendado:
                        btn_color, btn_text, text_btn_color, accion_btn = ft.colors.GREEN_500, "Agendado ✓", COLOR_TEXTO_BLANCO, lambda _: page.go("/perfil")
                    elif dia_ya_reservado:
                        btn_color, btn_text, text_btn_color, accion_btn = "#E5E5EA", "Día Reservado", COLOR_RESPIRO_DARK, None
                    else:
                        btn_color, btn_text, text_btn_color = "#E5E5EA" if is_full else COLOR_CREMA_BOTON, "Lleno" if is_full else "Reservar", COLOR_RESPIRO_DARK if is_full else "#6b5b50"
                        accion_btn = (lambda e, c=h: confirmar_reserva(e, c)) if not is_full else None

                    horarios_ui.controls.append(
                        ft.Container(
                            content=ft.Row(controls=[
                                ft.Column(controls=[ft.Text(h.get("hora", ""), size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), ft.Text(f"Prof: {h.get('instructor', 'Staff')}", size=13, color=COLOR_RESPIRO_DARK), ft.Text(f"Lugares: {cupo_actual}", size=12, color=COLOR_RESPIRO if not is_full else ft.colors.RED_400)], spacing=2),
                                ft.Container(expand=True),
                                ft.Container(content=ft.Text(btn_text, weight=ft.FontWeight.BOLD, color=text_btn_color, size=13), bgcolor=btn_color, padding=ft.padding.symmetric(horizontal=20, vertical=10), border_radius=20, on_click=accion_btn),
                            ]), bgcolor=COLOR_TEXTO_BLANCO, padding=20, border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color="#0A000000", offset=ft.Offset(0, 4))
                        )
                    )
            page.update()

        def al_seleccionar_dia(nueva_fecha):
            vista_estado["fecha_activa"] = nueva_fecha
            recargar_pantalla()

        def al_seleccionar_servicio(nuevo_servicio):
            vista_estado["servicio_activo"] = nuevo_servicio
            recargar_pantalla()

        def confirmar_reserva(e, clase):
            if e and e.control:
                e.control.disabled = True
                e.control.content = ft.ProgressRing(width=15, height=15, color=COLOR_TEXTO_BLANCO, stroke_width=2)
                page.update()

            try:
                usuario_actual = AppDB.verificar_usuario(telefono_alumno)
                creditos_actuales = int(usuario_actual.get("credits", 0) if usuario_actual else 0)
                
                if creditos_actuales <= 0:
                    page.go("/paquetes")
                    return
                    
                if AppDB.reservar_clase(telefono_alumno, clase["id"]):
                    AppDB.asignar_creditos(telefono_alumno, max(0, creditos_actuales - 1))
                    mostrar_snack("¡Reserva confirmada! Se descontó 1 clase.", ft.colors.GREEN_600)
                    recargar_pantalla()
                else:
                    mostrar_snack("No fue posible reservar la clase.", ft.colors.RED_500)
                    if e and e.control:
                        e.control.disabled = False
                        page.update()
            except Exception as ex:
                print("Error reservando clase:", ex)
                mostrar_snack("Error al reservar la clase.", ft.colors.RED_500)
                if e and e.control:
                    e.control.disabled = False
                    page.update()

        recargar_pantalla()

        return ft.View(
            route="/servicios", bgcolor=COLOR_BG_CLARO, padding=20, scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(height=10),
                ft.Row(controls=[
                    ft.Column(controls=[ft.Text(f"Hola, {primer_nombre} 👋", size=26, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), ft.Text("Reserva tu próxima clase", size=15, color=COLOR_RESPIRO_DARK)], spacing=0),
                    ft.Container(expand=True),
                    ft.Container(content=ft.Text(inicial, size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_BLANCO), alignment=ft.alignment.center, width=45, height=45, bgcolor=COLOR_RESPIRO, shape=ft.BoxShape.CIRCLE, shadow=ft.BoxShadow(blur_radius=5, color="#33000000", offset=ft.Offset(0, 2)), on_click=lambda _: page.go("/perfil")),
                ]),
                ft.Container(height=25), servicios_ui, ft.Container(height=25), dias_ui, ft.Container(height=25),
                ft.Text("Horarios Disponibles", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                ft.Container(height=10), horarios_ui, ft.Container(height=40),
            ]
        )

    def build_perfil_view():
        telefono_alumno = page.session.get("user_phone") or cs_get("user_phone", "")
        sync_creditos_silencioso(telefono_alumno)
        try: usuario = AppDB.verificar_usuario(telefono_alumno)
        except Exception: usuario = None
        clases_restantes = int(usuario.get("credits", 0) if usuario else 0)

        try: mis_reservas = AppDB.obtener_reservas_usuario(telefono_alumno)
        except Exception: mis_reservas = []

        seccion_sin_creditos = ft.Container(
            content=ft.Column(controls=[ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.ORANGE_500, size=40), ft.Text("¡Te has quedado sin clases!", size=18, weight=ft.FontWeight.BOLD), ft.ElevatedButton("Comprar Paquete", bgcolor=COLOR_RESPIRO, color="white", on_click=lambda _: page.go("/paquetes"))], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="white", padding=20, border_radius=15, margin=ft.margin.only(bottom=20)
        ) if clases_restantes <= 0 else ft.Container()

        def refrescar_creditos_click(e):
            try:
                original = e.control.content
                e.control.content = ft.ProgressRing(width=20, height=20, color=COLOR_RESPIRO)
                page.update()
                u_sync = AppDB.verificar_usuario(telefono_alumno)
                monto = page.session.get("monto_pendiente") or cs_get("monto_pendiente", "")
                if u_sync and str(u_sync.get("active_package", "")).lower().strip() == "pagado":
                    if int(u_sync.get("credits", 0) or 0) <= 0 and monto:
                        nuevos_creditos = get_creditos_por_monto(monto)
                        if nuevos_creditos > 0: AppDB.asignar_creditos(telefono_alumno, nuevos_creditos)
                    page.session.set("monto_pendiente", "")
                    cs_remove("monto_pendiente")
                    mostrar_snack("¡Tus clases han sido sincronizadas!", ft.colors.GREEN_600)
                else: mostrar_snack("Aún no detectamos tu pago en la base de datos.", ft.colors.ORANGE_600)
                e.control.content = original
                
                page.route = "/recargando"
                page.update()
                time.sleep(0.01)
                page.go("/perfil") 
            except Exception: mostrar_snack("Error refrescando tus clases.", ft.colors.RED_500)

        boton_refrescar = ft.Container(
            content=ft.Row(controls=[ft.Icon(ft.icons.REFRESH, color=COLOR_RESPIRO, size=20), ft.Text("¿Pagaste y no ves tus clases? Toca aquí", color=COLOR_RESPIRO, size=13, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER),
            padding=12, border=ft.border.all(1, COLOR_RESPIRO), border_radius=10, on_click=refrescar_creditos_click, margin=ft.margin.only(bottom=15)
        )

        reserva_a_cancelar, aplica_penalizacion = [None], [False]
        dlg_cancelar = ft.AlertDialog(title=ft.Text("Cancelar Sesión", weight=ft.FontWeight.BOLD), content=ft.Text(""))
        add_overlay_once(dlg_cancelar)

        def ejecutar_cancelacion_final(e):
            rid, penalizar = reserva_a_cancelar[0], aplica_penalizacion[0]
            dlg_cancelar.open = False
            contenedor_reservas.content = ft.Container(content=ft.Column(controls=[ft.ProgressRing(color=COLOR_RESPIRO), ft.Text("Procesando cancelación...", color=COLOR_RESPIRO_DARK)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), alignment=ft.alignment.center, height=200)
            page.update()
            try:
                AppDB.cancelar_reserva(rid)
                if not penalizar:
                    u_actual = AppDB.verificar_usuario(telefono_alumno)
                    AppDB.asignar_creditos(telefono_alumno, int(u_actual.get("credits", 0) if u_actual else 0) + 1)
                mostrar_snack("Sesión cancelada. Se aplicó la penalidad de 12 horas." if penalizar else "Sesión cancelada. Se devolvió 1 clase.", ft.colors.ORANGE_600 if penalizar else ft.colors.GREEN_600)
            except Exception:
                mostrar_snack("No fue posible cancelar la sesión.", ft.colors.RED_500)
            
            page.route = "/recargando"
            page.update()
            time.sleep(0.01)
            page.go("/perfil") 

        dlg_cancelar.actions = [ft.TextButton("Volver", on_click=lambda _: setattr(dlg_cancelar, 'open', False) or page.update()), ft.ElevatedButton("Sí, Cancelar", bgcolor=ft.colors.RED_500, color="white", on_click=ejecutar_cancelacion_final)]

        def preparar_cancelacion(res):
            reserva_a_cancelar[0] = res.get("id")
            es_penalizable = False
            try:
                c_date, s_time = res.get("class_date") or res.get("fecha"), res.get("start_time") or res.get("hora")
                if c_date and s_time:
                    dt_str = f"{str(c_date).split()[0]} {str(s_time).strip()}"
                    try: dt_clase = datetime.datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
                    except ValueError: dt_clase = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                    ahora_mexico = obtener_ahora_mexico()
                    if dt_clase.tzinfo: dt_clase = dt_clase.replace(tzinfo=None)
                    if ahora_mexico.tzinfo: ahora_mexico = ahora_mexico.replace(tzinfo=None)
                    
                    horas_diff = (dt_clase - ahora_mexico).total_seconds() / 3600
                    if horas_diff <= 12: es_penalizable = True
            except Exception: pass
            
            aplica_penalizacion[0] = es_penalizable
            dlg_cancelar.content = ft.Text("Faltan menos de 12 horas para tu clase. Si cancelas ahora perderás esta clase.\n\n¿Deseas cancelarla de todos modos?", color=ft.colors.RED_600) if es_penalizable else ft.Text("¿Estás seguro de que deseas cancelar tu clase?\n\nTu crédito será devuelto automáticamente.")
            dlg_cancelar.open = True
            page.update()

        lista_reservas_ui = ft.Column(spacing=15)
        for res in mis_reservas:
            is_futura = res.get("estado", "").lower() == "futura"
            elementos_tarjeta = [
                ft.Row(controls=[ft.Text(res.get("servicio", "Clase"), size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), ft.Container(expand=True), ft.Text(res.get("estado", "").capitalize(), size=12, color=COLOR_RESPIRO if is_futura else COLOR_RESPIRO_DARK, weight=ft.FontWeight.BOLD)]),
                ft.Text(res.get("fecha", ""), size=14, color=COLOR_RESPIRO_DARK),
            ]
            if is_futura: elementos_tarjeta.append(ft.Row(controls=[ft.Container(expand=True), ft.TextButton("Cancelar Clase", icon=ft.icons.CANCEL, style=ft.ButtonStyle(color=ft.colors.RED_400), on_click=lambda e, r=res: preparar_cancelacion(r))]))
            lista_reservas_ui.controls.append(ft.Container(content=ft.Column(controls=elementos_tarjeta, spacing=5), bgcolor="white", padding=20, border_radius=15, shadow=ft.BoxShadow(blur_radius=5, color="#0A000000", offset=ft.Offset(0, 2))))
        if not mis_reservas: lista_reservas_ui.controls.append(ft.Text("Aún no tienes historial de reservas.", color=COLOR_RESPIRO_DARK))
        contenedor_reservas = ft.Container(content=lista_reservas_ui)

        def ejecutar_cierre_sesion(e):
            for k in ["is_logged_in", "has_active_package", "user_phone", "user_name", "monto_pendiente"]: page.session.set(k, False if 'is' in k or 'has' in k else "")
            for k in ["user_phone", "user_name", "monto_pendiente"]: cs_remove(k)
            page.go("/login")

        return ft.View(
            route="/perfil", bgcolor=COLOR_BG_CLARO, padding=20, scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(controls=[ft.IconButton(icon=ft.icons.ARROW_BACK_IOS_NEW, icon_color=COLOR_RESPIRO, on_click=lambda _: page.go("/servicios")), ft.Text("Mi Perfil", size=24, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO)]),
                boton_refrescar,
                ft.Container(content=ft.Row(controls=[ft.Column(controls=[ft.Text("Clases Restantes", size=14, color=COLOR_TEXTO_OSCURO), ft.Text(f"{clases_restantes}", size=40, weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO)]), ft.Container(expand=True), ft.Icon(ft.icons.FITNESS_CENTER, size=40, color=COLOR_RESPIRO)]), bgcolor="white", padding=25, border_radius=15, shadow=ft.BoxShadow(blur_radius=5, color="#0A000000")),
                ft.Container(height=20), seccion_sin_creditos,
                ft.Text("Tus Reservas", size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                contenedor_reservas, ft.Container(height=30),
                ft.TextButton("Cerrar Sesión", icon=ft.icons.LOGOUT, style=ft.ButtonStyle(color=ft.colors.RED_400), on_click=ejecutar_cierre_sesion),
            ]
        )

    def build_admin_view():
        fecha_activa = [datetime.date.today()]
        txt_fecha_top = ft.Text(fecha_activa[0].strftime("%Y-%m-%d"), size=18, weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO)
        modo_agenda = ["30"]

        def recargar_listas():
            f_str = fecha_activa[0].strftime("%Y-%m-%d")
            lista_agenda.controls.clear()
            lista_agenda.controls.append(ft.Container(content=ft.ProgressRing(color=COLOR_RESPIRO), alignment=ft.alignment.center, padding=40))
            page.update()
            lista_agenda.controls.clear()
            try:
                if modo_agenda[0] == "30":
                    hoy_str = datetime.date.today().strftime("%Y-%m-%d")
                    fin_str = (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
                    clases = AppDB.obtener_agenda_rango(hoy_str, fin_str)
                else: clases = AppDB.obtener_todas_las_clases_dia(f_str)
            except Exception: clases = []

            if not clases: lista_agenda.controls.append(ft.Text("No hay clases programadas.", color=COLOR_RESPIRO_DARK))
            for c in clases:
                if not c.get("is_blocked"):
                    fecha_lbl = f"{c['class_date']} | " if modo_agenda[0] == "30" else ""
                    lista_agenda.controls.append(
                        ft.Container(
                            content=ft.Row(controls=[
                                ft.Column(controls=[ft.Text(f"{fecha_lbl}{c['start_time']} - {c['service_name']}", weight=ft.FontWeight.BOLD), ft.Text(f"Prof: {c['instructor']} | Cupo: {c.get('capacity', 10)}", size=12)], spacing=0),
                                ft.Container(expand=True),
                                ft.Row(controls=[ft.IconButton(icon=ft.icons.INFO_OUTLINE, icon_color=COLOR_RESPIRO, on_click=lambda e, cid=c["id"]: ver_detalles_clase(cid)), ft.IconButton(icon=ft.icons.DELETE, icon_color=ft.colors.RED_400, on_click=lambda e, cid=c["id"]: borrar_clase(cid))], spacing=0),
                            ]), bgcolor=COLOR_TEXTO_BLANCO, padding=15, border_radius=10, border=ft.border.all(1, "#E5E5EA")
                        )
                    )

            lista_bloqueos.controls.clear()
            try: bloqueos = AppDB.obtener_dias_bloqueados()
            except Exception: bloqueos = []
            if not bloqueos: lista_bloqueos.controls.append(ft.Text("No hay días cerrados programados.", color=COLOR_RESPIRO_DARK))
            for b in bloqueos:
                lista_bloqueos.controls.append(
                    ft.Container(
                        content=ft.Row(controls=[ft.Icon(ft.icons.BLOCK, color=ft.colors.RED_400), ft.Text(b["class_date"], weight=ft.FontWeight.BOLD), ft.Container(expand=True), ft.IconButton(icon=ft.icons.DELETE, icon_color=ft.colors.RED_400, on_click=lambda e, bid=b["id"]: (AppDB.desbloquear_dia(bid), recargar_listas()))]),
                        bgcolor=COLOR_TEXTO_BLANCO, padding=15, border_radius=10
                    )
                )
            page.update()

        def set_modo_30(e):
            modo_agenda[0] = "30"
            btn_modo_30.bgcolor, btn_modo_30.color, btn_modo_dia.bgcolor, btn_modo_dia.color = COLOR_RESPIRO, "white", "transparent", COLOR_RESPIRO
            recargar_listas()

        def set_modo_dia(e):
            modo_agenda[0] = "dia"
            btn_modo_dia.bgcolor, btn_modo_dia.color, btn_modo_30.bgcolor, btn_modo_30.color = COLOR_RESPIRO, "white", "transparent", COLOR_RESPIRO
            recargar_listas()

        btn_modo_30 = ft.ElevatedButton("30 Días", on_click=set_modo_30, bgcolor=COLOR_RESPIRO, color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))
        btn_modo_dia = ft.ElevatedButton("Día Específico", on_click=set_modo_dia, bgcolor="transparent", color=COLOR_RESPIRO, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))

        try: opciones_servicios = [ft.dropdown.Option(s["name"]) for s in AppDB.obtener_servicios()]
        except Exception: opciones_servicios = []
        drop_serv = ft.Dropdown(label="Servicio", options=opciones_servicios, border_color=COLOR_RESPIRO)
        drop_hora = ft.Dropdown(label="Horario", options=[ft.dropdown.Option("08:00 AM"), ft.dropdown.Option("09:15 AM"), ft.dropdown.Option("06:30 PM")], border_color=COLOR_RESPIRO)
        txt_inst = ft.TextField(label="Instructor", value="Staff", border_color=COLOR_RESPIRO, expand=True)
        txt_cupo = ft.TextField(label="Cupo", value="10", keyboard_type=ft.KeyboardType.NUMBER, border_color=COLOR_RESPIRO, width=100)
        
        lista_agenda = ft.ListView(expand=True, spacing=10)
        lista_bloqueos = ft.ListView(expand=True, spacing=10)

        dlg_detalles = ft.AlertDialog(title=ft.Text("Alumnos en la clase", color=COLOR_RESPIRO, weight=ft.FontWeight.BOLD), content=ft.Column(controls=[], scroll=ft.ScrollMode.AUTO, height=300, width=300), actions=[ft.TextButton("Cerrar", on_click=lambda _: setattr(dlg_detalles, "open", False) or page.update())])
        add_overlay_once(dlg_detalles)

        def ver_detalles_clase(cid):
            dlg_detalles.content.controls.clear()
            dlg_detalles.content.controls.append(ft.Container(content=ft.ProgressRing(color=COLOR_RESPIRO), alignment=ft.alignment.center, padding=20))
            dlg_detalles.open = True
            page.update()
            try: alumnos = AppDB.obtener_alumnos_clase(cid) if hasattr(AppDB, "obtener_alumnos_clase") else []
            except Exception: alumnos = []
            dlg_detalles.content.controls.clear()
            if not alumnos: dlg_detalles.content.controls.append(ft.Text("No hay alumnos inscritos aún.", color=COLOR_RESPIRO_DARK))
            else:
                dlg_detalles.content.controls.append(ft.Text(f"Total inscritos: {len(alumnos)}", weight=ft.FontWeight.BOLD))
                for al in alumnos:
                    nombre_al, estado_al = al.get("full_name", "Desconocido"), al.get("active_package", "Sin paquete")
                    color_icono = ft.colors.GREEN_600 if str(estado_al).lower() == "pagado" else ft.colors.ORANGE_600
                    dlg_detalles.content.controls.append(ft.ListTile(leading=ft.Icon(ft.icons.PERSON, color=color_icono), title=ft.Text(nombre_al, weight=ft.FontWeight.BOLD), subtitle=ft.Text(f"Estado: {str(estado_al).capitalize()}")))
            page.update()

        def borrar_clase(cid):
            try: AppDB.eliminar_clase(cid); recargar_listas(); mostrar_snack("Clase eliminada del sistema.", ft.colors.RED_500)
            except Exception: mostrar_snack("No se pudo eliminar la clase.", ft.colors.RED_500)

        def al_cambiar_fecha_admin(e):
            if dp_admin.value:
                v = dp_admin.value.date() if isinstance(dp_admin.value, datetime.datetime) else dp_admin.value
                fecha_activa[0] = v
                txt_fecha_top.value = fecha_activa[0].strftime("%Y-%m-%d")
                set_modo_dia(None)

        dp_admin = ft.DatePicker(on_change=al_cambiar_fecha_admin)
        add_overlay_once(dp_admin)
        def abrir_dp_admin(e=None):
            try: page.open(dp_admin)
            except Exception: dp_admin.open = True; page.update()

        def accion_publicar_clase(e):
            f_str = fecha_activa[0].strftime("%Y-%m-%d")
            try:
                if AppDB.es_dia_bloqueado(f_str): mostrar_snack("¡Error! Este día está marcado como Cerrado.", ft.colors.RED_500)
                elif AppDB.verificar_disponibilidad(f_str, drop_hora.value): mostrar_snack("¡Horario ocupado! Revisa la agenda.", ft.colors.RED_500)
                elif drop_serv.value and drop_hora.value:
                    AppDB.crear_clase(drop_serv.value, f_str, drop_hora.value, txt_inst.value, txt_cupo.value)
                    mostrar_snack("Clase creada.", ft.colors.GREEN_600)
                    drop_serv.value, drop_hora.value = None, None
                    recargar_listas()
                else: mostrar_snack("Selecciona servicio y horario.", ft.colors.ORANGE_500)
                page.update()
            except Exception: mostrar_snack("No se pudo crear la clase.", ft.colors.RED_500)

        txt_fecha_bloqueo = ft.TextField(label="Fecha a bloquear", hint_text="Toca el calendario ->", read_only=True, expand=True, border_color=COLOR_RESPIRO)
        def on_bloqueo_date_change(e):
            if dp_bloqueo.value:
                v = dp_bloqueo.value.date() if isinstance(dp_bloqueo.value, datetime.datetime) else dp_bloqueo.value
                txt_fecha_bloqueo.value = v.strftime("%Y-%m-%d")
                page.update()

        dp_bloqueo = ft.DatePicker(on_change=on_bloqueo_date_change, first_date=datetime.date.today())
        add_overlay_once(dp_bloqueo)
        def abrir_dp_bloqueo(e=None):
            try: page.open(dp_bloqueo)
            except Exception: dp_bloqueo.open = True; page.update()

        def accion_bloquear_dia(e):
            f_str = txt_fecha_bloqueo.value
            if f_str:
                try:
                    if not AppDB.es_dia_bloqueado(f_str):
                        AppDB.bloquear_dia(f_str); recargar_listas(); mostrar_snack(f"El día {f_str} ha sido bloqueado.", ft.colors.GREEN_600); txt_fecha_bloqueo.value = ""
                    else: mostrar_snack("Ese día ya está bloqueado.", ft.colors.ORANGE_500)
                except Exception: mostrar_snack("No se pudo bloquear la fecha.", ft.colors.RED_500)
            else: mostrar_snack("Por favor, selecciona una fecha en el calendario.", ft.colors.RED_500)
            page.update()

        recargar_listas()

        tab_crear = ft.Tab(text="Crear", icon=ft.icons.ADD_BOX, content=ft.Container(padding=20, content=ft.Column(controls=[ft.Text("Agendar Nueva Clase", size=18, weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO), ft.Container(height=10), drop_serv, drop_hora, ft.Row(controls=[txt_inst, txt_cupo]), ft.Container(height=20), ft.ElevatedButton("Publicar", bgcolor=COLOR_RESPIRO, color="white", width=300, height=50, on_click=accion_publicar_clase)])))
        tab_agenda = ft.Tab(text="Agenda", icon=ft.icons.FORMAT_LIST_BULLETED, content=ft.Container(padding=20, content=ft.Column(controls=[ft.Row(controls=[btn_modo_30, btn_modo_dia], spacing=10), ft.Container(height=10), lista_agenda])))
        tab_bloqueos = ft.Tab(text="Cierres", icon=ft.icons.BLOCK, content=ft.Container(padding=20, content=ft.Column(controls=[ft.Text("Días Inhábiles", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.RED_400), ft.Text("Elige cualquier fecha futura para cerrar el estudio.", size=12, color=COLOR_RESPIRO_DARK), ft.Container(height=10), ft.Row(controls=[txt_fecha_bloqueo, ft.IconButton(icon=ft.icons.CALENDAR_MONTH, icon_color=ft.colors.RED_400, icon_size=35, on_click=abrir_dp_bloqueo)]), ft.Container(height=10), ft.ElevatedButton("Bloquear Fecha", bgcolor=ft.colors.RED_400, color="white", width=300, height=50, on_click=accion_bloquear_dia), ft.Container(height=20), ft.Text("Próximos cierres:", weight=ft.FontWeight.BOLD), lista_bloqueos])))

        return ft.View(
            route="/admin", bgcolor=COLOR_BG_CLARO, padding=0,
            controls=[
                ft.Container(bgcolor="white", padding=ft.padding.only(left=10, right=20, top=20, bottom=10), shadow=ft.BoxShadow(blur_radius=5, color="#1A000000"), content=ft.Row(controls=[ft.IconButton(icon=ft.icons.ARROW_BACK, icon_color=COLOR_RESPIRO, on_click=lambda _: page.go("/login")), ft.Text("Admin", size=22, weight=ft.FontWeight.BOLD), ft.Container(expand=True), txt_fecha_top, ft.IconButton(icon=ft.icons.CALENDAR_MONTH, icon_color=COLOR_RESPIRO, on_click=abrir_dp_admin)])),
                ft.Tabs(selected_index=0, animation_duration=300, unselected_label_color=COLOR_RESPIRO_DARK, label_color=COLOR_RESPIRO, indicator_color=COLOR_RESPIRO, expand=True, tabs=[tab_crear, tab_agenda, tab_bloqueos])
            ]
        )

    def build_recargando_view():
        return ft.View(route="/recargando", bgcolor=COLOR_BG_CLARO, controls=[ft.Container(expand=True, alignment=ft.alignment.center, content=ft.ProgressRing(color=COLOR_RESPIRO))])

    # -------------------------------------------------------------------------
    # 5. ENRUTADOR CENTRAL CON INTERCEPTOR DE PANTALLA DE CARGA
    # -------------------------------------------------------------------------
    def route_change(e):
        # Mapeo universal de rutas limpiando parámetros basura de Openpay (?id=trx...)
        base_route = page.route.split("?")[0]
        
        page.views.clear()
        page.views.append(
            ft.View(
                route=base_route,
                bgcolor=COLOR_BG_CLARO,
                padding=0,
                controls=[
                    ft.Container(
                        expand=True,
                        alignment=ft.alignment.center,
                        content=ft.Column(
                            controls=[
                                ft.ProgressRing(width=45, height=45, color=COLOR_RESPIRO, stroke_width=4),
                                ft.Container(height=15),
                                ft.Text("Preparando tu espacio...", color=COLOR_RESPIRO_DARK, size=15, weight=ft.FontWeight.W_500)
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        )
                    )
                ]
            )
        )
        page.update()
        
        time.sleep(0.01)

        if not page.session.get("user_phone"):
            tel_guardado = cs_get("user_phone", "")
            if tel_guardado:
                page.session.set("user_phone", tel_guardado)
                page.session.set("user_name", cs_get("user_name", ""))
                page.session.set("monto_pendiente", cs_get("monto_pendiente", ""))
                
                if base_route in ["/login", "/"]:
                    if cs_get("monto_pendiente", ""):
                        base_route = "/pago/verificando"
                    else:
                        try:
                            usuario_rec = AppDB.verificar_usuario(tel_guardado)
                            if usuario_rec and str(usuario_rec.get("active_package", "")).lower().strip() == "pagado" and int(usuario_rec.get("credits", 0) or 0) > 0:
                                base_route = "/servicios"
                            else: 
                                base_route = "/paquetes"
                        except Exception as ex: 
                            print("Error recuperando usuario:", ex)

        rutas_estaticas = {
            "/login": build_login_view,
            "/formulario_ingreso": build_formulario_view,
            "/paquetes": build_paquetes_view,
            "/pago/verificando": build_verificando_view,
            "/servicios": build_servicios_view,
            "/perfil": build_perfil_view,
            "/admin": build_admin_view,
            "/recargando": build_recargando_view
        }

        if base_route in rutas_estaticas:
            nueva_vista = rutas_estaticas[base_route]()
        elif base_route.startswith("/pago/") and base_route != "/pago/verificando":
            monto = base_route.split("/")[2]
            nueva_vista = build_pago_view(monto)
        else:
            nueva_vista = build_login_view()

        page.views.clear()
        page.views.append(nueva_vista)
        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.go(page.views[-1].route.split("?")[0])
        else:
            page.go("/login")

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        port=port,
        host="0.0.0.0",
        assets_dir="assets",
    )
