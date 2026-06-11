# --- RECUPERACIÓN DE SESIÓN (iOS / ANDROID) ---
        if not page.session.get("user_phone"):
            try:
                tel_guardado = page.client_storage.get("user_phone")
                nombre_guardado = page.client_storage.get("user_name")
                monto_guardado = page.client_storage.get("monto_pendiente") # Recuperamos el pago

                if tel_guardado:
                    page.session.set("user_phone", tel_guardado)
                    if nombre_guardado:
                        page.session.set("user_name", nombre_guardado)
                    if monto_guardado:
                        page.session.set("monto_pendiente", monto_guardado)
                    
                    if page.route == "/login" or page.route == "/":
                        # ¡NUEVO! Si la app se recargó y estabas pagando, te devuelve a la pantalla de espera
                        if monto_guardado:
                            page.go("/pago/verificando")
                            return

                        usuario_rec = AppDB.verificar_usuario(tel_guardado)
                        if usuario_rec and str(usuario_rec.get('active_package', '')).lower().strip() == 'pagado' and usuario_rec.get('credits', 0) > 0:
                            page.go("/servicios")
                        else:
                            page.go("/paquetes")
                        return
            except: pass
