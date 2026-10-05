import base64
import json
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

def generate_key_pair():
    """Genera un nuevo par de llaves RSA de 2048 bits para ti."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    with open("private_key.pem", "wb") as f:
        f.write(private_pem)
    with open("public_key.pem", "wb") as f:
        f.write(public_pem)
        
    print("🔑 Par de llaves RSA generado exitosamente (private_key.pem / public_key.pem).")

def issue_license(client_name: str, hwid: str, exp_date_str: str, private_key_path: str = "private_key.pem"):
    """
    Emite un archivo toolmaker.lic firmado digitalmente.
    exp_date_str format: 'YYYY-MM-DD' o 'PERPETUAL'
    """
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    payload = {
        "client": client_name,
        "hwid": hwid,
        "issued_at": datetime.now().strftime("%Y-%m-%d"),
        "expires": exp_date_str
    }
    
    payload_str = json.dumps(payload, sort_keys=True)
    
    # Firmar el payload con la Clave Privada
    signature = private_key.sign(
        payload_str.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    license_file_content = {
        "payload": payload_str,
        "signature": base64.b64encode(signature).decode('utf-8')
    }
    
    output_filename = f"toolmaker_{client_name.lower().replace(' ', '_')}.lic"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(license_file_content, f, indent=4)
        
    print(f"✅ Licencia emitida con éxito: {output_filename}")

# Ejemplo de Uso:
if __name__ == "__main__":
    # 1. Descomentar si no tienes llaves generadas
    # generate_key_pair()
    
    # 2. Emitir licencia para un cliente
    # issue_license("Taller CNC Precision", "TM-A8F3-91B2-C4E7", "2027-12-31")
    pass