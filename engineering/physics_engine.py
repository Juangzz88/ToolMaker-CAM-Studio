# -*- coding: utf-8 -*-
"""
Motor Fisico Determinista - Mecanica de Rectificado, Fuerzas y Dinamica.
ToolMaker CAM Studio - Fase 2
"""

import math
from typing import Dict, Any

def calcular_parametros_rectificado(payload: Dict[str, Any]) -> Dict[str, Any]:
    diametro_mm = float(payload.get("diametro_rueda", 125.0))
    rpm = float(payload.get("rpm", 4500.0))
    profundidad_ae_mm = float(payload.get("profundidad_pasada", 0.02))
    avance_vf_mm_min = float(payload.get("avance_mesa", 500.0))
    ancho_b_mm = float(payload.get("ancho_rueda", 10.0))
    
    vc_m_s = (math.pi * diametro_mm * rpm) / 60000.0
    q_prime_w = (profundidad_ae_mm * avance_vf_mm_min) / 60.0
    ft_prime = 1.5 * (q_prime_w ** 0.6) if q_prime_w > 0 else 0.0
    potencia_kw = (ft_prime * ancho_b_mm * vc_m_s) / 1000.0
    
    return {
        "velocidad_corte_vc": round(vc_m_s, 2),
        "tasa_remocion_qw": round(q_prime_w, 3),
        "fuerza_tangencial_ft_prime": round(ft_prime, 2),
        "potencia_estimada_kw": round(potencia_kw, 2),
        "status": "success"
    }

def calculate_drill_forces(diameter: float, feed_mm_rev: float, vc_m_min: float, iso_code: str = "P") -> Dict[str, Any]:
    from engineering.material_data import get_material_by_iso
    mat = get_material_by_iso(iso_code)
    kc1_1 = mat["kc1_1"]
    mc = mat["mc"]
    
    h = feed_mm_rev / 2.0
    kc = kc1_1 * (h ** -mc) if h > 0 else kc1_1
    fc = kc * (diameter / 2.0) * h
    mc_nm = (fc * (diameter / 4.0)) / 1000.0
    fz_n = fc * 1.2
    
    return {
        "fuerza_axial_fz_n": round(fz_n, 1),
        "torque_mc_nm": round(mc_nm, 2),
        "fuerza_especifica_kc": round(kc, 1)
    }
