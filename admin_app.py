import flet as ft
import os
import datetime
from supa_config import obtener_citas, marcar_asistencia

PIN_SECRETO = "2026"  
BG_COLOR = "#0C1533"
CARD_COLOR = "#1D284C"
ACCENT_COLOR = "#89F336" 
TEXT_WHITE = ft.Colors.WHITE

# Respaldo de precios para las citas viejas que no tenían el $ guardado
PRECIOS_HISTORICOS = {
    "Relajantes": 500, "Descontracturantes": 600, "Deportivo": 700, "Holístico": 650, "Aromaterapia": 550,
    "Limpieza profunda": 400, "Hidratante": 450, "Anti-acné": 500, "Anti-edad": 550,
    "Cavitación": 800, "Radiofrecuencia": 750, "PRP (plasma)": 1200, "Lipoenzimas": 1500
}

def main(page: ft.Page):
    page.title = "Fisi-K Admin"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_COLOR
    page.locale = "es"
    page.theme = ft.Theme(color_scheme_seed=ACCENT_COLOR)
    page.scroll = "adaptive"
    page.window.width = 400
    page.window.height = 750

    ahora_mx = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
    fecha_consulta = ahora_mx.strftime("%Y-%m-%d")

    # --- 1. PANTALLA DE LOGIN ---
    input_pin = ft.TextField(label="PIN de Seguridad", password=True, can_reveal_password=True, text_align=ft.TextAlign.CENTER, keyboard_type=ft.KeyboardType.NUMBER, width=250, border_radius=15, border_color=ACCENT_COLOR)
    texto_error = ft.Text("", color=ft.Colors.RED_400, visible=False)

    def verificar_pin(e):
        if input_pin.value == PIN_SECRETO:
            pantalla_login.visible = False
            pantalla_admin.visible = True
            cargar_agenda()
        else:
            texto_error.value, texto_error.visible, input_pin.value = "PIN Incorrecto.", True, ""
        page.update()

    btn_entrar = ft.ElevatedButton("Entrar al Panel", bgcolor=ACCENT_COLOR, color=BG_COLOR, on_click=verificar_pin)

    pantalla_login = ft.Column([
        ft.Container(height=100), ft.Icon(ft.Icons.LOCK_OUTLINE, size=80, color=ACCENT_COLOR),
        ft.Text("ACCESO RESTRINGIDO", size=20, weight="bold"), ft.Text("Solo personal autorizado", color=ft.Colors.WHITE54),
        ft.Container(height=20), input_pin, texto_error, btn_entrar
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=True)

    # --- 2. PESTAÑAS DEL PANEL ---
    lista_agenda_ui = ft.Column(spacing=15)
    lista_historial_ui = ft.Column(spacing=15)
    texto_fecha_ui = ft.Text(f"AGENDA: {fecha_consulta}", size=16, weight="bold", color=ACCENT_COLOR)
    
    # Textos de finanzas
    texto_ganancias = ft.Text("$0", size=40, weight="bold", color=ACCENT_COLOR)
    texto_pacientes = ft.Text("0 pacientes", size=18, color=TEXT_WHITE)

    def confirmar_asistencia(e, cita_id, boton):
        try:
            boton.disabled, boton.text, boton.bgcolor = True, "Aprobado ✅", ft.Colors.GREEN_700
            page.update()
            marcar_asistencia(cita_id)
            page.show_dialog(ft.SnackBar(ft.Text("Asistencia y sellito registrado."), bgcolor=ft.Colors.GREEN, open=True))
        except Exception as ex:
            page.show_dialog(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED, open=True))

    def crear_tarjeta_cita(cita):
        ya_asistio = cita.get('asistio', False)
        btn_wa = ft.IconButton(icon=ft.Icons.CHAT, icon_color=ft.Colors.GREEN_400, on_click=lambda e: page.launch_url(f"https://wa.me/52{cita.get('cliente_telefono')}?text=Hola {cita.get('cliente_nombre')}, te escribimos de Fisi-K Center."))
        btn_asistencia = ft.ElevatedButton("Aprobado ✅" if ya_asistio else "Dar Sellito", bgcolor=ft.Colors.GREEN_700 if ya_asistio else ACCENT_COLOR, color=TEXT_WHITE if ya_asistio else BG_COLOR, disabled=ya_asistio, on_click=lambda e, cid=cita.get('id'): confirmar_asistencia(e, cid, e.control))
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Text(f"📅 {cita.get('fecha')} - {cita.get('hora')}", size=14, weight="bold", color=ACCENT_COLOR), btn_wa], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(cita.get('cliente_nombre', 'Cliente').upper(), size=16, weight="bold"),
                ft.Text(f"📞 {cita.get('cliente_telefono', 'S/N')}", color=ft.Colors.WHITE70),
                ft.Text(f"💆‍♀️ {cita.get('servicio', 'S/N')}", color=ft.Colors.WHITE70),
                ft.Divider(color=ft.Colors.WHITE24), btn_asistencia
            ]), bgcolor=CARD_COLOR, padding=15, border_radius=15, border=ft.border.all(1, ft.Colors.WHITE10)
        )

    def cargar_agenda():
        lista_agenda_ui.controls.clear()
        try:
            todas = obtener_citas()
            citas_dia = [c for c in todas if c.get('fecha') == fecha_consulta]
            citas_dia.sort(key=lambda x: datetime.datetime.strptime(x.get('hora', '10:00 AM'), "%I:%M %p"))
            if not citas_dia:
                lista_agenda_ui.controls.append(ft.Text("No hay citas para esta fecha.", color=ft.Colors.WHITE54, italic=True))
            for c in citas_dia:
                lista_agenda_ui.controls.append(crear_tarjeta_cita(c))
        except Exception as ex:
            lista_agenda_ui.controls.append(ft.Text(f"Error: {ex}", color=ft.Colors.RED))
        page.update()

    def cargar_historial():
        lista_historial_ui.controls.clear()
        try:
            todas = obtener_citas()
            # Mostramos las ultimas 30 citas, sin importar la fecha
            todas.reverse() 
            for c in todas[:30]:
                lista_historial_ui.controls.append(crear_tarjeta_cita(c))
        except Exception as ex:
            lista_historial_ui.controls.append(ft.Text(f"Error: {ex}", color=ft.Colors.RED))
        page.update()

    def cargar_finanzas():
        try:
            todas = obtener_citas()
            # Solo contamos los que SÍ asistieron y pagaron
            completadas = [c for c in todas if c.get('asistio') == True]
            total_dinero = 0
            
            for c in completadas:
                servicio_str = c.get('servicio', '')
                # Si tiene el $ en el nombre (como el nuevo portal)
                if '$' in servicio_str:
                    try:
                        precio = int(servicio_str.split('$')[-1].replace(')', '').replace(' MXN', '').strip())
                        total_dinero += precio
                    except: pass
                # Si es una cita vieja sin $, usamos el diccionario de respaldo
                else:
                    for nombre, precio in PRECIOS_HISTORICOS.items():
                        if nombre in servicio_str:
                            total_dinero += precio
                            break
                            
            texto_ganancias.value = f"${total_dinero:,.2f}"
            texto_pacientes.value = f"{len(completadas)} pacientes atendidos"
        except Exception as ex:
            texto_ganancias.value = "Error"
        page.update()

    # --- VISTAS DE PESTAÑAS ---
    def cambiar_fecha_admin(e):
        nonlocal fecha_consulta
        if e.control.value:
            fecha_consulta = e.control.value.strftime("%Y-%m-%d")
            texto_fecha_ui.value = f"AGENDA: {fecha_consulta}"
            cargar_agenda()

    date_picker_admin = ft.DatePicker(on_change=cambiar_fecha_admin)
    btn_buscar_fecha = ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, icon_color=ACCENT_COLOR, on_click=lambda _: page.show_dialog(date_picker_admin))

    vista_agenda = ft.Column([
        ft.Row([texto_fecha_ui, btn_buscar_fecha], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        lista_agenda_ui
    ], visible=True)

    vista_historial = ft.Column([
        ft.Text("ÚLTIMAS 30 CITAS", size=16, weight="bold", color=ACCENT_COLOR),
        lista_historial_ui
    ], visible=False)

    vista_finanzas = ft.Column([
        ft.Text("RESUMEN DE GANANCIAS", size=16, weight="bold", color=ACCENT_COLOR),
        ft.Container(height=20),
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ATTACH_MONEY, size=50, color=ACCENT_COLOR),
                ft.Text("Ingresos Brutos", color=ft.Colors.WHITE54),
                texto_ganancias,
                ft.Divider(color=ft.Colors.WHITE24),
                texto_pacientes
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=CARD_COLOR, padding=30, border_radius=20, width=380, border=ft.border.all(1, ACCENT_COLOR)
        )
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    def cambiar_tab(e):
        idx = e.control.selected_index
        vista_agenda.visible = (idx == 0)
        vista_historial.visible = (idx == 1)
        vista_finanzas.visible = (idx == 2)
        if idx == 0: cargar_agenda()
        if idx == 1: cargar_historial()
        if idx == 2: cargar_finanzas()
        page.update()

    tabs_menu = ft.Tabs(
        selected_index=0, animation_duration=300,
        tabs=[
            ft.Tab(text="📅 Agenda"),
            ft.Tab(text="📚 Historial"),
            ft.Tab(text="📈 Finanzas"),
        ],
        on_change=cambiar_tab
    )

    pantalla_admin = ft.Column([
        tabs_menu, ft.Divider(color=ft.Colors.TRANSPARENT),
        vista_agenda, vista_historial, vista_finanzas
    ], visible=False)

    page.add(pantalla_login, pantalla_admin)

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.environ.get("PORT", 8080)), host="0.0.0.0", assets_dir=".")
