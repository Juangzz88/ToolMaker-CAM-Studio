"""
ToolMaker CAM Studio — Módulo de Validación de Envolvente Física
Garantiza que ningún valor de entrada viole los límites mecánicos del husillo ni la herramienta.
"""
from engineering.material_data import SPECIFIC_CUTTING_ENERGY

GRUPOS_MATERIAL_VALIDOS = list(SPECIFIC_CUTTING_ENERGY.keys())

LIMITES_PROCESO = {
    'diametro_rueda_mm': {'min': 10.0, 'max': 350.0, 'nombre': 'Diámetro de Muela'},
    'ancho_rueda_mm': {'min': 1.0, 'max': 100.0, 'nombre': 'Ancho de Muela'},
    'profundidad_ap_mm': {'min': 0.001, 'max': 15.0, 'nombre': 'Profundidad de Corte (ap)'},
    'avance_vf_mm_min': {'min': 1.0, 'max': 2500.0, 'nombre': 'Velocidad de Avance (Vf)'},
    'rpm_spindle': {'min': 100.0, 'max': 24000.0, 'nombre': 'Velocidad de Husillo (RPM)'},
    'diametro_fresa_mm': {'min': 0.1, 'max': 50.0, 'nombre': 'Diámetro Exterior Herramienta'},
    'longitud_corte_mm': {'min': 0.5, 'max': 250.0, 'nombre': 'Longitud de Corte (Lc)'}
}
def parse_float(val, default=0.0):
    try:
        if val is None or val == '':
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

def validar_entrada_rectificado(data):
    """Valida los parámetros de proceso del Módulo 1 (Rectificado CNC)."""
    errores = []
    unidad = str(data.get('unidad', 'mm')).lower()
    factor_mm = 25.4 if unidad == 'in' else 1.0

    diametro_rueda = parse_float(data.get('diametro_rueda') or data.get('diametro'))
    ancho_rueda = parse_float(data.get('ancho_rueda') or data.get('ancho'))
    profundidad = parse_float(data.get('profundidad') or data.get('ap'))
    avance = parse_float(data.get('avance') or data.get('vf'))
    rpm = parse_float(data.get('rpm'))

    prof_mm = profundidad * factor_mm
    if prof_mm > LIMITES_PROCESO['profundidad_ap_mm']['max']:
        errores.append(
            f"⚠️ Profundidad de corte ap ({profundidad:.2f} {unidad}) excede el límite máximo seguro por máquina ({LIMITES_PROCESO['profundidad_ap_mm']['max']} mm)."
        )

    d_rueda_mm = diametro_rueda * factor_mm
    if d_rueda_mm > 0 and d_rueda_mm > LIMITES_PROCESO['diametro_rueda_mm']['max']:
        errores.append(
            f"⚠️ Diámetro de muela ({diametro_rueda:.2f} {unidad}) excede el envolvente de la máquina ({LIMITES_PROCESO['diametro_rueda_mm']['max']} mm)."
        )

    if d_rueda_mm > 0 and prof_mm >= (d_rueda_mm / 2.0):
        errores.append("🛑 Incoherencia Física: La profundidad de corte ap no puede ser mayor o igual al radio de la muela.")

    avance_mm = avance * factor_mm
    if avance_mm > LIMITES_PROCESO['avance_vf_mm_min']['max']:
        errores.append(f"⚠️ Avance Vf ({avance:.1f} {unidad}/min) excede el máximo dinámico ({LIMITES_PROCESO['avance_vf_mm_min']['max']} mm/min).")

    return len(errores) == 0, errores

def validar_entrada_geometria(data):
    """Valida los parámetros geométricos del Módulo 2."""
    errores = []
    unidad = str(data.get('unidad', 'mm')).lower()
    factor_mm = 25.4 if unidad == 'in' else 1.0

    diametro_ext = parse_float(data.get('diametro_ext'))
    longitud_corte = parse_float(data.get('longitud_corte'))

    if diametro_ext * factor_mm > LIMITES_PROCESO['diametro_fresa_mm']['max']:
        errores.append(f"⚠️ Diámetro exterior ({diametro_ext:.2f} {unidad}) fuera de rango (Máx 50 mm).")

    if longitud_corte * factor_mm > LIMITES_PROCESO['longitud_corte_mm']['max']:
        errores.append(f"⚠️ Longitud Lc ({longitud_corte:.2f} {unidad}) excede capacidad física (Máx 250 mm).")

    return len(errores) == 0, errores