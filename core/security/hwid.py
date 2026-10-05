"""
Módulo de Generación de Hardware ID (HWID).
ToolMaker CAM Studio — Compatible con Windows 11 (PowerShell/CIM) y Linux/macOS.
"""

import platform
import subprocess
import uuid

def generate_hwid() -> str:
    """
    Genera un HWID único para la máquina del cliente.
    Evita la dependencia de 'wmic' (obsoleto en Windows 11) mediante PowerShell / Get-CimInstance.
    """
    system = platform.system()

    if system == "Windows":
        try:
            cmd = "powershell -Command \"(Get-CimInstance -ClassName Win32_ComputerSystemProduct).UUID\""
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
            if output and len(output) >= 8:
                clean_uuid = output.replace("-", "").upper()
                return f"TM-{clean_uuid[:4]}-{clean_uuid[4:8]}-{clean_uuid[8:12]}"
        except Exception:
            pass

    node_id = str(uuid.getnode())
    if len(node_id) < 12:
        node_id = node_id.zfill(12)
    
    return f"TM-{node_id[:4]}-{node_id[4:8]}-{node_id[8:12]}".upper()

if __name__ == "__main__":
    print(f"HWID Detectado: {generate_hwid()}")