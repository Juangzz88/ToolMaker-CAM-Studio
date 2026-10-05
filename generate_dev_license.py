"""
Generador de Licencia de Desarrollo Local para ToolMaker CAM Studio.
"""
import json
import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def generar_licencia_dev():
    private_key_path = "private_key.pem"
    lic_output_path = "toolmaker.lic"
    
    # 1. Tu HWID real detectado en Windows 11
    hwid_actual = "TM-4C4C-4544-0054"
    
    if not os.path.exists(private_key_path):
        print(f"❌ Error: No se encontró la clave privada '{private_key_path}' para firmar.")
        return

    # 2. Construir payload de la licencia
    payload_data = {
        "client": "Desarrollador Principal (Master Dev)",
        "hwid": hwid_actual,
        "expires": "PERPETUAL",
        "type": "DEVELOPMENT_FULL"
    }
    
    payload_str = json.dumps(payload_data, separators=(',', ':'))

    # 3. Cargar llave privada RSA
    with open(private_key_path, "rb") as f:
        private_key = load_pem_private_key(f.read(), password=None)

    # 4. Firmar el payload con RSA-PSS SHA-256
    signature = private_key.sign(
        payload_str.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    signature_b64 = base64.b64encode(signature).decode('utf-8')

    # 5. Guardar archivo toolmaker.lic
    license_file_content = {
        "payload": payload_str,
        "signature": signature_b64
    }

    with open(lic_output_path, "w", encoding="utf-8") as f:
        json.dump(license_file_content, f, indent=4)

    print("==========================================================")
    print(f"✅ Licencia regenerada con éxito para HWID: {hwid_actual}")
    print(f"📄 Archivo actualizado: {os.path.abspath(lic_output_path)}")
    print("==========================================================")

if __name__ == "__main__":
    generar_licencia_dev()