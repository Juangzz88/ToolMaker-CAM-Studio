LIMITES_RECUBRIMIENTO = {
    'ALTIN': {'tmax': 900.0,  'dureza_gpa': 38.0, 'mu': 0.35, 'c_termico': 310.0, 'exp_vc': 0.68, 'exp_fz': 0.22},
    'TIALN': {'tmax': 800.0,  'dureza_gpa': 33.0, 'mu': 0.40, 'c_termico': 325.0, 'exp_vc': 0.70, 'exp_fz': 0.20},
    'ALCRN': {'tmax': 1100.0, 'dureza_gpa': 32.0, 'mu': 0.30, 'c_termico': 290.0, 'exp_vc': 0.65, 'exp_fz': 0.24},
    'DLC':   {'tmax': 350.0,  'dureza_gpa': 60.0, 'mu': 0.10, 'c_termico': 180.0, 'exp_vc': 0.50, 'exp_fz': 0.15}
}

VB_CRITICO_UM = 100.0  # Criterio estándar de fallo por desgaste de flanco en sustrato (100 µm)

def estimar_recubrimiento_pvd(data):
    """
    Modelo Paramétrico Calibrado de Temperatura de Interface y Desgaste Bimodal.
    Basado en normalización empírica de Jaeger/Shaw y Ley de Desgaste de Archard.
    """
    recubrimiento = str(data.get('recubrimiento', 'ALTIN')).upper()
    e_capa_um = float(data.get('e_capa_um', 3.0))
    material_iso = str(data.get('material_iso', 'P')).upper()
    vc = float(data.get('vc_m_min', 180.0))
    fz = float(data.get('fz_mm_diente', 0.05))

    prop = LIMITES_RECUBRIMIENTO.get(recubrimiento, LIMITES_RECUBRIMIENTO['ALTIN'])
    tmax = prop['tmax']
    factor_iso = {'P': 1.0, 'M': 1.25, 'K': 0.9, 'N': 0.6, 'S': 1.45, 'H': 1.35}.get(material_iso, 1.0)

    # 1. Estimación Paramétrica Térmica (Jaeger/Shaw Normalizado)
    t_corte = 25.0 + (prop['c_termico'] * ((vc / 180.0) ** prop['exp_vc']) * ((fz / 0.05) ** prop['exp_fz']) * factor_iso * (prop['mu'] / 0.35))

    # 2. Desgaste Bimodal de Archard
    factor_termico = 1.0 + (3.5 * max(0.0, (t_corte - tmax) / tmax) ** 1.8)
    tasa_desgaste_um_min = (0.015 * (vc / 180.0) * (factor_iso / (prop['dureza_gpa'] / 30.0))) * factor_termico

    # Fase 1: Vida de la Capa PVD
    vida_capa_min = e_capa_um / max(tasa_desgaste_um_min, 0.0001)
    
    # Fase 2: Desgaste del Sustrato de Carburo hasta el Criterio VB Crítico
    tasa_sustrato = tasa_desgaste_um_min * 2.2
    espesor_desgaste_sustrato = max(0.0, VB_CRITICO_UM - e_capa_um)
    vida_fase2_min = espesor_desgaste_sustrato / max(tasa_sustrato, 0.0001)
    vida_total_min = vida_capa_min + vida_fase2_min

    estado_termico = 'SOBREPASA_LIMITE' if t_corte >= tmax else ('ZONA_CRITICA' if t_corte >= 0.90 * tmax else 'DENTRO_DE_LIMITE')

    return {
        'success': True,
        'data': {
            'modelo_info': "Modelo Paramétrico Calibrado (Jaeger/Shaw + Archard)",
            'temperatura': {
                't_corte_c': round(t_corte, 1),
                'tmax_recubrimiento_c': tmax,
                'estado': estado_termico
            },
            'desgaste': {
                'tasa_um_min': round(tasa_desgaste_um_min, 4)
            },
            'vida': {
                'vida_capa_min': round(vida_capa_min, 1),
                'vida_hasta_vb_critico_min': round(vida_total_min, 1),
                'criterio_vb_um': VB_CRITICO_UM
            }
        }
    }