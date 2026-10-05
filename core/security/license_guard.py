import base64
import json
import os
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from core.security.hwid import generate_hwid

class LicenseValidationError(Exception):
    pass

def cargar_clave_publica(public_key_path: str = "public_key.pem") -> bytes:
    """Carga la clave pública directamente desde el archivo PEM en disco."""
    if not os.path.exists(public_key_path):
        raise LicenseValidationError(f"No se encontró el archivo de clave pública ('{public_key_path}').")
    
    with open(public_key_path, "rb") as f:
        return f.read().strip()

def verify_license(license_path: str = "toolmaker.lic") -> dict:
    """
    Verifica la autenticidad, vigencia y correspondencia de hardware de la licencia.
    """
    if not os.path.exists(license_path):
        raise LicenseValidationError("No se encontró el archivo de licencia ('toolmaker.lic').")

    try:
        with open(license_path, "r", encoding="utf-8") as f:
            lic_data = json.load(f)
            
        payload_str = lic_data.get("payload")
        signature_b64 = lic_data.get("signature")
        
        if not payload_str or not signature_b64:
            raise LicenseValidationError("Estructura de licencia corrupta.")

        # 1. Cargar y Validar la Firma Criptográfica RSA desde el archivo PEM
        public_key_bytes = cargar_clave_publica("public_key.pem")
        public_key = load_pem_public_key(public_key_bytes)
        signature = base64.b64decode(signature_b64)
        
        public_key.verify(
            signature,
            payload_str.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # 2. Decodificar Payload de la licencia
        payload = json.loads(payload_str)
        cliente_hwid = payload.get("hwid")
        exp_date_str = payload.get("expires")
        
        # 3. Validar HWID
        current_hwid = generate_hwid()
        if cliente_hwid != current_hwid:
            raise LicenseValidationError(f"Licencia no autorizada para este equipo (HWID detectado: {current_hwid}).")
            
        # 4. Validar Fecha de Expiración
        if exp_date_str != "PERPETUAL":
            exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d")
            if datetime.now() > exp_date:
                raise LicenseValidationError(f"La licencia expiró el {exp_date_str}.")

        return payload

    except LicenseValidationError as e:
        raise e
    except Exception as e:
        raise LicenseValidationError(f"Fallo en la validación criptográfica: {str(e)}")