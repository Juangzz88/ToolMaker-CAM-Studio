"""
Motor de Geometría de Herramientas y Hélices.
ToolMaker CAM Studio - Fase 2
"""

import math
from typing import Dict, Any

def calculate_tool_geometry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula la geometría real de la herramienta sin datos hardcodeados.
    """
    diameter = float(payload.get('diametro', 10.0))
    helix_angle_deg = float(payload.get('angulo_helice', 30.0))
    num_flutes = int(payload.get('numero_labios', 4))
    core_ratio = float(payload.get('porcentaje_nucleo', 60.0)) / 100.0
    taper_angle_deg = float(payload.get('angulo_conicidad', 0.0))

    # 1. Cálculo del paso de hélice real: Pitch = (pi * D) / tan(beta)
    helix_rad = math.radians(helix_angle_deg)
    if helix_rad > 0:
        helix_pitch = (math.pi * diameter) / math.tan(helix_rad)
    else:
        helix_pitch = 0.0

    # 2. Ángulo de indizado entre labios: 360° / Z
    indexing_angle = 360.0 / num_flutes if num_flutes > 0 else 90.0

    # 3. Cálculo de diámetro de núcleo base y afectado por conicidad
    core_diameter_base = diameter * core_ratio
    taper_rad = math.radians(taper_angle_deg)
    core_diameter_tapered = core_diameter_base * (1.0 + math.sin(taper_rad))

    return {
        "diametro_nom": round(diameter, 3),
        "paso_helice_mm": round(helix_pitch, 2),
        "angulo_indizado_deg": round(indexing_angle, 2),
        "diametro_nucleo_base": round(core_diameter_base, 3),
        "diametro_nucleo_efectivo": round(core_diameter_tapered, 3),
        "numero_labios": num_flutes,
        "status": "success"
    }