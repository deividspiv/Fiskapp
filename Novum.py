import flet as ft
from flet_webview import WebView
from database import AppDB
from pagos import generar_enlace_pago
import time
import datetime

# --- PALETA DE COLORES "RESPIRO" ---
COLOR_RESPIRO = "#a3968d"
COLOR_RESPIRO_DARK = "#8e8279"
COLOR_CREMA_BOTON = "#dfd0c1"
COLOR_BG_CLARO = "#f4f2f1"
COLOR_TEXTO_OSCURO = "#4a4a4a"
COLOR_TEXTO_BLANCO = "#FFFFFF"

def main(page: ft.Page):
    page.title = "Novum Pilates"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Variables de Sesión
    page.session.set("is_logged_in", False)
    page.session.set("has_active_package", False)
    page.session.set("user_phone", "")
    page.session.set("monto_pendiente", "")

    # --- LÓGICA DE SINCRONIZACIÓN INVISIBLE ---
    def sync_creditos_silencioso(telefono):
        if not telefono:
            return
        try:
            u_sync = AppDB.verificar_usuario(telefono)
            if u_sync and str(u_sync.get('active_package', '')).lower().strip() == 'pagado':
                if u_sync.get('credits', 0) <= 0:
                    monto_guardado = None
                    try:
                        monto_guardado = page.client_storage.get("monto_pendiente")
                    except:
                        pass
                    monto = page.session.get("monto_pendiente") or monto_guardado
                    if monto:
                        nuevos_creditos = {"100": 1, "650": 8, "800": 12, "1000": 30}.get(str(monto), 0)
                        if nuevos_creditos > 0:
                            AppDB.asignar_creditos(telefono, nuevos_creditos)
                        page.session.set("monto_pendiente", "")
                        try:
                            page.client_storage.remove("monto_pendiente")
                        except:
                            pass
        except Exception as e:
            print("Error en sincronización silenciosa:", e)

    # --- DIÁLOGO ADMIN ---
    admin_pwd_field = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
        border_radius=10,
        border_color=COLOR_RESPIRO,
        cursor_color=COLOR_RESPIRO
    )

    def check_admin_pwd(e):
        if admin_pwd_field.value == "3157525":
            admin_dlg.open = False
            page.update()
            page.go("/admin")
        else:
            admin_pwd_field.error_text = "Contraseña incorrecta"
            page.update()

    admin_dlg = ft.AlertDialog(
        title=ft.Text("Acceso Administrativo", color=COLOR_RESPIRO),
        content=admin_pwd_field,
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _: setattr(admin_dlg, 'open', False) or page.update()),
            ft.ElevatedButton("Entrar", bgcolor=COLOR_RESPIRO, color=COLOR_TEXTO_BLANCO, on_click=check_admin_pwd)
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    page.overlay.append(admin_dlg)

    # --- TARJETAS DE PAQUETES ---
    def RespiroPricingCard(title, price, savings_text, features_list, package_id):
        features_ui = [
            ft.Row([
                ft.Icon(ft.icons.CHECK_CIRCLE_ROUNDED, size=16, color=COLOR_RESPIRO),
                ft.Text(feat, size=13, weight=ft.FontWeight.W_500, color=COLOR_TEXTO_OSCURO)
            ], spacing=8)
            for feat in features_list
        ]
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                ft.Text(price, size=34, weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO),
                ft.Text(savings_text, size=13, color=COLOR_RESPIRO_DARK),
                ft.Divider(height=30, color="#E5E5EA"),
                ft.Column(features_ui, spacing=10),
                ft.Container(height=10),
                ft.ElevatedButton(
                    content=ft.Text("Elegir paquete", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.W_600),
                    bgcolor=COLOR_RESPIRO,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
                    on_click=lambda _: page.go(f"/pago/{package_id}")
                )
            ]),
            bgcolor=COLOR_TEXTO_BLANCO,
            padding=25,
            border_radius=20,
            border=ft.border.all(1, "#E5E5EA"),
            width=280,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color="#1A000000", offset=ft.Offset(0, 8)),
        )

    # --- ENRUTAMIENTO PRINCIPAL ---
    def route_change(e):
        page.views.clear()

        # =====================================================================
        # 1. PORTADA
        # =====================================================================
        if page.route == "/login":
            page.views.append(ft.View("/login", bgcolor=COLOR_RESPIRO, padding=0, controls=[
                ft.Container(
                    expand=True,
                    padding=ft.padding.only(left=30, right=30, top=40, bottom=40),
                    content=ft.Column([
                        ft.Row([
                            ft.Container(expand=True),
                            ft.IconButton(
                                ft.icons.SETTINGS,
                                icon_color="white70",
                                on_click=lambda _: setattr(admin_dlg, 'open', True) or page.update()
                            )
                        ]),
                        ft.Container(height=0),
                        ft.Container(
                            content=ft.Image(src="logo_respiros.png", width=280, fit=ft.ImageFit.CONTAIN),
                            alignment=ft.alignment.center
                        ),
                        ft.Icon(ft.icons.SPA, size=100, color=COLOR_TEXTO_BLANCO),
                        ft.Text("Pilates/Yoga/Relax", size=36, color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.W_300),
                        ft.Container(expand=True),
                        ft.Text("Tu espacio de bienestar", size=17, color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.W_400),
                        ft.Text("Registrate y agenda tu cita", color="white70"),
                        ft.Container(height=40),
                        ft.Container(
                            content=ft.Text("Iniciar Sesión", color="#6b5b50", weight=ft.FontWeight.BOLD, size=15),
                            alignment=ft.alignment.center,
                            width=300, height=55,
                            bgcolor=COLOR_CREMA_BOTON,
                            border_radius=27,
                            shadow=ft.BoxShadow(blur_radius=10, color="#33000000", offset=ft.Offset(0, 4)),
                            on_click=lambda _: page.go("/formulario_ingreso")
                        ),
                        ft.Container(height=10),
                        ft.TextButton(
                            content=ft.Text("¿Nuevo? Regístrate aquí", color="white", size=14, weight=ft.FontWeight.W_300),
                            on_click=lambda _: page.go("/formulario_ingreso")
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            ]))

        # =====================================================================
        # 1.5 FORMULARIO
        # =====================================================================
        elif page.route == "/formulario_ingreso":
            nombre_field = ft.TextField(
                label="Nombre completo", border_radius=10,
                prefix_icon=ft.icons.PERSON,
                border_color=COLOR_RESPIRO, cursor_color=COLOR_RESPIRO
            )
            celular_field = ft.TextField(
                label="Número celular (10 dígitos)", border_radius=10,
                prefix_icon=ft.icons.PHONE,
                keyboard_type=ft.KeyboardType.PHONE,
                border_color=COLOR_RESPIRO, cursor_color=COLOR_RESPIRO
            )

            def do_login(e):
                if nombre_field.value and celular_field.value:
                    e.control.content = ft.ProgressRing(width=20, height=20, color=COLOR_TEXTO_BLANCO, stroke_width=2)
                    e.control.update()
                    usuario = AppDB.verificar_usuario(celular_field.value)
                    if not usuario:
                        AppDB.registrar_usuario(celular_field.value, nombre_field.value)
                        nombre_final = nombre_field.value
                    else:
                        nombre_final = usuario.get('full_name', nombre_field.value)

                    sync_creditos_silencioso(celular_field.value)
                    usuario_actualizado = AppDB.verificar_usuario(celular_field.value)
                    tiene_paquete_activo = False
                    if usuario_actualizado and str(usuario_actualizado.get('active_package', '')).lower().strip() == 'pagado':
                        if usuario_actualizado.get('credits', 0) > 0:
                            tiene_paquete_activo = True

                    e.control.content = ft.Text("Continuar", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.W_600)
                    e.control.update()
                    page.session.set("user_phone", celular_field.value)
                    page.session.set("user_name", nombre_final)
                    page.session.set("has_active_package", tiene_paquete_activo)
                    page.go("/servicios" if tiene_paquete_activo else "/paquetes")

            page.views.append(ft.View(
                "/formulario_ingreso",
                bgcolor=COLOR_TEXTO_BLANCO,
                padding=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row([
                        ft.IconButton(ft.icons.ARROW_BACK_IOS_NEW, icon_color=COLOR_RESPIRO,
                                      on_click=lambda _: page.go("/login")),
                        ft.Container(expand=True)
                    ]),
                    ft.Container(height=20),
                    ft.Icon(ft.icons.SPA, size=80, color=COLOR_RESPIRO),
                    ft.Text("Tus Datos", size=32, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                    ft.Text("Ingresa para ver tus reservaciones", size=16, color=COLOR_RESPIRO_DARK,
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(height=30),
                    nombre_field,
                    celular_field,
                    ft.Container(height=30),
                    ft.ElevatedButton(
                        "Continuar",
                        bgcolor=COLOR_RESPIRO, color=COLOR_TEXTO_BLANCO,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                        width=300, height=50,
                        on_click=do_login
                    )
                ]
            ))

        # =====================================================================
        # 2. PAQUETES
        # =====================================================================
        elif page.route == "/paquetes":
            paquetes_db = AppDB.obtener_paquetes()
            lista_tarjetas = [ft.Container(width=10)]
            for pq in paquetes_db:
                creditos_texto = f"{pq['credits']} clases a elegir" if pq.get('credits') else "Clases ilimitadas"
                precio_entero = int(pq['price'])
                lista_tarjetas.append(RespiroPricingCard(
                    pq["name"], f"${precio_entero}",
                    f"Vigencia: {pq['validity_days']} días",
                    [creditos_texto, "Reserva desde la app"],
                    str(precio_entero)
                ))
            lista_tarjetas.append(ft.Container(width=10))

            page.views.append(ft.View("/paquetes", bgcolor=COLOR_BG_CLARO, padding=0, controls=[
                ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Container(height=20),
                        ft.Text("Elige tu plan", size=34, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                        ft.Text("Selecciona el paquete que mejor se adapte a tu rutina.",
                                size=16, color=COLOR_RESPIRO_DARK)
                    ])
                ),
                ft.Container(height=450, content=ft.ListView(lista_tarjetas, horizontal=True, spacing=15))
            ]))

        # =====================================================================
        # 3. PAGOS CON WEBVIEW EMBEBIDO — SIN SALIR DE LA APP
        # =====================================================================
        elif page.route.startswith("/pago/") and not page.route.endswith("/verificando"):
            monto = page.route.split("/")[2]
            page.session.set("monto_pendiente", monto)

            estado = {
                "link_generado": None,
                "webview_activo": False,
            }

            # ── Barra superior del banco ──────────────────────────────────
            barra_banco = ft.Container(
                visible=False,
                bgcolor="#004481",
                padding=ft.padding.only(left=6, right=16, top=44, bottom=10),
                content=ft.Row([
                    ft.IconButton(
                        ft.icons.CLOSE,
                        icon_color=COLOR_TEXTO_BLANCO,
                        tooltip="Volver al checkout",
                        on_click=lambda _: cerrar_webview(),
                    ),
                    ft.Column([
                        ft.Text("Pago Seguro", color=COLOR_TEXTO_BLANCO,
                                weight=ft.FontWeight.BOLD, size=15),
                        ft.Text("bbva.mx", color="white60", size=11),
                    ], spacing=0),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.Icon(ft.icons.LOCK, color=ft.colors.GREEN_300, size=14),
                        ft.Text("Seguro", color=ft.colors.GREEN_300, size=12),
                    ], spacing=4),
                ]),
            )

            # ── WebView del banco (flet-webview) ──────────────────────────
            web_view = WebView(
                url="about:blank",
                expand=True,
                visible=False,
                javascript_enabled=True,
                on_page_started=lambda e: on_navegacion(e.url if hasattr(e, "url") else ""),
                on_page_ended=lambda e: on_navegacion(e.url if hasattr(e, "url") else ""),
                on_url_change=lambda e: on_navegacion(e.url if hasattr(e, "url") else ""),
            )

            # ── Spinner mientras carga el banco ───────────────────────────
            cargando_banco = ft.Container(
                visible=False,
                expand=True,
                bgcolor=COLOR_TEXTO_BLANCO,
                content=ft.Column([
                    ft.ProgressRing(color=COLOR_RESPIRO, width=50, height=50, stroke_width=4),
                    ft.Container(height=20),
                    ft.Text("Conectando con el banco...", color=COLOR_RESPIRO_DARK, size=15),
                    ft.Text("Por favor espera", color=COLOR_RESPIRO_DARK, size=13),
                ], alignment=ft.MainAxisAlignment.CENTER,
                   horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            )

            # ── Botón BBVA ────────────────────────────────────────────────
            icono_btn = ft.Icon(ft.icons.CREDIT_CARD, color=COLOR_TEXTO_BLANCO)
            texto_btn = ft.Text("Pagar en línea (BBVA)", color=COLOR_TEXTO_BLANCO,
                                weight=ft.FontWeight.BOLD)
            fila_btn = ft.Row([icono_btn, texto_btn], alignment=ft.MainAxisAlignment.CENTER)
            btn_bbva = ft.Container(
                content=fila_btn,
                bgcolor="#004481",
                padding=15,
                border_radius=12,
            )

            # ── Checkout normal ───────────────────────────────────────────
            checkout_col = ft.Column([
                ft.Container(height=10),
                ft.Row([
                    ft.IconButton(ft.icons.ARROW_BACK_IOS_NEW, icon_color=COLOR_RESPIRO,
                                  on_click=lambda _: page.go("/paquetes")),
                    ft.Text("Checkout", size=24, weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXTO_OSCURO),
                ]),
                ft.Container(height=30),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.SHOPPING_BAG_OUTLINED, size=48, color=COLOR_RESPIRO),
                        ft.Container(height=8),
                        ft.Text("Total a pagar", size=14, color=COLOR_RESPIRO_DARK),
                        ft.Text(f"${monto}.00 MXN", size=36,
                                weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=COLOR_BG_CLARO,
                    border_radius=16,
                    padding=ft.padding.symmetric(vertical=24),
                    width=float("inf"),
                ),
                ft.Container(height=30),
                ft.Text("Selecciona tu método de pago", size=14,
                        weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO_DARK),
                ft.Container(height=12),
                btn_bbva,
                ft.Container(height=12),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.STORE, color=COLOR_TEXTO_OSCURO),
                        ft.Text("Pagar en Recepción", color=COLOR_TEXTO_OSCURO,
                                weight=ft.FontWeight.BOLD),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor=COLOR_BG_CLARO,
                    padding=15,
                    border_radius=12,
                    on_click=lambda e: (
                        page.overlay.append(
                            ft.SnackBar(
                                ft.Text("Solicitud enviada. Paga en recepción.",
                                        color=COLOR_TEXTO_BLANCO),
                                bgcolor=COLOR_RESPIRO
                            )
                        ),
                        setattr(page.overlay[-1], "open", True),
                        page.update(),
                    ),
                ),
            ], scroll=ft.ScrollMode.AUTO)

            checkout_container = ft.Container(
                content=checkout_col,
                expand=True,
                padding=20,
                visible=True,
            )

            # ── Lógica de navegación del WebView ──────────────────────────
            def on_navegacion(url: str):
                if not url:
                    return
                url_lower = url.lower()
                keywords_exito = [
                    "exito", "success", "gracias", "confirmacion",
                    "paid", "approved", "completado", "thankyou",
                    "thank-you", "pago-exitoso",
                ]
                if any(k in url_lower for k in keywords_exito):
                    page.session.set("monto_pendiente", monto)
                    try:
                        page.client_storage.set("monto_pendiente", str(monto))
                    except Exception:
                        pass
                    page.go("/pago/verificando")

            def cerrar_webview():
                barra_banco.visible = False
                web_view.visible = False
                cargando_banco.visible = False
                checkout_container.visible = True
                estado["webview_activo"] = False
                fila_btn.controls.clear()
                fila_btn.controls.append(ft.Icon(ft.icons.CREDIT_CARD, color=COLOR_TEXTO_BLANCO))
                fila_btn.controls.append(
                    ft.Text("Pagar en línea (BBVA)", color=COLOR_TEXTO_BLANCO,
                            weight=ft.FontWeight.BOLD)
                )
                btn_bbva.bgcolor = "#004481"
                btn_bbva.on_click = pagar_bbva
                page.update()

            def abrir_webview(link: str):
                checkout_container.visible = False
                cargando_banco.visible = True
                page.update()
                web_view.url = link
                web_view.visible = True
                barra_banco.visible = True
                cargando_banco.visible = False
                estado["webview_activo"] = True
                page.update()

            def pagar_bbva(e):
                fila_btn.controls.clear()
                fila_btn.controls.append(
                    ft.ProgressRing(width=20, height=20, color=COLOR_TEXTO_BLANCO, stroke_width=2)
                )
                fila_btn.controls.append(
                    ft.Text(" Conectando...", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD)
                )
                btn_bbva.on_click = None
                page.update()

                telefono = page.session.get("user_phone")
                nombre = page.session.get("user_name")

                try:
                    AppDB.crear_registro_pago(telefono, monto)
                except Exception:
                    pass
                try:
                    page.client_storage.set("monto_pendiente", str(monto))
                except Exception:
                    pass

                link = generar_enlace_pago(
                    monto,
                    f"Paquete Novum Pilates {monto}",
                    nombre,
                    telefono,
                )

                if link:
                    estado["link_generado"] = link
                    abrir_webview(link)
                else:
                    fila_btn.controls.clear()
                    fila_btn.controls.append(
                        ft.Icon(ft.icons.ERROR_OUTLINE, color=COLOR_TEXTO_BLANCO)
                    )
                    fila_btn.controls.append(
                        ft.Text("Error al conectar. Toca para reintentar.",
                                color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD)
                    )
                    btn_bbva.bgcolor = ft.colors.RED_600
                    btn_bbva.on_click = pagar_bbva
                    page.update()

            btn_bbva.on_click = pagar_bbva

            # ── Vista final: Stack con todas las capas ────────────────────
            page.views.append(ft.View(
                page.route,
                bgcolor=COLOR_TEXTO_BLANCO,
                padding=0,
                controls=[
                    ft.Stack(
                        expand=True,
                        controls=[
                            checkout_container,
                            cargando_banco,
                            ft.Column(
                                [barra_banco, web_view],
                                spacing=0,
                                expand=True
                            ),
                        ],
                    )
                ],
            ))

        # =====================================================================
        # 3.5 VERIFICANDO PAGO
        # =====================================================================
        elif page.route == "/pago/verificando":
            estado_ui = ft.Container(
                content=ft.Column([
                    ft.ProgressRing(width=60, height=60, color=COLOR_RESPIRO, stroke_width=4),
                    ft.Container(height=20),
                    ft.Text("Aprobando automáticamente...", size=16, color=COLOR_RESPIRO_DARK)
                ], alignment=ft.MainAxisAlignment.CENTER,
                   horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                height=300
            )

            def auto_check_payment():
                telefono_alumno = page.session.get("user_phone")
                if not telefono_alumno:
                    return
                for _ in range(60):
                    if page.route != "/pago/verificando":
                        break
                    time.sleep(2)
                    try:
                        u = AppDB.verificar_usuario(telefono_alumno)
                        if u and str(u.get('active_package', '')).lower().strip() == 'pagado':
                            sync_creditos_silencioso(telefono_alumno)
                            page.session.set("monto_pendiente", "")
                            page.go("/servicios")
                            return
                    except Exception:
                        pass

            page.run_task(auto_check_payment)

            def verificar_estado_pago_manual(e):
                telefono_alumno = page.session.get("user_phone")
                sync_creditos_silencioso(telefono_alumno)
                page.session.set("monto_pendiente", "")
                page.go("/servicios")

            btn_accion = ft.ElevatedButton(
                "Comprobar Manualmente",
                color=COLOR_TEXTO_BLANCO,
                bgcolor=COLOR_RESPIRO,
                width=300, height=50,
                on_click=verificar_estado_pago_manual
            )
            page.views.append(ft.View(
                "/pago/verificando",
                bgcolor=COLOR_TEXTO_BLANCO,
                padding=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(height=50),
                    ft.Text("Checkout Seguro", size=24, weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXTO_OSCURO),
                    ft.Container(height=40),
                    estado_ui,
                    ft.Container(height=40),
                    btn_accion
                ]
            ))

        # =====================================================================
        # 4. SERVICIOS Y AGENDA ALUMNO
        # =====================================================================
        elif page.route == "/servicios":
            telefono_alumno = page.session.get("user_phone")
            sync_creditos_silencioso(telefono_alumno)

            nombre_usuario = page.session.get('user_name')
            primer_nombre = nombre_usuario.split()[0] if nombre_usuario else 'Alumno'
            inicial = primer_nombre[0].upper() if primer_nombre else "A"
            hoy = datetime.date.today()
            vista_estado = {"fecha_activa": hoy, "servicio_activo": "Pilates"}

            servicios_ui = ft.Row(spacing=10, scroll=ft.ScrollMode.HIDDEN)
            dias_ui = ft.Row(spacing=15, scroll=ft.ScrollMode.HIDDEN)
            horarios_ui = ft.Column(spacing=15)

            def recargar_pantalla():
                horarios_ui.controls.clear()
                horarios_ui.controls.append(
                    ft.Container(content=ft.ProgressRing(color=COLOR_RESPIRO),
                                 alignment=ft.alignment.center, padding=40)
                )
                page.update()

                mis_reservas = AppDB.obtener_reservas_usuario(telefono_alumno)
                fechas_reservadas_limpias = []
                clases_agendadas = []
                for r in mis_reservas:
                    if r.get("estado", "").lower() == "futura":
                        clases_agendadas.append(r.get("class_id"))
                        f_raw = str(r.get("class_date") or r.get("fecha", "")).strip()
                        if " " in f_raw:
                            f_raw = f_raw.split(" ")[0]
                        fechas_reservadas_limpias.append(f_raw)

                servicios_ui.controls.clear()
                for serv in ["Pilates", "Yoga", "Ejercicios Funcionales"]:
                    es_activo = (serv == vista_estado["servicio_activo"])
                    servicios_ui.controls.append(ft.Container(
                        content=ft.Text(serv, weight=ft.FontWeight.BOLD,
                                        color=COLOR_TEXTO_BLANCO if es_activo else COLOR_RESPIRO),
                        bgcolor=COLOR_RESPIRO if es_activo else COLOR_TEXTO_BLANCO,
                        padding=ft.padding.symmetric(horizontal=20, vertical=10),
                        border_radius=20,
                        border=ft.border.all(1, COLOR_RESPIRO) if not es_activo else None,
                        on_click=lambda e, s=serv: al_seleccionar_servicio(s)
                    ))

                dias_ui.controls.clear()
                nombres_dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
                for i in range(14):
                    fecha_iter = hoy + datetime.timedelta(days=i)
                    es_dia_seleccionado = (fecha_iter == vista_estado["fecha_activa"])
                    bg_color = COLOR_RESPIRO if es_dia_seleccionado else COLOR_TEXTO_BLANCO
                    text_color = COLOR_TEXTO_BLANCO if es_dia_seleccionado else COLOR_TEXTO_OSCURO

                    dia_str = fecha_iter.strftime("%Y-%m-%d")
                    tiene_reserva_hoy = False
                    for f_res in fechas_reservadas_limpias:
                        if dia_str in f_res or f_res in dia_str:
                            tiene_reserva_hoy = True
                            break

                    col_dia = [
                        ft.Text(nombres_dias[fecha_iter.weekday()], size=14,
                                color=text_color, weight=ft.FontWeight.W_500),
                        ft.Text(str(fecha_iter.day), size=20,
                                color=text_color, weight=ft.FontWeight.BOLD)
                    ]
                    if tiene_reserva_hoy:
                        col_dia.append(ft.Icon(ft.icons.CHECK_CIRCLE, color=text_color, size=12))
                    else:
                        col_dia.append(ft.Container(height=12))

                    dias_ui.controls.append(ft.Container(
                        content=ft.Column(col_dia, alignment=ft.MainAxisAlignment.CENTER,
                                          horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                        bgcolor=bg_color,
                        width=65, height=85,
                        border_radius=15,
                        border=ft.border.all(1, "#E5E5EA") if not es_dia_seleccionado else None,
                        on_click=lambda e, f=fecha_iter: al_seleccionar_dia(f)
                    ))

                horarios_ui.controls.clear()
                fecha_str = str(vista_estado["fecha_activa"])

                if AppDB.es_dia_bloqueado(fecha_str):
                    horarios_ui.controls.append(ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.NIGHTLIGHT_ROUND, size=50, color=COLOR_RESPIRO),
                            ft.Text("Estudio Cerrado", size=20, weight=ft.FontWeight.BOLD,
                                    color=COLOR_TEXTO_OSCURO),
                            ft.Text("Tómate un descanso. Nos vemos pronto.",
                                    text_align=ft.TextAlign.CENTER, color=COLOR_RESPIRO_DARK)
                        ], alignment=ft.MainAxisAlignment.CENTER,
                           horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=COLOR_TEXTO_BLANCO,
                        padding=40, border_radius=15, width=float('inf')
                    ))
                else:
                    clases_del_dia = AppDB.obtener_clases(vista_estado["servicio_activo"], fecha_str)

                    dia_ya_reservado = False
                    for f_res in fechas_reservadas_limpias:
                        if fecha_str in f_res or f_res in fecha_str:
                            dia_ya_reservado = True
                            break

                    if not clases_del_dia:
                        horarios_ui.controls.append(
                            ft.Text(f"No hay clases de {vista_estado['servicio_activo']} programadas.",
                                    color=COLOR_RESPIRO_DARK)
                        )

                    for h in clases_del_dia:
                        is_full = h["cupo"] <= 0
                        ya_agendado = h["id"] in clases_agendadas

                        if ya_agendado:
                            btn_color = ft.colors.GREEN_500
                            btn_text = "Agendado ✓"
                            text_btn_color = COLOR_TEXTO_BLANCO
                            accion_btn = lambda _: page.go("/perfil")
                        elif dia_ya_reservado:
                            btn_color = "#E5E5EA"
                            btn_text = "Día Reservado"
                            text_btn_color = COLOR_RESPIRO_DARK
                            accion_btn = None
                        else:
                            btn_color = "#E5E5EA" if is_full else COLOR_CREMA_BOTON
                            btn_text = "Lleno" if is_full else "Reservar"
                            text_btn_color = COLOR_RESPIRO_DARK if is_full else "#6b5b50"
                            accion_btn = (lambda e, c=h: confirmar_reserva(c)) if not is_full else None

                        horarios_ui.controls.append(ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(h["hora"], size=18, weight=ft.FontWeight.BOLD,
                                            color=COLOR_TEXTO_OSCURO),
                                    ft.Text(f"Prof: {h['instructor']}", size=13, color=COLOR_RESPIRO_DARK),
                                    ft.Text(f"Lugares: {h['cupo']}", size=12,
                                            color=COLOR_RESPIRO if not is_full else ft.colors.RED_400)
                                ], spacing=2),
                                ft.Container(expand=True),
                                ft.Container(
                                    content=ft.Text(btn_text, weight=ft.FontWeight.BOLD,
                                                    color=text_btn_color, size=13),
                                    bgcolor=btn_color,
                                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                                    border_radius=20,
                                    on_click=accion_btn
                                )
                            ]),
                            bgcolor=COLOR_TEXTO_BLANCO,
                            padding=20, border_radius=15,
                            shadow=ft.BoxShadow(blur_radius=10, color="#0A000000", offset=ft.Offset(0, 4))
                        ))
                page.update()

            def al_seleccionar_dia(nueva_fecha):
                vista_estado["fecha_activa"] = nueva_fecha
                recargar_pantalla()

            def al_seleccionar_servicio(nuevo_servicio):
                vista_estado["servicio_activo"] = nuevo_servicio
                recargar_pantalla()

            def confirmar_reserva(clase):
                usuario_actual = AppDB.verificar_usuario(telefono_alumno)
                if (usuario_actual.get('credits', 0) if usuario_actual else 0) <= 0:
                    page.go("/paquetes")
                    return
                if AppDB.reservar_clase(telefono_alumno, clase["id"]):
                    snack = ft.SnackBar(
                        ft.Text("¡Reserva confirmada! Se descontó 1 clase."),
                        bgcolor=ft.colors.GREEN_600
                    )
                    page.overlay.append(snack)
                    snack.open = True
                    recargar_pantalla()

            recargar_pantalla()

            avatar_perfil = ft.Container(
                content=ft.Text(inicial, size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_BLANCO),
                alignment=ft.alignment.center,
                width=45, height=45,
                bgcolor=COLOR_RESPIRO,
                shape=ft.BoxShape.CIRCLE,
                shadow=ft.BoxShadow(blur_radius=5, color="#33000000", offset=ft.Offset(0, 2)),
                on_click=lambda _: page.go("/perfil")
            )

            page.views.append(ft.View(
                "/servicios",
                bgcolor=COLOR_BG_CLARO,
                padding=20,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(height=10),
                    ft.Row([
                        ft.Column([
                            ft.Text(f"Hola, {primer_nombre} 👋", size=26,
                                    weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                            ft.Text("Reserva tu próxima clase", size=15, color=COLOR_RESPIRO_DARK)
                        ], spacing=0),
                        ft.Container(expand=True),
                        avatar_perfil
                    ]),
                    ft.Container(height=25),
                    servicios_ui,
                    ft.Container(height=25),
                    dias_ui,
                    ft.Container(height=25),
                    ft.Text("Horarios Disponibles", size=16, weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXTO_OSCURO),
                    ft.Container(height=10),
                    horarios_ui,
                    ft.Container(height=40)
                ]
            ))

        # =====================================================================
        # 4.5 HISTORIAL Y PERFIL
        # =====================================================================
        elif page.route == "/perfil":
            telefono_alumno = page.session.get("user_phone")
            sync_creditos_silencioso(telefono_alumno)

            usuario = AppDB.verificar_usuario(telefono_alumno)
            clases_restantes = usuario.get('credits', 0) if usuario else 0
            mis_reservas = AppDB.obtener_reservas_usuario(telefono_alumno)

            seccion_sin_creditos = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.ORANGE_500, size=40),
                    ft.Text("¡Te has quedado sin clases!", size=18, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton("Comprar Paquete", bgcolor=COLOR_RESPIRO, color="white",
                                      on_click=lambda _: page.go("/paquetes"))
                ], alignment="center"),
                bgcolor="white", padding=20, border_radius=15,
                margin=ft.margin.only(bottom=20)
            ) if clases_restantes <= 0 else ft.Container()

            def forzar_recarga_perfil():
                page.route = "/recargando"
                page.update()
                page.go("/perfil")

            def refrescar_creditos_click(e):
                e.control.content = ft.ProgressRing(width=20, height=20, color=COLOR_RESPIRO)
                e.control.update()
                u_sync = AppDB.verificar_usuario(telefono_alumno)

                monto_guardado = None
                try:
                    monto_guardado = page.client_storage.get("monto_pendiente")
                except:
                    pass

                monto = page.session.get("monto_pendiente") or monto_guardado

                if u_sync and str(u_sync.get('active_package', '')).lower().strip() == 'pagado':
                    if u_sync.get('credits', 0) <= 0 and monto:
                        nuevos_creditos = {"100": 1, "650": 8, "800": 12, "1000": 30}.get(str(monto), 0)
                        if nuevos_creditos > 0:
                            AppDB.asignar_creditos(telefono_alumno, nuevos_creditos)
                        page.session.set("monto_pendiente", "")
                        try:
                            page.client_storage.remove("monto_pendiente")
                        except:
                            pass
                    snack = ft.SnackBar(ft.Text("¡Tus clases han sido sincronizadas!"),
                                        bgcolor=ft.colors.GREEN_600)
                else:
                    snack = ft.SnackBar(ft.Text("Aún no detectamos tu pago en la base de datos."),
                                        bgcolor=ft.colors.ORANGE_600)
                page.overlay.append(snack)
                snack.open = True
                forzar_recarga_perfil()

            boton_refrescar = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.REFRESH, color=COLOR_RESPIRO, size=20),
                    ft.Text("¿Pagaste y no ves tus clases? Toca aquí",
                            color=COLOR_RESPIRO, size=13, weight=ft.FontWeight.BOLD)
                ], alignment="center"),
                padding=12,
                border=ft.border.all(1, COLOR_RESPIRO),
                border_radius=10,
                on_click=refrescar_creditos_click,
                margin=ft.margin.only(bottom=15)
            )

            reserva_a_cancelar = [None]
            aplica_penalizacion = [False]

            def ejecutar_cancelacion_final(e):
                rid = reserva_a_cancelar[0]
                penalizar = aplica_penalizacion[0]
                dlg_cancelar.open = False
                contenedor_reservas.content = ft.Container(
                    content=ft.Column([
                        ft.ProgressRing(color=COLOR_RESPIRO),
                        ft.Text("Procesando cancelación...", color=COLOR_RESPIRO_DARK)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    height=200
                )
                page.update()

                AppDB.cancelar_reserva(rid)
                if not penalizar:
                    u_actual = AppDB.verificar_usuario(telefono_alumno)
                    creditos_previos = u_actual.get('credits', 0) if u_actual else 0
                    AppDB.asignar_creditos(telefono_alumno, creditos_previos + 1)

                msg = ("Sesión cancelada. Se aplicó la penalidad de 12hrs."
                       if penalizar else
                       "Sesión cancelada. Se devolvió 1 clase a tu cuenta.")
                snack = ft.SnackBar(
                    ft.Text(msg),
                    bgcolor=ft.colors.ORANGE_600 if penalizar else ft.colors.GREEN_600
                )
                page.overlay.append(snack)
                snack.open = True
                forzar_recarga_perfil()

            dlg_cancelar = ft.AlertDialog(
                title=ft.Text("Cancelar Sesión", weight=ft.FontWeight.BOLD),
                content=ft.Text(""),
                actions=[
                    ft.TextButton("Volver",
                                  on_click=lambda _: setattr(dlg_cancelar, 'open', False) or page.update()),
                    ft.ElevatedButton("Sí, Cancelar", bgcolor=ft.colors.RED_500, color="white",
                                      on_click=ejecutar_cancelacion_final)
                ]
            )
            page.overlay.append(dlg_cancelar)

            def preparar_cancelacion(res):
                reserva_a_cancelar[0] = res.get("id")
                es_penalizable = False
                try:
                    c_date = res.get("class_date") or res.get("fecha")
                    s_time = res.get("start_time") or res.get("hora")
                    if c_date and s_time:
                        dt_str = f"{c_date.split()[0]} {s_time.strip()}"
                        try:
                            dt_clase = datetime.datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
                        except ValueError:
                            dt_clase = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                        ahora_mexico = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
                        horas_diff = (dt_clase - ahora_mexico).total_seconds() / 3600
                        if 0 < horas_diff <= 12:
                            es_penalizable = True
                except Exception as ex:
                    print("Error calculando tiempo:", ex)

                aplica_penalizacion[0] = es_penalizable
                if es_penalizable:
                    dlg_cancelar.content = ft.Text(
                        "Faltan menos de 12 horas para tu clase. Si cancelas ahora perderás esta clase "
                        "según nuestra política.\n\n¿Deseas cancelarla de todos modos?",
                        color=ft.colors.RED_600
                    )
                else:
                    dlg_cancelar.content = ft.Text(
                        "¿Estás seguro de que deseas cancelar tu clase?\n\n"
                        "Tu crédito será devuelto automáticamente a tu perfil."
                    )
                dlg_cancelar.open = True
                page.update()

            lista_reservas_ui = ft.Column(spacing=15)
            for res in mis_reservas:
                is_futura = res.get("estado", "").lower() == "futura"
                fila_superior = ft.Row([
                    ft.Text(res.get("servicio", "Clase"), size=16,
                            weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                    ft.Container(expand=True),
                    ft.Text(res.get("estado", "").capitalize(), size=12,
                            color=COLOR_RESPIRO if is_futura else COLOR_RESPIRO_DARK,
                            weight=ft.FontWeight.BOLD)
                ])
                elementos_tarjeta = [
                    fila_superior,
                    ft.Text(res.get("fecha", ""), size=14, color=COLOR_RESPIRO_DARK)
                ]
                if is_futura:
                    elementos_tarjeta.append(ft.Row([
                        ft.Container(expand=True),
                        ft.TextButton(
                            "Cancelar Clase",
                            icon=ft.icons.CANCEL,
                            style=ft.ButtonStyle(color=ft.colors.RED_400),
                            on_click=lambda e, r=res: preparar_cancelacion(r)
                        )
                    ]))
                lista_reservas_ui.controls.append(ft.Container(
                    content=ft.Column(elementos_tarjeta, spacing=5),
                    bgcolor="white", padding=20, border_radius=15,
                    shadow=ft.BoxShadow(blur_radius=5, color="#0A000000", offset=ft.Offset(0, 2))
                ))

            if not mis_reservas:
                lista_reservas_ui.controls.append(
                    ft.Text("Aún no tienes historial de reservas.", color=COLOR_RESPIRO_DARK)
                )
            contenedor_reservas = ft.Container(content=lista_reservas_ui)

            page.views.append(ft.View(
                "/perfil",
                bgcolor=COLOR_BG_CLARO,
                padding=20,
                scroll="auto",
                controls=[
                    ft.Row([
                        ft.IconButton(ft.icons.ARROW_BACK_IOS_NEW, icon_color=COLOR_RESPIRO,
                                      on_click=lambda _: page.go("/servicios")),
                        ft.Text("Mi Perfil", size=24, weight="bold", color=COLOR_TEXTO_OSCURO)
                    ]),
                    boton_refrescar,
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text("Clases Restantes", size=14, color=COLOR_TEXTO_OSCURO),
                                ft.Text(f"{clases_restantes}", size=40, weight="bold", color=COLOR_RESPIRO)
                            ]),
                            ft.Container(expand=True),
                            ft.Icon(ft.icons.FITNESS_CENTER, size=40, color=COLOR_RESPIRO)
                        ]),
                        bgcolor="white", padding=25, border_radius=15,
                        shadow=ft.BoxShadow(blur_radius=5, color="#0A000000")
                    ),
                    ft.Container(height=20),
                    seccion_sin_creditos,
                    ft.Text("Tus Reservas", size=18, weight="bold", color=COLOR_TEXTO_OSCURO),
                    contenedor_reservas,
                    ft.Container(height=30),
                    ft.TextButton(
                        "Cerrar Sesión",
                        icon=ft.icons.LOGOUT,
                        style=ft.ButtonStyle(color=ft.colors.RED_400),
                        on_click=lambda _: page.go("/login")
                    )
                ]
            ))

        # =====================================================================
        # 5. PANEL ADMIN
        # =====================================================================
        elif page.route == "/admin":
            fecha_activa = [datetime.date.today()]
            txt_fecha_top = ft.Text(fecha_activa[0].strftime("%Y-%m-%d"), size=18,
                                    weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO)
            modo_agenda = ["30"]

            def set_modo_30(e):
                modo_agenda[0] = "30"
                btn_modo_30.bgcolor, btn_modo_30.color = COLOR_RESPIRO, "white"
                btn_modo_dia.bgcolor, btn_modo_dia.color = "transparent", COLOR_RESPIRO
                recargar_listas()

            def set_modo_dia(e):
                modo_agenda[0] = "dia"
                btn_modo_dia.bgcolor, btn_modo_dia.color = COLOR_RESPIRO, "white"
                btn_modo_30.bgcolor, btn_modo_30.color = "transparent", COLOR_RESPIRO
                recargar_listas()

            btn_modo_30 = ft.ElevatedButton(
                "30 Días", on_click=set_modo_30, bgcolor=COLOR_RESPIRO, color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            )
            btn_modo_dia = ft.ElevatedButton(
                "Día Específico", on_click=set_modo_dia, bgcolor="transparent", color=COLOR_RESPIRO,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            )

            opciones_servicios = [ft.dropdown.Option(s["name"]) for s in AppDB.obtener_servicios()]
            drop_serv = ft.Dropdown(label="Servicio", options=opciones_servicios, border_color=COLOR_RESPIRO)
            drop_hora = ft.Dropdown(
                label="Horario",
                options=[
                    ft.dropdown.Option("08:00 AM"),
                    ft.dropdown.Option("09:15 AM"),
                    ft.dropdown.Option("06:30 PM")
                ],
                border_color=COLOR_RESPIRO
            )
            txt_inst = ft.TextField(label="Instructor", value="Staff",
                                    border_color=COLOR_RESPIRO, expand=True)
            txt_cupo = ft.TextField(label="Cupo", value="10",
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    border_color=COLOR_RESPIRO, width=100)

            lista_agenda = ft.ListView(expand=True, spacing=10)
            lista_bloqueos = ft.ListView(expand=True, spacing=10)

            dlg_detalles = ft.AlertDialog(
                title=ft.Text("Alumnos en la clase", color=COLOR_RESPIRO, weight="bold"),
                content=ft.Column([], scroll="auto", height=300, width=300),
                actions=[
                    ft.TextButton("Cerrar",
                                  on_click=lambda _: setattr(dlg_detalles, 'open', False) or page.update())
                ]
            )
            page.overlay.append(dlg_detalles)

            def ver_detalles_clase(cid):
                dlg_detalles.content.controls.clear()
                dlg_detalles.content.controls.append(
                    ft.Container(content=ft.ProgressRing(color=COLOR_RESPIRO),
                                 alignment=ft.alignment.center, padding=20)
                )
                dlg_detalles.open = True
                page.update()

                alumnos = []
                if hasattr(AppDB, 'obtener_alumnos_clase'):
                    alumnos = AppDB.obtener_alumnos_clase(cid)
                else:
                    alumnos = [{"full_name": "¡Aviso! Agrega el método AppDB.obtener_alumnos_clase(class_id).",
                                "active_package": "pagado"}]

                dlg_detalles.content.controls.clear()
                if not alumnos:
                    dlg_detalles.content.controls.append(
                        ft.Text("No hay alumnos inscritos aún.", color=COLOR_RESPIRO_DARK)
                    )
                else:
                    dlg_detalles.content.controls.append(
                        ft.Text(f"Total inscritos: {len(alumnos)}", weight="bold")
                    )
                    for al in alumnos:
                        nombre_al = al.get('full_name', 'Desconocido')
                        estado_al = al.get('active_package', 'Sin paquete')
                        color_icono = ft.colors.GREEN_600 if estado_al.lower() == 'pagado' else ft.colors.ORANGE_600
                        dlg_detalles.content.controls.append(ft.ListTile(
                            leading=ft.Icon(ft.icons.PERSON, color=color_icono),
                            title=ft.Text(nombre_al, weight="bold"),
                            subtitle=ft.Text(f"Estado: {estado_al.capitalize()}")
                        ))
                page.update()

            def borrar_clase(cid):
                AppDB.eliminar_clase(cid)
                recargar_listas()
                snack = ft.SnackBar(ft.Text("Clase eliminada del sistema."), bgcolor=ft.colors.RED_500)
                page.overlay.append(snack)
                snack.open = True
                page.update()

            def recargar_listas():
                f_str = fecha_activa[0].strftime("%Y-%m-%d")
                lista_agenda.controls.clear()
                lista_agenda.controls.append(
                    ft.Container(content=ft.ProgressRing(color=COLOR_RESPIRO),
                                 alignment=ft.alignment.center, padding=40)
                )
                page.update()
                lista_agenda.controls.clear()

                if modo_agenda[0] == "30":
                    hoy_str = datetime.date.today().strftime("%Y-%m-%d")
                    fin_str = (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
                    clases = AppDB.obtener_agenda_rango(hoy_str, fin_str)
                else:
                    clases = AppDB.obtener_todas_las_clases_dia(f_str)

                if not clases:
                    lista_agenda.controls.append(
                        ft.Text("No hay clases programadas.", color=COLOR_RESPIRO_DARK)
                    )

                for c in clases:
                    if not c.get('is_blocked'):
                        fecha_lbl = f"{c['class_date']} | " if modo_agenda[0] == "30" else ""
                        lista_agenda.controls.append(ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(f"{fecha_lbl}{c['start_time']} - {c['service_name']}",
                                            weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Prof: {c['instructor']} | Cupo: {c.get('capacity', 10)}",
                                            size=12)
                                ], spacing=0),
                                ft.Container(expand=True),
                                ft.Row([
                                    ft.IconButton(ft.icons.INFO_OUTLINE, icon_color=COLOR_RESPIRO,
                                                  on_click=lambda e, cid=c['id']: ver_detalles_clase(cid)),
                                    ft.IconButton(ft.icons.DELETE, icon_color=ft.colors.RED_400,
                                                  on_click=lambda e, cid=c['id']: borrar_clase(cid))
                                ], spacing=0)
                            ]),
                            bgcolor=COLOR_TEXTO_BLANCO, padding=15, border_radius=10,
                            border=ft.border.all(1, "#E5E5EA")
                        ))

                lista_bloqueos.controls.clear()
                bloqueos = AppDB.obtener_dias_bloqueados()
                if not bloqueos:
                    lista_bloqueos.controls.append(
                        ft.Text("No hay días cerrados programados.", color=COLOR_RESPIRO_DARK)
                    )
                for b in bloqueos:
                    lista_bloqueos.controls.append(ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.BLOCK, color=ft.colors.RED_400),
                            ft.Text(b['class_date'], weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.IconButton(ft.icons.DELETE, icon_color=ft.colors.RED_400,
                                          on_click=lambda e, bid=b['id']: (
                                              AppDB.desbloquear_dia(bid), recargar_listas()
                                          ))
                        ]),
                        bgcolor=COLOR_TEXTO_BLANCO, padding=15, border_radius=10
                    ))
                page.update()

            def al_cambiar_fecha_admin(e):
                if dp_admin.value:
                    fecha_activa[0] = dp_admin.value
                    txt_fecha_top.value = fecha_activa[0].strftime("%Y-%m-%d")
                    set_modo_dia(None)

            dp_admin = ft.DatePicker(on_change=al_cambiar_fecha_admin)
            page.overlay.append(dp_admin)

            def accion_publicar_clase(e):
                f_str = fecha_activa[0].strftime("%Y-%m-%d")
                if AppDB.es_dia_bloqueado(f_str):
                    snack = ft.SnackBar(ft.Text("¡Error! Este día está marcado como Cerrado."),
                                        bgcolor=ft.colors.RED_500)
                    page.overlay.append(snack)
                    snack.open = True
                elif AppDB.verificar_disponibilidad(f_str, drop_hora.value):
                    snack = ft.SnackBar(ft.Text("¡Horario ocupado! Revisa la agenda."),
                                        bgcolor=ft.colors.RED_500)
                    page.overlay.append(snack)
                    snack.open = True
                elif drop_serv.value and drop_hora.value:
                    AppDB.crear_clase(drop_serv.value, f_str, drop_hora.value,
                                      txt_inst.value, txt_cupo.value)
                    snack = ft.SnackBar(ft.Text("Clase creada."), bgcolor=ft.colors.GREEN_600)
                    page.overlay.append(snack)
                    snack.open = True
                    drop_serv.value, drop_hora.value = None, None
                    recargar_listas()
                page.update()

            txt_fecha_bloqueo = ft.TextField(
                label="Fecha a bloquear", hint_text="Toca el calendario ->",
                read_only=True, expand=True, border_color=COLOR_RESPIRO
            )
            dp_bloqueo = ft.DatePicker(
                on_change=lambda e: (
                    setattr(txt_fecha_bloqueo, 'value', dp_bloqueo.value.strftime("%Y-%m-%d")),
                    page.update()
                ) if dp_bloqueo.value else None,
                first_date=datetime.date.today()
            )
            page.overlay.append(dp_bloqueo)

            def accion_bloquear_dia(e):
                f_str = txt_fecha_bloqueo.value
                if f_str:
                    if not AppDB.es_dia_bloqueado(f_str):
                        AppDB.bloquear_dia(f_str)
                        recargar_listas()
                        snack = ft.SnackBar(ft.Text(f"El día {f_str} ha sido bloqueado."),
                                            bgcolor=ft.colors.GREEN_600)
                        txt_fecha_bloqueo.value = ""
                    else:
                        snack = ft.SnackBar(ft.Text("Ese día ya está bloqueado."),
                                            bgcolor=ft.colors.ORANGE_500)
                else:
                    snack = ft.SnackBar(ft.Text("Por favor, selecciona una fecha en el calendario."),
                                        bgcolor=ft.colors.RED_500)
                page.overlay.append(snack)
                snack.open = True
                page.update()

            recargar_listas()

            tab_crear = ft.Tab(
                text="Crear", icon=ft.icons.ADD_BOX,
                content=ft.Container(padding=20, content=ft.Column([
                    ft.Text("Agendar Nueva Clase", size=18, weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO),
                    ft.Container(height=10),
                    drop_serv, drop_hora,
                    ft.Row([txt_inst, txt_cupo]),
                    ft.Container(height=20),
                    ft.ElevatedButton("Publicar", bgcolor=COLOR_RESPIRO, color="white",
                                      width=float('inf'), height=50, on_click=accion_publicar_clase)
                ]))
            )
            tab_agenda = ft.Tab(
                text="Agenda", icon=ft.icons.FORMAT_LIST_BULLETED,
                content=ft.Container(padding=20, content=ft.Column([
                    ft.Row([btn_modo_30, btn_modo_dia], spacing=10),
                    ft.Container(height=10),
                    lista_agenda
                ]))
            )
            tab_bloqueos = ft.Tab(
                text="Cierres", icon=ft.icons.BLOCK,
                content=ft.Container(padding=20, content=ft.Column([
                    ft.Text("Días Inhábiles", size=18, weight=ft.FontWeight.BOLD,
                            color=ft.colors.RED_400),
                    ft.Text("Elige cualquier fecha futura para cerrar el estudio.",
                            size=12, color=COLOR_RESPIRO_DARK),
                    ft.Container(height=10),
                    ft.Row([
                        txt_fecha_bloqueo,
                        ft.IconButton(ft.icons.CALENDAR_MONTH, icon_color=ft.colors.RED_400,
                                      icon_size=35, on_click=lambda _: dp_bloqueo.pick_date())
                    ]),
                    ft.Container(height=10),
                    ft.ElevatedButton("Bloquear Fecha", bgcolor=ft.colors.RED_400, color="white",
                                      width=float('inf'), height=50, on_click=accion_bloquear_dia),
                    ft.Container(height=20),
                    ft.Text("Próximos cierres:", weight=ft.FontWeight.BOLD),
                    lista_bloqueos
                ]))
            )

            page.views.append(ft.View(
                "/admin",
                bgcolor=COLOR_BG_CLARO,
                padding=0,
                controls=[
                    ft.Container(
                        bgcolor="white",
                        padding=ft.padding.only(left=10, right=20, top=20, bottom=10),
                        shadow=ft.BoxShadow(blur_radius=5, color="#1A000000"),
                        content=ft.Row([
                            ft.IconButton(ft.icons.ARROW_BACK, icon_color=COLOR_RESPIRO,
                                          on_click=lambda _: page.go("/login")),
                            ft.Text("Admin", size=22, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            txt_fecha_top,
                            ft.IconButton(ft.icons.CALENDAR_MONTH, icon_color=COLOR_RESPIRO,
                                          on_click=lambda _: dp_admin.pick_date())
                        ])
                    ),
                    ft.Tabs(
                        selected_index=0,
                        animation_duration=300,
                        unselected_label_color=COLOR_RESPIRO_DARK,
                        label_color=COLOR_RESPIRO,
                        indicator_color=COLOR_RESPIRO,
                        expand=True,
                        tabs=[tab_crear, tab_agenda, tab_bloqueos]
                    )
                ]
            ))

        elif page.route == "/recargando":
            pass  # Puente para evitar pantalla blanca

        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)
        else:
            page.go("/login")

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8080))
    ft.app(
        target=main,
     
