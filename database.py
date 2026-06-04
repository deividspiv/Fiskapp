import requests
import urllib3

# Apagamos advertencias del firewall
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- LLAVES DE TU PROYECTO (Webhook) ---
SUPABASE_URL = "https://fdhjanrmfgevuxzersnd.supabase.co/rest/v1/" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZkaGphbnJtZmdldnV4emVyc25kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4NjQ0NzcsImV4cCI6MjA4OTQ0MDQ3N30.-Q0mZwmSWvLAgsb0p4w7LGtN2DvHGOcvUyjmMoiNLJg"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

class AppDB:
    # ---------------------------------------------------------
    # USUARIOS (clients)
    # ---------------------------------------------------------
    @staticmethod
    def verificar_usuario(celular):
        url = f"{SUPABASE_URL}/rest/v1/clients"
        params = {"phone": f"eq.{celular}", "select": "*"}
        response = requests.get(url, headers=HEADERS, params=params, verify=False)
        if response.status_code == 200 and len(response.json()) > 0:
            return response.json()[0]
        return None

    @staticmethod
    def registrar_usuario(celular, nombre):
        url = f"{SUPABASE_URL}/rest/v1/clients"
        data = {
            "phone": celular, 
            "full_name": nombre,
            "active_package": "inactivo",
            "credits": 0 
        }
        response = requests.post(url, headers=HEADERS, json=data, verify=False)
        return response.status_code == 201

    # ---------------------------------------------------------
    # PAQUETES (packages)
    # ---------------------------------------------------------
    @staticmethod
    def obtener_paquetes():
        url = f"{SUPABASE_URL}/rest/v1/packages"
        params = {"select": "*", "order": "price.asc"}
        response = requests.get(url, headers=HEADERS, params=params, verify=False)
        if response.status_code == 200:
            return response.json()
        return []

    # ---------------------------------------------------------
    # PAGOS (payments)
    # ---------------------------------------------------------
    @staticmethod
    def crear_registro_pago(celular, monto):
        url = f"{SUPABASE_URL}/rest/v1/payments"
        data = {"client_phone": celular, "amount": float(monto), "status": "PENDIENTE"}
        response = requests.post(url, headers=HEADERS, json=data, verify=False)
        return response.status_code == 201

    # ---------------------------------------------------------
    # CLASES Y CALENDARIO (classes)
    # ---------------------------------------------------------
    @staticmethod
    def get_reservation_count(class_id):
        url = f"{SUPABASE_URL}/rest/v1/reservations"
        params = {"class_id": f"eq.{class_id}", "status": "eq.activa", "select": "id"}
        headers_count = HEADERS.copy()
        headers_count["Prefer"] = "count=exact"
        response = requests.get(url, headers=headers_count, params=params, verify=False)
        rango = response.headers.get("Content-Range", "0-0/0")
        try:
            return int(rango.split("/")[-1])
        except:
            return 0

    @staticmethod
    def obtener_clases(servicio, fecha):
        url = f"{SUPABASE_URL}/rest/v1/classes"
        params = {
            "select": "*", 
            "service_name": f"eq.{servicio}", 
            "class_date": f"eq.{fecha}",
            "is_blocked": "is.false",
            "order": "start_time.asc"
        }
        response = requests.get(url, headers=HEADERS, params=params, verify=False)
        clases_formateadas = []
        if response.status_code == 200:
            for c in response.json():
                reservas_actuales = AppDB.get_reservation_count(c["id"])
                cupo_total = c.get("capacity", 10) 
                clases_formateadas.append({
                    "id": c["id"],
                    "hora": c.get("start_time", "00:00"),
                    "instructor": c.get("instructor", "Staff"),
                    "cupo": cupo_total - reservas_actuales
                })
        return clases_formateadas

    # ---------------------------------------------------------
    # RESERVAS (reservations)
    # ---------------------------------------------------------
    @staticmethod
    def obtener_reservas_usuario(telefono):
        url = f"{SUPABASE_URL}/rest/v1/reservations"
        params = {
            "select": "id, status, class_id, classes(class_date, start_time, service_name)", 
            "client_phone": f"eq.{telefono}",
            "order": "id.desc"
        }
        response = requests.get(url, headers=HEADERS, params=params, verify=False)
        reservas_formateadas = []
        if response.status_code == 200:
            for r in response.json():
                clase_info = r.get("classes") or {}
                estado_ui = "futura" if r.get("status") == "activa" else "cancelada"
                reservas_formateadas.append({
                    "id": r["id"],
                    "class_id": r.get("class_id"), 
                    "servicio": clase_info.get("service_name", "Clase"), 
                    "class_date": clase_info.get('class_date', ''),
                    "start_time": clase_info.get('start_time', ''),
                    "fecha": f"{clase_info.get('class_date', '')}, {clase_info.get('start_time', '')}",
                    "estado": estado_ui
                })
        return reservas_formateadas

    @staticmethod
    def reservar_clase(telefono, clase_id):
        user = AppDB.verificar_usuario(telefono)
        creditos = user.get("credits", 0) if user else 0
        if creditos <= 0: 
            return False 
        
        url_update = f"{SUPABASE_URL}/rest/v1/clients"
        requests.patch(url_update, headers=HEADERS, params={"phone": f"eq.{telefono}"}, json={"credits": creditos - 1}, verify=False)

        url_res = f"{SUPABASE_URL}/rest/v1/reservations"
        data = {"client_phone": telefono, "class_id": clase_id, "status": "activa"}
        response = requests.post(url_res, headers=HEADERS, json=data, verify=False)
        return response.status_code == 201

    @staticmethod
    def cancelar_reserva(reserva_id):
        url = f"{SUPABASE_URL}/rest/v1/reservations"
        params = {"id": f"eq.{reserva_id}"}
        data = {"status": "cancelada"}
        response = requests.patch(url, headers=HEADERS, params=params, json=data, verify=False)
        return response.status_code in [200, 204]

    @staticmethod
    def asignar_creditos(telefono, cantidad_creditos):
        url = f"{SUPABASE_URL}/rest/v1/clients"
        params = {"phone": f"eq.{telefono}"}
        data = {"credits": cantidad_creditos}
        response = requests.patch(url, headers=HEADERS, params=params, json=data, verify=False)
        return response.status_code in [200, 204]

    # ---------------------------------------------------------
    # ADMIN Y CREACIÓN DE CLASES
    # ---------------------------------------------------------
    @staticmethod
    def obtener_servicios():
        url = f"{SUPABASE_URL}/rest/v1/services"
        response = requests.get(url, headers=HEADERS, verify=False)
        if response.status_code == 200:
            return response.json()
        return []

    @staticmethod
    def crear_clase(service_name, fecha, hora, instructor, cupo):
        url = f"{SUPABASE_URL}/rest/v1/classes"
        data = {
            "service_name": service_name, 
            "class_date": fecha,
            "start_time": hora,
            "instructor": instructor,
            "capacity": int(cupo),
            "is_blocked": False
        }
        response = requests.post(url, headers=HEADERS, json=data, verify=False)
        if response.status_code != 201:
            print(f"ERROR DE SUPABASE: {response.text}")
        return response.status_code == 201

    @staticmethod
    def verificar_disponibilidad(fecha, hora):
        url = f"{SUPABASE_URL}/rest/v1/classes"
        params = {
            "class_date": f"eq.{fecha}",
            "start_time": f"eq.{hora}",
            "select": "*"
        }
        response = requests.get(url, headers=HEADERS, params=params, verify=False)
        return len(response.json()) > 0

    @staticmethod
    def actualizar_clase(clase_id, service_name, fecha, hora, instructor, cupo):
        url = f"{SUPABASE_URL}/rest/v1/classes"
        params = {"id": f"eq.{clase_id}"}
        data = {
            "service_name": service_name,
            "class_date": fecha,
            "start_time": hora,
            "instructor": instructor,
            "capacity": int(cupo)
        }
        response = requests.patch(url, headers=HEADERS, params=params, json=data, verify=False)
        return response.status_code in [200, 204]

    @staticmethod
    def obtener_todas_las_clases_dia(fecha):
        url = f"{SUPABASE_URL}/rest/v1/classes"
        params = {
            "class_date": f"eq.{fecha}",
            "order": "start_time.asc"
        }
        response = requests.get(url, headers=HEADERS, params=params, verify=False)
        return response.json() if response.status_code == 200 else []

    # ---------------------------------------------------------
    # SISTEMA DE BLOQUEO DE DÍAS 
    # ---------------------------------------------------------
    @staticmethod
    def bloquear_dia(fecha):
        url = f"{SUPABASE_URL}/rest/v1/classes"
        data = {
            "service_name": "Bloqueo",
            "class_date": fecha,
            "start_time": "00:00",
            "instructor": "Sistema",
            "capacity": 0,
            "is_blocked": True
        }
        response = requests.post(url, headers=HEADERS, json=data, verify=False)
        return response.status_code == 201

    @staticmethod
    def obtener_dias_bloqueados():
        url = f"{SUPABASE_URL}/rest/v1/classes"
        params = {"is_blocked": "is.true", "select": "id, class_date", "order": "class_date.asc"}
        response = requests.get(url, headers=HEADERS, params=params, verify=False)
        return response.json() if response.status_code == 200 else []

    @staticmethod
    def desbloquear_dia(bloqueo_id):
        url = f"{SUPABASE_URL}/rest/v1/classes"
        params = {"id": f"eq.{bloqueo_id}"}
        response = requests.delete(url, headers=HEADERS, params=params, verify=False)
        return response.status_code in [200, 204]

    @staticmethod
    def es_dia_bloqueado(fecha):
        url = f"{SUPABASE_URL}/rest/v1/classes"
        params = {"class_date": f"eq.{fecha}", "is_blocked": "is.true", "select": "id"}
        response = requests.get(url, headers=HEADERS, params=params, verify=False)
        return len(response.json()) > 0 if response.status_code == 200 else False

    @staticmethod
    def eliminar_clase(clase_id):
        url = f"{SUPABASE_URL}/rest/v1/classes"
        params = {"id": f"eq.{clase_id}"}
        response = requests.delete(url, headers=HEADERS, params=params, verify=False)
        return response.status_code in [200, 204]

    @staticmethod
    def obtener_agenda_rango(fecha_inicio, fecha_fin):
        url = f"{SUPABASE_URL}/rest/v1/classes"
        query = f"class_date=gte.{fecha_inicio}&class_date=lte.{fecha_fin}&order=class_date.asc,start_time.asc"
        response = requests.get(f"{url}?{query}", headers=HEADERS, verify=False)
        return response.json() if response.status_code == 200 else []

    # ---------------------------------------------------------
    # OBTENER ALUMNOS POR CLASE
    # ---------------------------------------------------------
    @staticmethod
    def obtener_alumnos_clase(class_id):
        try:
            url_res = f"{SUPABASE_URL}/rest/v1/reservations"
            params_res = {
                "class_id": f"eq.{class_id}",
                "status": "eq.activa",
                "select": "client_phone"
            }
            resp_res = requests.get(url_res, headers=HEADERS, params=params_res, verify=False)
            
            if resp_res.status_code != 200:
                return []
                
            telefonos = [r.get("client_phone") for r in resp_res.json() if r.get("client_phone")]
            
            alumnos_detalles = []
            if telefonos:
                telefonos_str = ",".join(telefonos)
                url_cli = f"{SUPABASE_URL}/rest/v1/clients"
                params_cli = {
                    "phone": f"in.({telefonos_str})",
                    "select": "full_name, active_package"
                }
                resp_cli = requests.get(url_cli, headers=HEADERS, params=params_cli, verify=False)
                
                if resp_cli.status_code == 200:
                    alumnos_detalles = resp_cli.json()
                    
            return alumnos_detalles
            
        except Exception as e:
            print(f"Error obteniendo alumnos de la clase: {e}")
            return []
