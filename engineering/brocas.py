# -*- coding: utf-8 -*-
"""
Motor de Geometria y Estabilidad de Brocas (Modulo 3).
ToolMaker CAM Studio - Fase 2
"""
from typing import Dict, List, Any

def evaluar_estabilidad_broca(data: Dict[str, Any]) -> List[str]:
    """
    Evalua la esbeltez y estabilidad cinetica de la broca.
    """
    diagnostico = []
    if not data:
        return diagnostico
        
    longitud = float(data.get("longitud", 100.0) or 100.0)
    diametro = max(float(data.get("diametro", 10.0) or 10.0), 0.1)
    esbeltez = longitud / diametro
    
    if esbeltez > 30.0:
        diagnostico.append("⚠️ Alta relacion de esbeltez (L/D > 30). Requiere luneta o ciclo de taladrado profundo con picoteo.")
        
    return diagnostico

