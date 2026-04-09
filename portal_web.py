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

# --- COLORES NEÓN ---
COLOR_VERDE_LED = "#00FF00"
COLOR_NEON_AMARILLO = "#FFFF00"

RGB_NEON_COLORS = [
    "#FF003C", 
    "#00FF33", 
    "#00E5FF", 
    "#B200FF", 
    "#FF00FF", 
    "#FFFF00"  
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

    fecha_val = ""
    hora_val = ""
    servicio_val = "" 
    header_logo = ft.Image(src=header_logo_src, width=120, height=120, fit="contain")

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

    def reiniciar_proceso(e):
        nonlocal fecha_val, hora_val, servicio_val
        fecha_val = ""
        hora_val = ""
        servicio_val = ""
        texto_fecha_sel.value = "Ninguna fecha seleccionada"
        contenedor_horarios.controls.clear()
        btn_siguiente_1.disabled = True
        btn_siguiente_2.disabled = True
        grid_servicios.controls.clear()
        grid_servicios.controls.append(ft.Text("👈 Toca una categoría arriba", italic=True, color=ft.Colors.WHITE54))
        for btn in row_categorias.controls:
            btn.bgcolor = CARD_COLOR
            btn.color = TEXT_WHITE
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

    texto_fecha_sel = ft.Text("Ninguna fecha seleccionada", italic=True, color=ft.Colors.WHITE54)
    contenedor_horarios = ft.Row(spacing=10, run_spacing=10, alignment=ft.MainAxisAlignment.CENTER, wrap=True, width=380)
    btn_siguiente_1 = ft.ElevatedButton("Siguiente Paso ➡️", bgcolor=ACCENT_COLOR, color=TEXT_WHITE, disabled=True, on_click=lambda _: cambiar_vista(vista_paso2))

    # ==========================================
    # LÓGICA DE HORAS CON VERDE LED Y NEÓN AMARILLO
    # ==========================================
    def seleccionar_hora(e, hora):
        nonlocal hora_val
        hora_val = hora
        for btn in contenedor_horarios.controls:
            if btn.data == hora:
                # SELECCIONADO: Verde LED dentro, Amarillo Neón fuera
                btn.bgcolor = COLOR_VERDE_LED
                btn.color = "#000000" # Letra oscura para que se lea en el fondo verde
                btn.icon_color = "#000000"
                btn.style = ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    side=ft.BorderSide(2, COLOR_NEON_AMARILLO), # Borde amarillo
                    shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=COLOR_NEON_AMARILLO) # Sombra Neón
                )
            elif not btn.disabled:
                # NORMAL: Regresa a colores base
                btn.bgcolor = CARD_COLOR
                btn.color = TEXT_WHITE
                btn.icon_color = ACCENT_COLOR
                btn.style = ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    side=ft.BorderSide(1, ft.Colors.TRANSPARENT),
                    shadow=None
                )
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
                contenedor_horarios.controls.append(
                    ft.ElevatedButton(
                        h, data=h, icon=ft.Icons.LOCK, width=115, disabled=True, 
                        color=ft.Colors.WHITE30, bgcolor=MUTED_COLOR, 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    )
                )
            else:
                contenedor_horarios.controls.append(
                    ft.ElevatedButton(
                        h, data=h, icon=ft.Icons.RADIO_BUTTON_UNCHECKED, icon_color=ACCENT_COLOR, 
                        color=TEXT_WHITE, bgcolor=CARD_COLOR, width=115, 
                        on_click=lambda e, hb=h: seleccionar_hora(e, hb), 
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                            side=ft.BorderSide(1, ft.Colors.TRANSPARENT)
                        )
                    )
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
    # PASO 2: CUADRÍCULA DE SERVICIOS CENTRADA Y NEÓN
    # ==========================================
    btn_siguiente_2 = ft.ElevatedButton("Siguiente Paso ➡️", bgcolor=ACCENT_COLOR, color=TEXT_WHITE, disabled=True, on_click=lambda _: ir_a_paso3())
    
    row_categorias = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=10, wrap=True, width=380)
    grid_servicios = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=15, run_spacing=15, width=380)
    grid_servicios.controls.append(ft.Text("👈 Toca una categoría arriba", italic=True, color=ft.Colors.WHITE54))

    def seleccionar_servicio(e, servicio_completo):
        nonlocal servicio_val
        servicio_val = servicio_completo
        
        for card in grid_servicios.controls:
            if isinstance(card, ft.Container):
                if card.data == servicio_completo:
                    color_neon = random.choice(RGB_NEON_COLORS)
                    card.bgcolor = CARD_COLOR
                    card.border = ft.border.all(2, color_neon)
                    card.shadow = ft.BoxShadow(spread_radius=1, blur_radius=15, color=color_neon)
                else:
                    card.bgcolor = MUTED_COLOR
                    card.border = ft.border.all(1, ft.Colors.WHITE10)
                    card.shadow = None
        btn_siguiente_2.disabled = False
        page.update()

    def mostrar_subservicios(e, categoria):
        for btn in row_categorias.controls:
            if btn.data == categoria:
                btn.bgcolor = ACCENT_COLOR
                btn.color = BG_COLOR
            else:
                btn.bgcolor = CARD_COLOR
                btn.color = TEXT_WHITE

        grid_servicios.controls.clear()

        for sub, precio in servicios_disponibles[categoria].items():
            servicio_db = f"{categoria.split(' ')[1]} - {sub} (${precio})"
            tarjeta = ft.Container(
                data=servicio_db,
                # CONTENIDO PERFECTAMENTE CENTRADO EN LA TARJETA
                content=ft.Column([
                    ft.Text(sub, size=13, weight="bold", color=TEXT_WHITE, text_align=ft.TextAlign.CENTER),
                    ft.Text(f"${precio} MXN", size=12, color=ACCENT_COLOR, weight="bold", text_align=ft.TextAlign.CENTER)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                width=116, 
                height=110, 
                bgcolor=MUTED_COLOR,
                border_radius=15,
                border=ft.border.all(1, ft.Colors.WHITE10),
                padding=5,
                on_click=lambda ev, s=servicio_db: seleccionar_servicio(ev, s),
                animate=300 
            )
            grid_servicios.controls.append(tarjeta)
        page.update()

    for cat in servicios_disponibles.keys():
        row_categorias.controls.append(
            ft.ElevatedButton(
                content=ft.Text(cat, size=12, weight="bold"),
                data=cat,
                bgcolor=CARD_COLOR,
                color=TEXT_WHITE,
                style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=12)),
                on_click=lambda e, c=cat: mostrar_subservicios(e, c)
            )
        )

    vista_paso2 = ft.Column([
        ft.Text("PASO 2 DE 3", size=12, color=ACCENT_COLOR, weight="bold"),
        ft.Text("¿Qué servicio buscas?", size=20, weight="bold"),
        ft.Container(height=10),
        row_categorias, 
        ft.Container(height=15),
        ft.Container(
            content=grid_servicios, 
            padding=10, 
            width=380
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
        btn_confirmar_final.content = ft.Text("Guardando...", weight="bold")
        page.update()
        try:
            guardar_cita(fecha_val, hora_val, input_nombre.value, input_telefono.value, servicio_val)
            cambiar_vista(vista_exito)
        except Exception as ex:
            page.show_dialog(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED, open=True))
        btn_confirmar_final.disabled = False
        btn_confirmar_final.content = ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE), ft.Text("¡Confirmar Cita!", weight="bold")])
        page.update()

    btn_confirmar_final = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE), ft.Text("¡Confirmar Cita!", weight="bold")]), 
        bgcolor=ACCENT_COLOR, color=TEXT_WHITE, 
        style=ft.ButtonStyle(padding=20, shape=ft.RoundedRectangleBorder(radius=15)), 
        on_click=confirmar_reserva
    )

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

    vista_exito = ft.Column([
        ft.Container(height=50), 
        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ACCENT_COLOR, size=100),
        ft.Text("¡Cita Confirmada!", size=30, weight="bold", color=TEXT_WHITE), 
        ft.Text("Tu espacio ha sido reservado.", color=ft.Colors.WHITE70),
        ft.Container(height=30), 
        ft.ElevatedButton("Volver al Menú", bgcolor=CARD_COLOR, color=TEXT_WHITE, on_click=reiniciar_proceso)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    input_cancelar_tel = ft.TextField(label="Ingresa tu WhatsApp", hint_text="Ej: 777...", width=250, border_radius=15, bgcolor=MUTED_COLOR, border_color=ACCENT_COLOR, color=TEXT_WHITE)
    lista_citas_cancelar = ft.Column(spacing=10, width=350)

    def buscar_mis_citas(e):
        tel = input_cancelar_tel.value
        if not tel: return
        lista_citas_cancelar.controls.clear()
        btn_buscar_citas.content = ft.Text("Buscando...", weight="bold")
        page.update()
        try:
            todas = obtener_citas()
            ahora_mx = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
            mis_citas = [c for c in todas if str(c.get('cliente_telefono')) == str(tel) and c.get('fecha') >= ahora_mx.strftime("%Y-%m-%d")]
            if not mis_citas:
                lista_citas_cancelar.controls.append(ft.Text("No tienes citas próximas con este número.", color=ft.Colors.WHITE54, text_align=ft.TextAlign.CENTER))
            else:
                for c in mis_citas:
                    def cancelar_esta(e, cid=c.get('id')):
                        try:
                            borrar_cita(cid)
                            page.show_dialog(ft.SnackBar(ft.Text("Cita cancelada con éxito"), bgcolor=ft.Colors.GREEN, open=True))
                            buscar_mis_citas(None)
                        except Exception as ex:
                            page.show_dialog(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED, open=True))
                    
                    lista_citas_cancelar.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(f"📅 {c.get('fecha')} - {c.get('hora')}\n💆‍♀️ {c.get('servicio')}", size=13, color=TEXT_WHITE, expand=True), 
                                ft.ElevatedButton("Cancelar", icon=ft.Icons.DELETE, bgcolor=ft.Colors.RED_700, color=TEXT_WHITE, on_click=lambda e, cid=c.get('id'): cancelar_esta(e, cid))
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), 
                            bgcolor=CARD_COLOR, padding=15, border_radius=15, border=ft.border.all(1, ft.Colors.RED_900)
                        )
                    )
        except Exception as ex:
            lista_citas_cancelar.controls.append(ft.Text(f"Error: {ex}", color=ft.Colors.RED))
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

    input_wa_lealtad = ft.TextField(label="Tu WhatsApp", hint_text="Ej: 777...", width=250, border_radius=15, bgcolor=MUTED_COLOR, border_color=ACCENT_COLOR, color=TEXT_WHITE)
    grid_sellos = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, visible=False)
    mensaje_lealtad = ft.Text("", weight="bold", size=16, color=TEXT_WHITE, text_align=ft.TextAlign.CENTER, visible=False)

    def consultar_lealtad(e):
        whatsapp = input_wa_lealtad.value
        if not whatsapp: return
        btn_verificar_lealtad.disabled = True
        btn_verificar_lealtad.content = ft.Text("Buscando...", weight="bold") 
        page.update()
        try:
            citas_aprobadas = [c for c in obtener_citas() if str(c.get('cliente_telefono')) == str(whatsapp) and c.get('asistio') == True]
            conteo_historico = len(citas_aprobadas)
            conteo = conteo_historico % 6
            if conteo == 0 and conteo_historico > 0:
                conteo = 6

            grid_sellos.controls.clear()
            for i in range(1, 7):
                esta_lleno = i <= conteo
                icono_sello = ft.Image(src=header_logo_src, width=30, height=30, fit="cover", border_radius=15) if esta_lleno else ft.Icon(ft.Icons.CIRCLE_OUTLINED, color=ft.Colors.WHITE24, size=24)
                grid_sellos.controls.append(
                    ft.Container(
                        content=ft.Row([icono_sello], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER), 
                        width=50, height=50, bgcolor=MUTED_COLOR if esta_lleno else ft.Colors.TRANSPARENT, 
                        border=ft.border.all(1, ACCENT_COLOR if esta_lleno else ft.Colors.WHITE24), border_radius=25
                    )
                )
            
            if conteo == 6:
                mensaje_lealtad.value = "¡Completaste tus 6 masajes!\n🎉 ¡Tu próxima visita es GRATIS! 🎉"
            else:
                mensaje_lealtad.value = f"¡Llevas {conteo} de 6 masajes!\n¡Sigue así para tu premio!"
                
            mensaje_lealtad.visible, grid_sellos.visible = True, True
        except Exception as ex:
             page.show_dialog(ft.SnackBar(ft.Text(f"Error: {ex}"), open=True))
        btn_verificar_lealtad.disabled = False
        btn_verificar_lealtad.content = ft.Text("Verificar Mi Plan", weight="bold")
        page.update()

    btn_verificar_lealtad = ft.ElevatedButton(
        content=ft.Text("Verificar Mi Plan", weight="bold"), 
        bgcolor=ACCENT_COLOR, color=TEXT_WHITE, 
        on_click=consultar_lealtad, 
        style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=15))
    )

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

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.environ.get("PORT", 8080)), host="0.0.0.0")
