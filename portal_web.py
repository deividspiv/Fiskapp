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
        "Limpieza profunda", "Hidratante", "Anti-acné", "Anti-edad"
    ],
    "✨ Trat. Corporales": [
        "Cavitación", "Radiofrecuencia", "PRP (plasma)", "Lipoenzimas"
    ]
}

header_logo_src = "fisik.png" 

def main(page: ft.Page):
    page.title = "Agenda tu Cita - Fisi-K Center"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.locale = "es" # Mantenemos el calendario en español
    
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

    input_nombre = ft.TextField(label="Tu Nombre Completo", icon=ft.Icons.PERSON, visible=False)
    input_telefono = ft.TextField(label="Tu WhatsApp (ej: 777...)", icon=ft.Icons.PHONE, visible=False)
    
    contenedor_horarios = ft.Row(
        spacing=10, run_spacing=10, 
        alignment=ft.MainAxisAlignment.CENTER, 
        wrap=True, visible=False, width=380
    )

    def seleccionar_servicio(servicio_completo):
        nonlocal servicio_val
        servicio_val = servicio_completo
        texto_resumen.controls[2].value = f"Servicio: {servicio_completo}"
        
        contenedor_servicios.visible = False
        input_nombre.visible = True
        input_telefono.visible = True
        btn_confirmar.visible = True
        texto_resumen.controls[2].color = ft.Colors.PURPLE_800
        page.update()

    # --- LÓGICA DE 2 COLUMNAS (CON MINI-SCROLL ARREGLADO) ---
    col_categorias = ft.Column(spacing=10, width=150)
    
    col_subservicios = ft.Column([
        ft.Text("👈 Toca una categoría", italic=True, color=ft.Colors.GREY, size=13)
    ], width=180, spacing=8, scroll=ft.ScrollMode.ADAPTIVE, height=220)

    def mostrar_subservicios(categoria):
        col_subservicios.controls.clear()
        col_subservicios.controls.append(ft.Text(categoria, weight="bold", size=14, color=ft.Colors.PURPLE_600))
        
        for sub in servicios_disponibles[categoria]:
            col_subservicios.controls.append(
                ft.ElevatedButton(
                    content=ft.Text(sub, size=12),
                    width=180,
                    bgcolor=ft.Colors.PURPLE_50,
                    color=ft.Colors.PURPLE_900,
                    style=ft.ButtonStyle(padding=5),
                    on_click=lambda e, s=f"{categoria.split(' ')[1]} - {sub}": seleccionar_servicio(s)
                )
            )
        page.update()

    for cat in servicios_disponibles.keys():
        col_categorias.controls.append(
            ft.ElevatedButton(
                content=ft.Text(cat, size=13, text_align=ft.TextAlign.CENTER),
                width=150,
                style=ft.ButtonStyle(padding=5),
                on_click=lambda e, c=cat: mostrar_subservicios(c)
            )
        )

    contenedor_servicios = ft.Column([
        ft.Text("Paso 3: Selecciona tu servicio", size=18, weight="bold", color=ft.Colors.PURPLE_400),
        ft.Container(
            content=ft.Row([
                col_categorias,
                ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
                col_subservicios
            ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START),
            padding=10,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.PURPLE_100),
            width=380
        )
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    def confirmar_reserva(e):
        if not input_nombre.value or not input_telefono.value or not servicio_val:
            page.show_dialog(ft.SnackBar(ft.Text("Por favor, llena todos los campos."), open=True))
            return

        btn_confirmar.disabled = True
        btn_confirmar.text = "Guardando..."
        page.update()

        try:
            guardar_cita(fecha_val, hora_val, input_nombre.value, input_telefono.value, servicio_val)
            page.controls.clear() 
            page.add(
                ft.Column(
                    [
                        ft.Container(height=50),
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=100),
                        ft.Text("¡Cita Confirmada!", size=30, weight="bold"),
                        ft.Text(f"Te esperamos el {fecha_val}", size=18),
                        ft.Text(f"a las {hora_val}", size=18, color=ft.Colors.BLUE, weight="bold"),
                        ft.Text(f"Para tu servicio de:", size=16),
                        ft.Text(f"{servicio_val}", size=18, color=ft.Colors.PURPLE_800, weight="bold"),
                        ft.Divider(height=40, color=ft.Colors.PURPLE_200),
                        ft.Text("Ya puedes cerrar esta ventana.", italic=True, color=ft.Colors.GREY_600)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
            page.update()
        except Exception as ex:
            page.show_dialog(ft.SnackBar(ft.Text(f"Ups, error de conexión: {ex}"), open=True))
            btn_confirmar.disabled = False
            btn_confirmar.text = "Confirmar Cita"
            page.update()

    btn_confirmar = ft.ElevatedButton(
        "Confirmar Cita", 
        icon=ft.Icons.CHECK, 
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.GREEN, 
        visible=False, 
        on_click=confirmar_reserva
    )

    def seleccionar_hora(hora):
        nonlocal hora_val
        hora_val = hora
        texto_resumen.controls[1].value = f"Hora elegida: {hora}"
        
        contenedor_horarios.visible = False
        contenedor_servicios.visible = True
        btn_cambiar_hora.visible = True 
        texto_resumen.visible = True
        page.update()

    def mostrar_horarios(fecha):
        contenedor_horarios.controls.clear()
        texto_carga = ft.
