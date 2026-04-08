import flet as ft
import os
import datetime 
from supa_config import guardar_cita, obtener_citas, borrar_cita 

# --- CONFIGURACIÓN DE COLORES ---
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
    page.title = "Fisi-K Center"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_COLOR
    page.locale = "es" 
    page.theme = ft.Theme(color_scheme_seed=ACCENT_COLOR) 
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window.width = 400
    page.window.height = 750
    page.scroll = "adaptive"

    # --- VARIABLES DE ESTADO ---
    fecha_val = ""
    hora_val = ""
    servicio_val = "" 

    header_logo = ft.Image(src=header_logo_src, width=120, height=120, fit="contain")

    # --- FUNCIÓN DE NAVEGACIÓN ---
    def cambiar_vista(vista_activa):
        vista_inicio.visible = False
        vista_paso1.visible = False
        vista_paso2.visible = False
        vista_paso3.visible = False
        vista_cancelar.visible = False
        vista_lealtad.visible = False
        vista_exito.visible = False
        
        vista_activa.visible = True
        page.update()

    # ==========================================
    # VISTA 0: MENÚ DE INICIO
    # ==========================================
    def reiniciar_proceso(e):
        nonlocal fecha_val, hora_val, servicio_val
        fecha_val = hora_val = servicio_val = ""
        texto_fecha_sel.value = "Ninguna fecha seleccionada"
        contenedor_horarios.controls.clear()
        btn_siguiente_1.disabled = True
        btn_siguiente_2.disabled = True
        col_subservicios.controls.clear()
        col_subservicios.controls.append(ft.Text("👈 Toca una categoría", italic=True, color=ft.Colors.WHITE54, size=13))
        input_nombre.value = ""
        input_telefono.value = ""
        cambiar_vista(vista_inicio)

    vista_inicio = ft.Column([
        ft.Text("¿QUÉ DESEAS HACER?", size=14, weight="bold", color=ft.Colors.WHITE54),
        ft.Container(height=10),
        ft.ElevatedButton(
            "Agendar Nueva Cita", icon=ft.Icons.CALENDAR_MONTH, bgcolor=ACCENT_COLOR, color=TEXT_WHITE,
            style=ft.ButtonStyle(padding=20, shape=ft.RoundedRectangleBorder(radius=15)), width=280,
            on_click=lambda _: cambiar_vista(vista_paso1)
        ),
        ft.Container(height=10),
        ft.ElevatedButton(
            "Cancelar mi Cita", icon=ft.Icons.CANCEL, bgcolor=CARD_COLOR, color=TEXT_WHITE,
            style=ft.ButtonStyle(padding=20, shape=ft.RoundedRectangleBorder(radius=15)), width=280,
            on_click=lambda _: cambiar_vista(vista_cancelar)
        ),
        ft.Container(height=10),
        ft.ElevatedButton(
            "Mi Plan de Lealtad", icon=ft.Icons.FAVORITE, bgcolor=CARD_COLOR, color=TEXT_WHITE,
            style=ft.ButtonStyle(padding=20, shape=ft.RoundedRectangleBorder(radius=15)), width=280,
            on_click=lambda _: cambiar_vista(vista_lealtad)
        )
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=True)


    # ==========================================
    # VISTA PASO 1: FECHA Y HORA
    # ==========================================
    texto_fecha_sel = ft.Text("Ninguna fecha seleccionada", italic=True, color=ft.Colors.WHITE54)
    contenedor_horarios = ft.Row(spacing=10, run_spacing=10, alignment=ft.MainAxisAlignment.CENTER, wrap=True, width=380)
    btn_siguiente_1 = ft.ElevatedButton("Siguiente Paso ➡️", bgcolor=ACCENT_COLOR, color=TEXT_WHITE, disabled=True, on_click=lambda _: cambiar_vista(vista_paso2))

    def seleccionar_hora(e, hora):
        nonlocal hora_val
        hora_val = hora
        # ¡CORRECCIÓN! Usamos .data en lugar de .text para que sea 100% seguro
        for btn in contenedor_horarios.controls:
            if btn.data == hora:
                btn.bgcolor = ACCENT_COLOR
                btn.color = TEXT_WHITE
                btn.icon_color = TEXT_WHITE
            elif not btn.disabled:
                btn.bgcolor = CARD_COLOR
                btn.color = TEXT_WHITE
                btn.icon_color = ACCENT_COLOR
        btn_siguiente_1.disabled = False
        page.update()

    def mostrar_horarios(fecha):
        contenedor_horarios.controls.clear()
        todas_las_horas = ["10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM"]

        try:
            citas_existentes = obtener_citas()
            horas_ocupadas = [cita.get('hora') for cita in citas_existentes if cita.get('fecha') == fecha]
        except:
            horas_ocupadas = [] 

        ahora_mx = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
        fecha_hoy_str = ahora_mx.strftime("%Y-%m-%d")

        for h in todas_las_horas:
            hora_formato = datetime.datetime.strptime(h, "%I:%M %p").time()
            ya_paso = (fecha == fecha_hoy_str) and (hora_formato <= ahora_mx.time())

            if (h in horas_ocupadas) or ya_paso:
                contenedor_horarios.controls.append(
                    ft.ElevatedButton(h, data=h, icon=ft.Icons.LOCK, width=115, disabled=True, color=ft.Colors.WHITE30, bgcolor=MUTED_COLOR, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
                )
            else:
                contenedor_horarios.controls.append(
                    ft.ElevatedButton(h, data=h, icon=ft.Icons.RADIO_BUTTON_UNCHECKED, icon_color=ACCENT_COLOR, color=TEXT_WHITE, bgcolor=CARD_COLOR, width=115, on_click=lambda e, hora_btn=h: seleccionar_hora(e, hora_btn), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
                )
        page.update()

    def cambiar_fecha(e):
        nonlocal fecha_val, hora_val
        if e.control.value:
            fecha_val = e.control.value.strftime("%Y-%m-%d")
            hora_val = ""
            btn_siguiente_1.disabled = True
            texto_fecha_sel.value = f"📅 Fecha elegida: {fecha_val}"
            texto_fecha_sel.italic = False
            texto_fecha_sel.color = ACCENT_COLOR
            texto_fecha_sel.weight = "bold"
            mostrar_horarios(fecha_val)
            page.update()

    ahora_mx_inicio = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
    date_picker = ft.DatePicker(first_date=ahora_mx_inicio, on_change=cambiar_fecha, help_text="Selecciona tu día", cancel_text="Cancelar", confirm_text="Aceptar")
    
    vista_paso1 = ft.Column([
        ft.Text("PASO 1 DE 3", size=12, color=ACCENT_COLOR, weight="bold"),
        ft.Text("Elige Día y Hora", size=20, weight="bold"),
        ft.ElevatedButton("Abrir Calendario", icon=ft.Icons.CALENDAR_MONTH, bgcolor=CARD_COLOR, color=TEXT_WHITE, on_click=lambda _: page.show_dialog(date_picker)),
        texto_fecha_sel,
        ft.Divider(color=CARD_COLOR),
        contenedor_horarios,
        ft.Container(height=20),
        ft.Row([
            ft.TextButton("⬅️ Menú", on_click=reiniciar_proceso, style=ft.ButtonStyle(color=ft.Colors.WHITE54)),
            btn_siguiente_1
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=380)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)


    # ==========================================
    # VISTA PASO 2: SERVICIOS
    # ==========================================
    btn_siguiente_2 = ft.ElevatedButton("Siguiente Paso ➡️", bgcolor=ACCENT_COLOR, color=TEXT_WHITE, disabled=True, on_click=lambda _: ir_a_paso3())
    col_categorias = ft.Column(spacing=10, width=150)
    col_subservicios = ft.Column([ft.Text("👈 Toca una categoría", italic=True, color=ft.Colors.WHITE54, size=13)], width=180, scroll=ft.ScrollMode.ADAPTIVE, height=220)

    def seleccionar_servicio(e, servicio_completo):
        nonlocal servicio_val
        servicio_val = servicio_completo
        for btn in col_subservicios.controls:
            if isinstance(btn, ft.ElevatedButton):
                if btn.content.controls[1].value == servicio_completo.split(" - ")[1]:
                    btn.bgcolor = ACCENT_COLOR
                else:
                    btn.bgcolor = MUTED_COLOR
        btn_siguiente_2.disabled = False
        page.update()

    def mostrar_subservicios(categoria):
        col_subservicios.controls.clear()
        col_subservicios.controls.append(ft.Text(categoria, weight="bold", size=14, color=TEXT_WHITE))
        for sub in servicios_disponibles[categoria]:
            col_subservicios.controls.append(
                ft.ElevatedButton(
                    content=ft.Row([ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, color=TEXT_WHITE, size=16), ft.Text(sub, size=12, color=TEXT_WHITE)]),
                    width=180, bgcolor=MUTED_COLOR, style=ft.ButtonStyle(padding=10, shape=ft.RoundedRectangleBorder(radius=12)),
                    on_click=lambda e, s=f"{categoria.split(' ')[1]} - {sub}": seleccionar_servicio(e, s)
                )
            )
        page.update()

    for cat in servicios_disponibles.keys():
        col_categorias.controls.append(
            ft.ElevatedButton(
                content=ft.Text(cat, size=13, text_align=ft.TextAlign.CENTER, color=TEXT_WHITE), width=150, bgcolor=CARD_COLOR,
                style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10)), on_click=lambda e, c=cat: mostrar_subservicios(c)
            )
        )

    vista_paso2 = ft.Column([
        ft.Text("PASO 2 DE 3", size=12, color=ACCENT_COLOR, weight="bold"),
        ft.Text("¿Qué servicio buscas?", size=20, weight="bold"),
        ft.Container(
            content=ft.Row([col_categorias, ft.VerticalDivider(width=1, color=BG_COLOR), col_subservicios], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START),
            padding=15, border_radius=20, bgcolor=CARD_COLOR, width=380
        ),
        ft.Container(height=20),
        ft.Row([
            ft.TextButton("⬅️ Atrás", on_click=lambda _: cambiar_vista(vista_paso1), style=ft.ButtonStyle(color=ft.Colors.WHITE54)),
            btn_siguiente_2
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=380)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)


    # ==========================================
    # VISTA PASO 3: CONFIRMACIÓN Y DATOS
    # ==========================================
    texto_resumen_final = ft.Text("", size=16, color=TEXT_WHITE, weight="bold", text_align=ft.TextAlign.CENTER)
    input_nombre = ft.TextField(label="Tu Nombre", icon=ft.Icons.PERSON, bgcolor=CARD_COLOR, border_color=ACCENT_COLOR, color=TEXT_WHITE, border_radius=15)
    input_telefono = ft.TextField(label="Tu WhatsApp", icon=ft.Icons.PHONE, bgcolor=CARD_COLOR, border_color=ACCENT_COLOR, color=TEXT_WHITE, border_radius=15)
    
    def ir_a_paso3():
        texto_resumen_final.value = f"📅 {fecha_val}  |  ⏰ {hora_val}\n💆‍♀️ {servicio_val}"
        cambiar_vista(vista_paso3)

    def confirmar_reserva(e):
        if not input_nombre.value or not input_telefono.value:
            page.show_dialog(ft.SnackBar(ft.Text("Llena tus datos"), bgcolor=ACCENT_COLOR, open=True))
            return
        btn_confirmar_final.disabled = True
        btn_confirmar_final.content = ft.Text("Guardando...", weight="bold") # Corrección content
        page.update()
        try:
            guardar_cita(fecha_val, hora_val, input_nombre.value, input_telefono.value, servicio_val)
            cambiar_vista(vista_exito)
        except Exception as ex:
            page.show_dialog(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED, open=True))
        btn_confirmar_final.disabled = False
        btn_confirmar_final.content = ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE), ft.Text("¡Confirmar Cita!", weight="bold")])
        page.update()

    btn_confirmar_final = ft.ElevatedButton(content=ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE), ft.Text("¡Confirmar Cita!", weight="bold")]), bgcolor=ACCENT_COLOR, color=TEXT_WHITE, style=ft.ButtonStyle(padding=20, shape=ft.RoundedRectangleBorder(radius=15)), on_click=confirmar_reserva)

    vista_paso3 = ft.Column([
        ft.Text("PASO 3 DE 3", size=12, color=ACCENT_COLOR, weight="bold"),
        ft.Text("Confirma tus datos", size=20, weight="bold"),
        ft.Container(content=texto_resumen_final, bgcolor=MUTED_COLOR, padding=15, border_radius=10, width=350),
        ft.Divider(color=CARD_COLOR),
        input_nombre,
        input_telefono,
        ft.Container(height=20),
        ft.Row([
            ft.TextButton("⬅️ Atrás", on_click=lambda _: cambiar_vista(vista_paso2), style=ft.ButtonStyle(color=ft.Colors.WHITE54)),
            btn_confirmar_final
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=380)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    # ==========================================
    # VISTA ÉXITO
    # ==========================================
    vista_exito = ft.Column([
        ft.Container(height=50),
        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ACCENT_COLOR, size=100),
        ft.Text("¡Cita Confirmada!", size=30, weight="bold", color=TEXT_WHITE),
        ft.Text("Tu espacio ha sido reservado.", color=ft.Colors.WHITE70),
        ft.Container(height=30),
        ft.ElevatedButton("Volver al Menú", bgcolor=CARD_COLOR, color=TEXT_WHITE, on_click=reiniciar_proceso)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)


    # ==========================================
    # VISTA: CANCELAR CITA
    # ==========================================
    input_cancelar_tel = ft.TextField(label="Ingresa tu WhatsApp", hint_text="Ej: 777...", width=250, border_radius=15, bgcolor=MUTED_COLOR, border_color=ACCENT_COLOR, color=TEXT_WHITE)
    lista_citas_cancelar = ft.Column(spacing=10, width=350)

    def buscar_mis_citas(e):
        tel = input_cancelar_tel.value
        if not tel:
            return
        lista_citas_cancelar.controls.clear()
        btn_buscar_citas.content = ft.Text("Buscando...", weight="bold") # Corrección content
        page.update()
        try:
            todas = obtener_citas()
            ahora_mx = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
            hoy_str = ahora_mx.strftime("%Y-%m-%d")
            mis_citas = [c for c in todas if str(c.get('cliente_telefono')) == str(tel) and c.get('fecha') >= hoy_str]

            if not mis_citas:
                lista_citas_cancelar.controls.append(ft.Text("No tienes citas próximas con este número.", color=ft.Colors.WHITE54, text_align=ft.TextAlign.CENTER))
            else:
                for c in mis_citas:
                    cita_id = c.get('id')
                    texto_desc = f"📅 {c.get('fecha')} - {c.get('hora')}\n💆‍♀️ {c.get('servicio')}"
                    
                    def cancelar_esta(e, cid=cita_id):
                        try:
                            borrar_cita(cid)
                            page.show_dialog(ft.SnackBar(ft.Text("Cita cancelada con éxito"), bgcolor=ft.Colors.GREEN, open=True))
                            buscar_mis_citas(None)
                        except Exception as ex:
                            page.show_dialog(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED, open=True))

                    tarjeta = ft.Container(
                        content=ft.Row([
                            ft.Text(texto_desc, size=13, color=TEXT_WHITE, expand=True),
                            ft.ElevatedButton("Cancelar", icon=ft.Icons.DELETE, bgcolor=ft.Colors.RED_700, color=TEXT_WHITE, on_click=lambda e, cid=cita_id: cancelar_esta(e, cid))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        bgcolor=CARD_COLOR, padding=15, border_radius=15, border=ft.border.all(1, ft.Colors.RED_900)
                    )
                    lista_citas_cancelar.controls.append(tarjeta)
        except Exception as ex:
            lista_citas_cancelar.controls.append(ft.Text(f"Error de conexión: {ex}", color=ft.Colors.RED))
        
        btn_buscar_citas.content = ft.Text("Buscar mis citas", weight="bold")
        page.update()

    btn_buscar_citas = ft.ElevatedButton(content=ft.Text("Buscar mis citas", weight="bold"), bgcolor=ACCENT_COLOR, color=TEXT_WHITE, on_click=buscar_mis_citas)

    vista_cancelar = ft.Column([
        ft.Text("CANCELAR CITA", size=20, weight="bold"),
        ft.Text("Ingresa el número con el que agendaste.", color=ft.Colors.WHITE54, text_align=ft.TextAlign.CENTER),
        ft.Container(height=10),
        input_cancelar_tel,
        btn_buscar_citas,
        ft.Divider(color=CARD_COLOR),
        lista_citas_cancelar,
        ft.Container(height=20),
        ft.TextButton("⬅️ Volver al Menú", on_click=reiniciar_proceso, style=ft.ButtonStyle(color=ft.Colors.WHITE54))
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)


    # ==========================================
    # VISTA: PLAN DE LEALTAD
    # ==========================================
    input_wa_lealtad = ft.TextField(label="Tu WhatsApp", hint_text="Ej: 777...", width=250, border_radius=15, bgcolor=MUTED_COLOR, border_color=ACCENT_COLOR, color=TEXT_WHITE)
    grid_sellos = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, visible=False)
    mensaje_lealtad = ft.Text("", weight="bold", size=16, color=TEXT_WHITE, text_align=ft.TextAlign.CENTER, visible=False)

    def consultar_lealtad(e):
        whatsapp = input_wa_lealtad.value
        if not whatsapp:
            return
        btn_verificar_lealtad.disabled = True
        btn_verificar_lealtad.content = ft.Text("Buscando...", weight="bold") # Corrección content
        page.update()
        try:
            todas = obtener_citas()
            citas_aprobadas = [c for c in todas if str(c.get('cliente_telefono')) == str(whatsapp) and c.get('asistio') == True]
            conteo = len(citas_aprobadas)
            
            grid_sellos.controls.clear()
            for i in range(1, 7):
                esta_lleno = i <= conteo
                if esta_lleno:
                    icono_sello = ft.Image(src=header_logo_src, width=30, height=30, fit="cover", border_radius=15)
                else:
                    icono_sello = ft.Icon(ft.Icons.CIRCLE_OUTLINED, color=ft.Colors.WHITE24, size=24)

                grid_sellos.controls.append(
                    ft.Container(content=ft.Row([icono_sello], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        width=50, height=50, bgcolor=MUTED_COLOR if esta_lleno else ft.Colors.TRANSPARENT, border=ft.border.all(1, ACCENT_COLOR if esta_lleno else ft.Colors.WHITE24), border_radius=25
                    )
                )
            mensaje_lealtad.value = f"¡Llevas {conteo} de 6 masajes!\n" + ("¡Felicidades, el próximo es GRATIS!" if conteo >= 6 else "¡Sigue así!")
            mensaje_lealtad.visible = True
            grid_sellos.visible = True
        except Exception as ex:
             page.show_dialog(ft.SnackBar(ft.Text(f"Error: {ex}"), open=True))
        
        btn_verificar_lealtad.disabled = False
        btn_verificar_lealtad.content = ft.Text("Verificar Mi Plan", weight="bold")
        page.update()

    btn_verificar_lealtad = ft.ElevatedButton(content=ft.Text("Verificar Mi Plan", weight="bold"), bgcolor=ACCENT_COLOR, color=TEXT_WHITE, on_click=consultar_lealtad, style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=15)))

    vista_lealtad = ft.Column([
        ft.Text("PROGRAMA DE LEALTAD", size=14, weight="bold", color=ACCENT_COLOR),
        ft.Text("6to Masaje GRATIS", size=20, weight="bold", color=TEXT_WHITE),
        ft.Container(height=10),
        input_wa_lealtad,
        btn_verificar_lealtad,
        ft.Container(height=10),
        grid_sellos,
        mensaje_lealtad,
        ft.Container(height=30),
        ft.TextButton("⬅️ Volver al Menú", on_click=reiniciar_proceso, style=ft.ButtonStyle(color=ft.Colors.WHITE54))
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)


    # ==========================================
    # ENSAMBLE FINAL EN LA PÁGINA
    # ==========================================
    page.add(
        ft.Container(height=10),
        header_logo, 
        ft.Text("FISI-K CENTER", size=22, weight="bold", color=TEXT_WHITE),
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        
        vista_inicio,
        vista_paso1,
        vista_paso2,
        vista_paso3,
        vista_exito,
        vista_cancelar,
        vista_lealtad,
        
        ft.Container(height=50) 
    )

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.environ.get("PORT", 8080)), host="0.0.0.0", assets_dir=".")
