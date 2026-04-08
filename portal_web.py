import flet as ft
import os
import datetime 
import random 
from supa_config import guardar_cita, obtener_citas, borrar_cita 

BG_COLOR = "#2D3E6B"        
CARD_COLOR = "#0C1533"      
ACCENT_COLOR = "#D200AC"    
MUTED_COLOR = "#1D284C"     
TEXT_WHITE = ft.Colors.WHITE

# ¡CORRECCIÓN! Usamos códigos Hexadecimales puros para evitar errores de versión
RGB_NEON_COLORS = [
    "#FF003C", # Rojo Neón
    "#00FF33", # Verde Neón
    "#00E5FF", # Azul/Cyan Neón
    "#B200FF", # Morado Neón
    "#FF00FF", # Magenta Neón
    "#FFFF00"  # Amarillo Neón
]

servicios_disponibles = {
    "💆‍♀️ Masajes": {
        "Relajantes": 500, "Descontracturantes": 600, "Deportivo": 700, "Holístico": 650, "Aromaterapia": 550
    },
    "🧖‍♀️ Faciales": {
        "Limpieza profunda": 400, "Hidratante": 450, "Anti-acné": 500, "Anti-edad": 550
    },
    "✨ Corporales": {
        "Cavitación": 800, "Radiofrecuencia": 750, "PRP (plasma)": 1200, "Lipoenzimas": 1500
    }
}

header_logo_src = "fisik.png" 

def main(page: ft.Page):
    page.title = "Fisi-K Center"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_COLOR
    page.locale = "es" 
    page.theme = ft.Theme(color_scheme_seed=ACCENT_COLOR) 
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window.width = 400
    page.window.height = 750
    page.scroll = "adaptive"

    fecha_val = hora_val = servicio_val = "" 
    header_logo = ft.Image(src=header_logo_src, width=120, height=120, fit="contain")

    def cambiar_vista(vista_activa):
        for v in [vista_inicio, vista_paso1, vista_paso2, vista_paso3, vista_cancelar, vista_lealtad, vista_exito]:
            v.visible = False
        vista_activa.visible = True
        page.update()

    def reiniciar_proceso(e):
        nonlocal fecha_val, hora_val, servicio_val
        fecha_val = hora_val = servicio_val = ""
        texto_fecha_sel.value = "Ninguna fecha seleccionada"
        contenedor_horarios.controls.clear()
        btn_siguiente_1.disabled = btn_siguiente_2.disabled = True
        grid_servicios.controls.clear()
        grid_servicios.controls.append(ft.Text("👈 Toca una categoría arriba", italic=True, color=ft.Colors.WHITE54))
        for btn in row_categorias.controls:
            btn.bgcolor = CARD_COLOR
            btn.color = TEXT_WHITE
        input_nombre.value = input_telefono.value = ""
        cambiar_vista(vista_inicio)

    vista_inicio = ft.Column([
        ft.Text("¿QUÉ DESEAS HACER?", size=14, weight="bold", color=ft.Colors.WHITE54),
        ft.Container(height=10),
        ft.ElevatedButton("Agendar Nueva Cita", icon=ft.Icons.CALENDAR_MONTH, bgcolor=ACCENT_COLOR, color=TEXT_WHITE, style=ft.ButtonStyle(padding=20, shape=ft.RoundedRectangleBorder(radius=15)), width=280, on_click=lambda _: cambiar_vista(vista_paso1)),
        ft.Container(height=10),
        ft.ElevatedButton("Cancelar mi Cita", icon=ft.Icons.CANCEL, bgcolor=CARD_COLOR, color=TEXT_WHITE, style=ft.ButtonStyle(padding=20, shape=ft.RoundedRectangleBorder(radius=15)), width=280, on_click=lambda _: cambiar_vista(vista_cancelar)),
        ft.Container(height=10),
        ft.ElevatedButton("Mi Plan de Lealtad", icon=ft.Icons.FAVORITE, bgcolor=CARD_COLOR, color=TEXT_WHITE, style=ft.ButtonStyle(padding=20, shape=ft.RoundedRectangleBorder(radius=15)), width=280, on_click=lambda _: cambiar_vista(vista_lealtad))
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=True)

    texto_fecha_sel = ft.Text("Ninguna fecha seleccionada", italic=True, color=ft.Colors.WHITE54)
    contenedor_horarios = ft.Row(spacing=10, run_spacing=10, alignment=ft.MainAxisAlignment.CENTER, wrap=True, width=380)
    btn_siguiente_1 = ft.ElevatedButton("Siguiente Paso ➡️", bgcolor=ACCENT_COLOR, color=TEXT_WHITE, disabled=True, on_click=lambda _: cambiar_vista(vista_paso2))

    def seleccionar_hora(e, hora):
        nonlocal hora_val
        hora_val = hora
        for btn in contenedor_horarios.controls:
            if btn.data == hora:
                btn.bgcolor, btn.color, btn.icon_color = ACCENT_COLOR, TEXT_WHITE, TEXT_WHITE
            elif not btn.disabled:
                btn.bgcolor, btn.color, btn.icon_color = CARD_COLOR, TEXT_WHITE, ACCENT_COLOR
        btn_siguiente_1.disabled = False
        page.update()

    def mostrar_horarios(fecha):
        contenedor_horarios.controls.clear()
        todas_las_horas = ["10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM"]
        try:
            horas_ocupadas = [c.get('hora') for c in obtener_citas() if c.get('fecha') == fecha]
        except:
            horas_ocupadas = [] 

        ahora_mx = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
        fecha_hoy_str = ahora_mx.strftime("%Y-%m-%d")

        for h in todas_las_horas:
            hora_formato = datetime.datetime.strptime(h, "%I:%M %p").time()
            ya_paso = (fecha == fecha_hoy_str) and (hora_formato <= ahora_mx.time())
            if (h in horas_ocupadas) or ya_paso:
                contenedor_horarios.controls.append(ft.ElevatedButton(h, data=h, icon=ft.Icons.LOCK, width=115, disabled=True, color=ft.Colors.WHITE30, bgcolor=MUTED_COLOR, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))))
            else:
                contenedor_horarios.controls.append(ft.ElevatedButton(h, data=h, icon=ft.Icons.RADIO_BUTTON_UNCHECKED, icon_color=ACCENT_COLOR, color=TEXT_WHITE, bgcolor=CARD_COLOR, width=115, on_click=lambda e, hb=h: seleccionar_hora(e, hb), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))))
        page.update()

    def cambiar_fecha(e):
        nonlocal fecha_val, hora_val
        if e.control.value:
            fecha_val = e.control.value.strftime("%Y-%m-%d")
            hora_val = ""
            btn_siguiente_1.disabled = True
            texto_fecha_sel.value, texto_fecha_sel.italic, texto_fecha_sel.color, texto_fecha_sel.weight = f"📅 Fecha elegida: {fecha_val}", False, ACCENT_COLOR, "bold"
            mostrar_horarios(fecha_val)
            page.update()

    ahora_mx_inicio = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
    date_picker = ft.DatePicker(first_date=ahora_mx_inicio, on_change=cambiar_fecha, help_text="Selecciona tu día", cancel_text="Cancelar", confirm_text="Aceptar")
    
    vista_paso1 = ft.Column([
        ft.Text("PASO 1 DE 3", size=12, color=ACCENT_COLOR, weight="bold"),
        ft.Text("Elige Día y Hora", size=20, weight="bold"),
        ft.ElevatedButton("Abrir Calendario", icon=ft.Icons.CALENDAR_MONTH, bgcolor=CARD_COLOR, color=TEXT_WHITE, on_click=lambda _: page.show_dialog(date_picker)),
        texto_fecha_sel, ft.Divider(color=CARD_COLOR), contenedor_horarios, ft.Container(height=20),
        ft.
