import flet as ft
import os
import datetime 
from supa_config import guardar_cita, obtener_citas 

# --- CONFIGURACIÓN DE COLORES ---
BG_COLOR = "#2D3E6B"        
CARD_COLOR = "#0C1533"      
ACCENT_COLOR = "#D200AC"    
TEXT_WHITE = ft.Colors.WHITE

servicios_disponibles = {
    "💆‍♀️ Masajes": ["Relajantes", "Descontracturantes", "Deportivo", "Holístico", "Aromaterapia"],
    "🧖‍♀️ Limpiezas faciales": ["Limpieza profunda", "Hidratante", "Anti-acné", "Anti-edad"],
    "✨ Trat. Corporales": ["Cavitación", "Radiofrecuencia", "PRP (plasma)", "Lipoenzimas"]
}

header_logo_src = "fisik.png" 

def main(page: ft.Page):
    page.title = "Fisi-K Center - Lealtad"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_COLOR
    page.locale = "es" 
    page.theme = ft.Theme(color_scheme_seed=ACCENT_COLOR)
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = "adaptive"

    # --- LÓGICA DE SELLITOS ---
    def consultar_sellitos(e):
        whatsapp = input_wa_sellitos.value
        if not whatsapp:
            page.show_dialog(ft.SnackBar(ft.Text("Pon tu WhatsApp para ver tus premios"), open=True))
            return
        
        btn_verificar.disabled = True
        btn_verificar.text = "Buscando..."
        page.update()

        try:
            todas = obtener_citas()
            # FILTRO MÁGICO: Solo contamos las del usuario Y que el Admin ya aprobó
            citas_aprobadas = [c for c in todas if str(c.get('telefono')) == str(whatsapp) and c.get('asistio') == True]
            conteo = len(citas_aprobadas)
            
            # Limpiamos el contenedor de sellos
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
                        bgcolor=CARD_COLOR if esta_lleno else ft.Colors.TRANSPARENT,
                        border=ft.border.all(1, ACCENT_COLOR if esta_lleno else ft.Colors.WHITE24),
                        border_radius=25,
                        alignment=ft.alignment.center
                    )
                )
            
            mensaje_lealtad.value = f"¡Llevas {conteo} de 6 masajes! " + ("¡Felicidades, el próximo es GRATIS!" if conteo >= 6 else "¡Sigue así!")
            mensaje_lealtad.visible = True
            grid_sellos.visible = True
            
        except Exception as ex:
            page.show_dialog(ft.SnackBar(ft.Text(f"Error: {ex}"), open=True))
        
        btn_verificar.disabled = False
        btn_verificar.text = "Verificar Mis Sellos"
        page.update()

    # Componentes de la tarjeta de lealtad
    input_wa_sellitos = ft.TextField(label="Tu WhatsApp", prefix_text="+52 ", width=250, border_radius=15, bgcolor=CARD_COLOR)
    btn_verificar = ft.ElevatedButton("Verificar Mis Sellos", bgcolor=ACCENT_COLOR, color=TEXT_WHITE, on_click=consultar_sellitos)
    grid_sellos = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, visible=False)
    mensaje_lealtad = ft.Text("", weight="bold", size=16, text_align=ft.TextAlign.CENTER, visible=False)

    tarjeta_lealtad = ft.Container(
        content=ft.Column([
            ft.Text("PROGRAMA DE LEALTAD", size=14, weight="bold", color=ACCENT_COLOR),
            ft.Text("6to Masaje GRATIS", size=18, weight="bold"),
            input_wa_sellitos,
            btn_verificar,
            grid_sellos,
            mensaje_lealtad
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
        padding=20, border_radius=25, bgcolor=CARD_COLOR, width=380
    )

    # --- RESTO DEL CÓDIGO (Agendar cita) ---
    fecha_val, hora_val, servicio_val = "", "", ""

    def seleccionar_servicio(s):
        nonlocal servicio_val
        servicio_val = s
        contenedor_servicios.visible = False
        input_nombre.visible = input_telefono.visible = btn_confirmar.visible = True
        page.update()

    col_categorias = ft.Column(spacing=10, width=150)
    col_subservicios = ft.Column([ft.Text("👈 Elige categoría", italic=True, size=13)], width=180, scroll="adaptive", height=220)

    def mostrar_subservicios(cat):
        col_subservicios.controls.clear()
        col_subservicios.controls.append(ft.Text(cat, weight="bold", size=14))
        for sub in servicios_disponibles[cat]:
            col_subservicios.controls.append(ft.ElevatedButton(sub, on_click=lambda e, s=f"{cat} - {sub}": seleccionar_servicio(s), bgcolor=ft.Colors.WHITE10, width=180))
        page.update()

    for c in servicios_disponibles.keys():
        col_categorias.controls.append(ft.ElevatedButton(c, width=150, on_click=lambda e, cat=c: mostrar_subservicios(cat)))

    contenedor_servicios = ft.Column([
        ft.Text("Paso 3: Selecciona tu servicio", size=18, weight="bold"),
        ft.Container(content=ft.Row([col_categorias, ft.VerticalDivider(), col_subservicios]), padding=15, bgcolor=CARD_COLOR, border_radius=20, width=380)
    ], visible=False, horizontal_alignment="center")

    input_nombre = ft.TextField(label="Nombre Completo", visible=False, border_radius=15, bgcolor=CARD_COLOR)
    input_telefono = ft.TextField(label="WhatsApp", visible=False, border_radius=15, bgcolor=CARD_COLOR)
    btn_confirmar = ft.ElevatedButton("Confirmar Cita", bgcolor=ACCENT_COLOR, visible=False, on_click=lambda _: None) # (Lógica de guardado igual a la anterior)

    # UI Principal
    page.add(
        ft.Container(height=10),
        ft.Image(src=header_logo_src, width=100),
        ft.Text("FISI-K CENTER", size=22, weight="bold", tracking=2),
        
        # Primero mostramos la tarjeta de lealtad
        tarjeta_lealtad,
        
        ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
        
        # Luego el botón de agendar
        ft.Text("¿QUIERES AGENDAR NUEVA CITA?", size=14, color=ft.Colors.WHITE54),
        ft.ElevatedButton("Ir al Calendario", icon=ft.Icons.CALENDAR_MONTH, bgcolor=CARD_COLOR, on_click=lambda _: page.show_dialog(date_picker)),
        
        contenedor_servicios,
        input_nombre, input_telefono, btn_confirmar,
        ft.Container(height=50)
    )

    date_picker = ft.DatePicker(on_change=lambda e: mostrar_horarios(e.control.value.strftime("%Y-%m-%d"))) # (Lógica de horarios igual)

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.environ.get("PORT", 8080)), host="0.0.0.0", assets_dir=".")
