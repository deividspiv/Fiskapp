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
                            ft.Container(height=0), 
                            # Logo corregido
                            ft.Container(content=ft.Image(src="logo_respiros.png", width=280, fit=ft.ImageFit.CONTAIN), alignment=ft.alignment.center),
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
                    tiene_paquete_activo = False

                    if not usuario:
                        AppDB.registrar_usuario(celular_field.value, nombre_field.value)
                        nombre_final = nombre_field.value
                    else:
                        nombre_final = usuario.get('full_name', nombre_field.value)
                        estado_paquete = str(usuario.get('active_package', '')).lower().strip()
                        if estado_paquete == 'pagado':
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

        # 3. PAGOS (VERSIÓN ANTI-SAFARI CON BOTÓN DE EFECTIVO)
        elif page.route.startswith("/pago/") and not page.route.endswith("/verificando"):
            monto = page.route.split("/")[2]
            page.session.set("monto_pendiente", monto)
            
            btn_bbva = ft.Container(
                content=ft.Row([ft.Icon(ft.icons.CREDIT_CARD, color=COLOR_TEXTO_BLANCO), ft.Text("Pagar en línea (BBVA)", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER), 
                bgcolor="#004481", padding=15, border_radius=12
            )
            
            def pagar_bbva(e):
                btn_bbva.content = ft.Row([ft.ProgressRing(width=20, height=20, color=COLOR_TEXTO_BLANCO, stroke_width=2), ft.Text(" Conectando...", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER)
                btn_bbva.on_click = None
                page.update()
                
                telefono, nombre = page.session.get("user_phone"), page.session.get("user_name")
                AppDB.crear_registro_pago(telefono, monto)
                link = generar_enlace_pago(monto, f"Paquete Novum Pilates {monto}", nombre, telefono)
                
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
                # Botón de efectivo restaurado
                ft.Container(
                    content=ft.Row([ft.Icon(ft.icons.MONEY, color=COLOR_TEXTO_OSCURO), ft.Text("Pagar en Recepción", color=COLOR_TEXTO_OSCURO, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER), 
                    bgcolor=COLOR_BG_CLARO, padding=15, border_radius=12, 
                    on_click=pagar_recepcion_click
                )
            ]))
            
        elif page.route == "/pago/verificando":
            estado_ui = ft.Container(content=ft.Column([ft.ProgressRing(width=60, height=60, color=COLOR_RESPIRO, stroke_width=4), ft.Container(height=20), ft.Text("Esperando confirmación...", size=16, color=COLOR_RESPIRO_DARK)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), alignment=ft.alignment.center, height=300)
            def verificar_estado_pago(e):
                monto = page.session.get("monto_pendiente")
                telefono_alumno = page.session.get("user_phone")
                for _ in range(5):
                    time.sleep(2)
                    usuario = AppDB.verificar_usuario(telefono_alumno)
                    if usuario and str(usuario.get('active_package', '')).lower().strip() == 'pagado':
                        if usuario.get('credits', 0) <= 0 and monto:
                            AppDB.asignar_creditos(telefono_alumno, {"100": 1, "650": 8, "800": 12, "1000": 999}.get(monto, 0))
                        page.go("/servicios")
                        return
            btn_accion = ft.ElevatedButton("Ya realicé mi pago", color=COLOR_TEXTO_BLANCO, bgcolor=COLOR_RESPIRO, width=300, height=50, on_click=verificar_estado_pago)
            page.views.append(ft.View("/pago/verificando", bgcolor=COLOR_TEXTO_BLANCO, padding=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Container(height=50), ft.Text("Checkout Seguro", size=24, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), ft.Container(height=40), estado_ui, ft.Container(height=40), btn_accion]))

        # 4. SERVICIOS Y AGENDA (FUSIONADA)
        elif page.route == "/servicios":
            nombre_usuario = page.session.get('user_name')
            primer_nombre = nombre_usuario.split()[0] if nombre_usuario else 'Alumno'
            inicial = primer_nombre[0].upper() if primer_nombre else "A"
            hoy = datetime.date.today()
            vista_estado = {"fecha_activa": hoy, "servicio_activo": "Pilates"}

            servicios_ui, dias_ui, horarios_ui = ft.Row(spacing=10, scroll=ft.ScrollMode.HIDDEN), ft.Row(spacing=15, scroll=ft.ScrollMode.HIDDEN), ft.Column(spacing=15)

            def recargar_pantalla():
                horarios_ui.controls.clear()
                horarios_ui.controls.append(ft.Container(content=ft.ProgressRing(color=COLOR_RESPIRO), alignment=ft.alignment.center, padding=40))
                page.update()

                servicios_ui.controls.clear()
                for serv in ["Pilates", "Yoga", "Ejercicios Funcionales"]:
                    es_activo = (serv == vista_estado["servicio_activo"])
                    servicios_ui.controls.append(ft.Container(content=ft.Text(serv, weight="bold", color="white" if es_activo else COLOR_RESPIRO), bgcolor=COLOR_RESPIRO if es_activo else "white", padding=ft.padding.symmetric(horizontal=20, vertical=10), border_radius=20, border=ft.border.all(1, COLOR_RESPIRO) if not es_activo else None, on_click=lambda e, s=serv: al_seleccionar_servicio(s)))

                dias_ui.controls.clear()
                nombres_dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
                for i in range(14):
                    fecha_iter = hoy + datetime.timedelta(days=i)
                    es_dia = (fecha_iter == vista_estado["fecha_activa"])
                    dias_ui.controls.append(ft.Container(content=ft.Column([ft.Text(nombres_dias[fecha_iter.weekday()], size=14, color="white" if es_dia else COLOR_TEXTO_OSCURO), ft.Text(str(fecha_iter.day), size=20, weight="bold", color="white" if es_dia else COLOR_TEXTO_OSCURO)], alignment="center"), bgcolor=COLOR_RESPIRO if es_dia else "white", width=65, height=80, border_radius=15, border=ft.border.all(1, "#E5E5EA") if not es_dia else None, on_click=lambda e, f=fecha_iter: al_seleccionar_dia(f)))

                horarios_ui.controls.clear() 
                f_str = str(vista_estado["fecha_activa"])
                if AppDB.es_dia_bloqueado(f_str):
                    horarios_ui.controls.append(ft.Container(content=ft.Column([ft.Icon(ft.icons.NIGHTLIGHT_ROUND, size=50, color=COLOR_RESPIRO), ft.Text("Estudio Cerrado", size=20, weight="bold")], alignment="center"), padding=40, width=float('inf')))
                else:
                    clases = AppDB.obtener_clases(vista_estado["servicio_activo"], f_str)
                    if not clases: horarios_ui.controls.append(ft.Text("Sin clases programadas."))
                    for h in clases:
                        is_full = h["cupo"] <= 0
                        horarios_ui.controls.append(ft.Container(content=ft.Row([ft.Column([ft.Text(h["hora"], size=18, weight="bold"), ft.Text(f"Prof: {h['instructor']}")]), ft.Container(expand=True), ft.ElevatedButton("Reservar" if not is_full else "Lleno", bgcolor=COLOR_CREMA_BOTON if not is_full else "#E5E5EA", on_click=lambda e, c=h: confirmar_reserva(c) if not is_full else None)]), bgcolor="white", padding=20, border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color="#1A000000")))
                page.update()

            def al_seleccionar_dia(f): vista_estado["fecha_activa"] = f; recargar_pantalla()
            def al_seleccionar_servicio(s): vista_estado["servicio_activo"] = s; recargar_pantalla()
            def confirmar_reserva(clase):
                user = AppDB.verificar_usuario(page.session.get("user_phone"))
                if user.get('credits', 0) <= 0: page.go("/paquetes"); return
                if AppDB.reservar_clase(page.session.get("user_phone"), clase["id"]): recargar_pantalla()

            recargar_pantalla()
            avatar = ft.Container(content=ft.Text(inicial, weight="bold", color="white"), alignment=ft.alignment.center, width=45, height=45, bgcolor=COLOR_RESPIRO, shape=ft.BoxShape.CIRCLE, on_click=lambda _: page.go("/perfil"))

            page.views.append(ft.View("/servicios", bgcolor=COLOR_BG_CLARO, padding=20, scroll="auto", controls=[
                ft.Container(height=10), ft.Row([ft.Column([ft.Text(f"Hola, {primer_nombre} 👋", size=26, weight="bold"), ft.Text("Reserva tu clase")], spacing=0), ft.Container(expand=True), avatar]),
                ft.Container(height=25), servicios_ui, ft.Container(height=25), dias_ui, ft.Container(height=25), ft.Text("Horarios Disponibles", weight="bold"), horarios_ui
            ]))
            
        # 4.5 PERFIL (Intacto)
        elif page.route == "/perfil":
            telefono_alumno = page.session.get("user_phone")
            usuario = AppDB.verificar_usuario(telefono_alumno)
            clases_restantes = usuario.get('credits', 0) if usuario else 0
            mis_reservas = AppDB.obtener_reservas_usuario(telefono_alumno)
            lista_res = ft.Column([ft.Container(content=ft.Row([ft.Text(f"{r['servicio']} - {r['fecha']}")]), bgcolor="white", padding=15, border_radius=10) for r in mis_reservas])
            page.views.append(ft.View("/perfil", bgcolor=COLOR_BG_CLARO, padding=20, controls=[
                ft.Row([ft.IconButton(ft.icons.ARROW_BACK_IOS_NEW, on_click=lambda _: page.go("/servicios")), ft.Text("Mi Perfil", size=24, weight="bold")]), 
                ft.Container(content=ft.Column([ft.Text("Clases Restantes"), ft.Text(f"{clases_restantes}", size=40, weight="bold", color=COLOR_RESPIRO)]), bgcolor="white", padding=25, border_radius=15),
                ft.Container(height=20), ft.Text("Historial", weight="bold"), lista_res, ft.TextButton("Cerrar Sesión", on_click=lambda _: page.go("/login"))
            ]))

        # =========================================================================
        # 5. ADMIN (CORRECCIÓN DE CALENDARIOS)
        # =========================================================================
        elif page.route == "/admin":
            fecha_activa = [datetime.date.today()]
            txt_fecha_top = ft.Text(fecha_activa[0].strftime("%Y-%m-%d"), size=18, weight="bold", color=COLOR_RESPIRO)
            modo_agenda = ["30"]
            
            opciones_servicios = [ft.dropdown.Option(s["name"]) for s in AppDB.obtener_servicios()]
            drop_serv = ft.Dropdown(label="Servicio", options=opciones_servicios, border_color=COLOR_RESPIRO)
            drop_hora = ft.Dropdown(label="Horario", options=[ft.dropdown.Option("08:00 AM"), ft.dropdown.Option("09:15 AM"), ft.dropdown.Option("06:30 PM")], border_color=COLOR_RESPIRO)
            txt_inst, txt_cupo = ft.TextField(label="Instructor", value="Staff"), ft.TextField(label="Cupo", value="10", width=100)
            lista_agenda, lista_bloqueos = ft.ListView(expand=True, spacing=10), ft.ListView(expand=True, spacing=10)

            def recargar_listas():
                lista_agenda.controls.clear()
                f_str = fecha_activa[0].strftime("%Y-%m-%d")
                clases = AppDB.obtener_agenda_rango(datetime.date.today().strftime("%Y-%m-%d"), (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")) if modo_agenda[0] == "30" else AppDB.obtener_todas_las_clases_dia(f_str)
                for c in clases:
                    if not c.get('is_blocked'):
                        lista_agenda.controls.append(ft.Container(content=ft.Row([ft.Column([ft.Text(f"{c['start_time']} - {c['service_name']}", weight="bold")]), ft.Container(expand=True), ft.IconButton(ft.icons.DELETE, icon_color="red", on_click=lambda e, cid=c['id']: (AppDB.eliminar_clase(cid), recargar_listas()))]), bgcolor="white", padding=15, border_radius=10))
                
                lista_bloqueos.controls.clear()
                for b in AppDB.obtener_dias_bloqueados():
                    lista_bloqueos.controls.append(ft.Container(content=ft.Row([ft.Icon(ft.icons.BLOCK, color="red"), ft.Text(b['class_date']), ft.Container(expand=True), ft.IconButton(ft.icons.DELETE, on_click=lambda e, bid=b['id']: (AppDB.desbloquear_dia(bid), recargar_listas()))]), bgcolor="white", padding=15, border_radius=10))
                page.update()

            def al_cambiar_fecha_admin(e):
                if dp_admin.value:
                    fecha_activa[0] = dp_admin.value
                    txt_fecha_top.value = fecha_activa[0].strftime("%Y-%m-%d")
                    modo_agenda[0] = "dia"
                    recargar_listas()

            # Calendarios con método universal .pick_date()
            dp_admin = ft.DatePicker(on_change=al_cambiar_fecha_admin)
            page.overlay.append(dp_admin)

            def accion_publicar(e):
                if drop_serv.value and drop_hora.value:
                    AppDB.crear_clase(drop_serv.value, fecha_activa[0].strftime("%Y-%m-%d"), drop_hora.value, txt_inst.value, txt_cupo.value)
                    recargar_listas()

            txt_fecha_bloqueo = ft.TextField(label="Fecha a bloquear", read_only=True, expand=True)
            def al_cambio_bloqueo(e):
                if dp_bloqueo.value: txt_fecha_bloqueo.value = dp_bloqueo.value.strftime("%Y-%m-%d"); page.update()
            
            dp_bloqueo = ft.DatePicker(on_change=al_cambio_bloqueo)
            page.overlay.append(dp_bloqueo)

            tab_crear = ft.Tab(text="Crear", content=ft.Container(padding=20, content=ft.Column([drop_serv, drop_hora, ft.Row([txt_inst, txt_cupo]), ft.ElevatedButton("Publicar", bgcolor=COLOR_RESPIRO, color="white", width=float('inf'), on_click=accion_publicar)])))
            tab_agenda = ft.Tab(text="Agenda", content=ft.Container(padding=20, content=lista_agenda))
            tab_bloqueos = ft.Tab(text="Cierres", content=ft.Container(padding=20, content=ft.Column([ft.Row([txt_fecha_bloqueo, ft.IconButton(ft.icons.CALENDAR_MONTH, on_click=lambda _: dp_bloqueo.pick_date())]), ft.ElevatedButton("Bloquear", bgcolor="red", color="white", width=float('inf'), on_click=lambda _: (AppDB.bloquear_dia(txt_fecha_bloqueo.value), recargar_listas()))])))

            page.views.append(ft.View("/admin", bgcolor=COLOR_BG_CLARO, padding=0, controls=[
                ft.Container(bgcolor="white", padding=20, content=ft.Row([ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/login")), ft.Text("Admin", size=22, weight="bold"), ft.Container(expand=True), txt_fecha_top, ft.IconButton(ft.icons.CALENDAR_MONTH, on_click=lambda _: dp_admin.pick_date())])),
                ft.Tabs(expand=True, tabs=[tab_crear, tab_agenda, tab_bloqueos])
            ]))
            recargar_listas()

        page.update()

    def view_pop(e):
        page.views.pop()
        page.go(page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8080))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0", assets_dir="assets")
