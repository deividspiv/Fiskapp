import flet as ft
import os
import datetime
from supa_config import obtener_citas, marcar_asistencia, guardar_cita

PIN_SECRETO = "2026"  
BG_COLOR = "#0C1533"
CARD_COLOR = "#1D284C"
ACCENT_COLOR = "#89F336" 
TEXT_WHITE = ft.Colors.WHITE

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
    # Quitamos el padding horizontal extra para que quepan los 4 botones
    page.padding = ft.padding.all(10)

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

    # --- 2. VISTAS DEL PANEL ---
    lista_agenda_ui = ft.Column(spacing=15)
    lista_historial_ui = ft.Column(spacing=15)
    texto_fecha_ui = ft.Text(f"AGENDA: {fecha_consulta}", size=16, weight="bold", color=ACCENT_COLOR)
    texto_ganancias = ft.Text("$0", size=40, weight="bold", color=ACCENT_COLOR)
    texto_pacientes = ft.Text("0 pacientes", size=18, color=TEXT_WHITE)

    def confirmar_asistencia(e, cita_id, boton):
        try:
            boton.disabled = True
            boton.content = ft.Text("Aprobado ✅", weight="bold")
            boton.bgcolor = ft.Colors.GREEN_700
            page.update()
            marcar_asistencia(cita_id)
            page.show_dialog(ft.SnackBar(ft.Text("Asistencia y sellito registrado."), bgcolor=ft.Colors.GREEN, open=True))
        except Exception as ex:
            page.show_dialog(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED, open=True))
            boton.disabled = False
            page.update()

    def crear_tarjeta_cita(cita):
        ya_asistio = cita.get('asistio', False)
        btn_wa = ft.IconButton(icon=ft.Icons.CHAT, icon_color=ft.Colors.GREEN_400, on_click=lambda e: page.launch_url(f"https://wa.me/52{cita.get('cliente_telefono')}?text=Hola {cita.get('cliente_nombre')}, te escribimos de Fisi-K Center."))
        btn_asistencia = ft.ElevatedButton(
            content=ft.Text("Aprobado ✅" if ya_asistio else "Dar Sellito", weight="bold"), 
            bgcolor=ft.Colors.GREEN_700 if ya_asistio else ACCENT_COLOR, 
            color=TEXT_WHITE if ya_asistio else BG_COLOR, 
            disabled=ya_asistio, 
            on_click=lambda e, cid=cita.get('id'): confirmar_asistencia(e, cid, e.control)
        )
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
            todas.reverse() 
            for c in todas[:30]:
                lista_historial_ui.controls.append(crear_tarjeta_cita(c))
        except Exception as ex:
            lista_historial_ui.controls.append(ft.Text(f"Error: {ex}", color=ft.Colors.RED))
        page.update()

    def cargar_finanzas():
        try:
            todas = obtener_citas()
            completadas = [c for c in todas if c.get('asistio') == True]
            total_dinero = 0
            
            for c in completadas:
                servicio_str = c.get('servicio', '')
                if '$' in servicio_str:
                    try:
                        precio = int(servicio_str.split('$')[-1].replace(')', '').replace(' MXN', '').strip())
                        total_dinero += precio
                    except: pass
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

    # --- VISTAS EXISTENTES ---
    def cambiar_fecha_admin(e):
        nonlocal fecha_consulta
        if e.control.value:
            fecha_consulta = e.control.value.strftime("%Y-%m-%d")
            texto_fecha_ui.value = f"AGENDA: {fecha_consulta}"
            cargar_agenda()

    date_picker_admin = ft.DatePicker(on_change=cambiar_fecha_admin)
    btn_buscar_fecha = ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, icon_color=ACCENT_COLOR, on_click=lambda _: page.show_dialog(date_picker_admin))

    vista_agenda = ft.Column([ft.Row([texto_fecha_ui, btn_buscar_fecha], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), lista_agenda_ui], visible=True)
    vista_historial = ft.Column([ft.Text("ÚLTIMAS 30 CITAS", size=16, weight="bold", color=ACCENT_COLOR), lista_historial_ui], visible=False)
    vista_finanzas = ft.Column([
        ft.Text("RESUMEN DE GANANCIAS", size=16, weight="bold", color=ACCENT_COLOR), ft.Container(height=20),
        ft.Container(content=ft.Column([ft.Icon(ft.Icons.ATTACH_MONEY, size=50, color=ACCENT_COLOR), ft.Text("Ingresos Brutos", color=ft.Colors.WHITE54), texto_ganancias, ft.Divider(color=ft.Colors.WHITE24), texto_pacientes], horizontal_alignment=ft.CrossAxisAlignment.CENTER), bgcolor=CARD_COLOR, padding=30, border_radius=20, width=380, border=ft.border.all(1, ACCENT_COLOR))
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    # ==========================================
    # ¡NUEVO! VISTA DE AGENDAR (INTELIGENTE)
    # ==========================================
    servicios_admin = [
        "Masajes - Relajantes ($500)", "Masajes - Descontracturantes ($600)", "Masajes - Deportivo ($700)", "Masajes - Holístico ($650)",
        "Limpiezas - Profunda ($400)", "Limpiezas - Hidratante ($450)", "Limpiezas - Anti-acné ($500)", "Limpiezas - Anti-edad ($550)",
        "Corporal - Cavitación ($800)", "Corporal - Radiofrecuencia ($750)", "Corporal - PRP ($1200)", "Corporal - Lipoenzimas ($1500)"
    ]
    
    fecha_nueva_val = ahora_mx.strftime("%Y-%m-%d")
    texto_fecha_nueva = ft.Text(f"📅 Fecha: {fecha_nueva_val}", size=14, weight="bold", color=ACCENT_COLOR)
    
    input_admin_hora = ft.Dropdown(label="Buscando horarios...", bgcolor=CARD_COLOR, border_color=ACCENT_COLOR, color=TEXT_WHITE, border_radius=15, disabled=True)
    input_admin_nombre = ft.TextField(label="Nombre del Paciente", icon=ft.Icons.PERSON, bgcolor=CARD_COLOR, border_color=ACCENT_COLOR, color=TEXT_WHITE, border_radius=15)
    input_admin_telefono = ft.TextField(label="Teléfono (Pon 0000000000 si no tiene)", value="0000000000", icon=ft.Icons.PHONE, bgcolor=CARD_COLOR, border_color=ACCENT_COLOR, color=TEXT_WHITE, border_radius=15)
    input_admin_servicio = ft.Dropdown(label="Servicio a realizar", options=[ft.dropdown.Option(s) for s in servicios_admin], bgcolor=CARD_COLOR, border_color=ACCENT_COLOR, color=TEXT_WHITE, border_radius=15)

    def actualizar_horas_disponibles(fecha_str):
        todas_las_horas = ["10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM"]
        try:
            citas_existentes = obtener_citas()
            horas_ocupadas = [c.get('hora') for c in citas_existentes if c.get('fecha') == fecha_str]
        except:
            horas_ocupadas = []

        ahora_mx_calc = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
        fecha_hoy_str = ahora_mx_calc.strftime("%Y-%m-%d")

        opciones_libres = []
        for h in todas_las_horas:
            hora_formato = datetime.datetime.strptime(h, "%I:%M %p").time()
            ya_paso = (fecha_str == fecha_hoy_str) and (hora_formato <= ahora_mx_calc.time())
            if (h not in horas_ocupadas) and not ya_paso:
                opciones_libres.append(ft.dropdown.Option(h))

        input_admin_hora.options = opciones_libres
        input_admin_hora.value = None
        input_admin_hora.disabled = False
        
        if not opciones_libres:
            input_admin_hora.label = "Todo ocupado este día ❌"
            input_admin_hora.disabled = True
        else:
            input_admin_hora.label = "Selecciona la hora disponible"
            
        page.update()

    def cambiar_fecha_nueva(e):
        nonlocal fecha_nueva_val
        if e.control.value:
            fecha_nueva_val = e.control.value.strftime("%Y-%m-%d")
            texto_fecha_nueva.value = f"📅 Fecha: {fecha_nueva_val}"
            input_admin_hora.label = "Buscando horarios..."
            input_admin_hora.disabled = True
            page.update()
            actualizar_horas_disponibles(fecha_nueva_val)

    date_picker_nueva = ft.DatePicker(first_date=ahora_mx, on_change=cambiar_fecha_nueva)
    btn_abrir_calendario_nuevo = ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, icon_color=ACCENT_COLOR, on_click=lambda _: page.show_dialog(date_picker_nueva))

    def guardar_cita_manual(e):
        if not input_admin_nombre.value or not input_admin_hora.value or not input_admin_servicio.value:
            page.show_dialog(ft.SnackBar(ft.Text("Por favor, llena los datos principales."), bgcolor=ft.Colors.RED, open=True))
            return
        btn_guardar_manual.disabled = True
        btn_guardar_manual.content = ft.Text("Guardando...", weight="bold")
        page.update()
        try:
            guardar_cita(fecha_nueva_val, input_admin_hora.value, input_admin_nombre.value, input_admin_telefono.value, input_admin_servicio.value)
            page.show_dialog(ft.SnackBar(ft.Text("¡Cita agendada con éxito!"), bgcolor=ft.Colors.GREEN, open=True))
            input_admin_nombre.value = "" 
            input_admin_telefono.value = "0000000000"
            navegar_tab(None, 0) # Regresa a la agenda
        except Exception as ex:
            page.show_dialog(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED, open=True))
        btn_guardar_manual.disabled = False
        btn_guardar_manual.content = ft.Text("Agendar Cita", weight="bold")
        page.update()

    btn_guardar_manual = ft.ElevatedButton(content=ft.Text("Agendar Cita", weight="bold"), bgcolor=ACCENT_COLOR, color=BG_COLOR, on_click=guardar_cita_manual, style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=15)))

    vista_nueva = ft.Column([
        ft.Text("AGENDAR MANUALMENTE", size=16, weight="bold", color=ACCENT_COLOR),
        ft.Text("Solo verás horas desocupadas.", color=ft.Colors.WHITE54, size=12),
        ft.Container(
            content=ft.Row([texto_fecha_nueva, btn_abrir_calendario_nuevo], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=CARD_COLOR, padding=5, border_radius=15, border=ft.border.all(1, ft.Colors.WHITE10)
        ),
        input_admin_hora, input_admin_nombre, input_admin_telefono, input_admin_servicio,
        ft.Container(height=10),
        btn_guardar_manual
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    # --- CONTROL DE NAVEGACIÓN (BOTONES AJUSTADOS PARA 1 FILA) ---
    def navegar_tab(e, indice):
        vista_agenda.visible = (indice == 0)
        vista_historial.visible = (indice == 1)
        vista_finanzas.visible = (indice == 2)
        vista_nueva.visible = (indice == 3) 
        
        btn_agenda.bgcolor = ACCENT_COLOR if indice == 0 else CARD_COLOR
        btn_historial.bgcolor = ACCENT_COLOR if indice == 1 else CARD_COLOR
        btn_finanzas.bgcolor = ACCENT_COLOR if indice == 2 else CARD_COLOR
        btn_nueva.bgcolor = ACCENT_COLOR if indice == 3 else CARD_COLOR
        
        btn_agenda.color = BG_COLOR if indice == 0 else TEXT_WHITE
        btn_historial.color = BG_COLOR if indice == 1 else TEXT_WHITE
        btn_finanzas.color = BG_COLOR if indice == 2 else TEXT_WHITE
        btn_nueva.color = BG_COLOR if indice == 3 else TEXT_WHITE
        
        if indice == 0: cargar_agenda()
        if indice == 1: cargar_historial()
        if indice == 2: cargar_finanzas()
        if indice == 3: actualizar_horas_disponibles(fecha_nueva_val) # Calcula horas al entrar a la pestaña
        
        page.update()

    # Estilo especial para hacer los botones compactos y que quepan en 1 fila
    estilo_pestañas = ft.ButtonStyle(padding=0, shape=ft.RoundedRectangleBorder(radius=10))

    btn_agenda = ft.ElevatedButton(content=ft.Text("📅 Agenda", size=11, weight="bold"), bgcolor=ACCENT_COLOR, color=BG_COLOR, style=estilo_pestañas, width=88, on_click=lambda e: navegar_tab(e, 0))
    btn_historial = ft.ElevatedButton(content=ft.Text("📚 Hist", size=11, weight="bold"), bgcolor=CARD_COLOR, color=TEXT_WHITE, style=estilo_pestañas, width=80, on_click=lambda e: navegar_tab(e, 1))
    btn_finanzas = ft.ElevatedButton(content=ft.Text("📈 $$$", size=11, weight="bold"), bgcolor=CARD_COLOR, color=TEXT_WHITE, style=estilo_pestañas, width=80, on_click=lambda e: navegar_tab(e, 2))
    btn_nueva = ft.ElevatedButton(content=ft.Text("➕ Nueva", size=11, weight="bold"), bgcolor=CARD_COLOR, color=TEXT_WHITE, style=estilo_pestañas, width=85, on_click=lambda e: navegar_tab(e, 3))

    menu_tabs_custom = ft.Row([btn_agenda, btn_historial, btn_finanzas, btn_nueva], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    pantalla_admin = ft.Column([
        menu_tabs_custom, ft.Divider(color=ft.Colors.WHITE10),
        vista_agenda, vista_historial, vista_finanzas, vista_nueva
    ], visible=False)

    page.add(pantalla_login, pantalla_admin)

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.environ.get("PORT", 8080)), host="0.0.0.0", assets_dir=".")
