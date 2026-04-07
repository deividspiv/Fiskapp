import flet as ft
from supa_config import guardar_cita

# --- TU MENÚ DE SERVICIOS ---
servicios_disponibles = {
    "💆💆‍♀️ Masajes": [
        "Relajantes", "Descontracturantes", "Deportivo", "Holístico", "Aromaterapia"
    ],
    "🧖🧖‍♀️ Limpiezas faciales": [
        "Limpieza facial profunda", "Hidratante", "Anti-acné", "Anti-edad"
    ],
    "✨ Tratamientos Corporales y faciales": [
        "Cavitación", "Radiofrecuencia", "PRP (plasma rico)", "Lipoenzimas"
    ]
}

def main(page: ft.Page):
    # -----------------------------
    # CONFIG GENERAL / TEMA
    # -----------------------------
    page.title = "Agenda tu Cita - Fisi-K Center"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.GREY_50
    page.padding = 0
    page.scroll = "adaptive"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Para escritorio (en web puede ignorarse)
    page.window.width = 420
    page.window.height = 780

    # Paleta / tema
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.PURPLE,
            secondary=ft.Colors.PINK_200,
            background=ft.Colors.GREY_50,
        ),
        font_family="Roboto",
    )

    # -----------------------------
    # ESTILOS REUTILIZABLES
    # -----------------------------
    APP_WIDTH = 380

    def show_snack(msg: str, color=ft.Colors.WHITE, bgcolor=ft.Colors.BLACK87):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg, color=color),
            bgcolor=bgcolor
        )
        page.snack_bar.open = True
        page.update()

    def card(title: str, content: ft.Control, icon: str = ""):
        header = ft.Row(
            controls=[
                ft.Text(f"{icon} {title}".strip(), size=16, weight="bold", color=ft.Colors.BLACK87),
            ],
            alignment=ft.MainAxisAlignment.START
        )

        return ft.Card(
            elevation=3,
            content=ft.Container(
                width=APP_WIDTH,
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=16,
                content=ft.Column(
                    controls=[
                        header,
                        ft.Divider(height=12, color=ft.Colors.GREY_200),
                        content
                    ],
                    spacing=10
                ),
            ),
        )

    def soft_button(text, icon, on_click, width=260, bgcolor=ft.Colors.PURPLE_50, color=ft.Colors.PURPLE_800):
        return ft.ElevatedButton(
            text=text,
            icon=icon,
            width=width,
            bgcolor=bgcolor,
            color=color,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=14),
                elevation=0
            ),
            on_click=on_click
        )

    def primary_button(text, icon, on_click, width=260, bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE, disabled=False):
        return ft.ElevatedButton(
            text=text,
            icon=icon,
            width=width,
            bgcolor=bgcolor,
            color=color,
            disabled=disabled,
            height=48,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=16),
                elevation=2
            ),
            on_click=on_click
        )

    # -----------------------------
    # VARIABLES DE ESTADO
    # -----------------------------
    fecha_val = ""
    hora_val = ""
    servicio_val = ""

    # -----------------------------
    # HEADER (HERO)
    # -----------------------------
    header_logo = ft.Image(
        src="fisik.png",
        width=110,
        height=110,
        fit="contain",
    )

    header = ft.Container(
        width=float("inf"),
        padding=20,
        bgcolor=ft.Colors.PURPLE_600,
        border_radius=ft.border_radius.only(bottom_left=28, bottom_right=28),
        content=ft.Column(
            controls=[
                header_logo,
                ft.Text("Fisi‑K Center", size=26, weight="bold", color=ft.Colors.WHITE),
                ft.Text("Agenda tu cita en minutos", size=14, color=ft.Colors.WHITE70),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        )
    )

    # -----------------------------
    # RESUMEN (TICKET)
    # -----------------------------
    txt_resumen_titulo = ft.Text("Resumen de tu cita", weight="bold", size=14, color=ft.Colors.PURPLE_900)
    txt_fecha = ft.Text("Fecha: —", color=ft.Colors.BLACK87)
    txt_hora = ft.Text("Hora: —", color=ft.Colors.BLACK87)
    txt_servicio = ft.Text("Servicio: —", color=ft.Colors.BLACK87)

    resumen_box = ft.Container(
        width=APP_WIDTH,
        padding=14,
        border_radius=16,
        bgcolor=ft.Colors.PURPLE_50,
        visible=False,
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.PURPLE_700),
                        txt_resumen_titulo,
                    ],
                    spacing=8
                ),
                ft.Divider(height=10, color=ft.Colors.PURPLE_100),
                txt_fecha,
                txt_hora,
                ft.Container(height=2),
                ft.Text("Servicio:", weight="bold", color=ft.Colors.PURPLE_900),
                ft.Text("", ref=None),  # placeholder (no hace nada, es solo espacio)
                txt_servicio,
            ],
            spacing=6
        )
    )

    # -----------------------------
    # INPUTS
    # -----------------------------
    input_nombre = ft.TextField(
        label="Tu Nombre Completo",
        prefix_icon=ft.Icons.PERSON,
        filled=True,
        border_radius=14,
        visible=False,
        width=APP_WIDTH
    )
    input_telefono = ft.TextField(
        label="Tu WhatsApp (ej: 777...)",
        prefix_icon=ft.Icons.PHONE,
        filled=True,
        border_radius=14,
        visible=False,
        width=APP_WIDTH
    )

    # -----------------------------
    # CONTENEDORES
    # -----------------------------
    contenedor_horarios = ft.Column(
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False
    )

    # Se construye después: contenedor_servicios
    contenedor_servicios = ft.Column(
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False
    )

    # -----------------------------
    # LÓGICA: SERVICIOS
    # -----------------------------
    def seleccionar_servicio(servicio_completo: str):
        nonlocal servicio_val
        servicio_val = servicio_completo

        txt_servicio.value = f"{servicio_completo}"
        resumen_box.visible = True

        # Al seleccionar servicio, mostramos inputs + botón
        contenedor_servicios.visible = False
        input_nombre.visible = True
        input_telefono.visible = True
        btn_confirmar.visible = True

        page.update()

    panels_servicios = []
    for categoria, tipos in servicios_disponibles.items():
        column_tipos = ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        for tipo in tipos:
            # 👇 Esto construye un string limpio: "Masajes - Relajantes", etc.
            cat_limpia = categoria.replace("💆💆‍♀️", "").replace("🧖🧖‍♀️", "").replace("✨", "").strip()
            servicio_final = f"{cat_limpia} - {tipo}"

            column_tipos.controls.append(
                soft_button(
                    text=tipo,
                    icon=ft.Icons.SPA,
                    width=APP_WIDTH - 60,
                    bgcolor=ft.Colors.PURPLE_50,
                    color=ft.Colors.PURPLE_800,
                    on_click=lambda e, s=servicio_final: seleccionar_servicio(s)
                )
            )

        panels_servicios.append(
            ft.ExpansionPanel(
                header=ft.ListTile(
                    title=ft.Text(categoria, weight="bold", size=16),
                    leading=ft.Icon(ft.Icons.CATEGORY, color=ft.Colors.PURPLE_600),
                ),
                content=ft.Container(
                    padding=10,
                    content=column_tipos
                )
            )
        )

    expansion_list = ft.ExpansionPanelList(
        controls=panels_servicios,
        expand_icon_color=ft.Colors.PURPLE
    )

    contenedor_servicios.controls = [
        ft.Text("Selecciona una categoría y elige tu servicio:", color=ft.Colors.BLACK54),
        expansion_list
    ]

    # -----------------------------
    # LÓGICA: CONFIRMAR RESERVA
    # -----------------------------
    def confirmar_reserva(e):
        if not input_nombre.value or not input_telefono.value or not servicio_val or not fecha_val or not hora_val:
            show_snack("Por favor, completa todos los pasos y campos.", bgcolor=ft.Colors.RED_600)
            return

        btn_confirmar.disabled = True
        btn_confirmar.text = "Guardando..."
        page.update()

        try:
            guardar_cita(fecha_val, hora_val, input_nombre.value, input_telefono.value, servicio_val)

            # Pantalla final
            page.controls.clear()
            page.add(
                ft.Container(height=30),
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=100),
                ft.Text("¡Cita Confirmada!", size=30, weight="bold"),
                ft.Container(height=10),
                ft.Text(f"📅 {fecha_val}", size=18),
                ft.Text(f"⏰ {hora_val}", size=18, color=ft.Colors.PURPLE, weight="bold"),
                ft.Container(height=10),
                ft.Text("Servicio:", size=16),
                ft.Text(servicio_val, size=18, color=ft.Colors.PURPLE_800, weight="bold"),
                ft.Container(height=25),
                ft.Divider(height=30),
                ft.Text("Gracias. Ya puedes cerrar esta ventana.", italic=True, color=ft.Colors.BLACK54)
            )
            page.update()

        except Exception as ex:
            show_snack(f"Ups, error de conexión: {ex}", bgcolor=ft.Colors.RED_600)
            btn_confirmar.disabled = False
            btn_confirmar.text = "✅ Confirmar Cita"
            page.update()

    btn_confirmar = ft.ElevatedButton(
        "✅ Confirmar Cita",
        icon=ft.Icons.CHECK,
        bgcolor=ft.Colors.GREEN_600,
        color=ft.Colors.WHITE,
        height=52,
        width=APP_WIDTH,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=18),
            elevation=3
        ),
        visible=False,
        on_click=confirmar_reserva
    )

    # -----------------------------
    # LÓGICA: HORAS
    # -----------------------------
    def seleccionar_hora(hora: str):
        nonlocal hora_val
        hora_val = hora

        txt_hora.value = f"Hora: {hora}"
        resumen_box.visible = True

        contenedor_horarios.visible = False
        contenedor_servicios.visible = True

        # reset inputs si cambia hora
        input_nombre.visible = False
        input_telefono.visible = False
        btn_confirmar.visible = False

        page.update()

    def mostrar_horarios(fecha: str):
        # Aquí puedes cambiar a horarios reales por día
        horarios = ["10:00 AM", "11:30 AM", "01:00 PM", "04:00 PM"]
        contenedor_horarios.controls.clear()

        contenedor_horarios.controls.append(
            ft.Text("Selecciona un horario disponible:", color=ft.Colors.BLACK54)
        )

        for h in horarios:
            contenedor_horarios.controls.append(
                primary_button(
                    text=f"Elegir {h}",
                    icon=ft.Icons.ACCESS_TIME,
                    width=APP_WIDTH - 20,
                    bgcolor=ft.Colors.BLUE_600,
                    on_click=lambda e, hora_btn=h: seleccionar_hora(hora_btn)
                )
            )
        page.update()

    # -----------------------------
    # LÓGICA: FECHA (DATEPICKER)
    # -----------------------------
    def cambiar_fecha(e):
        nonlocal fecha_val
        if e.control.value:
            fecha_val = e.control.value.strftime("%Y-%m-%d")

            # Actualiza resumen
            txt_fecha.value = f"Fecha: {fecha_val}"
            txt_hora.value = "Hora: —"
            txt_servicio.value = "Servicio: —"
            resumen_box.visible = True

            # Reset flujo
            contenedor_horarios.visible = True
            contenedor_servicios.visible = False
            input_nombre.visible = False
            input_telefono.visible = False
            btn_confirmar.visible = False

            # Reset estado
            nonlocal hora_val, servicio_val
            hora_val = ""
            servicio_val = ""

            mostrar_horarios(fecha_val)
            page.update()

    date_picker = ft.DatePicker(
        on_change=cambiar_fecha
    )
    page.overlay.append(date_picker)  # Recomendado para que abra bien

    # -----------------------------
    # UI DE PASOS (CARDS)
    # -----------------------------
    btn_abrir_fecha = primary_button(
        text="Seleccionar fecha",
        icon=ft.Icons.CALENDAR_TODAY,
        width=APP_WIDTH - 20,
        bgcolor=ft.Colors.PURPLE_600,
        on_click=lambda e: date_picker.pick_date()
    )

    card_fecha = card("Paso 1: Elige el día", btn_abrir_fecha, icon="🗓")
    card_horas = card("Paso 2: Elige la hora", contenedor_horarios, icon="⏰")
    card_serv = card("Paso 3: Selecciona tu servicio", contenedor_servicios, icon="✨")

    # -----------------------------
    # LAYOUT FINAL
    # -----------------------------
    page.add(
        header,
        ft.Container(height=12),
        ft.Container(
            width=APP_WIDTH,
            padding=ft.padding.only(left=12, right=12),
            content=ft.Column(
                controls=[
                    card_fecha,
                    resumen_box,
                    card_horas,
                    card_serv,
                    input_nombre,
                    input_telefono,
                    ft.Container(height=6),
                    btn_confirmar,
                    ft.Container(height=20),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12
            )
        )
    )

    # Estado inicial
    contenedor_horarios.visible = False
    contenedor_servicios.visible = False


ft.app(target=main, view=ft.AppView.WEB_BROWSER)
``
