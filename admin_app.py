import flet as ft
import os
import datetime
from supa_config import obtener_citas, marcar_asistencia

# --- CONFIGURACIÓN ---
PIN_SECRETO = "2026"  # <--- Cambia esto por el NIP que tú quieras
BG_COLOR = "#0C1533"
CARD_COLOR = "#1D284C"
ACCENT_COLOR = "#89F336" # Usamos tu verde lima para el admin
TEXT_WHITE = ft.Colors.WHITE

def main(page: ft.Page):
    page.title = "Fisi-K Admin"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_COLOR
    page.scroll = "adaptive"
    page.window.width = 400
    page.window.height = 750

    # --- 1. PANTALLA DE LOGIN ---
    input_pin = ft.TextField(
        label="PIN de Seguridad", 
        password=True, 
        can_reveal_password=True,
        text_align=ft.TextAlign.CENTER,
        keyboard_type=ft.KeyboardType.NUMBER,
        width=250,
        border_radius=15,
        border_color=ACCENT_COLOR
    )
    
    texto_error = ft.Text("", color=ft.Colors.RED_400, visible=False)

    def verificar_pin(e):
        if input_pin.value == PIN_SECRETO:
            pantalla_login.visible = False
            pantalla_admin.visible = True
            cargar_citas_hoy()
        else:
            texto_error.value = "PIN Incorrecto. Intenta de nuevo."
            texto_error.visible = True
            input_pin.value = ""
        page.update()

    btn_entrar = ft.ElevatedButton("Entrar al Panel", bgcolor=ACCENT_COLOR, color=BG_COLOR, on_click=verificar_pin)

    pantalla_login = ft.Column([
        ft.Container(height=100),
        ft.Icon(ft.Icons.LOCK_OUTLINE, size=80, color=ACCENT_COLOR),
        ft.Text("ACCESO RESTRINGIDO", size=20, weight="bold", tracking=2),
        ft.Text("Solo personal autorizado", color=ft.Colors.WHITE54),
        ft.Container(height=20),
        input_pin,
        texto_error,
        btn_entrar
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=True)

    # --- 2. PANTALLA DE ADMINISTRADOR ---
    lista_citas_ui = ft.Column(spacing=15)
    
    def confirmar_asistencia(e, cita_id, boton):
        try:
            boton.disabled = True
            boton.text = "Aprobado ✅"
            boton.bgcolor = ft.Colors.GREEN_700
            page.update()
            marcar_asistencia(cita_id)
            page.show_dialog(ft.SnackBar(ft.Text("Asistencia y sellito registrado."), bgcolor=ft.Colors.GREEN, open=True))
        except Exception as ex:
            page.show_dialog(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED, open=True))

    def cargar_citas_hoy():
        lista_citas_ui.controls.clear()
        
        # Ajuste de hora local
        ahora_mx = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
        hoy_str = ahora_mx.strftime("%Y-%m-%d")
        
        try:
            todas_las_citas = obtener_citas()
            # Filtramos solo las de hoy
            citas_hoy = [c for c in todas_las_citas if c.get('fecha') == hoy_str]
            
            # Ordenamos por hora
            citas_hoy.sort(key=lambda x: datetime.datetime.strptime(x['hora'], "%I:%M %p"))

            if not citas_hoy:
                lista_citas_ui.controls.append(
                    ft.Text("No hay citas agendadas para hoy.", color=ft.Colors.WHITE54, italic=True)
                )
            
            for cita in citas_hoy:
                ya_asistio = cita.get('asistio', False)
                
                # Botón inteligente para WhatsApp (Funciona perfecto en Android/iOS)
                btn_wa = ft.IconButton(
                    icon=ft.Icons.CHAT, 
                    icon_color=ft.Colors.GREEN_400,
                    tooltip="Enviar WhatsApp",
                    on_click=lambda e, tel=cita['telefono'], nom=cita['nombre']: page.launch_url(f"https://wa.me/52{tel}?text=Hola {nom}, te escribimos de Fisi-K Center para confirmar tu cita de hoy.")
                )
                
                btn_asistencia = ft.ElevatedButton(
                    "Aprobado ✅" if ya_asistio else "Dar Sellito", 
                    bgcolor=ft.Colors.GREEN_700 if ya_asistio else ACCENT_COLOR,
                    color=TEXT_WHITE if ya_asistio else BG_COLOR,
                    disabled=ya_asistio,
                    on_click=lambda e, cid=cita.get('id'): confirmar_asistencia(e, cid, e.control)
                )

                tarjeta = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(cita['hora'], size=18, weight="bold", color=ACCENT_COLOR),
                            btn_wa
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(cita['nombre'].upper(), size=16, weight="bold"),
                        ft.Text(f"📞 {cita['telefono']}", color=ft.Colors.WHITE70),
                        ft.Text(f"💆‍♀️ {cita['servicio']}", color=ft.Colors.WHITE70),
                        ft.Divider(color=ft.Colors.WHITE24),
                        btn_asistencia
                    ]),
                    bgcolor=CARD_COLOR,
                    padding=15,
                    border_radius=15,
                    border=ft.border.all(1, ft.Colors.WHITE10)
                )
                lista_citas_ui.controls.append(tarjeta)
                
        except Exception as ex:
            lista_citas_ui.controls.append(ft.Text(f"Error al cargar: {ex}", color=ft.Colors.RED))
        
        page.update()

    btn_refrescar = ft.FloatingActionButton(
        icon=ft.Icons.REFRESH, 
        bgcolor=ACCENT_COLOR, 
        on_click=lambda _: cargar_citas_hoy()
    )

    pantalla_admin = ft.Column([
        ft.Container(height=10),
        ft.Row([
            ft.Text("CITAS DE HOY", size=24, weight="bold", tracking=2),
            btn_refrescar
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(color=ACCENT_COLOR),
        lista_citas_ui
    ], visible=False)

    page.add(pantalla_login, pantalla_admin)

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.environ.get("PORT", 8080)), host="0.0.0.0", assets_dir=".")
