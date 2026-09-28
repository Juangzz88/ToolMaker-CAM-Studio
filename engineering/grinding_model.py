"""
Módulo de Ingeniería: Modelo Físico de Rectificado e Interacción con Muelas (FEPA).

Este módulo procesa las variables operativas de entrada para calcular
las características cinemáticas, mecánicas y térmicas de la operación.
"""

def calcular_parametros_rectificado(datos: dict) -> dict:
    """
    Calcula los parámetros cinemáticos y de potencia para el proceso de rectificado.
    
    Parámetros recibidos en el diccionario 'datos':
      - diametro_rueda (float): Diámetro de la muela en mm.
      - rpm (float): Velocidad de rotación en revoluciones por minuto.
      - profundidad (float): Profundidad de corte (a_e) en mm.
      - avance (float): Velocidad de avance de la pieza (v_w) en mm/min.
      - ancho_rueda (float): Ancho de contacto o labio (b) en mm.
      - material_iso (str): Categoría ISO del material ('K', 'P', 'M', 'N', 'S', 'H').
      
    Retorna:
      - dict: Resultados de velocidad periférica (Vs), caudal específico (Q'w),
              potencia (kW), fuerza tangencial (Ft) y tiempos de proceso.
    """
    # 1. Extracción y conversión de datos de entrada
    ds = float(datos.get('diametro_rueda', 200.0) or 200.0)
    rpm = float(datos.get('rpm', 3000.0) or 3000.0)
    ae = float(datos.get('profundidad', 0.02) or 0.02)
    vw_mm_min = float(datos.get('avance', 500.0) or 500.0)
    b = float(datos.get('ancho_rueda', 10.0) or 10.0)
    material_iso = str(datos.get('material_iso', 'K')).upper()

    # Conversión de velocidad de avance a mm/segundo
    vw_mm_s = vw_mm_min / 60.0

    # 2. Velocidad periférica de la rueda Vs (m/s)
    # Fórmula: Vs = (pi * d_s * RPM) / (60 * 1000)
    import math
    vs_m_s = (math.pi * ds * rpm) / 60000.0

    # 3. Tasa específica de remoción de material Q'w (mm³/mm·s)
    # Fórmula: Q'w = (a_e * v_w) / 60
    q_prime_mm2_s = ae * vw_mm_s

    # 4. Caudal volumétrico total Q_total (mm³/s)
    q_total_mm3_s = q_prime_mm2_s * b

    # 5. Energía específica de rectificado u_g (J/mm³) según ISO
    # Valores de referencia de literatura técnica (Malkin & Guo / Klocke)
    energia_especifica = {
        'K': 38.0,  # Carburo Sólido / Fundición
        'P': 42.0,  # Aceros al Carbono
        'M': 45.0,  # Aceros Inoxidables
        'N': 18.0,  # Aluminios
        'S': 52.0,  # Superaleaciones Titanio/Inconel
        'H': 48.0   # Aceros Templados >55 HRC
    }
    u_g = energia_especifica.get(material_iso, 38.0)

    # 6. Cálculo de Potencia (kW) y Fuerza Específica Tangencial Ft' (N/mm)
    # Potencia Pc = (u_g * Q_total) / 1000
    potencia_kw = (u_g * q_total_mm3_s) / 1000.0 if vs_m_s > 0 else 0.0
    
    # Fuerza tangencial total Ft = (Pc * 1000) / Vs
    ft_total = (potencia_kw * 1000.0) / vs_m_s if vs_m_s > 0 else 0.0
    ft_especifica = ft_total / max(b, 0.001)

    # 7. Diagnósticos y estados operativos
    if vs_m_s < 18.0:
        estado_vs = "Bajo (Riesgo de desgaste prematuro de muela)"
    elif vs_m_s > 45.0:
        estado_vs = "Alto (Riesgo de quemado térmico / Daño superficial)"
    else:
        estado_vs = "Nominal (Rango Óptimo de Rectificado)"

    return {
        'success': True,
        'vs': round(vs_m_s, 2),
        'q_prime': round(q_prime_mm2_s, 2),
        'potencia_kw': round(potencia_kw, 2),
        'ft_especifica': round(ft_especifica, 1),
        'estado_vs': estado_vs,
        'estado_q': "Fluting Pesado" if q_prime_mm2_s > 3.0 else "Envolvente Normal"
    }