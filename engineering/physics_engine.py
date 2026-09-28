import math
from validation.inputs import validar_entrada_rectificado, validar_entrada_geometria

MODULO_YOUNG_CARBURO = {
    '6': 630000.0,
    '8': 610000.0,
    '10': 590000.0,
    '12': 560000.0
}

K_FACTOR_EULER = 0.7

def ejecutar_motor_fisico_local(modulo, contexto):
    broca_data = contexto.get('broca', {})
    geom_data = contexto.get('geometria', {})
    operacion_data = contexto.get('operacion', {})

    alerta = False
    diagnostico = []

    # 1. Validar Envolvente Física en Rectificado
    if operacion_data:
        es_val, errs = validar_entrada_rectificado(operacion_data)
        if not es_val:
            alerta = True
            diagnostico.extend(errs)

    # 2. Validar Envolvente Física en Geometría
    if geom_data:
        es_val, errs = validar_entrada_geometria(geom_data)
        if not es_val:
            alerta = True
            diagnostico.extend(errs)

    # 3. Pandeo Crítico de Euler (Brocas)
    if 'broca' in str(modulo).lower() or broca_data:
        fz = float(broca_data.get('res_fz', broca_data.get('fz_calculado', 0)) or 0)
        d1 = float(broca_data.get('diametro_broca', 8.0) or 8.0)
        lc = float(broca_data.get('longitud_canal', 53.0) or 53.0)
        pct_dw = float(broca_data.get('pct_nucleo_broca', 28.0) or 28.0)
        co = str(broca_data.get('carburo_co', '10'))
        fajas = broca_data.get('tipo_fajas', '2_fajas')
        ld = lc / max(d1, 0.1)

        d_nucleo = d1 * (pct_dw / 100.0)
        e_carburo = MODULO_YOUNG_CARBURO.get(co, 590000.0)
        iz_nucleo = (math.pi * (d_nucleo ** 4)) / 64.0
        
        longitud_efectiva = K_FACTOR_EULER * lc
        p_cr = (math.pi ** 2 * e_carburo * iz_nucleo) / (longitud_efectiva ** 2)

        if fz >= p_cr * 0.8 and fz > 0:
            alerta = True
            diagnostico.append(f"⚠️ Empuje axial Fz ({fz:.0f} N) cercano a la Carga Crítica Equivalente ({p_cr:.0f} N, K={K_FACTOR_EULER}).")
        if ld >= 8.0 and fajas != '4_fajas':
            alerta = True
            diagnostico.append("⚠️ Regla de Diseño (L/D >= 8x): Se recomiendan 4 fajas guía para estabilidad.")

    if not diagnostico:
        diagnostico.append("✅ Parámetros nominales seguros en envolvente física.")

    return {
        "status": "ok",
        "provider": "Motor Físico Local",
        "alerta_critica": alerta,
        "diagnostico": "\n".join(diagnostico)
    }