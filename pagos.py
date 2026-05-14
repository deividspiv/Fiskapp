import requests
import urllib3
import time
import re # Importamos para limpiar texto

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CREDENCIALES OPENPAY (Modo Pruebas / Sandbox) ---
MERCHANT_ID = "masn8o1jtcm5vp1dyz9e"
PRIVATE_KEY = "sk_d75c8f4ed6914e6fa873716bb6b6a529"

def generar_enlace_pago(monto, descripcion, nombre_cliente, telefono_cliente):
    url = f"https://sandbox-api.openpay.mx/v1/{MERCHANT_ID}/checkouts"
    auth = (PRIVATE_KEY, "")
    
    # LIMPIEZA: Quitamos el "$" y cualquier caracter que no sea letra, número o espacio
    desc_limpia = re.sub(r'[^a-zA-Z0-9\s]', '', descripcion)
    nombre_limpio = re.sub(r'[^a-zA-Z0-9\s]', '', nombre_cliente)
    
    numero_orden = f"NOVUM-{telefono_cliente}-{int(time.time())}"
    
    payload = {
        "amount": float(monto),
        "description": desc_limpia, # Usamos la descripción sin símbolos
        "order_id": numero_orden,
        "currency": "MXN",
        "customer": {
            "name": nombre_limpio,
            "phone_number": telefono_cliente,
            "email": "cliente@novumpilates.com"
        },
        "send_email": False,
        "redirect_url": "https://fiskapp-hm70.onrender.com/"
    }
    
    try:
        response = requests.post(url, json=payload, auth=auth, verify=False)
        
        if response.status_code == 200:
            return response.json().get("checkout_link")
        else:
            print("❌ Error del banco:", response.text)
            return None
    except Exception as e:
        print("❌ Error de conexión con Openpay:", e)
        return None