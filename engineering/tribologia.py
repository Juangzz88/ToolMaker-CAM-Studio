# -*- coding: utf-8 -*-
"""
Motor Tribológico de Recubrimientos PVD/CVD (Módulo 5).
Estructura JSON alineada estrictamente con el Frontend original de ToolMaker CAM Studio.
"""
import math
from typing import Dict, Any

COATING_DATABASE = {
    "ALTIN": {"tmax_c": 900.0, "friction_coeff": 0.30, "hardness_gpa": 38.0},
    "TIALN": {"tmax_c": 800.0, "friction_coeff": 0.35, "hardness_gpa": 33.0},
    "ALCRN": {"tmax_c": 1100.0, "friction_coeff": 0.32, "hardness_gpa": 32.0},
    "DLC":   {"tmax_c": 350.0, "friction_coeff": 0.10, "hardness_gpa": 60.0},
    "UNCOATED": {"tmax_c": 500.0, "friction_coeff": 0.60, "hardness_gpa": 18.0}
}

def estimar_desgaste_recubrimiento(payload: Dict[str, Any]) -> Dict[str, Any]:
    rec_key = str(payload.get("recubrimiento", "ALTIN")).upper()
    props = COATING_DATABASE.get(rec_key, COATING_DATABASE["ALTIN"])

    e_capa_um = float(payload.get("e_capa_um", payload.get("espesor", 3.0)) or 3.0)
    material_iso = str(payload.get("material_iso", "P")).upper()
    vc_m_min = float(payload.get("vc_m_min", payload.get("vc", 180.0)) or 180.0)
    fz_mm_diente = float(payload.get("fz_mm_diente", payload.get("fz", 0.05)) or 0.05)

    iso_factors = {"P": 1.0, "M": 1.25, "K": 0.85, "N": 0.5, "S": 1.4, "H": 1.6}
    k_iso = iso_factors.get(material_iso[0] if material_iso else "P", 1.0)

    # 1. Cálculo Térmico
    tmax_c = props["tmax_c"]
    temp_base = 25.0 + (0.85 * vc_m_min * math.sqrt(fz_mm_diente * 100.0) * props["friction_coeff"] * k_iso)
    t_corte_c = round(min(temp_base, 1400.0), 1)

    estado_temp = "NOMINAL"
    if t_corte_c > tmax_c:
        estado_temp = "SOBREPASA_LIMITE"

    # 2. Tasa de Desgaste
    tasa_um_min = round(0.015 * (vc_m_min / 100.0)**1.8 * props["friction_coeff"] * k_iso, 3)
    if tasa_um_min <= 0:
        tasa_um_min = 0.001

    # 3. Vida Bimodal
    vida_capa_min = round(e_capa_um / tasa_um_min, 1)
    vida_fase2_min = round(vida_capa_min * 2.2 / k_iso, 1)
    vida_hasta_vb_critico_min = round(vida_capa_min + vida_fase2_min, 1)

    # ESTRUCTURA ANIDADA EXACTA QUE EXIGE EL JS
    return {
        "temperatura": {
            "t_corte_c": t_corte_c,
            "tmax_recubrimiento_c": tmax_c,
            "estado": estado_temp
        },
        "desgaste": {
            "tasa_um_min": tasa_um_min
        },
        "vida": {
            "vida_capa_min": vida_capa_min,
            "vida_hasta_vb_critico_min": vida_hasta_vb_critico_min,
            "criterio_vb_um": 0.10
        }
    }
