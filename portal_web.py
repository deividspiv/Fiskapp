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
    page.title = "Fisik-App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.locale = "es" 
    page.theme = ft.Theme(color_scheme_seed="#89F336") 
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window.width = 400
    page.window.height = 750

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

    # --- NUEVO: LÓGICA DE 2 COLUMNAS PARA EL MENÚ ---
    col_categorias = ft.Column(spacing=10, width=150)
    col_subservicios = ft.Column([
        ft.Text("👈 Toca una categoría", italic=True, color=ft.Colors.GREY, size=13)
    ], width=180, spacing=8)

    def mostrar_subservicios(categoria):
        col_subservicios.controls.clear()
        # Titulito para saber qué seleccionaste
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

    # Llenamos la columna izquierda con las categorías
    for cat in servicios_disponibles.keys():
        col_categorias.controls.append(
            ft.ElevatedButton(
                content=ft.Text(cat, size=13, text_align=ft.TextAlign.CENTER),
                width=150,
                style=ft.ButtonStyle(padding=5),
                on_click=lambda e, c=cat: mostrar_subservicios(c)
            )
        )

    # Armamos el contenedor de 2 columnas con un divisor en medio
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
    # ------------------------------------------------

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
        texto_carga = ft.Text("Verificando disponibilidad...", italic=True, color=ft.Colors.GREY)
        contenedor_horarios.controls.append(texto_carga)
        page.update()

        todas_las_horas = [
            "10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM",
            "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM"
        ]

        try:
            citas_existentes = obtener_citas()
            horas_ocupadas = [cita.get('hora') for cita in citas_existentes if cita.get('fecha') == fecha]
        except:
            horas_ocupadas = [] 

        contenedor_horarios.controls.clear()

        for h in todas_las_horas:
            if h in horas_ocupadas:
                contenedor_horarios.controls.append(
                    ft.ElevatedButton(
                        h, icon=ft.Icons.LOCK, width=115, disabled=True,
                        color=ft.Colors.GREY_500, bgcolor=ft.Colors.GREY_200, style=ft.ButtonStyle(padding=5)
                    )
                )
            else:
                contenedor_horarios.controls.append(
                    ft.ElevatedButton(
                        h, icon=ft.Icons.CHECK_CIRCLE_OUTLINE, icon_color=ft.Colors.GREEN_400,
                        width=115, on_click=lambda e, hora_btn=h: seleccionar_hora(hora_btn),
                        style=ft.ButtonStyle(padding=5)
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
            btn_cambiar_hora.visible = False 
            
            contenedor_horarios.visible = True
            contenedor_servicios.visible = False
            input_nombre.visible = False
            input_telefono.visible = False
            btn_confirmar.visible = False
            
            mostrar_horarios(fecha_val)
            page.update()

    hoy = datetime.datetime.now()
    date_picker = ft.DatePicker(
        first_date=hoy, 
        on_change=cambiar_fecha,
        help_text="Selecciona tu día de cita",
        cancel_text="Cancelar",
        confirm_text="Aceptar"
    )

    page.add(
        ft.Container(height=20),
        header_logo, 
        ft.Text("Reserva tu espacio", size=24, weight="bold"),
        ft.Divider(height=20, color=ft.Colors.PURPLE_200),
        
        ft.ElevatedButton("Paso 1: Elegir Día", icon=ft.Icons.CALENDAR_TODAY, color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE, on_click=lambda _: page.show_dialog(date_picker)),
        ft.Container(height=10),
        
        texto_resumen,
        btn_cambiar_hora, 
        
        ft.Divider(height=20, color=ft.Colors.PURPLE_200),
        contenedor_horarios, 
        
        contenedor_servicios, 
        
        ft.Divider(height=20, visible=False),
        input_nombre, 
        input_telefono, 
        
        ft.Container(height=30),
        btn_confirmar 
    )

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.environ.get("PORT", 8080)), host="0.0.0.0", assets_dir=".")
