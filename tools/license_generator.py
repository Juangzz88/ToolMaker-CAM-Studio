# -*- coding: utf-8 -*-
"""
Generador de Claves de Licencia por Código Vinculadas a HWID
ToolMaker CAM Studio
"""
import json
import base64
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

PRIVATE_KEY_PATH = "private_key.pem"

def load_private_key():
    with open(PRIVATE_KEY_PATH, "rb") as key_file:
        return serialization.load_pem_private_key(key_file.read(), password=None)

def generar_clave_licencia(cliente, hwid, dias_validez, modulos=None):
    if modulos is None:
        modulos = [1, 2, 3, 4, 5]

    fecha_exp = (datetime.now() + timedelta(days=dias_validez)).strftime("%Y-%m-%d")
    
    payload = {
        "client": cliente,
        "hwid": hwid,
        "exp": fecha_exp,
        "mods": modulos
    }
    
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    
    private_key = load_private_key()
    signature = private_key.sign(
        payload_json,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    token_data = {
        "p": payload,
        "s": base64.b64encode(signature).decode('utf-8')
    }
    
    token_bytes = json.dumps(token_data, separators=(',', ':')).encode('utf-8')
    license_key = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
    
    print("\n====================================================")
    print(" ✅ ¡CLAVE FIRMADA CON HWID GENERADA!")
    print("====================================================")
    print(f" Cliente:    {cliente}")
    print(f" HWID Equipo:{hwid}")
    print(f" Expiración: {fecha_exp} ({dias_validez} días)")
    print("----------------------------------------------------")
    print(" CÓDIGO DE ACTIVACIÓN:")
    print(f"\n {license_key}\n")
    print("====================================================\n")
    return license_key

if __name__ == "__main__":
    print("====================================================")
    print(" GENERADOR DE CÓDIGOS HWID - TOOLMAKER CAM STUDIO")
    print("====================================================")
    cli = input("Nombre del Cliente: ").strip() or "Usuario Prueba"
    hw = input("HWID del Equipo del Cliente: ").strip()
    dias = input("Días de activación (ej. 30): ").strip() or "30"
    
    if not hw:
        print("❌ Error: El HWID es obligatorio para vincular la clave al equipo.")
    else:
        generar_clave_licencia(cli, hw, int(dias))