import flet as ft
import os
import datetime 
from supa_config import guardar_cita, obtener_citas 

# --- CONFIGURACIÓN DE COLORES "DARK PREMIUM" ---
BG_COLOR = "#2D3E6B"        
CARD_COLOR = "#0C1533"      
ACCENT_COLOR = "#D200AC"    
MUTED_COLOR = "#1D284C"     
TEXT_WHITE = ft.Colors.WHITE

servicios_disponibles = {
    "💆‍♀️ Masajes": ["Relajantes", "Descontracturantes", "Deportivo", "Holístico", "Aromaterapia"],
    "🧖‍♀️ Limpiezas faciales": ["Limpieza profunda", "Hidratante", "Anti-acné", "Anti-edad"],
    "✨ Trat. Corporales": ["Cavitación", "Radiofrecuencia", "PRP (plasma)", "Lipoenzimas"]
}

header_logo_src = "fisik.png" 

def main(page: ft.Page):
    page.title = "Agenda tu Cita - Fisi-K Center"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_COLOR
    page.locale = "es" 
    page.theme = ft.Theme(color_scheme_seed=ACCENT_COLOR) 
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window.width = 400
    page.window.height = 750
    page.scroll = "adaptive"

    fecha_val = ""
    hora_val = ""
    servicio_val = "" 

    header_logo = ft.Image(src=header_logo_src, width=120, height=120, fit="contain", visible=True)
    
    # --- LÓGICA DE SELLITOS (LEALTAD) ---
    def consultar_sellitos(e):
        whatsapp = input_wa_sellitos.value
        if not whatsapp:
            page.show_dialog(ft.SnackBar(ft.Text("Pon tu WhatsApp para ver tus premios"), bgcolor=ACCENT_COLOR, open=True))
            return
        
        btn_verificar.disabled = True
        btn_verificar.text = "Buscando..."
        page.update()

        try:
            todas = obtener_citas()
            # Filtramos las del usuario que ya fueron marcadas como "asistio = True"
            citas_aprobadas = [c for c in todas if str(c.get('telefono')) == str(whatsapp) and c.get('asistio') == True]
            conteo = len(citas_aprobadas)
            
            grid_sellos.controls.clear()
            for i in range(1, 7):
                esta_lleno = i <= conteo
                grid_sellos.controls.append(
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.FAVORITE if esta_lleno else ft.Icons.FAVORITE_BORDER,
                            color=ACCENT_COLOR if esta_lleno else ft.Colors.WHITE24,
                            size=30
                        ),
                        width=50, height=50,
                        bgcolor=MUTED_COLOR if esta_lleno else ft.Colors.TRANSPARENT,
                        border=ft.border.all(1, ACCENT_COLOR if esta_lleno else ft.Colors.WHITE24),
                        border_radius=25,
                        alignment=ft.alignment.center
                    )
                )
            
            mensaje_lealtad.value = f"¡Llevas {conteo} de 6 masajes!\n" + ("¡Felicidades, el próximo es GRATIS!" if conteo >= 6 else "¡Sigue así!")
            mensaje_lealtad.visible = True
            grid_sellos.visible = True
            
        except Exception as ex:
            page.show_dialog(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED, open=True))
        
        btn_verificar.disabled = False
        btn_verificar.text = "Verificar Mis Sellos"
        page.update()

    # ¡ERROR CORREGIDO AQUÍ! Cambiamos prefix_text por hint_text
    input_wa_sellitos = ft.TextField(
        label="Tu WhatsApp", 
        hint_text="Ej: 777...", 
        width=250, 
        border_radius=15, 
        bgcolor=MUTED_COLOR,
        border_color=ACCENT_COLOR,
        color=TEXT_WHITE
    )
    btn_verificar = ft.ElevatedButton(
        "Verificar Mis Sellos", 
        bgcolor=ACCENT_COLOR, 
        color=TEXT_WHITE, 
        on_click=consultar_sellitos,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
    )
    grid_sellos = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, visible=False)
    mensaje_lealtad = ft.Text("", weight="bold", size=16, color=TEXT_WHITE, text_align=ft.TextAlign.CENTER, visible=False)

    tarjeta_lealtad = ft.Container(
        content=ft.Column([
            ft.Text("PROGRAMA DE LEALTAD", size=14, weight="bold", color=ACCENT_COLOR),
            ft.Text("6to Masaje GRATIS", size=18, weight="bold", color=TEXT_WHITE),
            input_wa_sellitos,
            btn_verificar,
            grid_sellos,
            mensaje_lealtad
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
        padding=20, border_radius=25, bgcolor=CARD_COLOR, width=380
    )

    # --- LÓGICA DE AGENDAR CITA ---
    texto_resumen = ft.Column([
        ft.Text("Ninguna fecha seleccionada", italic=True, color=ft.Colors.WHITE54),
        ft.Text("", weight="bold", color=TEXT_WHITE),
        ft.Text("", weight="bold", color=ACCENT_COLOR), 
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    def volver_a_hora(e):
        contenedor_servicios.visible = False
        input_nombre.visible = False
        input_telefono.visible = False
        btn_confirmar.visible = False
        btn_cambiar_hora.visible = False 
        
        contenedor_horarios.visible = True
        texto_resumen.controls[1].value = "" 
        texto_resumen.controls[2].value = "" 
        page.update()

    btn_cambiar_hora = ft.TextButton(
        "✏️ Cambiar Hora", 
        style=ft.ButtonStyle(color=ACCENT_COLOR), 
        visible=False, 
        on_click=volver_a_hora
    )

    input_nombre = ft.TextField(
        label="Tu Nombre Completo", icon=ft.Icons.PERSON, visible=False,
        bgcolor=CARD_COLOR, border_color=ACCENT_COLOR, color=TEXT_WHITE, border_radius=15
    )
