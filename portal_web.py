import flet as ft
from supa_config import guardar_cita

servicios_disponibles = {
    "💆💆‍♀️ Masajes": ["Relajantes", "Descontracturantes", "Deportivo", "Holístico", "Aromaterapia"],
    "🧖🧖‍♀️ Limpiezas faciales": ["Limpieza facial profunda", "Hidratante", "Anti-acné", "Anti-edad"],
    "✨ Tratamientos Corporales y faciales": ["Cavitación", "Radiofrecuencia", "PRP (plasma rico)", "Lipoenzimas"],
}

def main(page: ft.Page):
    page.title = "Agenda tu Cita - Fisi-K Center"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = "adaptive"
    page.padding = 0
    page.bgcolor = ft.Colors.TRANSPARENT  # porque usaremos fondo con gradiente
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # ========= ESTADO =========
    fecha_val = ""
    hora_val = ""
    servicio_val = ""
    paso = 1  # 1 fecha, 2 hora, 3 servicio, 4 datos

    # ========= HELPERS =========
    def snack(msg, bgcolor=ft.Colors.BLACK87):
        page.snack_bar = ft.SnackBar(ft.Text(msg, color=ft.Colors.WHITE), bgcolor=bgcolor)
        page.snack_bar.open = True
        page.update()

    def limpiar_emoji_categoria(cat: str) -> str:
        return cat.replace("💆💆‍♀️", "").replace("🧖🧖‍♀️", "").replace("✨", "").strip()

    def set_paso(n: int):
        nonlocal paso
        paso = n
        render_step()
        page.update()

    # ========= UI: STEPPER =========
    def step_chip(n, label):
        active = (paso == n)
        done = (paso > n)

        if done:
            bg = ft.Colors.GREEN_100
            fg = ft.Colors.GREEN_800
            icon = ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=fg)
        elif active:
            bg = ft.Colors.PURPLE_600
            fg = ft.Colors.WHITE
            icon = ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED, size=16, color=fg)
        else:
            bg = ft.Colors.WHITE
            fg = ft.Colors.BLACK54
            icon = ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, size=16, color=fg)

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=10, vertical=7),
            border_radius=999,
            bgcolor=bg,
            border=ft.border.all(1, ft.Colors.BLACK12),
            content=ft.Row([icon, ft.Text(f"{n}. {label}", color=fg, size=12, weight="bold")], spacing=6),
        )

    stepper = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=8,
        controls=[
            step_chip(1, "Fecha"),
            step_chip(2, "Hora"),
            step_chip(3, "Servicio"),
            step_chip(4, "Datos"),
        ],
    )

    def render_stepper():
        stepper.controls = [
            step_chip(1, "Fecha"),
            step_chip(2, "Hora"),
            step_chip(3, "Servicio"),
            step_chip(4, "Datos"),
        ]

    # ========= RESUMEN =========
    resumen = ft.Container(
        visible=False,
        border_radius=18,
        padding=14,
        bgcolor=ft.Colors.WHITE,
        border=ft.border.all(1, ft.Colors.BLACK12),
        shadow=ft.BoxShadow(blur_radius=18, color=ft.Colors.BLACK12, offset=ft.Offset(0, 8)),
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Row(
                    [ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.PURPLE_600), ft.Text("Tu resumen", weight="bold")],
                    spacing=8
                ),
                ft.Divider(height=8, color=ft.Colors.BLACK12),
                ft.Text("📅 Fecha: —", key="r_fecha"),
                ft.Text("⏰ Hora: —", key="r_hora"),
                ft.Text("✨ Servicio: —", key="r_servicio"),
            ],
        ),
    )

    def set_resumen():
        # actualiza textos dentro del resumen
        for c in resumen.content.controls:
            if isinstance(c, ft.Text) and c.key == "r_fecha":
                c.value = f"📅 Fecha: {fecha_val or '—'}"
            if isinstance(c, ft.Text) and c.key == "r_hora":
                c.value = f"⏰ Hora: {hora_val or '—'}"
            if isinstance(c, ft.Text) and c.key == "r_servicio":
                c.value = f"✨ Servicio: {servicio_val or '—'}"

        resumen.visible = True if (fecha_val or hora_val or servicio_val) else False

    # ========= INPUTS =========
    input_nombre = ft.TextField(
        label="Tu nombre completo",
        prefix_icon=ft.Icons.PERSON,
        filled=True,
        border_radius=14,
    )
    input_telefono = ft.TextField(
        label="WhatsApp (ej: 777...)",
        prefix_icon=ft.Icons.PHONE,
        filled=True,
        border_radius=14,
        keyboard_type=ft.KeyboardType.PHONE,
    )

    # ========= PANEL: FECHA =========
    def cambiar_fecha(e):
        nonlocal fecha_val, hora_val, servicio_val
        if e.control.value:
            fecha_val = e.control.value.strftime("%Y-%m-%d")
            hora_val = ""
            servicio_val = ""
            set_resumen()
            set_paso(2)
            construir_horarios()

    date_picker = ft.DatePicker(on_change=cambiar_fecha)
    page.overlay.append(date_picker)

    btn_fecha = ft.FilledButton(
        "Elegir fecha",
        icon=ft.Icons.CALENDAR_MONTH,
        on_click=lambda e: date_picker.pick_date(),
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16)),
    )

    panel_fecha = ft.Column(
        spacing=12,
        controls=[
            ft.Text("Elige el día de tu cita", size=18, weight="bold"),
            ft.Text("Selecciona una fecha disponible en el calendario.", color=ft.Colors.BLACK54),
            btn_fecha,
        ],
    )

    # ========= PANEL: HORARIOS (chips) =========
    horarios_wrap = ft.Wrap(spacing=10, run_spacing=10, alignment=ft.WrapAlignment.CENTER)

    def seleccionar_hora(h):
        nonlocal hora_val
        hora_val = h
        set_resumen()
        set_paso(3)
        construir_servicios()

    def chip_hora(h, selected=False):
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            border_radius=999,
            bgcolor=ft.Colors.PURPLE_600 if selected else ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.BLACK12),
            shadow=ft.BoxShadow(blur_radius=14, color=ft.Colors.BLACK12, offset=ft.Offset(0, 6)),
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.ACCESS_TIME, size=18,
                            color=ft.Colors.WHITE if selected else ft.Colors.PURPLE_600),
                    ft.Text(h, weight="bold",
                            color=ft.Colors.WHITE if selected else ft.Colors.BLACK87),
                ],
            ),
            on_click=lambda e: seleccionar_hora(h),
        )

    def construir_horarios():
        horarios = ["10:00 AM", "11:30 AM", "01:00 PM", "04:00 PM"]
        horarios_wrap.controls.clear()
        for h in horarios:
            horarios_wrap.controls.append(chip_hora(h, selected=(h == hora_val)))
        page.update()

    panel_hora = ft.Column(
        spacing=12,
        controls=[
            ft.Text("Elige un horario", size=18, weight="bold"),
            ft.Text("Toca un horario para continuar.", color=ft.Colors.BLACK54),
            horarios_wrap,
        ],
        visible=False,
    )

    # ========= PANEL: SERVICIOS (cards + expansion) =========
    def seleccionar_servicio(s):
        nonlocal servicio_val
        servicio_val = s
        set_resumen()
        set_paso(4)

    panels_servicios = []

    def construir_servicios():
        panels_servicios.clear()
        for categoria, tipos in servicios_disponibles.items():
            cat_limpia = limpiar_emoji_categoria(categoria)
            botones = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

            for tipo in tipos:
                servicio_final = f"{cat_limpia} - {tipo}"
                botones.controls.append(
                    ft.Container(
                        width=340,
                        border_radius=16,
                        padding=12,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, ft.Colors.BLACK12),
                        shadow=ft.BoxShadow(blur_radius=16, color=ft.Colors.BLACK12, offset=ft.Offset(0, 7)),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(tipo, weight="bold"),
                                        ft.Text(cat_limpia, size=12, color=ft.Colors.BLACK54),
                                    ],
                                ),
                                ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=18, color=ft.Colors.PURPLE_600),
                            ],
                        ),
                        on_click=lambda e, s=servicio_final: seleccionar_servicio(s),
                    )
                )

            panels_servicios.append(
                ft.ExpansionPanel(
                    header=ft.ListTile(
                        leading=ft.Icon(ft.Icons.SPA, color=ft.Colors.PURPLE_600),
                        title=ft.Text(categoria, weight="bold"),
                    ),
                    content=ft.Container(padding=10, content=botones),
                )
            )

        expansion.controls = panels_servicios
        page.update()

    expansion = ft.ExpansionPanelList(expand_icon_color=ft.Colors.PURPLE_600, controls=[])

    panel_servicio = ft.Column(
        spacing=12,
        controls=[
            ft.Text("Selecciona tu servicio", size=18, weight="bold"),
            ft.Text("Abre una categoría y elige el servicio.", color=ft.Colors.BLACK54),
            expansion,
        ],
        visible=False,
    )

    # ========= PANEL: DATOS + CONFIRMAR =========
    btn_confirmar = ft.FilledButton(
        "Confirmar cita",
        icon=ft.Icons.CHECK_CIRCLE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=18)),
    )

    def confirmar(e):
        if not (fecha_val and hora_val and servicio_val and input_nombre.value and input_telefono.value):
            snack("Completa todos los campos para confirmar.", bgcolor=ft.Colors.RED_600)
            return

        btn_confirmar.disabled = True
        btn_confirmar.text = "Guardando..."
        page.update()

        try:
            guardar_cita(fecha_val, hora_val, input_nombre.value, input_telefono.value, servicio_val)

            page.controls.clear()
            page.add(
                ft.Container(
                    expand=True,
                    alignment=ft.alignment.center,
                    content=ft.Container(
                        width=380,
                        padding=20,
                        border_radius=22,
                        bgcolor=ft.Colors.WHITE,
                        shadow=ft.BoxShadow(blur_radius=22, color=ft.Colors.BLACK12, offset=ft.Offset(0, 10)),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                            controls=[
                                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=100),
                                ft.Text("¡Cita confirmada!", size=28, weight="bold"),
                                ft.Text(f"📅 {fecha_val}", size=16),
                                ft.Text(f"⏰ {hora_val}", size=16, weight="bold", color=ft.Colors.PURPLE_700),
                                ft.Text(servicio_val, size=16, weight="bold", color=ft.Colors.PURPLE_900),
                                ft.Divider(height=25),
                                ft.Text("Ya puedes cerrar esta ventana.", color=ft.Colors.BLACK54),
                            ],
                        ),
                    ),
                )
            )
            page.update()
        except Exception as ex:
            snack(f"Error: {ex}", bgcolor=ft.Colors.RED_600)
            btn_confirmar.disabled = False
            btn_confirmar.text = "Confirmar cita"
            page.update()

    btn_confirmar.on_click = confirmar

    panel_datos = ft.Column(
        spacing=12,
        controls=[
            ft.Text("Tus datos", size=18, weight="bold"),
            ft.Text("Completa tu información para terminar.", color=ft.Colors.BLACK54),
            input_nombre,
            input_telefono,
            ft.Container(height=4),
            ft.Container(
                padding=ft.padding.only(top=6),
                content=btn_confirmar
            )
        ],
        visible=False,
    )

    # ========= CONTENEDOR PRINCIPAL + ANIMACIÓN =========
    content_holder = ft.AnimatedSwitcher(
        duration=350,
        transition=ft.AnimatedSwitcherTransition.FADE,
        content=panel_fecha,
    )

    def render_step():
        render_stepper()
        set_resumen()

        panel_fecha.visible = (paso == 1)
        panel_hora.visible = (paso == 2)
        panel_servicio.visible = (paso == 3)
        panel_datos.visible = (paso == 4)

        if paso == 1:
            content_holder.content = panel_fecha
        elif paso == 2:
            content_holder.content = panel_hora
        elif paso == 3:
            content_holder.content = panel_servicio
        else:
            content_holder.content = panel_datos

    # ========= APP BAR =========
    page.appbar = ft.AppBar(
        title=ft.Text("Fisi‑K Center"),
        center_title=True,
        bgcolor=ft.Colors.PURPLE_600,
        color=ft.Colors.WHITE,
        actions=[
            ft.IconButton(ft.Icons.RESTART_ALT, icon_color=ft.Colors.WHITE,
                          tooltip="Reiniciar", on_click=lambda e: reiniciar())
        ],
    )

    def reiniciar():
        nonlocal fecha_val, hora_val, servicio_val, paso
        fecha_val = ""
        hora_val = ""
        servicio_val = ""
        input_nombre.value = ""
        input_telefono.value = ""
        paso = 1
        horarios_wrap.controls.clear()
        expansion.controls = []
        set_resumen()
        render_step()
        page.update()

    # ========= FONDO (GRADIENTE) =========
    background = ft.Container(
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.Colors.PURPLE_100, ft.Colors.PINK_50, ft.Colors.GREY_50],
        ),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(height=10),
                ft.Container(
                    width=390,
                    padding=14,
                    content=stepper,
                ),
                ft.Container(
                    width=380,
                    padding=12,
                    content=resumen,
                ),
                ft.Container(
                    width=380,
                    padding=16,
                    border_radius=22,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.BLACK12),
                    shadow=ft.BoxShadow(blur_radius=26, color=ft.Colors.BLACK12, offset=ft.Offset(0, 12)),
                    content=content_holder,
                ),
                ft.Container(height=24),
            ]
        )
    )

    # ========= INIT =========
    page.add(background)
    construir_horarios()  # prepara lista si se necesita
    render_step()

ft.app(target=main, view=ft.AppView.WEB_BROWSER)
``
