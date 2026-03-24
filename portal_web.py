import flet as ft
import os
import datetime 
from supa_config import guardar_cita, obtener_citas 

# --- TU MENÚ DE SERVICIOS ---
servicios_disponibles = {
    "💆‍♀️ Masajes": [
        "Relajantes", "Descontracturantes", "Deportivo", "Holístico", "Aromaterapia"
    ],
    "🧖‍♀️ Limpiezas faciales": [
        "Limpieza facial profunda", "Hidratante", "Anti-acné", "Anti-edad"
    ],
    "✨ Tratamientos Corporales y faciales": [
        "Cavitación", "Radiofrecuencia", "PRP (plasma rico)", "Lipoenzimas"
    ]
}

# --- CONFIGURACIÓN DE IMÁGENES ---
header_logo_src = "fisik.png" 

def main(page: ft.Page):
    page.title = "Agenda tu Cita - Fisi-K Center"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # --- ¡NUEVO! COLOR VERDE LIMA ---
    # Esto pintará tu calendario con el color de tu marca
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.LIME_600)
    
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window.width = 400
    page.window.height = 750
    page.scroll = "adaptive" 

    fecha_val = ""
    hora_val = ""
    servicio_val = "" 

    header_logo = ft.Image(src=header_logo_src, width=120, height=120, fit="contain", visible=True)
    
    texto_resumen = ft.Column([
        ft.Text("Ninguna fecha seleccionada", italic=True),
        ft.Text("", weight="bold", color=ft.Colors.BLUE),
        ft.Text("", weight="bold", color=ft.Colors.PURPLE), 
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

    btn_cambiar_hora = ft.TextButton("✏️ Cambiar Hora", visible=False, on_click=volver_a_hora)

    input_nombre = ft.TextField(
        label="Tu Nombre Completo", 
        icon=ft.Icons.PERSON, 
        visible=False
    )
    input_telefono = ft.TextField(
        label="Tu WhatsApp (ej: 777...)", 
        icon=ft.Icons.PHONE, 
        visible=False
    )
    
    contenedor_horarios = ft.Row(
        spacing=10, 
        run_spacing=10, 
        alignment=ft.MainAxisAlignment.CENTER,
