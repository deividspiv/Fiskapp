import flet as ft
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
    # Esta función se encarga de rellenar los créditos si el usuario ya pagó en Supabase pero la UI no se ha enterado
    def sync_creditos_silencioso(telefono):
        if not telefono: 
            return
        try:
            u_sync = AppDB.verificar_usuario(telefono)
            # Si el webhook ya marcó 'pagado' pero los créditos siguen en 0
            if u_sync and str(u_sync.get('active_package','')).lower().strip() == 'pagado':
                if u_sync.get('credits', 0) <= 0:
                    monto_guardado = None
                    try: 
                        monto_guardado = page.client_storage.get("monto_pendiente")
                    except: 
                        pass
                    
                    # Intentamos recuperar el monto de la sesión, del storage profundo, o asignamos el de 650 por defecto
                    monto = page.session.get("monto_pendiente") or monto_guardado or "650"
                    nuevos_creditos = {"100": 1, "650": 8, "800": 12, "1000": 999}.get(str(monto), 8)
                    
                    # Asignamos los créditos y limpiamos la memoria
                    AppDB.asignar_creditos(telefono, nuevos_creditos)
                    try: 
                        page.client_storage.remove("monto_pendiente")
                    except: 
                        pass
        except Exception as e:
            print("Error en sincronización silenciosa:", e)

    # --- DIÁLOGO ADMIN ---
    admin_pwd_field = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, border_radius=10, border_color=COLOR_RESPIRO, cursor_color=COLOR_RESPIRO)
    
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
        ], actions_alignment=ft.MainAxisAlignment.END
    )
    page.overlay.append(admin_dlg)

    # --- TARJETAS DE PAQUETES ---
    def RespiroPricingCard(title, price, savings_text, features_list, package_id):
        features_ui = [ft.Row([ft.Icon(ft.icons.CHECK_CIRCLE_ROUNDED, size=16, color=COLOR_RESPIRO), ft.Text(feat, size=13, weight=ft.FontWeight.W_500, color=COLOR_TEXTO_OSCURO)], spacing=8) for feat in features_list]
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), 
                ft.Text(price, size=34, weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO), 
                ft.Text(savings_text, size=13, color=COLOR_RESPIRO_DARK), 
                ft.Divider(height=30, color="#E5E5EA"), 
                ft.Column(features_ui, spacing=10), 
                ft.Container(height=10), 
                ft.ElevatedButton(content=ft.Text("Elegir paquete", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.W_600), bgcolor=COLOR_RESPIRO, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)), on_click=lambda _: page.go(f"/pago/{package_id}"))
            ]), bgcolor=COLOR_TEXTO_BLANCO, padding=25, border_radius=20, border=ft.border.all(1, "#E5E5EA"), width=280, shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color="#1A000000", offset=ft.Offset(0, 8)),
        )

    # --- ENRUTAMIENTO PRINCIPAL ---
    def route_change(e):
        page.views.clear()
        
        # 1. PORTADA
        if page.route == "/login":
            page.views.append(ft.View(
                "/login", bgcolor=COLOR_RESPIRO, padding=0, 
                controls=[
                    ft.Container(
                        expand=True, padding=ft.padding.only(left=30, right=30, top=40, bottom=40),
                        content=ft.Column([
                            ft.Row([ft.Container(expand=True), ft.IconButton(ft.icons.SETTINGS, icon_color="white70", on_click=lambda _: setattr(admin_dlg, 'open', True) or page.update())]),
                            ft.Container(height=0), ft.Container(content=ft.Image(src="logo_respiros.png", width=280, fit=ft.ImageFit.CONTAIN), alignment=ft.alignment.center),
                            ft.Icon(ft.icons.SPA, size=100, color=COLOR_TEXTO_BLANCO), ft.Text("Pilates/Yoga/Relax", size=36, color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.W_300),
                            ft.Container(expand=True), ft.Text("Tu espacio de bienestar", size=17, color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.W_400),
                            ft.Text("Registrate y agenda tu cita", color="white70"), ft.Container(height=40),
                            ft.Container(content=ft.Text("Iniciar Sesión", color="#6b5b50", weight=ft.FontWeight.BOLD, size=15), alignment=ft.alignment.center, width=300, height=55, bgcolor=COLOR_CREMA_BOTON, border_radius=27, shadow=ft.BoxShadow(blur_radius=10, color="#33000000", offset=ft.Offset(0, 4)), on_click=lambda _: page.go("/formulario_ingreso")),
                            ft.Container(height=10), ft.TextButton(content=ft.Text("¿Nuevo? Regístrate aquí", color="white", size=14, weight=ft.FontWeight.W_300), on_click=lambda _: page.go("/formulario_ingreso")),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                ]
            ))

        # 1.5 FORMULARIO
        elif page.route == "/formulario_ingreso":
            nombre_field = ft.TextField(label="Nombre completo", border_radius=10, prefix_icon=ft.icons.PERSON, border_color=COLOR_RESPIRO, cursor_color=COLOR_RESPIRO)
            celular_field = ft.TextField(label="Número celular (10 dígitos)", border_radius=10, prefix_icon=ft.icons.PHONE, keyboard_type=ft.KeyboardType.PHONE, border_color=COLOR_RESPIRO, cursor_color=COLOR_RESPIRO)
            
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
                    
                    # Forzamos sincronización invisible por si acaba de pagar y la UI no lo sabe
                    sync_creditos_silencioso(celular_field.value)

                    # Verificamos de nuevo para rutearlo correctamente
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
                "/formulario_ingreso", bgcolor=COLOR_TEXTO_BLANCO, padding=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                controls=[
                    ft.Row([ft.IconButton(ft.icons.ARROW_BACK_IOS_NEW, icon_color=COLOR_RESPIRO, on_click=lambda _: page.go("/login")), ft.Container(expand=True)]),
                    ft.Container(height=20), ft.Icon(ft.icons.SPA, size=80, color=COLOR_RESPIRO), ft.Text("Tus Datos", size=32, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), 
                    ft.Text("Ingresa para ver tus reservaciones", size=16, color=COLOR_RESPIRO_DARK, text_align=ft.TextAlign.CENTER), 
                    ft.Container(height=30), nombre_field, celular_field, ft.Container(height=30), 
                    ft.ElevatedButton("Continuar", bgcolor=COLOR_RESPIRO, color=COLOR_TEXTO_BLANCO, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), width=300, height=50, on_click=do_login)
                ]
            ))

        # 2. PAQUETES
        elif page.route == "/paquetes":
            paquetes_db = AppDB.obtener_paquetes()
            lista_tarjetas = [ft.Container(width=10)] 
            for pq in paquetes_db:
                creditos_texto = f"{pq['credits']} clases a elegir" if pq.get('credits') else "Clases ilimitadas"
                precio_entero = int(pq['price']) 
                lista_tarjetas.append(RespiroPricingCard(pq["name"], f"${precio_entero}", f"Vigencia: {pq['validity_days']} días", [creditos_texto, "Reserva desde la app"], str(precio_entero)))
            lista_tarjetas.append(ft.Container(width=10)) 

            page.views.append(ft.View("/paquetes", bgcolor=COLOR_BG_CLARO, padding=0, controls=[
                ft.Container(padding=20, content=ft.Column([ft.Container(height=20), ft.Text("Elige tu plan", size=34, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), ft.Text("Selecciona el paquete que mejor se adapte a tu rutina.", size=16, color=COLOR_RESPIRO_DARK)])), 
                ft.Container(height=450, content=ft.ListView(lista_tarjetas, horizontal=True, spacing=15))
            ]))

        # 3. PAGOS Y VERIFICACIÓN (VERSIÓN IPHONE/SAFARI SEGURA)
        elif page.route.startswith("/pago/") and not page.route.endswith("/verificando"):
            monto = page.route.split("/")[2]
            page.session.set("monto_pendiente", monto)
            
            btn_bbva = ft.Container(
                content=ft.Row([ft.Icon(ft.icons.CREDIT_CARD, color=COLOR_TEXTO_BLANCO), ft.Text("Pagar en línea (BBVA)", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER), 
                bgcolor="#004481", padding=15, border_radius=12
            )
            
            def pagar_bbva(e):
                # 1. Mostramos que estamos obteniendo el link
                btn_bbva.content = ft.Row([ft.ProgressRing(width=20, height=20, color=COLOR_TEXTO_BLANCO, stroke_width=2), ft.Text(" Conectando al banco...", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER)
                btn_bbva.on_click = None
                page.update()
                
                # 2. Generamos el link de pago en la DB
                telefono, nombre = page.session.get("user_phone"), page.session.get("user_name")
                AppDB.crear_registro_pago(telefono, monto)
                
                # Guardamos el monto en memoria profunda por si Safari recarga la app
                try: 
                    page.client_storage.set("monto_pendiente", str(monto))
                except: 
                    pass

                link = generar_enlace_pago(monto, f"Paquete Novum Pilates {monto}", nombre, telefono)
                
                # 3. ANTI-SAFARI: Transformamos el botón en un enlace nativo
                if link:
                    btn_bbva.content = ft.Row([ft.Icon(ft.icons.LOCK_OUTLINE, color=COLOR_TEXTO_BLANCO), ft.Text("Toca aquí para abrir el banco", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER)
                    btn_bbva.bgcolor = ft.colors.GREEN_600
                    btn_bbva.url = link
                    btn_bbva.on_click = lambda _: page.go("/pago/verificando")
                    page.update()
                    
            btn_bbva.on_click = pagar_bbva
                    
            def pagar_recepcion_click(e):
                snack = ft.SnackBar(ft.Text("Solicitud enviada. Paga en recepción.", color=COLOR_TEXTO_BLANCO), bgcolor=COLOR_RESPIRO)
                page.overlay.append(snack)
                snack.open = True
                page.update()

            page.views.append(ft.View(page.route, bgcolor=COLOR_TEXTO_BLANCO, padding=20, controls=[
                ft.Row([ft.IconButton(ft.icons.ARROW_BACK_IOS_NEW, icon_color=COLOR_RESPIRO, on_click=lambda _: page.go("/paquetes")), ft.Text("Checkout", size=24, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO)]), 
                ft.Container(height=30), ft.Text(f"Total a pagar: ${monto}.00 MXN", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), ft.Container(height=40), 
                ft.Text("Método de pago", size=14, weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO_DARK), ft.Container(height=10), 
                
                btn_bbva, 
                
                ft.Container(height=15), 
                ft.Container(content=ft.Row([ft.Icon(ft.icons.MONEY, color=COLOR_TEXTO_OSCURO), ft.Text("Pagar en Recepción", color=COLOR_TEXTO_OSCURO, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER), bgcolor=COLOR_BG_CLARO, padding=15, border_radius=12, on_click=pagar_recepcion_click)
            ]))
            
        elif page.route == "/pago/verificando":
            estado_ui = ft.Container(content=ft.Column([ft.ProgressRing(width=60, height=60, color=COLOR_RESPIRO, stroke_width=4), ft.Container(height=20), ft.Text("Aprobando automáticamente...", size=16, color=COLOR_RESPIRO_DARK)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), alignment=ft.alignment.center, height=300)
            
            def auto_check_payment():
                telefono_alumno = page.session.get("user_phone")
                if not telefono_alumno: return
                for _ in range(60): 
                    if page.route != "/pago/verificando": break 
                    time.sleep(2)
                    try:
                        u = AppDB.verificar_usuario(telefono_alumno)
                        if u and str(u.get('active_package', '')).lower().strip() == 'pagado':
                            sync_creditos_silencioso(telefono_alumno)
                            page.session.set("monto_pendiente", "")
                            page.go("/servicios") 
                            return
                    except Exception as e:
                        pass
            
            page.run_task(auto_check_payment)

            def verificar_estado_pago_manual(e):
                telefono_alumno = page.session.get("user_phone")
                sync_creditos_silencioso(telefono_alumno)
                page.session.set("monto_pendiente", "")
                page.go("/servicios")

            btn_accion = ft.ElevatedButton("Comprobar Manualmente", color=COLOR_TEXTO_BLANCO, bgcolor=COLOR_RESPIRO, width=300, height=50, on_click=verificar_estado_pago_manual)
            page.views.append(ft.View("/pago/verificando", bgcolor=COLOR_TEXTO_BLANCO, padding=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Container(height=50), ft.Text("Checkout Seguro", size=24, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), ft.Container(height=40), estado_ui, ft.Container(height=40), btn_accion]))

        # =========================================================================
        # 4. SERVICIOS Y AGENDA ALUMNO
        # =========================================================================
        elif page.route == "/servicios":
            telefono_alumno = page.session.get("user_phone")
            
            # Sincronización invisible forzada antes de mostrar la UI
            sync_creditos_silencioso(telefono_alumno)
            
            nombre_usuario = page.session.get('user_name')
            primer_nombre = nombre_usuario.split()[0] if nombre_usuario else 'Alumno'
            inicial = primer_nombre[0].upper() if primer_nombre else "A"
            
            hoy = datetime.date.today()
            vista_estado = {
                "fecha_activa": hoy,
                "servicio_activo": "Pilates" 
            }

            servicios_ui = ft.Row(spacing=10, scroll=ft.ScrollMode.HIDDEN)
            dias_ui = ft.Row(spacing=15, scroll=ft.ScrollMode.HIDDEN)
            horarios_ui = ft.Column(spacing=15)

            def recargar_pantalla():
                horarios_ui.controls.clear()
                horarios_ui.controls.append(ft.Container(content=ft.ProgressRing(color=COLOR_RESPIRO), alignment=ft.alignment.center, padding=40))
                page.update()

                servicios_ui.controls.clear()
                nombres_servicios = ["Pilates", "Yoga", "Ejercicios Funcionales"]
                for serv in nombres_servicios:
                    es_activo = (serv == vista_estado["servicio_activo"])
                    servicios_ui.controls.append(
                        ft.Container(
                            content=ft.Text(serv, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_BLANCO if es_activo else COLOR_RESPIRO),
                            bgcolor=COLOR_RESPIRO if es_activo else COLOR_TEXTO_BLANCO,
                            padding=ft.padding.symmetric(horizontal=20, vertical=10),
                            border_radius=20, border=ft.border.all(1, COLOR_RESPIRO) if not es_activo else None,
                            on_click=lambda e, s=serv: al_seleccionar_servicio(s)
                        )
                    )

                dias_ui.controls.clear()
                nombres_dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
                for i in range(14): 
                    fecha_iter = hoy + datetime.timedelta(days=i)
                    es_dia_seleccionado = (fecha_iter == vista_estado["fecha_activa"])
                    bg_color = COLOR_RESPIRO if es_dia_seleccionado else COLOR_TEXTO_BLANCO
                    text_color = COLOR_TEXTO_BLANCO if es_dia_seleccionado else COLOR_TEXTO_OSCURO

                    dias_ui.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text(nombres_dias[fecha_iter.weekday()], size=14, color=text_color, weight=ft.FontWeight.W_500),
                                ft.Text(str(fecha_iter.day), size=20, color=text_color, weight=ft.FontWeight.BOLD),
                            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            bgcolor=bg_color, width=65, height=80, border_radius=15, border=ft.border.all(1, "#E5E5EA") if not es_dia_seleccionado else None,
                            on_click=lambda e, f=fecha_iter: al_seleccionar_dia(f) 
                        )
                    )

                horarios_ui.controls.clear() 
                fecha_str = str(vista_estado["fecha_activa"])
                
                if AppDB.es_dia_bloqueado(fecha_str):
                    horarios_ui.controls.append(ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.NIGHTLIGHT_ROUND, size=50, color=COLOR_RESPIRO),
                            ft.Text("Estudio Cerrado", size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                            ft.Text("Tómate un descanso. Nos vemos pronto.", text_align=ft.TextAlign.CENTER, color=COLOR_RESPIRO_DARK)
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=COLOR_TEXTO_BLANCO, padding=40, border_radius=15, width=float('inf')
                    ))
                else:
                    clases_del_dia = AppDB.obtener_clases(vista_estado["servicio_activo"], fecha_str)
                    mis_reservas = AppDB.obtener_reservas_usuario(telefono_alumno)
                    clases_agendadas = [r.get("class_id") for r in mis_reservas if r.get("estado", "").lower() == "futura"]

                    if not clases_del_dia:
                        horarios_ui.controls.append(ft.Text(f"No hay clases de {vista_estado['servicio_activo']} programadas para esta fecha.", color=COLOR_RESPIRO_DARK))

                    for h in clases_del_dia:
                        is_full = h["cupo"] <= 0
                        ya_agendado = h["id"] in clases_agendadas

                        if ya_agendado:
                            btn_color = ft.colors.GREEN_500
                            btn_text = "Agendado ✓"
                            text_btn_color = COLOR_TEXTO_BLANCO
                            accion_btn = lambda _: page.go("/perfil") 
                        else:
                            btn_color = "#E5E5EA" if is_full else COLOR_CREMA_BOTON
                            btn_text = "Lleno" if is_full else "Reservar"
                            text_btn_color = COLOR_RESPIRO_DARK if is_full else "#6b5b50"
                            accion_btn = (lambda e, c=h: confirmar_reserva(c)) if not is_full else None

                        horarios_ui.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Column([ft.Text(h["hora"], size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), ft.Text(f"Prof: {h['instructor']}", size=13, color=COLOR_RESPIRO_DARK), ft.Text(f"Lugares: {h['cupo']}", size=12, color=COLOR_RESPIRO if not is_full else ft.colors.RED_400)], spacing=2),
                                    ft.Container(expand=True), 
                                    ft.Container(content=ft.Text(btn_text, weight=ft.FontWeight.BOLD, color=text_btn_color, size=13), bgcolor=btn_color, padding=ft.padding.symmetric(horizontal=20, vertical=10), border_radius=20, on_click=accion_btn)
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

            def confirmar_reserva(clase):
                usuario_actual = AppDB.verificar_usuario(telefono_alumno)
                creditos_actuales = usuario_actual.get('credits', 0) if usuario_actual else 0
                if creditos_actuales <= 0:
                    snack = ft.SnackBar(ft.Text("No tienes clases disponibles. Redirigiendo a la tienda..."), bgcolor=ft.colors.ORANGE_500)
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()
                    time.sleep(1.5)
                    page.go("/paquetes")
                    return
                exito = AppDB.reservar_clase(telefono_alumno, clase["id"])
                if exito:
                    snack = ft.SnackBar(ft.Text("¡Reserva confirmada! Se descontó 1 clase."), bgcolor=ft.colors.GREEN_600)
                    recargar_pantalla() 
                else:
                    snack = ft.SnackBar(ft.Text("Hubo un error al reservar. Intenta de nuevo."), bgcolor=ft.colors.RED_500)
                page.overlay.append(snack)
                snack.open = True
                page.update()

            recargar_pantalla()

            avatar_perfil = ft.Container(
                content=ft.Text(inicial, size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_BLANCO),
                alignment=ft.alignment.center, width=45, height=45, bgcolor=COLOR_RESPIRO, shape=ft.BoxShape.CIRCLE,
                shadow=ft.BoxShadow(blur_radius=5, color="#33000000", offset=ft.Offset(0, 2)),
                on_click=lambda _: page.go("/perfil")
            )

            page.views.append(ft.View(
                "/servicios", bgcolor=COLOR_BG_CLARO, padding=20, scroll=ft.ScrollMode.AUTO, 
                controls=[
                    ft.Container(height=10),
                    ft.Row([
                        ft.Column([
                            ft.Text(f"Hola, {primer_nombre} 👋", size=26, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), 
                            ft.Text("Reserva tu próxima clase", size=15, color=COLOR_RESPIRO_DARK)
                        ], spacing=0),
                        ft.Container(expand=True), avatar_perfil
                    ]),
                    ft.Container(height=25), servicios_ui, ft.Container(height=25), dias_ui, ft.Container(height=25),
                    ft.Text("Horarios Disponibles", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                    ft.Container(height=10), horarios_ui, ft.Container(height=40) 
                ]
            ))
            
        # =========================================================================
        # 4.5 HISTORIAL Y PERFIL
        # =========================================================================
        elif page.route == "/perfil":
            telefono_alumno = page.session.get("user_phone")
            
            # Sincronización invisible forzada
            sync_creditos_silencioso(telefono_alumno)
            
            usuario = AppDB.verificar_usuario(telefono_alumno)
            clases_restantes = usuario.get('credits', 0) if usuario else 0
            mis_reservas = AppDB.obtener_reservas_usuario(telefono_alumno)
            
            seccion_sin_creditos = ft.Container(content=ft.Column([ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.ORANGE_500, size=40), ft.Text("¡Te has quedado sin clases!", size=18, weight=ft.FontWeight.BOLD), ft.ElevatedButton("Comprar Paquete", bgcolor=COLOR_RESPIRO, color="white", on_click=lambda _: page.go("/paquetes"))], alignment="center"), bgcolor="white", padding=20, border_radius=15, margin=ft.margin.only(bottom=20)) if clases_restantes <= 0 else ft.Container()
            
            reserva_a_cancelar = [None]
            aplica_penalizacion = [False]
            
            def ejecutar_cancelacion_final(e):
                rid = reserva_a_cancelar[0]
                penalizar = aplica_penalizacion[0]
                dlg_cancelar.open = False
                
                contenedor_reservas.content = ft.Container(
                    content=ft.Column([ft.ProgressRing(color=COLOR_RESPIRO), ft.Text("Procesando cancelación...", color=COLOR_RESPIRO_DARK)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center, height=200
                )
                page.update()
                
                # Ejecutamos DB
                AppDB.cancelar_reserva(rid)
                
                if not penalizar:
                    u_actual = AppDB.verificar_usuario(telefono_alumno)
                    creditos_previos = u_actual.get('credits', 0) if u_actual else 0
                    AppDB.asignar_creditos(telefono_alumno, creditos_previos + 1)
                
                msg = "Sesión cancelada. Se aplicó la penalidad de 12hrs." if penalizar else "Sesión cancelada. Se devolvió 1 clase a tu cuenta."
                snack = ft.SnackBar(ft.Text(msg), bgcolor=ft.colors.ORANGE_600 if penalizar else ft.colors.GREEN_600)
                page.overlay.append(snack)
                snack.open = True
                
                # TRUCO DE RECARGA INSTANTÁNEA
                page.route = "/temp"
                page.go("/perfil") 
                
            dlg_cancelar = ft.AlertDialog(
                title=ft.Text("Cancelar Sesión", weight=ft.FontWeight.BOLD), content=ft.Text(""),
                actions=[
                    ft.TextButton("Volver", on_click=lambda _: setattr(dlg_cancelar, 'open', False) or page.update()),
                    ft.ElevatedButton("Sí, Cancelar", bgcolor=ft.colors.RED_500, color="white", on_click=ejecutar_cancelacion_final)
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
                            
                        # CORRECCIÓN DE HORA DE MÉXICO: Le restamos 6 horas al UTC global
                        ahora_mexico = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
                        horas_diff = (dt_clase - ahora_mexico).total_seconds() / 3600
                        
                        if 0 < horas_diff <= 12:
                            es_penalizable = True
                except Exception as e:
                    print("Error calculando tiempo:", e)
                
                aplica_penalizacion[0] = es_penalizable
                
                if es_penalizable:
                    dlg_cancelar.content = ft.Text("Faltan menos de 12 horas para tu clase. Si cancelas ahora perderás esta clase según nuestra política.\n\n¿Deseas cancelarla de todos modos?", color=ft.colors.RED_600)
                else:
                    dlg_cancelar.content = ft.Text("¿Estás seguro de que deseas cancelar tu clase?\n\nTu crédito será devuelto automáticamente a tu perfil.")
                
                dlg_cancelar.open = True
                page.update()

            lista_reservas_ui = ft.Column(spacing=15)
            
            for res in mis_reservas:
                is_futura = res.get("estado", "").lower() == "futura"
                fila_superior = ft.Row([
                    ft.Text(res.get("servicio", "Clase"), size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), 
                    ft.Container(expand=True), 
                    ft.Text(res.get("estado", "").capitalize(), size=12, color=COLOR_RESPIRO if is_futura else COLOR_RESPIRO_DARK, weight=ft.FontWeight.BOLD)
                ])
                elementos_tarjeta = [fila_superior, ft.Text(res.get("fecha", ""), size=14, color=COLOR_RESPIRO_DARK)]
                
                if is_futura:
                    btn_cancelar = ft.TextButton("Cancelar Clase", icon=ft.icons.CANCEL, style=ft.ButtonStyle(color=ft.colors.RED_400), on_click=lambda e, r=res: preparar_cancelacion(r))
                    elementos_tarjeta.append(ft.Container(height=5))
                    elementos_tarjeta.append(ft.Row([ft.Container(expand=True), btn_cancelar]))

                lista_reservas_ui.controls.append(ft.Container(content=ft.Column(elementos_tarjeta, spacing=5), bgcolor="white", padding=20, border_radius=15, shadow=ft.BoxShadow(blur_radius=5, color="#0A000000", offset=ft.Offset(0, 2))))
            
            if not mis_reservas: 
                lista_reservas_ui.controls.append(ft.Text("Aún no tienes historial de reservas.", color=COLOR_RESPIRO_DARK))
                
            contenedor_reservas = ft.Container(content=lista_reservas_ui)
                
            page.views.append(ft.View("/perfil", bgcolor=COLOR_BG_CLARO, padding=20, scroll="auto", controls=[
                ft.Row([ft.IconButton(ft.icons.ARROW_BACK_IOS_NEW, icon_color=COLOR_RESPIRO, on_click=lambda _: page.go("/servicios")), ft.Text("Mi Perfil", size=24, weight="bold", color=COLOR_TEXTO_OSCURO)]), 
                ft.Container(content=ft.Row([ft.Column([ft.Text("Clases Restantes", size=14, color=COLOR_TEXTO_OSCURO), ft.Text(f"{clases_restantes}", size=40, weight="bold", color=COLOR_RESPIRO)]), ft.Container(expand=True), ft.Icon(ft.icons.FITNESS_CENTER, size=40, color=COLOR_RESPIRO)]), bgcolor="white", padding=25, border_radius=15, shadow=ft.BoxShadow(blur_radius=5, color="#0A000000")),
                ft.Container(height=20), seccion_sin_creditos, ft.Text("Tus Reservas", size=18, weight="bold", color=COLOR_TEXTO_OSCURO), 
                contenedor_reservas, ft.Container(height=30), 
                ft.TextButton("Cerrar Sesión", icon=ft.icons.LOGOUT, style=ft.ButtonStyle(color=ft.colors.RED_400), on_click=lambda _: page.go("/login"))
            ]))

        # =========================================================================
        # 5. PANEL ADMIN
        # =========================================================================
        elif page.route == "/admin":
            fecha_activa = [datetime.date.today()]
            txt_fecha_top = ft.Text(fecha_activa[0].strftime("%Y-%m-%d"), size=18, weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO)
            
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
                
            btn_modo_30 = ft.ElevatedButton("30 Días", on_click=set_modo_30, bgcolor=COLOR_RESPIRO, color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))
            btn_modo_dia = ft.ElevatedButton("Día Específico", on_click=set_modo_dia, bgcolor="transparent", color=COLOR_RESPIRO, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))

            opciones_servicios = [ft.dropdown.Option(s["name"]) for s in AppDB.obtener_servicios()]
            drop_serv = ft.Dropdown(label="Servicio", options=opciones_servicios, border_color=COLOR_RESPIRO)
            drop_hora = ft.Dropdown(label="Horario", options=[ft.dropdown.Option("08:00 AM"), ft.dropdown.Option("09:15 AM"), ft.dropdown.Option("06:30 PM")], border_color=COLOR_RESPIRO)
            txt_inst = ft.TextField(label="Instructor", value="Staff", border_color=COLOR_RESPIRO, expand=True)
            txt_cupo = ft.TextField(label="Cupo", value="10", keyboard_type=ft.KeyboardType.NUMBER, border_color=COLOR_RESPIRO, width=100)
            
            lista_agenda = ft.ListView(expand=True, spacing=10)
            lista_bloqueos = ft.ListView(expand=True, spacing=10)
            
            id_edicion = [None]
            drop_serv_ed = ft.Dropdown(label="Servicio", options=opciones_servicios, border_color=COLOR_RESPIRO)
            drop_hora_ed = ft.Dropdown(label="Horario", options=[ft.dropdown.Option("08:00 AM"), ft.dropdown.Option("09:15 AM"), ft.dropdown.Option("06:30 PM")], border_color=COLOR_RESPIRO)
            
            def guardar_edicion(e):
                AppDB.actualizar_clase(id_edicion[0], drop_serv_ed.value, fecha_activa[0].strftime("%Y-%m-%d"), drop_hora_ed.value, "Staff", 10)
                dlg_edicion.open = False
                recargar_listas()
                page.update()

            dlg_edicion = ft.AlertDialog(title=ft.Text("Editar Clase", color=COLOR_RESPIRO), content=ft.Column([drop_serv_ed, drop_hora_ed], height=150), actions=[ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg_edicion, 'open', False) or page.update()), ft.ElevatedButton("Guardar", bgcolor=COLOR_RESPIRO, color="white", on_click=guardar_edicion)])
            page.overlay.append(dlg_edicion)

            def abrir_edicion(clase):
                id_edicion[0] = clase['id']
                drop_serv_ed.value = clase['service_name']
                drop_hora_ed.value = clase['start_time']
                dlg_edicion.open = True
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
                lista_agenda.controls.append(ft.Container(content=ft.ProgressRing(color=COLOR_RESPIRO), alignment=ft.alignment.center, padding=40))
                page.update() 
                
                lista_agenda.controls.clear()
                
                if modo_agenda[0] == "30":
                    hoy_str = datetime.date.today().strftime("%Y-%m-%d")
                    fin_str = (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
                    clases = AppDB.obtener_agenda_rango(hoy_str, fin_str)
                else:
                    clases = AppDB.obtener_todas_las_clases_dia(f_str)
                
                if not clases: lista_agenda.controls.append(ft.Text("No hay clases programadas.", color=COLOR_RESPIRO_DARK))
                
                for c in clases:
                    if not c.get('is_blocked'):
                        fecha_lbl = f"{c['class_date']} | " if modo_agenda[0] == "30" else ""
                        lista_agenda.controls.append(ft.Container(
                            content=ft.Row([
                                ft.Column([ft.Text(f"{fecha_lbl}{c['start_time']} - {c['service_name']}", weight=ft.FontWeight.BOLD), ft.Text(f"Prof: {c['instructor']} | Cupo: {c.get('capacity', 10)}", size=12)], spacing=0),
                                ft.Container(expand=True), 
                                ft.Row([
                                    ft.IconButton(ft.icons.EDIT, icon_color=COLOR_RESPIRO, on_click=lambda e, curr=c: abrir_edicion(curr)),
                                    ft.IconButton(ft.icons.DELETE, icon_color=ft.colors.RED_400, on_click=lambda e, cid=c['id']: borrar_clase(cid))
                                ], spacing=0)
                            ]), bgcolor=COLOR_TEXTO_BLANCO, padding=15, border_radius=10, border=ft.border.all(1, "#E5E5EA")
                        ))
                
                lista_bloqueos.controls.clear()
                bloqueos = AppDB.obtener_dias_bloqueados()
                if not bloqueos: lista_bloqueos.controls.append(ft.Text("No hay días cerrados programados.", color=COLOR_RESPIRO_DARK))
                for b in bloqueos:
                    lista_bloqueos.controls.append(ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.BLOCK, color=ft.colors.RED_400), ft.Text(b['class_date'], weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True), ft.IconButton(ft.icons.DELETE, icon_color=ft.colors.RED_400, on_click=lambda e, bid=b['id']: borrar_bloqueo(bid))
                        ]), bgcolor=COLOR_TEXTO_BLANCO, padding=15, border_radius=10
                    ))
                page.update()

            def borrar_bloqueo(bid):
                AppDB.desbloquear_dia(bid)
                recargar_listas()

            def al_cambiar_fecha_admin(e):
                if dp_admin.value:
                    fecha_activa[0] = dp_admin.value
                    txt_fecha_top.value = fecha_activa[0].strftime("%Y-%m-%d")
                    set_modo_dia(None) 
                    page.update()

            dp_admin = ft.DatePicker(on_change=al_cambiar_fecha_admin)
            page.overlay.append(dp_admin)

            def accion_publicar_clase(e):
                f_str = fecha_activa[0].strftime("%Y-%m-%d")
                if AppDB.es_dia_bloqueado(f_str):
                    snack = ft.SnackBar(ft.Text("¡Error! Este día está marcado como Cerrado."), bgcolor=ft.colors.RED_500)
                    page.overlay.append(snack)
                    snack.open = True
                elif AppDB.verificar_disponibilidad(f_str, drop_hora.value):
                    snack = ft.SnackBar(ft.Text("¡Horario ocupado! Revisa la agenda."), bgcolor=ft.colors.RED_500)
                    page.overlay.append(snack)
                    snack.open = True
                elif drop_serv.value and drop_hora.value:
                    AppDB.crear_clase(drop_serv.value, f_str, drop_hora.value, txt_inst.value, txt_cupo.value)
                    snack = ft.SnackBar(ft.Text("Clase creada."), bgcolor=ft.colors.GREEN_600)
                    page.overlay.append(snack)
                    snack.open = True
                    drop_serv.value, drop_hora.value = None, None
                    recargar_listas()
                page.update()

            txt_fecha_bloqueo = ft.TextField(label="Fecha a bloquear", hint_text="Toca el calendario ->", read_only=True, expand=True, border_color=COLOR_RESPIRO)
            def al_cambiar_fecha_bloqueo(e):
                if dp_bloqueo.value:
                    txt_fecha_bloqueo.value = dp_bloqueo.value.strftime("%Y-%m-%d")
                    page.update()

            dp_bloqueo = ft.DatePicker(on_change=al_cambiar_fecha_bloqueo, first_date=datetime.date.today())
            page.overlay.append(dp_bloqueo)

            def accion_bloquear_dia(e):
                f_str = txt_fecha_bloqueo.value
                if f_str:
                    if not AppDB.es_dia_bloqueado(f_str):
                        AppDB.bloquear_dia(f_str)
                        recargar_listas()
                        snack = ft.SnackBar(ft.Text(f"El día {f_str} ha sido bloqueado."), bgcolor=ft.colors.GREEN_600)
                        txt_fecha_bloqueo.value = ""
                    else:
                        snack = ft.SnackBar(ft.Text("Ese día ya está bloqueado."), bgcolor=ft.colors.ORANGE_500)
                else:
                    snack = ft.SnackBar(ft.Text("Por favor, selecciona una fecha en el calendario."), bgcolor=ft.colors.RED_500)
                page.overlay.append(snack)
                snack.open = True
                page.update()

            row_bloqueo = ft.Row([txt_fecha_bloqueo, ft.IconButton(ft.icons.CALENDAR_MONTH, icon_color=ft.colors.RED_400, icon_size=35, on_click=lambda _: dp_bloqueo.pick_date())])

            recargar_listas()

            tab_crear = ft.Tab(text="Crear", icon=ft.icons.ADD_BOX, content=ft.Container(padding=20, content=ft.Column([
                ft.Text("Agendar Nueva Clase", size=18, weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO),
                ft.Container(height=10), drop_serv, drop_hora, ft.Row([txt_inst, txt_cupo]), ft.Container(height=20),
                ft.ElevatedButton("Publicar", bgcolor=COLOR_RESPIRO, color="white", width=float('inf'), height=50, on_click=accion_publicar_clase)
            ])))
            
            tab_agenda = ft.Tab(text="Agenda", icon=ft.icons.FORMAT_LIST_BULLETED, content=ft.Container(padding=20, content=ft.Column([
                ft.Row([btn_modo_30, btn_modo_dia], spacing=10),
                ft.Container(height=10),
                lista_agenda
            ])))

            tab_bloqueos = ft.Tab(text="Cierres", icon=ft.icons.BLOCK, content=ft.Container(padding=20, content=ft.Column([
                ft.Text("Días Inhábiles", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.RED_400),
                ft.Text("Elige cualquier fecha futura para cerrar el estudio completo.", size=12, color=COLOR_RESPIRO_DARK),
                ft.Container(height=10), row_bloqueo, ft.Container(height=10),
                ft.ElevatedButton("Bloquear Fecha", bgcolor=ft.colors.RED_400, color="white", width=float('inf'), height=50, on_click=accion_bloquear_dia),
                ft.Container(height=20), ft.Text("Próximos cierres:", weight=ft.FontWeight.BOLD), lista_bloqueos
            ])))

            page.views.append(ft.View("/admin", bgcolor=COLOR_BG_CLARO, padding=0, controls=[
                ft.Container(bgcolor="white", padding=ft.padding.only(left=10, right=20, top=20, bottom=10), shadow=ft.BoxShadow(blur_radius=5, color="#1A000000"), content=ft.Row([
                    ft.IconButton(ft.icons.ARROW_BACK, icon_color=COLOR_RESPIRO, on_click=lambda _: page.go("/login")), ft.Text("Admin", size=22, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True), txt_fecha_top, 
                    ft.IconButton(ft.icons.CALENDAR_MONTH, icon_color=COLOR_RESPIRO, on_click=lambda _: dp_admin.pick_date())
                ])),
                ft.Tabs(selected_index=0, animation_duration=300, unselected_label_color=COLOR_RESPIRO_DARK, label_color=COLOR_RESPIRO, indicator_color=COLOR_RESPIRO, expand=True, tabs=[tab_crear, tab_agenda, tab_bloqueos])
            ]))

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
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0", assets_dir="assets")
