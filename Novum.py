import flet as ft
from database import AppDB
from pagos import generar_enlace_pago
import time
import datetime

# --- PALETA DE COLORES "RESPIRO" ---
COLOR_RESPIRO       = "#a3968d"
COLOR_RESPIRO_DARK  = "#8e8279"
COLOR_CREMA_BOTON   = "#dfd0c1"
COLOR_BG_CLARO      = "#f4f2f1"
COLOR_TEXTO_OSCURO  = "#4a4a4a"
COLOR_TEXTO_BLANCO  = "#FFFFFF"
COLOR_CARD_BG       = "#FFFFFF"
COLOR_DIVIDER       = "#ede8e4"
COLOR_ACCENT_LIGHT  = "#f0ebe7"


# ─── Helpers de UI (Mejoras visuales) ────────────────────────────────────────

def _label(text, size=11, color=COLOR_RESPIRO_DARK, spacing=1.5):
    """Pequeña etiqueta en mayúsculas."""
    return ft.Text(
        text.upper(),
        size=size,
        color=color,
        weight=ft.FontWeight.W_600,
    )

def _pill(text, bg=COLOR_RESPIRO, fg=COLOR_TEXTO_BLANCO, on_click=None, width=None):
    return ft.Container(
        content=ft.Text(text, color=fg, weight=ft.FontWeight.W_600, size=14),
        bgcolor=bg,
        padding=ft.padding.symmetric(horizontal=24, vertical=13),
        border_radius=30,
        width=width,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(blur_radius=16, color="#28a3968d", offset=ft.Offset(0, 6)),
        on_click=on_click,
        animate=ft.animation.Animation(150, ft.AnimationCurve.EASE_OUT),
    )

def _card(content, padding=20, radius=18, elevation=True):
    return ft.Container(
        content=content,
        bgcolor=COLOR_CARD_BG,
        padding=padding,
        border_radius=radius,
        border=ft.border.all(1, COLOR_DIVIDER),
        shadow=ft.BoxShadow(
            blur_radius=20 if elevation else 0,
            color="#14000000",
            offset=ft.Offset(0, 6),
        ),
    )

def _section_title(text):
    return ft.Row([
        ft.Container(width=3, height=18, bgcolor=COLOR_RESPIRO, border_radius=2),
        ft.Container(width=8),
        ft.Text(text, size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
    ])

def _avatar(inicial, size=44, on_click=None):
    return ft.Container(
        content=ft.Text(inicial, size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_BLANCO),
        alignment=ft.alignment.center,
        width=size, height=size,
        bgcolor=COLOR_RESPIRO,
        border_radius=size // 2,
        shadow=ft.BoxShadow(blur_radius=12, color="#33a3968d", offset=ft.Offset(0, 4)),
        on_click=on_click,
    )

def _back_btn(on_click):
    return ft.Container(
        content=ft.Icon(ft.icons.ARROW_BACK_IOS_NEW_ROUNDED, color=COLOR_RESPIRO, size=18),
        width=38, height=38,
        border_radius=19,
        bgcolor=COLOR_ACCENT_LIGHT,
        alignment=ft.alignment.center,
        on_click=on_click,
    )


# ─── Tarjeta de precio ───────────────────────────────────────────────────────

def RespiroPricingCard(title, price, savings_text, features_list, package_id, page):
    features_ui = [
        ft.Row([
            ft.Container(
                content=ft.Icon(ft.icons.CHECK_ROUNDED, size=12, color=COLOR_TEXTO_BLANCO),
                width=20, height=20, border_radius=10, bgcolor=COLOR_RESPIRO,
                alignment=ft.alignment.center,
            ),
            ft.Text(feat, size=13, weight=ft.FontWeight.W_500, color=COLOR_TEXTO_OSCURO),
        ], spacing=10)
        for feat in features_list
    ]

    return ft.Container(
        content=ft.Column([
            # Header degradado
            ft.Container(
                content=ft.Column([
                    _label(title, color="#e8ddd7"),
                    ft.Container(height=6),
                    ft.Text(price, size=38, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_BLANCO),
                    ft.Text(savings_text, size=12, color="#ccc4be"),
                ], spacing=0),
                bgcolor=COLOR_RESPIRO,
                padding=ft.padding.all(22),
                border_radius=ft.border_radius.only(top_left=18, top_right=18),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[COLOR_RESPIRO, COLOR_RESPIRO_DARK],
                ),
            ),
            # Body
            ft.Container(
                content=ft.Column([
                    ft.Container(height=4),
                    ft.Column(features_ui, spacing=12),
                    ft.Container(height=16),
                    ft.Container(
                        content=ft.Row([
                            ft.Text("Elegir plan", color=COLOR_RESPIRO, weight=ft.FontWeight.BOLD, size=14),
                            ft.Icon(ft.icons.ARROW_FORWARD_ROUNDED, color=COLOR_RESPIRO, size=16),
                        ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                        bgcolor=COLOR_ACCENT_LIGHT,
                        padding=ft.padding.symmetric(vertical=14),
                        border_radius=14,
                        on_click=lambda _: page.go(f"/pago/{package_id}"),
                    ),
                ], spacing=0),
                padding=ft.padding.only(left=22, right=22, top=18, bottom=20),
            ),
        ], spacing=0),
        bgcolor=COLOR_CARD_BG,
        border_radius=18,
        width=270,
        border=ft.border.all(1, COLOR_DIVIDER),
        shadow=ft.BoxShadow(blur_radius=24, color="#1Aa3968d", offset=ft.Offset(0, 8)),
    )


# ─── Función principal ───────────────────────────────────────────────────────

def main(page: ft.Page):
    page.title = "Novum Pilates"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.fonts = {
        "Playfair": "https://fonts.gstatic.com/s/playfairdisplay/v37/nuFiD-vYSZviVYUb_rj3ij__anPXDTnCjmHKM4nYO7KN_pqdbR7ods.ttf",
        "DM Sans": "https://fonts.gstatic.com/s/dmsans/v15/rP2tp2ywxg089UriI5-g4vlH9VoD8Cmcqbu6-K6z9mXgjU0.ttf",
    }
    page.theme = ft.Theme(font_family="DM Sans")

    # Variables de sesión
    page.session.set("is_logged_in", False)
    page.session.set("has_active_package", False)
    page.session.set("user_phone", "")
    page.session.set("monto_pendiente", "")

    # --- SINCRONIZACIÓN SILENCIOSA ---
    def sync_creditos_silencioso(telefono):
        if not telefono:
            return
        try:
            u_sync = AppDB.verificar_usuario(telefono)
            if u_sync and str(u_sync.get('active_package', '')).lower().strip() == 'pagado':
                if u_sync.get('credits', 0) <= 0:
                    monto_guardado = None
                    try:
                        monto_guardado = page.client_storage.get("monto_pendiente")
                    except:
                        pass
                    monto = page.session.get("monto_pendiente") or monto_guardado or "650"
                    nuevos_creditos = {"100": 1, "650": 8, "800": 12, "1000": 30}.get(str(monto), 8)
                    AppDB.asignar_creditos(telefono, nuevos_creditos)
                    try:
                        page.client_storage.remove("monto_pendiente")
                    except:
                        pass
        except Exception as e:
            print("Error en sincronización silenciosa:", e)

    # --- DIÁLOGO ADMIN ---
    admin_pwd_field = ft.TextField(
        label="Contraseña", password=True, can_reveal_password=True,
        border_radius=12, border_color=COLOR_RESPIRO,
        cursor_color=COLOR_RESPIRO, bgcolor=COLOR_BG_CLARO,
    )

    def check_admin_pwd(e):
        if admin_pwd_field.value == "3157525":
            admin_dlg.open = False
            page.update()
            page.go("/admin")
        else:
            admin_pwd_field.error_text = "Contraseña incorrecta"
            page.update()

    admin_dlg = ft.AlertDialog(
        title=ft.Text("Acceso Administrativo", color=COLOR_RESPIRO, weight=ft.FontWeight.BOLD),
        content=admin_pwd_field,
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _: setattr(admin_dlg, 'open', False) or page.update()),
            ft.ElevatedButton("Entrar", bgcolor=COLOR_RESPIRO, color=COLOR_TEXTO_BLANCO, on_click=check_admin_pwd),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=18),
    )
    page.overlay.append(admin_dlg)

    # =========================================================================
    # ENRUTAMIENTO
    # =========================================================================
    def route_change(e):
        page.views.clear()

        # ── 1. PORTADA ────────────────────────────────────────────────────────
        if page.route == "/login":
            page.views.append(ft.View(
                "/login",
                bgcolor=COLOR_RESPIRO,
                padding=0,
                controls=[
                    ft.Container(
                        expand=True,
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_center,
                            end=ft.alignment.bottom_center,
                            colors=[COLOR_RESPIRO, COLOR_RESPIRO_DARK],
                        ),
                        padding=ft.padding.only(left=30, right=30, top=50, bottom=48),
                        content=ft.Column(
                            [
                                ft.Row([
                                    ft.Container(expand=True),
                                    ft.Container(
                                        content=ft.Icon(ft.icons.SETTINGS_OUTLINED, color="white54", size=20),
                                        width=38, height=38, border_radius=19, bgcolor="#22FFFFFF",
                                        alignment=ft.alignment.center,
                                        on_click=lambda _: setattr(admin_dlg, 'open', True) or page.update(),
                                    ),
                                ]),
                                ft.Container(expand=True),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Container(
                                            content=ft.Icon(ft.icons.SPA_OUTLINED, size=52, color=COLOR_TEXTO_BLANCO),
                                            width=88, height=88, border_radius=44, bgcolor="#33FFFFFF",
                                            alignment=ft.alignment.center, border=ft.border.all(1.5, "#55FFFFFF"),
                                        ),
                                        ft.Container(height=20),
                                        ft.Image(src="logo_respiros.png", width=220, fit=ft.ImageFit.CONTAIN),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                                    alignment=ft.alignment.center,
                                ),
                                ft.Container(height=16),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("Pilates · Yoga · Relax", size=14, color="#BBFFFFFF", weight=ft.FontWeight.W_500),
                                        ft.Container(height=6),
                                        ft.Container(width=40, height=1, bgcolor="#44FFFFFF"),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                    alignment=ft.alignment.center,
                                ),
                                ft.Container(expand=True),
                                ft.Text("Tu espacio de bienestar", size=13, color="#99FFFFFF", weight=ft.FontWeight.W_400),
                                ft.Container(height=20),
                                ft.Container(
                                    content=ft.Row([
                                        ft.Text("Iniciar Sesión", color="#6b5b50", weight=ft.FontWeight.BOLD, size=15),
                                        ft.Icon(ft.icons.ARROW_FORWARD_ROUNDED, color="#6b5b50", size=16),
                                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                                    alignment=ft.alignment.center, width=320, height=56,
                                    bgcolor=COLOR_CREMA_BOTON, border_radius=28,
                                    shadow=ft.BoxShadow(blur_radius=20, color="#44000000", offset=ft.Offset(0, 6)),
                                    on_click=lambda _: page.go("/formulario_ingreso"),
                                ),
                                ft.Container(height=12),
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.icons.PERSON_ADD_ALT_1_OUTLINED, color="#CCFFFFFF", size=16),
                                        ft.Text("¿Nuevo? Regístrate aquí", color="#CCFFFFFF", size=13),
                                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                                    on_click=lambda _: page.go("/formulario_ingreso"),
                                    padding=ft.padding.all(12),
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    )
                ],
            ))

        # ── 1.5 FORMULARIO ────────────────────────────────────────────────────
        elif page.route == "/formulario_ingreso":
            nombre_field = ft.TextField(
                label="Nombre completo", border_radius=14, prefix_icon=ft.icons.PERSON_OUTLINE_ROUNDED,
                border_color=COLOR_DIVIDER, focused_border_color=COLOR_RESPIRO,
                cursor_color=COLOR_RESPIRO, bgcolor=COLOR_BG_CLARO, label_style=ft.TextStyle(color=COLOR_RESPIRO_DARK),
            )
            celular_field = ft.TextField(
                label="Número celular (10 dígitos)", border_radius=14, prefix_icon=ft.icons.PHONE_OUTLINED,
                keyboard_type=ft.KeyboardType.PHONE, border_color=COLOR_DIVIDER,
                focused_border_color=COLOR_RESPIRO, cursor_color=COLOR_RESPIRO,
                bgcolor=COLOR_BG_CLARO, label_style=ft.TextStyle(color=COLOR_RESPIRO_DARK),
            )

            btn_continuar = ft.Container(
                content=ft.Row([
                    ft.Text("Continuar", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD, size=15),
                    ft.Icon(ft.icons.ARROW_FORWARD_ROUNDED, color=COLOR_TEXTO_BLANCO, size=16),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                width=320, height=54, bgcolor=COLOR_RESPIRO, border_radius=27,
                alignment=ft.alignment.center, shadow=ft.BoxShadow(blur_radius=18, color="#28a3968d", offset=ft.Offset(0, 6)),
            )

            def do_login(e):
                if nombre_field.value and celular_field.value:
                    btn_continuar.content = ft.Row([
                        ft.ProgressRing(width=20, height=20, color=COLOR_TEXTO_BLANCO, stroke_width=2),
                        ft.Text(" Verificando...", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=8)
                    btn_continuar.update()

                    usuario = AppDB.verificar_usuario(celular_field.value)
                    if not usuario:
                        AppDB.registrar_usuario(celular_field.value, nombre_field.value)
                        nombre_final = nombre_field.value
                    else:
                        nombre_final = usuario.get('full_name', nombre_field.value)

                    sync_creditos_silencioso(celular_field.value)
                    usuario_actualizado = AppDB.verificar_usuario(celular_field.value)
                    tiene_paquete_activo = False
                    if usuario_actualizado and str(usuario_actualizado.get('active_package', '')).lower().strip() == 'pagado':
                        if usuario_actualizado.get('credits', 0) > 0:
                            tiene_paquete_activo = True

                    page.session.set("user_phone", celular_field.value)
                    page.session.set("user_name", nombre_final)
                    page.session.set("has_active_package", tiene_paquete_activo)
                    page.go("/servicios" if tiene_paquete_activo else "/paquetes")

            btn_continuar.on_click = do_login

            page.views.append(ft.View(
                "/formulario_ingreso",
                bgcolor=COLOR_BG_CLARO,
                padding=0,
                controls=[
                    ft.Container(
                        expand=True,
                        padding=ft.padding.only(left=28, right=28, top=56, bottom=40),
                        content=ft.Column(
                            [
                                ft.Row([_back_btn(lambda _: page.go("/login")), ft.Container(expand=True)]),
                                ft.Container(height=36),
                                ft.Container(
                                    content=ft.Icon(ft.icons.SPA_OUTLINED, size=32, color=COLOR_RESPIRO),
                                    width=64, height=64, border_radius=32, bgcolor=COLOR_ACCENT_LIGHT,
                                    alignment=ft.alignment.center,
                                ),
                                ft.Container(height=18),
                                ft.Text("Bienvenida", size=32, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                                ft.Text("Ingresa tus datos para acceder\na tu espacio de bienestar", size=14, color=COLOR_RESPIRO_DARK),
                                ft.Container(height=32),
                                nombre_field, ft.Container(height=12), celular_field,
                                ft.Container(expand=True), ft.Container(height=30), btn_continuar,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.START,
                        ),
                    )
                ],
            ))

        # ── 2. PAQUETES ───────────────────────────────────────────────────────
        elif page.route == "/paquetes":
            paquetes_db = AppDB.obtener_paquetes()
            lista_tarjetas = [ft.Container(width=16)]
            for pq in paquetes_db:
                creditos_texto = f"{pq['credits']} clases a elegir" if pq.get('credits') else "Clases ilimitadas"
                precio_entero = int(pq['price'])
                lista_tarjetas.append(
                    RespiroPricingCard(
                        pq["name"], f"${precio_entero}", f"Vigencia: {pq['validity_days']} días",
                        [creditos_texto, "Reserva desde la app"], str(precio_entero), page,
                    )
                )
            lista_tarjetas.append(ft.Container(width=16))

            page.views.append(ft.View(
                "/paquetes",
                bgcolor=COLOR_BG_CLARO,
                padding=0,
                controls=[
                    ft.Container(
                        expand=True,
                        content=ft.Column([
                            ft.Container(
                                content=ft.Column([
                                    ft.Container(height=52),
                                    _label("Membresías"), ft.Container(height=6),
                                    ft.Text("Elige tu plan", size=32, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                                    ft.Text("El que mejor se adapte a tu rutina.", size=14, color=COLOR_RESPIRO_DARK),
                                ]),
                                padding=ft.padding.only(left=24, right=24, bottom=24),
                            ),
                            ft.Container(
                                content=ft.ListView(lista_tarjetas, horizontal=True, spacing=14),
                                height=400,
                            ),
                        ], spacing=0),
                    )
                ],
            ))

        # ── 3. PAGO ───────────────────────────────────────────────────────────
        elif page.route.startswith("/pago/") and not page.route.endswith("/verificando"):
            monto = page.route.split("/")[2]
            page.session.set("monto_pendiente", monto)

            def _pago_btn(icono, label, bg, fg, on_click_fn=None, url=None):
                return ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(icono, color=fg, size=18),
                            width=36, height=36, border_radius=18, bgcolor=f"{fg}22", alignment=ft.alignment.center,
                        ),
                        ft.Text(label, color=fg, weight=ft.FontWeight.BOLD, size=14),
                        ft.Container(expand=True),
                        ft.Icon(ft.icons.ARROW_FORWARD_IOS_ROUNDED, color=f"{fg}88", size=14),
                    ], spacing=14),
                    bgcolor=bg, padding=ft.padding.all(18), border_radius=16,
                    border=ft.border.all(1, f"{fg}22"), shadow=ft.BoxShadow(blur_radius=12, color="#10000000", offset=ft.Offset(0, 4)),
                    on_click=on_click_fn, url=url,
                )

            btn_bbva_ctrl = _pago_btn(ft.icons.CREDIT_CARD_OUTLINED, "Pagar en línea (BBVA)", "#004481", "#FFFFFF")

            def pagar_bbva(e):
                btn_bbva_ctrl.content = ft.Row([
                    ft.ProgressRing(width=18, height=18, color=COLOR_TEXTO_BLANCO, stroke_width=2),
                    ft.Text(" Conectando al banco...", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD, size=14),
                ], spacing=12)
                btn_bbva_ctrl.on_click = None
                page.update()

                telefono = page.session.get("user_phone")
                nombre = page.session.get("user_name")
                AppDB.crear_registro_pago(telefono, monto)
                try: page.client_storage.set("monto_pendiente", str(monto))
                except: pass

                link = generar_enlace_pago(monto, f"Paquete Novum Pilates {monto}", nombre, telefono)
                if link:
                    btn_bbva_ctrl.content = ft.Row([
                        ft.Icon(ft.icons.LOCK_OUTLINE, color=COLOR_TEXTO_BLANCO, size=18),
                        ft.Text("Toca aquí para abrir el banco", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.Icon(ft.icons.OPEN_IN_NEW_ROUNDED, color="#AAFFFFFF", size=14),
                    ], spacing=12)
                    btn_bbva_ctrl.bgcolor = ft.colors.GREEN_600
                    btn_bbva_ctrl.url = link
                    btn_bbva_ctrl.on_click = lambda _: page.go("/pago/verificando")
                    page.update()

            btn_bbva_ctrl.on_click = pagar_bbva

            def pagar_recepcion_click(e):
                snack = ft.SnackBar(ft.Text("Solicitud enviada. Paga en recepción.", color=COLOR_TEXTO_BLANCO), bgcolor=COLOR_RESPIRO)
                page.overlay.append(snack)
                snack.open = True
                page.update()

            btn_recepcion = _pago_btn(ft.icons.PAYMENTS_OUTLINED, "Pagar en Recepción", COLOR_ACCENT_LIGHT, COLOR_RESPIRO_DARK, on_click_fn=pagar_recepcion_click)

            page.views.append(ft.View(
                page.route,
                bgcolor=COLOR_BG_CLARO,
                padding=0,
                controls=[
                    ft.Container(
                        expand=True,
                        padding=ft.padding.only(left=24, right=24, top=56, bottom=40),
                        content=ft.Column([
                            ft.Row([_back_btn(lambda _: page.go("/paquetes")), ft.Container(expand=True)]),
                            ft.Container(height=28), _label("Resumen de compra"), ft.Container(height=10),
                            _card(
                                ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.icons.RECEIPT_LONG_OUTLINED, color=COLOR_RESPIRO, size=22),
                                        ft.Container(expand=True),
                                        ft.Container(
                                            content=ft.Text("MXN", size=11, color=COLOR_RESPIRO, weight=ft.FontWeight.BOLD),
                                            bgcolor=COLOR_ACCENT_LIGHT, padding=ft.padding.symmetric(horizontal=10, vertical=4), border_radius=20,
                                        ),
                                    ]),
                                    ft.Container(height=12),
                                    ft.Text(f"${monto}.00", size=42, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                                    ft.Text("Total a pagar", size=13, color=COLOR_RESPIRO_DARK),
                                ]),
                                padding=ft.padding.all(22),
                            ),
                            ft.Container(height=28), _label("Método de pago"), ft.Container(height=12),
                            btn_bbva_ctrl, ft.Container(height=12), btn_recepcion,
                        ], spacing=0),
                    )
                ],
            ))

        # ── 3.5 VERIFICANDO PAGO ──────────────────────────────────────────────
        elif page.route == "/pago/verificando":
            def auto_check_payment():
                telefono_alumno = page.session.get("user_phone")
                if not telefono_alumno: return
                for _ in range(60):
                    if page.route != "/pago/verificando": break
                    time.sleep(2)
                    try:
                        u = AppDB.verificar_usuario(telefono_alumno)
                        if u and str(u.get('active_package', '')).lower().strip() == 'pagado':
                            sync_creditos_silencioso(telefono_alumno)
                            page.session.set("monto_pendiente", "")
                            page.go("/servicios")
                            return
                    except Exception: pass

            page.run_task(auto_check_payment)

            def verificar_manual(e):
                sync_creditos_silencioso(page.session.get("user_phone"))
                page.session.set("monto_pendiente", "")
                page.go("/servicios")

            page.views.append(ft.View(
                "/pago/verificando",
                bgcolor=COLOR_BG_CLARO,
                padding=24,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(height=60),
                    ft.Container(
                        content=ft.Icon(ft.icons.LOCK_OUTLINE, color=COLOR_RESPIRO, size=32),
                        width=72, height=72, border_radius=36, bgcolor=COLOR_ACCENT_LIGHT, alignment=ft.alignment.center,
                    ),
                    ft.Container(height=20),
                    ft.Text("Pago Seguro", size=26, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                    ft.Text("Verificando tu transacción…", size=14, color=COLOR_RESPIRO_DARK),
                    ft.Container(height=40),
                    ft.Container(
                        content=ft.Column([
                            ft.ProgressRing(width=48, height=48, color=COLOR_RESPIRO, stroke_width=3),
                            ft.Container(height=16),
                            ft.Text("Aprobando automáticamente", size=14, color=COLOR_RESPIRO_DARK),
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center, height=140,
                    ),
                    ft.Container(height=40),
                    _pill("Comprobar manualmente", on_click=verificar_manual, width=280),
                ],
            ))

        # ── 4. SERVICIOS Y AGENDA ─────────────────────────────────────────────
        elif page.route == "/servicios":
            telefono_alumno = page.session.get("user_phone")
            sync_creditos_silencioso(telefono_alumno)

            nombre_usuario = page.session.get('user_name')
            primer_nombre = nombre_usuario.split()[0] if nombre_usuario else 'Alumno'
            inicial = primer_nombre[0].upper() if primer_nombre else "A"
            hoy = datetime.date.today()
            vista_estado = {"fecha_activa": hoy, "servicio_activo": "Pilates"}

            servicios_ui = ft.Row(spacing=8, scroll=ft.ScrollMode.HIDDEN)
            dias_ui = ft.Row(spacing=10, scroll=ft.ScrollMode.HIDDEN)
            horarios_ui = ft.Column(spacing=12)

            def recargar_pantalla():
                horarios_ui.controls.clear()
                horarios_ui.controls.append(
                    ft.Container(content=ft.ProgressRing(color=COLOR_RESPIRO, width=32, height=32, stroke_width=3), alignment=ft.alignment.center, padding=40)
                )
                page.update()

                mis_reservas = AppDB.obtener_reservas_usuario(telefono_alumno)
                fechas_reservadas_limpias = []
                clases_agendadas = []
                for r in mis_reservas:
                    if r.get("estado", "").lower() == "futura":
                        clases_agendadas.append(r.get("class_id"))
                        f_raw = str(r.get("class_date") or r.get("fecha", "")).strip()
                        if " " in f_raw: f_raw = f_raw.split(" ")[0]
                        fechas_reservadas_limpias.append(f_raw)

                servicios_ui.controls.clear()
                for serv in ["Pilates", "Yoga", "Ejercicios Funcionales"]:
                    es_activo = (serv == vista_estado["servicio_activo"])
                    servicios_ui.controls.append(ft.Container(
                        content=ft.Text(serv, weight=ft.FontWeight.W_600, color=COLOR_TEXTO_BLANCO if es_activo else COLOR_RESPIRO_DARK, size=13),
                        bgcolor=COLOR_RESPIRO if es_activo else COLOR_CARD_BG,
                        padding=ft.padding.symmetric(horizontal=18, vertical=10), border_radius=22,
                        border=ft.border.all(1, COLOR_RESPIRO if es_activo else COLOR_DIVIDER),
                        shadow=ft.BoxShadow(blur_radius=10 if es_activo else 0, color="#20a3968d", offset=ft.Offset(0, 4)),
                        on_click=lambda e, s=serv: al_seleccionar_servicio(s),
                    ))

                dias_ui.controls.clear()
                nombres_dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
                for i in range(14):
                    fecha_iter = hoy + datetime.timedelta(days=i)
                    es_seleccionado = (fecha_iter == vista_estado["fecha_activa"])
                    bg = COLOR_RESPIRO if es_seleccionado else COLOR_CARD_BG
                    fg = COLOR_TEXTO_BLANCO if es_seleccionado else COLOR_TEXTO_OSCURO
                    fg2 = COLOR_TEXTO_BLANCO if es_seleccionado else COLOR_RESPIRO_DARK

                    dia_str = fecha_iter.strftime("%Y-%m-%d")
                    tiene_reserva = any((dia_str in f) or (f in dia_str) for f in fechas_reservadas_limpias)

                    indicador = ft.Container(width=6, height=6, bgcolor=COLOR_TEXTO_BLANCO if es_seleccionado else COLOR_RESPIRO, border_radius=3) if tiene_reserva else ft.Container(height=6)

                    dias_ui.controls.append(ft.Container(
                        content=ft.Column([
                            ft.Text(nombres_dias[fecha_iter.weekday()], size=11, color=fg2, weight=ft.FontWeight.W_500),
                            ft.Text(str(fecha_iter.day), size=20, color=fg, weight=ft.FontWeight.BOLD),
                            indicador,
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                        bgcolor=bg, width=58, height=80, border_radius=14,
                        border=ft.border.all(1, COLOR_DIVIDER) if not es_seleccionado else None,
                        shadow=ft.BoxShadow(blur_radius=14 if es_seleccionado else 0, color="#22a3968d", offset=ft.Offset(0, 4)),
                        on_click=lambda e, f=fecha_iter: al_seleccionar_dia(f),
                    ))

                horarios_ui.controls.clear()
                fecha_str = str(vista_estado["fecha_activa"])

                if AppDB.es_dia_bloqueado(fecha_str):
                    horarios_ui.controls.append(_card(
                        ft.Column([
                            ft.Container(
                                content=ft.Icon(ft.icons.NIGHTLIGHT_ROUND_OUTLINED, size=36, color=COLOR_RESPIRO),
                                width=68, height=68, border_radius=34, bgcolor=COLOR_ACCENT_LIGHT, alignment=ft.alignment.center,
                            ),
                            ft.Container(height=12),
                            ft.Text("Estudio Cerrado", size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                            ft.Text("Tómate un descanso.\nNos vemos pronto.", text_align=ft.TextAlign.CENTER, color=COLOR_RESPIRO_DARK, size=13),
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.all(32),
                    ))
                else:
                    clases_del_dia = AppDB.obtener_clases(vista_estado["servicio_activo"], fecha_str)
                    dia_ya_reservado = any((fecha_str in f) or (f in fecha_str) for f in fechas_reservadas_limpias)

                    if not clases_del_dia:
                        horarios_ui.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.icons.EVENT_BUSY_OUTLINED, size=36, color=COLOR_RESPIRO),
                                    ft.Container(height=8),
                                    ft.Text(f"Sin clases de {vista_estado['servicio_activo']}", color=COLOR_RESPIRO_DARK, size=14),
                                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=30,
                            )
                        )

                    for h in clases_del_dia:
                        is_full = h["cupo"] <= 0
                        ya_agendado = h["id"] in clases_agendadas

                        if ya_agendado:
                            badge_bg, badge_fg, badge_txt, accion_btn = ft.colors.GREEN_50, ft.colors.GREEN_700, "Agendado ✓", lambda _: page.go("/perfil")
                        elif dia_ya_reservado:
                            badge_bg, badge_fg, badge_txt, accion_btn = COLOR_ACCENT_LIGHT, COLOR_RESPIRO_DARK, "Día Reservado", None
                        else:
                            badge_bg = "#E5E5EA" if is_full else COLOR_CREMA_BOTON
                            badge_fg = COLOR_RESPIRO_DARK if is_full else "#6b5b50"
                            badge_txt = "Lleno" if is_full else "Reservar"
                            accion_btn = (lambda e, c=h: confirmar_reserva(c)) if not is_full else None

                        cupo_color = COLOR_RESPIRO if not is_full else ft.colors.RED_400

                        horarios_ui.controls.append(_card(
                            ft.Row([
                                ft.Column([
                                    ft.Text(h["hora"], size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                                    ft.Container(height=2),
                                    ft.Row([ft.Icon(ft.icons.PERSON_OUTLINE, size=13, color=COLOR_RESPIRO_DARK), ft.Text(h['instructor'], size=12, color=COLOR_RESPIRO_DARK)], spacing=4),
                                    ft.Row([ft.Icon(ft.icons.PEOPLE_OUTLINE, size=13, color=cupo_color), ft.Text(f"{h['cupo']} lugares", size=12, color=cupo_color)], spacing=4),
                                ], spacing=2),
                                ft.Container(expand=True),
                                ft.Container(
                                    content=ft.Text(badge_txt, weight=ft.FontWeight.BOLD, color=badge_fg, size=13),
                                    bgcolor=badge_bg, padding=ft.padding.symmetric(horizontal=16, vertical=10), border_radius=22, on_click=accion_btn,
                                ),
                            ]),
                            padding=ft.padding.all(18),
                        ))
                page.update()

            def al_seleccionar_dia(f): vista_estado["fecha_activa"] = f; recargar_pantalla()
            def al_seleccionar_servicio(s): vista_estado["servicio_activo"] = s; recargar_pantalla()

            def confirmar_reserva(clase):
                usuario_actual = AppDB.verificar_usuario(telefono_alumno)
                if (usuario_actual.get('credits', 0) if usuario_actual else 0) <= 0:
                    page.go("/paquetes"); return
                if AppDB.reservar_clase(telefono_alumno, clase["id"]):
                    snack = ft.SnackBar(ft.Text("¡Reserva confirmada! Se descontó 1 clase.", color=COLOR_TEXTO_BLANCO), bgcolor=ft.colors.GREEN_600)
                    page.overlay.append(snack); snack.open = True; recargar_pantalla()

            recargar_pantalla()

            page.views.append(ft.View(
                "/servicios",
                bgcolor=COLOR_BG_CLARO,
                padding=0,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(
                        content=ft.Column([
                            ft.Container(height=52),
                            ft.Container(
                                content=ft.Row([
                                    ft.Column([
                                        ft.Text(f"Hola, {primer_nombre} 👋", size=24, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                                        ft.Text("Reserva tu próxima clase", size=13, color=COLOR_RESPIRO_DARK),
                                    ], spacing=2),
                                    ft.Container(expand=True), _avatar(inicial, on_click=lambda _: page.go("/perfil")),
                                ]),
                                padding=ft.padding.symmetric(horizontal=24),
                            ),
                            ft.Container(height=24),
                            ft.Container(content=servicios_ui, padding=ft.padding.symmetric(horizontal=24)),
                            ft.Container(height=20),
                            ft.Container(content=dias_ui, padding=ft.padding.symmetric(horizontal=24)),
                            ft.Container(height=22),
                            ft.Container(content=_section_title("Horarios Disponibles"), padding=ft.padding.symmetric(horizontal=24)),
                            ft.Container(height=12),
                            ft.Container(content=horarios_ui, padding=ft.padding.symmetric(horizontal=24)),
                            ft.Container(height=48),
                        ], spacing=0),
                    )
                ],
            ))

        # ── 4.5 PERFIL ────────────────────────────────────────────────────────
        elif page.route == "/perfil":
            telefono_alumno = page.session.get("user_phone")
            sync_creditos_silencioso(telefono_alumno)

            usuario = AppDB.verificar_usuario(telefono_alumno)
            clases_restantes = usuario.get('credits', 0) if usuario else 0
            mis_reservas = AppDB.obtener_reservas_usuario(telefono_alumno)

            def forzar_recarga_perfil():
                page.route = "/recargando"; page.update(); page.go("/perfil")

            def refrescar_creditos_click(e):
                e.control.content = ft.Row([
                    ft.ProgressRing(width=18, height=18, color=COLOR_RESPIRO, stroke_width=2),
                    ft.Text(" Sincronizando...", color=COLOR_RESPIRO, size=13, weight=ft.FontWeight.W_600),
                ], alignment="center")
                e.control.update()
                u_sync = AppDB.verificar_usuario(telefono_alumno)
                monto = page.session.get("monto_pendiente") or "650"
                if u_sync and str(u_sync.get('active_package', '')).lower().strip() == 'pagado':
                    if u_sync.get('credits', 0) <= 0:
                        nuevos_creditos = {"100": 1, "650": 8, "800": 12, "1000": 30}.get(str(monto), 8)
                        AppDB.asignar_creditos(telefono_alumno, nuevos_creditos)
                    snack = ft.SnackBar(ft.Text("¡Tus clases han sido sincronizadas!"), bgcolor=ft.colors.GREEN_600)
                else:
                    snack = ft.SnackBar(ft.Text("Aún no detectamos tu pago."), bgcolor=ft.colors.ORANGE_600)
                page.overlay.append(snack); snack.open = True; forzar_recarga_perfil()

            reserva_a_cancelar = [None]
            aplica_penalizacion = [False]

            def ejecutar_cancelacion_final(e):
                rid = reserva_a_cancelar[0]
                penalizar = aplica_penalizacion[0]
                dlg_cancelar.open = False
                page.update()
                AppDB.cancelar_reserva(rid)
                if not penalizar:
                    u_actual = AppDB.verificar_usuario(telefono_alumno)
                    creditos_previos = u_actual.get('credits', 0) if u_actual else 0
                    AppDB.asignar_creditos(telefono_alumno, creditos_previos + 1)
                msg = "Cancelada con penalidad (< 12hrs)." if penalizar else "Clase cancelada. Se devolvió 1 crédito."
                snack = ft.SnackBar(ft.Text(msg, color=COLOR_TEXTO_BLANCO), bgcolor=ft.colors.ORANGE_600 if penalizar else ft.colors.GREEN_600)
                page.overlay.append(snack); snack.open = True; forzar_recarga_perfil()

            dlg_cancelar = ft.AlertDialog(
                title=ft.Text("Cancelar Sesión", weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                content=ft.Text(""), shape=ft.RoundedRectangleBorder(radius=18),
                actions=[
                    ft.TextButton("Volver", on_click=lambda _: setattr(dlg_cancelar, 'open', False) or page.update()),
                    ft.ElevatedButton("Sí, Cancelar", bgcolor=ft.colors.RED_500, color="white", on_click=ejecutar_cancelacion_final),
                ],
            )
            page.overlay.append(dlg_cancelar)

            def preparar_cancelacion(res):
                reserva_a_cancelar[0] = res.get("id")
                es_penalizable = False
                try:
                    c_date = res.get("class_date") or res.get("fecha")
                    s_time = res.get("start_time") or res.get("hora")
                    if c_date and s_time:
                        dt_str = f"{c_date.split()[0]} {s_time.strip()}"
                        try: dt_clase = datetime.datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
                        except ValueError: dt_clase = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                        ahora_mexico = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
                        horas_diff = (dt_clase - ahora_mexico).total_seconds() / 3600
                        if 0 < horas_diff <= 12: es_penalizable = True
                except Exception as ex: print("Error calculando tiempo:", ex)

                aplica_penalizacion[0] = es_penalizable
                if es_penalizable:
                    dlg_cancelar.content = ft.Text("Faltan menos de 12 horas para tu clase. Si cancelas perderás este crédito según nuestra política.\n\n¿Deseas cancelar de todos modos?", color=ft.colors.RED_600, size=13)
                else:
                    dlg_cancelar.content = ft.Text("¿Segura que deseas cancelar tu clase?\nTu crédito será devuelto automáticamente.", size=13)
                dlg_cancelar.open = True; page.update()

            lista_reservas_ui = ft.Column(spacing=12)
            for res in mis_reservas:
                is_futura = res.get("estado", "").lower() == "futura"
                estado_badge = ft.Container(
                    content=ft.Text(res.get("estado", "").capitalize(), size=11, color=COLOR_RESPIRO if is_futura else COLOR_RESPIRO_DARK, weight=ft.FontWeight.BOLD),
                    bgcolor=COLOR_ACCENT_LIGHT if is_futura else "#F5F5F5", padding=ft.padding.symmetric(horizontal=10, vertical=4), border_radius=20,
                )
                elementos = [
                    ft.Row([ft.Text(res.get("servicio", "Clase"), size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), ft.Container(expand=True), estado_badge]),
                    ft.Row([ft.Icon(ft.icons.CALENDAR_TODAY_OUTLINED, size=13, color=COLOR_RESPIRO_DARK), ft.Text(res.get("fecha", ""), size=13, color=COLOR_RESPIRO_DARK)], spacing=6),
                ]
                if is_futura:
                    elementos.append(ft.Row([
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Row([ft.Icon(ft.icons.CANCEL_OUTLINED, size=14, color=ft.colors.RED_400), ft.Text("Cancelar", size=13, color=ft.colors.RED_400, weight=ft.FontWeight.W_600)], spacing=4),
                            on_click=lambda e, r=res: preparar_cancelacion(r),
                        ),
                    ]))

                lista_reservas_ui.controls.append(_card(ft.Column(elementos, spacing=8), padding=ft.padding.all(18)))

            if not mis_reservas:
                lista_reservas_ui.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.EVENT_NOTE_OUTLINED, size=36, color=COLOR_RESPIRO), ft.Container(height=8),
                            ft.Text("Sin historial de reservas", color=COLOR_RESPIRO_DARK, size=14),
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=30,
                    )
                )

            alerta_creditos = ft.Container()
            if clases_restantes <= 0:
                alerta_creditos = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.ORANGE_600, size=22),
                        ft.Column([
                            ft.Text("Sin clases disponibles", size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                            ft.Text("Compra un paquete para continuar", size=12, color=COLOR_RESPIRO_DARK),
                        ], spacing=2),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Text("Comprar", size=12, color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD),
                            bgcolor=COLOR_RESPIRO, padding=ft.padding.symmetric(horizontal=14, vertical=8), border_radius=16,
                            on_click=lambda _: page.go("/paquetes"),
                        ),
                    ], spacing=12),
                    bgcolor="#FFF8F0", padding=ft.padding.all(16), border_radius=14, border=ft.border.all(1, "#FFD599"), margin=ft.margin.only(bottom=8),
                )

            page.views.append(ft.View(
                "/perfil",
                bgcolor=COLOR_BG_CLARO,
                padding=0, scroll="auto",
                controls=[
                    ft.Container(
                        content=ft.Column([
                            ft.Container(height=52),
                            ft.Container(
                                content=ft.Row([_back_btn(lambda _: page.go("/servicios")), ft.Container(expand=True), ft.Text("Mi Perfil", size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), ft.Container(expand=True), ft.Container(width=38)]),
                                padding=ft.padding.symmetric(horizontal=24),
                            ),
                            ft.Container(height=24),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=24),
                                content=ft.Column([
                                    _card(
                                        ft.Row([
                                            ft.Column([
                                                _label("Clases restantes"), ft.Container(height=4),
                                                ft.Text(str(clases_restantes), size=48, weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO),
                                            ]),
                                            ft.Container(expand=True),
                                            ft.Container(
                                                content=ft.Icon(ft.icons.FITNESS_CENTER_ROUNDED, size=28, color=COLOR_RESPIRO),
                                                width=60, height=60, border_radius=30, bgcolor=COLOR_ACCENT_LIGHT, alignment=ft.alignment.center,
                                            ),
                                        ]), padding=ft.padding.all(22),
                                    ),
                                    ft.Container(height=12),
                                    ft.Container(
                                        content=ft.Row([
                                            ft.Icon(ft.icons.SYNC_ROUNDED, color=COLOR_RESPIRO, size=16),
                                            ft.Text("¿Pagaste y no ves tus clases? Sincronizar", color=COLOR_RESPIRO, size=13, weight=ft.FontWeight.W_600),
                                        ], alignment="center", spacing=8),
                                        padding=ft.padding.all(14), border=ft.border.all(1.5, COLOR_RESPIRO), border_radius=12,
                                        on_click=refrescar_creditos_click,
                                    ),
                                    ft.Container(height=8), alerta_creditos,
                                    ft.Container(height=16), _section_title("Tus Reservas"), ft.Container(height=12), lista_reservas_ui,
                                    ft.Container(height=24),
                                    ft.Container(
                                        content=ft.Row([
                                            ft.Icon(ft.icons.LOGOUT_ROUNDED, color=ft.colors.RED_400, size=16),
                                            ft.Text("Cerrar Sesión", color=ft.colors.RED_400, weight=ft.FontWeight.W_600, size=14),
                                        ], alignment="center", spacing=8),
                                        on_click=lambda _: page.go("/login"), padding=ft.padding.all(14),
                                    ),
                                    ft.Container(height=48),
                                ], spacing=0),
                            ),
                        ], spacing=0),
                    )
                ],
            ))

        # ── 5. ADMIN ──────────────────────────────────────────────────────────
        elif page.route == "/admin":
            fecha_activa = [datetime.date.today()]
            txt_fecha_top = ft.Text(fecha_activa[0].strftime("%Y-%m-%d"), size=14, weight=ft.FontWeight.BOLD, color=COLOR_RESPIRO)
            modo_agenda = ["30"]

            def set_modo_30(e):
                modo_agenda[0] = "30"
                btn_modo_30.bgcolor, btn_modo_30.content.color = COLOR_RESPIRO, "white"
                btn_modo_dia.bgcolor, btn_modo_dia.content.color = COLOR_ACCENT_LIGHT, COLOR_RESPIRO
                recargar_listas()

            def set_modo_dia(e):
                modo_agenda[0] = "dia"
                btn_modo_dia.bgcolor, btn_modo_dia.content.color = COLOR_RESPIRO, "white"
                btn_modo_30.bgcolor, btn_modo_30.content.color = COLOR_ACCENT_LIGHT, COLOR_RESPIRO
                recargar_listas()

            def _tab_btn(label, active, on_click_fn):
                return ft.Container(
                    content=ft.Text(label, size=13, weight=ft.FontWeight.W_600, color="white" if active else COLOR_RESPIRO),
                    bgcolor=COLOR_RESPIRO if active else COLOR_ACCENT_LIGHT, padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    border_radius=20, on_click=on_click_fn,
                )

            btn_modo_30 = _tab_btn("30 Días", True, set_modo_30)
            btn_modo_dia = _tab_btn("Día Específico", False, set_modo_dia)

            opciones_servicios = [ft.dropdown.Option(s["name"]) for s in AppDB.obtener_servicios()]
            drop_serv = ft.Dropdown(label="Servicio", options=opciones_servicios, border_color=COLOR_DIVIDER, focused_border_color=COLOR_RESPIRO, border_radius=12, bgcolor=COLOR_BG_CLARO)
            drop_hora = ft.Dropdown(label="Horario", options=[ft.dropdown.Option("08:00 AM"), ft.dropdown.Option("09:15 AM"), ft.dropdown.Option("06:30 PM")], border_color=COLOR_DIVIDER, focused_border_color=COLOR_RESPIRO, border_radius=12, bgcolor=COLOR_BG_CLARO)
            txt_inst = ft.TextField(label="Instructor", value="Staff", border_color=COLOR_DIVIDER, focused_border_color=COLOR_RESPIRO, border_radius=12, bgcolor=COLOR_BG_CLARO, expand=True)
            txt_cupo = ft.TextField(label="Cupo", value="10", keyboard_type=ft.KeyboardType.NUMBER, border_color=COLOR_DIVIDER, focused_border_color=COLOR_RESPIRO, border_radius=12, bgcolor=COLOR_BG_CLARO, width=90)

            lista_agenda = ft.ListView(expand=True, spacing=10)
            lista_bloqueos = ft.ListView(expand=True, spacing=10)

            dlg_detalles = ft.AlertDialog(
                title=ft.Text("Alumnos en la clase", color=COLOR_RESPIRO, weight="bold"),
                content=ft.Column([], scroll="auto", height=300, width=300), shape=ft.RoundedRectangleBorder(radius=18),
                actions=[ft.TextButton("Cerrar", on_click=lambda _: setattr(dlg_detalles, 'open', False) or page.update())],
            )
            page.overlay.append(dlg_detalles)

            def ver_detalles_clase(cid):
                dlg_detalles.content.controls.clear()
                dlg_detalles.content.controls.append(ft.Container(content=ft.ProgressRing(color=COLOR_RESPIRO), alignment=ft.alignment.center, padding=20))
                dlg_detalles.open = True; page.update()

                alumnos = AppDB.obtener_alumnos_clase(cid) if hasattr(AppDB, 'obtener_alumnos_clase') else []
                dlg_detalles.content.controls.clear()
                if not alumnos:
                    dlg_detalles.content.controls.append(ft.Text("No hay alumnos inscritos aún.", color=COLOR_RESPIRO_DARK))
                else:
                    dlg_detalles.content.controls.append(ft.Text(f"Total inscritos: {len(alumnos)}", weight="bold", color=COLOR_TEXTO_OSCURO))
                    for al in alumnos:
                        estado_al = al.get('active_package', 'Sin paquete')
                        color_icono = ft.colors.GREEN_600 if estado_al.lower() == 'pagado' else ft.colors.ORANGE_600
                        dlg_detalles.content.controls.append(ft.ListTile(leading=ft.Icon(ft.icons.PERSON_ROUNDED, color=color_icono), title=ft.Text(al.get('full_name', 'Desconocido'), weight="bold"), subtitle=ft.Text(f"Estado: {estado_al.capitalize()}")))
                page.update()

            def borrar_clase(cid):
                AppDB.eliminar_clase(cid); recargar_listas()
                snack = ft.SnackBar(ft.Text("Clase eliminada.", color=COLOR_TEXTO_BLANCO), bgcolor=ft.colors.RED_500)
                page.overlay.append(snack); snack.open = True; page.update()

            def recargar_listas():
                f_str = fecha_activa[0].strftime("%Y-%m-%d")
                lista_agenda.controls.clear()
                lista_agenda.controls.append(ft.Container(content=ft.ProgressRing(color=COLOR_RESPIRO), alignment=ft.alignment.center, padding=40)); page.update()
                lista_agenda.controls.clear()

                if modo_agenda[0] == "30":
                    hoy_str = datetime.date.today().strftime("%Y-%m-%d")
                    fin_str = (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
                    clases = AppDB.obtener_agenda_rango(hoy_str, fin_str)
                else:
                    clases = AppDB.obtener_todas_las_clases_dia(f_str)

                if not clases: lista_agenda.controls.append(ft.Text("No hay clases programadas.", color=COLOR_RESPIRO_DARK))

                for c in clases:
                    if not c.get('is_blocked'):
                        fecha_lbl = f"{c['class_date']} · " if modo_agenda[0] == "30" else ""
                        lista_agenda.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(content=ft.Icon(ft.icons.FITNESS_CENTER_ROUNDED, size=18, color=COLOR_RESPIRO), width=38, height=38, border_radius=19, bgcolor=COLOR_ACCENT_LIGHT, alignment=ft.alignment.center),
                                    ft.Column([
                                        ft.Text(f"{fecha_lbl}{c['start_time']} — {c['service_name']}", weight=ft.FontWeight.BOLD, size=13, color=COLOR_TEXTO_OSCURO),
                                        ft.Text(f"Prof: {c['instructor']}  ·  Cupo: {c.get('capacity', 10)}", size=12, color=COLOR_RESPIRO_DARK),
                                    ], spacing=2, expand=True),
                                    ft.Container(expand=True),
                                    ft.Row([
                                        ft.Container(content=ft.Icon(ft.icons.PEOPLE_ALT_OUTLINED, size=16, color=COLOR_RESPIRO), width=32, height=32, border_radius=16, bgcolor=COLOR_ACCENT_LIGHT, alignment=ft.alignment.center, on_click=lambda e, cid=c['id']: ver_detalles_clase(cid)),
                                        ft.Container(content=ft.Icon(ft.icons.DELETE_OUTLINE_ROUNDED, size=16, color=ft.colors.RED_400), width=32, height=32, border_radius=16, bgcolor="#FFEBEE", alignment=ft.alignment.center, on_click=lambda e, cid=c['id']: borrar_clase(cid)),
                                    ], spacing=6),
                                ], spacing=12),
                                bgcolor=COLOR_CARD_BG, padding=ft.padding.all(14), border_radius=14, border=ft.border.all(1, COLOR_DIVIDER), shadow=ft.BoxShadow(blur_radius=8, color="#0A000000", offset=ft.Offset(0, 3)),
                            )
                        )

                lista_bloqueos.controls.clear()
                bloqueos = AppDB.obtener_dias_bloqueados()
                if not bloqueos: lista_bloqueos.controls.append(ft.Text("No hay días cerrados programados.", color=COLOR_RESPIRO_DARK))
                for b in bloqueos:
                    lista_bloqueos.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Container(content=ft.Icon(ft.icons.BLOCK_ROUNDED, size=16, color=ft.colors.RED_400), width=34, height=34, border_radius=17, bgcolor="#FFEBEE", alignment=ft.alignment.center),
                                ft.Text(b['class_date'], weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO),
                                ft.Container(expand=True),
                                ft.Container(content=ft.Icon(ft.icons.DELETE_OUTLINE_ROUNDED, size=16, color=ft.colors.RED_400), width=32, height=32, border_radius=16, bgcolor="#FFEBEE", alignment=ft.alignment.center, on_click=lambda e, bid=b['id']: (AppDB.desbloquear_dia(bid), recargar_listas())),
                            ], spacing=10),
                            bgcolor=COLOR_CARD_BG, padding=ft.padding.all(14), border_radius=14, border=ft.border.all(1, "#FFD7D7"),
                        )
                    )
                page.update()

            def al_cambiar_fecha_admin(e):
                if dp_admin.value:
                    fecha_activa[0] = dp_admin.value; txt_fecha_top.value = fecha_activa[0].strftime("%Y-%m-%d"); set_modo_dia(None)

            dp_admin = ft.DatePicker(on_change=al_cambiar_fecha_admin)
            page.overlay.append(dp_admin)

            def accion_publicar_clase(e):
                f_str = fecha_activa[0].strftime("%Y-%m-%d")
                if AppDB.es_dia_bloqueado(f_str):
                    snack = ft.SnackBar(ft.Text("¡Error! Día marcado como Cerrado."), bgcolor=ft.colors.RED_500)
                elif AppDB.verificar_disponibilidad(f_str, drop_hora.value):
                    snack = ft.SnackBar(ft.Text("¡Horario ocupado! Revisa la agenda."), bgcolor=ft.colors.RED_500)
                elif drop_serv.value and drop_hora.value:
                    AppDB.crear_clase(drop_serv.value, f_str, drop_hora.value, txt_inst.value, txt_cupo.value)
                    snack = ft.SnackBar(ft.Text("Clase publicada correctamente."), bgcolor=ft.colors.GREEN_600)
                    drop_serv.value, drop_hora.value = None, None; recargar_listas()
                else:
                    snack = ft.SnackBar(ft.Text("Completa todos los campos."), bgcolor=ft.colors.ORANGE_500)
                page.overlay.append(snack); snack.open = True; page.update()

            txt_fecha_bloqueo = ft.TextField(label="Fecha a bloquear", hint_text="Selecciona en el calendario →", read_only=True, expand=True, border_color=COLOR_DIVIDER, focused_border_color=COLOR_RESPIRO, border_radius=12, bgcolor=COLOR_BG_CLARO)
            dp_bloqueo = ft.DatePicker(on_change=lambda e: setattr(txt_fecha_bloqueo, 'value', dp_bloqueo.value.strftime("%Y-%m-%d")) or page.update() if dp_bloqueo.value else None, first_date=datetime.date.today())
            page.overlay.append(dp_bloqueo)

            def accion_bloquear_dia(e):
                f_str = txt_fecha_bloqueo.value
                if f_str:
                    if not AppDB.es_dia_bloqueado(f_str):
                        AppDB.bloquear_dia(f_str); recargar_listas()
                        snack = ft.SnackBar(ft.Text(f"Día {f_str} bloqueado."), bgcolor=ft.colors.GREEN_600); txt_fecha_bloqueo.value = ""
                    else: snack = ft.SnackBar(ft.Text("Ese día ya está bloqueado."), bgcolor=ft.colors.ORANGE_500)
                else: snack = ft.SnackBar(ft.Text("Selecciona una fecha primero."), bgcolor=ft.colors.RED_500)
                page.overlay.append(snack); snack.open = True; page.update()

            recargar_listas()

            tab_crear = ft.Tab(
                text="Crear", icon=ft.icons.ADD_BOX_OUTLINED,
                content=ft.Container(
                    padding=ft.padding.all(20),
                    content=ft.Column([
                        _section_title("Agendar Nueva Clase"), ft.Container(height=16), drop_serv, ft.Container(height=10), drop_hora, ft.Container(height=10),
                        ft.Row([txt_inst, txt_cupo], spacing=10), ft.Container(height=20),
                        ft.Container(
                            content=ft.Row([ft.Icon(ft.icons.ADD_ROUNDED, color=COLOR_TEXTO_BLANCO, size=18), ft.Text("Publicar Clase", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD, size=14)], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                            bgcolor=COLOR_RESPIRO, height=50, border_radius=14, alignment=ft.alignment.center, shadow=ft.BoxShadow(blur_radius=12, color="#28a3968d", offset=ft.Offset(0, 4)), on_click=accion_publicar_clase,
                        ),
                    ], spacing=0),
                ),
            )

            tab_agenda = ft.Tab(text="Agenda", icon=ft.icons.FORMAT_LIST_BULLETED_ROUNDED, content=ft.Container(padding=ft.padding.all(20), content=ft.Column([ft.Row([btn_modo_30, btn_modo_dia], spacing=8), ft.Container(height=14), lista_agenda])))
            
            tab_bloqueos = ft.Tab(
                text="Cierres", icon=ft.icons.BLOCK_ROUNDED,
                content=ft.Container(
                    padding=ft.padding.all(20),
                    content=ft.Column([
                        _section_title("Días Inhábiles"), ft.Container(height=4), ft.Text("Cierra el estudio en fechas específicas.", size=12, color=COLOR_RESPIRO_DARK), ft.Container(height=14),
                        ft.Row([
                            txt_fecha_bloqueo,
                            ft.Container(content=ft.Icon(ft.icons.CALENDAR_MONTH_OUTLINED, color=ft.colors.RED_400, size=22), width=46, height=46, border_radius=14, bgcolor="#FFEBEE", alignment=ft.alignment.center, on_click=lambda _: dp_bloqueo.pick_date()),
                        ], spacing=8),
                        ft.Container(height=10),
                        ft.Container(
                            content=ft.Row([ft.Icon(ft.icons.BLOCK_ROUNDED, color=COLOR_TEXTO_BLANCO, size=16), ft.Text("Bloquear Fecha", color=COLOR_TEXTO_BLANCO, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                            bgcolor=ft.colors.RED_400, height=48, border_radius=14, alignment=ft.alignment.center, on_click=accion_bloquear_dia,
                        ),
                        ft.Container(height=20), _section_title("Próximos cierres"), ft.Container(height=10), lista_bloqueos,
                    ], spacing=0),
                ),
            )

            page.views.append(ft.View(
                "/admin",
                bgcolor=COLOR_BG_CLARO,
                padding=0,
                controls=[
                    ft.Container(
                        bgcolor=COLOR_CARD_BG, padding=ft.padding.only(left=8, right=16, top=48, bottom=12),
                        border=ft.border.only(bottom=ft.BorderSide(1, COLOR_DIVIDER)), shadow=ft.BoxShadow(blur_radius=8, color="#0A000000"),
                        content=ft.Row([
                            _back_btn(lambda _: page.go("/login")), ft.Container(width=8),
                            ft.Column([ft.Text("Panel Admin", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_OSCURO), ft.Text("Novum Pilates", size=11, color=COLOR_RESPIRO_DARK)], spacing=0),
                            ft.Container(expand=True),
                            ft.Row([
                                txt_fecha_top,
                                ft.Container(content=ft.Icon(ft.icons.CALENDAR_MONTH_OUTLINED, color=COLOR_RESPIRO, size=18), width=36, height=36, border_radius=18, bgcolor=COLOR_ACCENT_LIGHT, alignment=ft.alignment.center, on_click=lambda _: dp_admin.pick_date()),
                            ], spacing=8),
                        ], spacing=0),
                    ),
                    ft.Tabs(selected_index=0, animation_duration=250, unselected_label_color=COLOR_RESPIRO_DARK, label_color=COLOR_RESPIRO, indicator_color=COLOR_RESPIRO, indicator_tab_size=True, expand=True, tabs=[tab_crear, tab_agenda, tab_bloqueos]),
                ],
            ))

        elif page.route == "/recargando":
            pass

        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)
        else:
            page.go("/login")

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8080))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0", assets_dir="assets")
