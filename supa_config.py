import requests
import warnings

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

SUPABASE_URL = "https://fdhjanrmfgevuxzersnd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZkaGphbnJtZmdldnV4emVyc25kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4NjQ0NzcsImV4cCI6MjA4OTQ0MDQ3N30.-Q0mZwmSWvLAgsb0p4w7LGtN2DvHGOcvUyjmMoiNLJg"

def obtener_citas():
    url = f"{SUPABASE_URL}/rest/v1/Citas?select=*" 
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    respuesta = requests.get(url, headers=headers, verify=False)
    if respuesta.status_code == 200:
        return respuesta.json()
    else:
        raise Exception(f"Error de conexión: {respuesta.text}")

def guardar_cita(fecha, hora, nombre, telefono, servicio):
    url = f"{SUPABASE_URL}/rest/v1/Citas" 
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal" 
    }
    datos = {
        "fecha": fecha,
        "hora": hora,
        "cliente_nombre": nombre,
        "cliente_telefono": telefono,
        "servicio": servicio 
    }
    respuesta = requests.post(url, headers=headers, json=datos, verify=False)
    if respuesta.status_code not in (200, 201, 204):
        raise Exception(f"Error al guardar: {respuesta.text}")

def borrar_cita(cita_id):
    url = f"{SUPABASE_URL}/rest/v1/Citas?id=eq.{cita_id}" 
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    respuesta = requests.delete(url, headers=headers, verify=False)
    
    if respuesta.status_code not in (200, 204):
        raise Exception(f"Error al borrar: {respuesta.text}")

# --- FUNCIÓN CORREGIDA CON REQUESTS ---
def marcar_asistencia(cita_id):
    """Cambia el estatus de asistencia a Verdadero para el programa de lealtad"""
    url = f"{SUPABASE_URL}/rest/v1/Citas?id=eq.{cita_id}" 
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal" 
    }
    datos = {
        "asistio": True
    }
    respuesta = requests.patch(url, headers=headers, json=datos, verify=False)
    
    if respuesta.status_code not in (200, 204):
        raise Exception(f"Error al marcar asistencia: {respuesta.text}")
