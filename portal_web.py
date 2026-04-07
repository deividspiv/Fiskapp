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

# --- NUEVA PALETA DE COLORES "DARK PREMIUM" ---
BG_COLOR = "#2D3E6B"        # Azul profundo de fondo
CARD_COLOR = "#0C1533"      # Azul casi negro para tarjetas y botones
ACCENT_COLOR = "#D200AC"    # Magenta/Neón brillante (como en tu imagen)
MUTED_COLOR = "#1D284C"     # Un azul intermedio para cosas inactivas
TEXT_WHITE = ft.Colors.WHITE

def main(page: ft.Page):
    page.title = "Agenda tu Cita - Fisi-K Center"
    
    # Activamos el modo oscuro y aplicamos los nuevos colores
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_COLOR
    page.locale = "es" 
    # El calendario usará el magenta como color principal
    page.theme = ft.Theme(color_scheme_seed=ACCENT_COLOR) 
    
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window.width = 400
    page.window.height = 750
    page.scroll = "adaptive"

    fecha_val = ""
    hora_val = ""
    servicio_val = "" 

    header_logo = ft.Image(src=header_logo_src, width=120, height=120, fit="contain", visible=True)
    
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

    btn_cambiar_hora = ft.TextButton("✏️ Cambiar Hora", icon_color=ACCENT_COLOR, color=ACCENT_COLOR, visible=False, on_click=volver_a_hora)

    # Campos de texto con bordes redondeados y estilo oscuro
    input_nombre = ft.TextField(
        label="Tu Nombre Completo", icon=ft.Icons.PERSON, visible=False,
        bgcolor=CARD_COLOR, border_color=ACCENT_COLOR, color=TEXT_WHITE, border_radius=15
    )
    input_telefono = ft.TextField(
        label="Tu WhatsApp (ej: 777...)", icon=ft.Icons.PHONE, visible=False,
        bgcolor=CARD_COLOR, border_color=ACCENT_COLOR, color=TEXT_WHITE, border_radius=15
    )
    
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
        page.update()

    col_categorias = ft.Column(spacing=10, width=150)
    
    col_subservicios = ft.Column([
        ft.Text("👈 Toca una categoría", italic=True, color=ft.Colors.WHITE54, size=13)
    ], width=180, spacing=8, scroll=ft.ScrollMode.ADAPTIVE, height=220)

    def mostrar_subservicios(categoria):
        col_subservicios.controls.clear()
        col_subservicios.controls.append(ft.Text(categoria, weight="bold", size=14, color=TEXT_WHITE))
        
        for sub in servicios_disponibles[categoria]:
            col_subservicios.controls.append(
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, color=ACCENT_COLOR, size=16),
                        ft.Text(sub, size=12, color=TEXT_WHITE)
                    ]),
                    width=180,
                    bgcolor=MUTED_COLOR, # Un azul ligeramente más claro para resaltar
                    style=ft.ButtonStyle(
                        padding=10, 
                        shape=ft.RoundedRectangleBorder(radius=12)
                    ),
                    on_click=lambda e, s=f"{categoria.split(' ')[1]} - {sub}": seleccionar_servicio(s)
                )
            )
        page.update()

    for cat in servicios_disponibles.keys():
        col_categorias.controls.append(
            ft.ElevatedButton(
                content=ft.Text(cat, size=13, text_align=ft.TextAlign.CENTER, color=TEXT_WHITE),
                width=150,
                bgcolor=ft.Colors.TRANSPARENT, # Fondo transparente para que resalte la derecha
                style=ft.ButtonStyle(
                    padding=5,
                    shape=ft.RoundedRectangleBorder(radius=10)
                ),
                on_click=lambda e, c=cat: mostrar_subservicios(c)
            )
        )

    # Contenedor de servicios estilo "Dark Dashboard"
    contenedor_servicios = ft.Column([
        ft.Text("Paso 3: Selecciona tu servicio", size=18, weight="bold", color=TEXT_WHITE),
        ft.Container(
            content=ft.Row([
                col_categorias,
                ft.VerticalDivider(width=1, color=BG_COLOR), # Divisor que combina con el fondo
                col_subservicios
            ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START),
            padding=15,
            border_radius=20, # Bordes súper redondos
            bgcolor=CARD_COLOR, # Tarjeta casi negra
            width=380
        )
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    def confirmar_reserva(e):
        if not input_nombre.value or not input_telefono.value or not servicio_val:
            page.show_dialog(ft.SnackBar(ft.Text("Por favor, llena todos los campos."), bgcolor=ACCENT_COLOR, open=True))
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
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ACCENT_COLOR, size=100),
                        ft.Text("¡Cita Confirmada!", size=30, weight="bold", color=TEXT_WHITE),
                        ft.Text(f"Te esperamos el {fecha_val}", size=18, color=ft.Colors.WHITE70),
                        ft.Text(f"a las {hora_val}", size=18, color=TEXT_WHITE, weight="bold"),
                        ft.Text(f"Para tu servicio de:", size=16, color=ft.Colors.WHITE70),
                        ft.Text(f"{servicio_val}", size=18, color=ACCENT_COLOR, weight="bold"),
                        ft.Divider(height=40, color=CARD_COLOR),
                        ft.Text("Ya puedes cerrar esta ventana.", italic=True, color=ft.Colors.WHITE54)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
            page.update()
        except Exception as ex:
            page.show_dialog(ft.SnackBar(ft.Text(f"Ups, error de conexión: {ex}"), bgcolor=ft.Colors.RED, open=True))
            btn_confirmar.disabled = False
            btn_confirmar.text = "Confirmar Cita"
            page.update()

    # Botón principal vibrante
    btn_confirmar = ft.ElevatedButton(
        "Confirmar Cita", 
        icon=ft.Icons.CHECK, 
        color=TEXT_WHITE,
        bgcolor=ACCENT_COLOR, 
        visible=False, 
        style=ft.ButtonStyle(padding=20, shape=ft.RoundedRectangleBorder(radius=20)),
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
        texto_carga = ft.Text("Verificando disponibilidad...", italic=True, color=ft.Colors.WHITE54)
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

        ahora_mx = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
        fecha_hoy_str = ahora_mx.strftime("%Y-%m-%d")

        contenedor_horarios.controls.clear()

        for h in todas_las_horas:
            hora_formato = datetime.datetime.strptime(h, "%I:%M %p").time()
            es_hoy = (fecha == fecha_hoy_str)
            ya_paso = es_hoy and (hora_formato <= ahora_mx.time())

            if (h in horas_ocupadas) or ya_paso:
                contenedor_horarios.controls.append(
                    ft.ElevatedButton(
                        h, icon=ft.Icons.LOCK, width=115, disabled=True,
                        color=ft.Colors.WHITE30, bgcolor=MUTED_COLOR, 
                        style=ft.ButtonStyle(padding=5, shape=ft.RoundedRectangleBorder(radius=12))
                    )
                )
            else:
                # Estilo de tarjeta oscura con círculo magenta (como en la imagen)
                contenedor_horarios.controls.append(
                    ft.ElevatedButton(
                        h, icon=ft.Icons.RADIO_BUTTON_UNCHECKED, icon_color=ACCENT_COLOR,
                        color=TEXT_WHITE, bgcolor=CARD_COLOR,
                        width=115, on_click=lambda e, hora_btn=h: seleccionar_hora(hora_btn),
                        style=ft.ButtonStyle(padding=5, shape=ft.RoundedRectangleBorder(radius=12))
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

    ahora_mx_inicio = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
    date_picker = ft.DatePicker(
        first_date=ahora_mx_inicio, 
        on_change=cambiar_fecha,
        help_text="Selecciona tu día de cita",
        cancel_text="Cancelar",
        confirm_text="Aceptar"
    )

    page.add(
        ft.Container(height=10),
        header_logo, 
        ft.Text("RESERVA TU ESPACIO", size=20, weight="bold", color=TEXT_WHITE, tracking=2),
        ft.Divider(height=20, color=CARD_COLOR),
        
        # Botón de Paso 1 estilo Premium
        ft.ElevatedButton(
            "Elegir Día en Calendario", 
            icon=ft.Icons.CALENDAR_MONTH, 
            icon_color=ACCENT_COLOR,
            color=TEXT_WHITE, 
            bgcolor=CARD_COLOR, 
            style=ft.ButtonStyle(padding=20, shape=ft.RoundedRectangleBorder(radius=15)),
            on_click=lambda _: page.show_dialog(date_picker)
        ),
        ft.Container(height=10),
        
        texto_resumen,
        btn_cambiar_hora, 
        
        ft.Divider(height=20, color=CARD_COLOR),
        contenedor_horarios, 
        
        contenedor_servicios, 
        
        ft.Divider(height=20, visible=False),
        input_nombre, 
        input_telefono, 
        
        ft.Container(height=20),
        btn_confirmar,
        ft.Container(height=50) 
    )

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.environ.get("PORT", 8080)), host="0.0.0.0", assets_dir=".")
