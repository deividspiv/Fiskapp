import flet as ft
from supa_config import guardar_cita 
import os

# --- TU MENÚ DE SERVICIOS (Basado en tu imagen) ---
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

def main(page: ft.Page):
    page.title = "Agenda tu Cita - Fisi-K Center"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window.width = 400
    page.window.height = 750
    page.scroll = "adaptive"

    fecha_val = ""
    hora_val = ""
    servicio_val = "" 

    header_logo = ft.Image(src="fisik.png", width=120, height=120, fit="contain", visible=True)
    
    texto_resumen = ft.Column([
        ft.Text("Ninguna fecha seleccionada", italic=True),
        ft.Text("", weight="bold", color=ft.Colors.BLUE),
        ft.Text("", weight="bold", color=ft.Colors.PURPLE), 
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    input_nombre = ft.TextField(label="Tu Nombre Completo", icon=ft.Icons.PERSON, visible=False)
    input_telefono = ft.TextField(label="Tu WhatsApp (ej: 777...)", icon=ft.Icons.PHONE, visible=False)
    
    contenedor_horarios = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

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

    panels_servicios = []
    for categoria, tipos in servicios_disponibles.items():
        column_tipos = ft.Column(spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        for tipo in tipos:
            column_tipos.controls.append(
                ft.ElevatedButton(
                    tipo,
                    width=250,
                    on_click=lambda e, s=f"{categoria.split(' ')[1]} - {tipo}": seleccionar_servicio(s)
                )
            )
            
        panels_servicios.append(
            ft.ExpansionPanel(
                header=ft.ListTile(
                    title=ft.Text(categoria, weight="bold", size=18)
                ),
                content=column_tipos
            )
        )

    # ¡AQUÍ ESTÁ LA LÍNEA CORREGIDA! Cambiamos panels= por controls=
    expansion_list = ft.ExpansionPanelList(controls=panels_servicios, expand_icon_color=ft.Colors.PURPLE)
    
    contenedor_servicios = ft.Column([
        ft.Text("Paso 3: Selecciona tu servicio", size=18, weight="bold", color=ft.Colors.PURPLE_400),
        expansion_list
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)


    def confirmar_reserva(e):
        if not input_nombre.value or not input_telefono.value or not servicio_val:
            page.show_dialog(ft.SnackBar(ft.Text("Por favor, llena todos los campos y selecciona un servicio."), open=True))
            return

        btn_confirmar.disabled = True
        btn_confirmar.text = "Guardando..."
        page.update()

        try:
            guardar_cita(fecha_val, hora_val, input_nombre.value, input_telefono.value, servicio_val)
            
            page.controls.clear()
            page.add(
                ft.Container(height=50),
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=100),
                ft.Text("¡Cita Confirmada!", size=30, weight="bold"),
                ft.Text(f"Te esperamos el {fecha_val}", size=18),
                ft.Text(f"a las {hora_val}", size=18, color=ft.Colors.BLUE, weight="bold"),
                ft.Text(f"Para tu servicio de:", size=16),
                ft.Text(f"{servicio_val}", size=18, color=ft.Colors.PURPLE_800, weight="bold"),
                ft.Divider(height=40),
                ft.Text("Ya puedes cerrar esta ventana.", italic=True)
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
        texto_resumen.visible = True
        page.update()

    def mostrar_horarios(fecha):
        horarios = ["10:00 AM", "11:30 AM", "01:00 PM", "04:00 PM"]
        contenedor_horarios.controls.clear()
        
        for h in horarios:
            contenedor_horarios.controls.append(
                ft.ElevatedButton(
                    f"Elegir las {h}",
                    icon=ft.Icons.ACCESS_TIME,
                    width=250,
                    on_click=lambda e, hora_btn=h: seleccionar_hora(hora_btn)
                )
            )
        page.update()

    def cambiar_fecha(e):
        nonlocal fecha_val
        if e.control.value:
            fecha_val = e.control.value.strftime("%Y-%m-%d")
            texto_resumen.controls[0].value = f"Fecha: {fecha_val}"
            texto_resumen.controls[0].italic = False
            texto_resumen.visible = True
            
            texto_resumen.controls[1].value = ""
            texto_resumen.controls[2].value = ""
            contenedor_horarios.visible = True
            contenedor_servicios.visible = False
            input_nombre.visible = False
            input_telefono.visible = False
            btn_confirmar.visible = False
            
            mostrar_horarios(fecha_val)
            page.update()

    date_picker = ft.DatePicker(on_change=cambiar_fecha)

    page.add(
        ft.Container(height=20),
        header_logo,
        ft.Text("Reserva tu espacio", size=24, weight="bold"),
        ft.Divider(height=20, color=ft.Colors.PURPLE_200),
        
        ft.ElevatedButton("Paso 1: Elegir Día", icon=ft.Icons.CALENDAR_TODAY, color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE, on_click=lambda _: page.show_dialog(date_picker)),
        ft.Container(height=10),
        texto_resumen,
        
        ft.Divider(height=20, color=ft.Colors.PURPLE_200),
        contenedor_horarios, 
        
        contenedor_servicios, 
        
        ft.Divider(height=20, visible=False),
        input_nombre, 
        input_telefono, 
        
        ft.Container(height=30),
        btn_confirmar 
    )

# Le decimos a Flet que escuche al servidor de internet (0.0.0.0)
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.environ.get("PORT", 8080)), host="0.0.0.0")
