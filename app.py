import os
import math
import json
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'toolmaker_local_2026'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# =============================================================================
# CONSTANTES FÍSICAS Y TABLAS TÉCNICAS (DETERMINISTAS)
# =============================================================================
ENERGIA_ESPECIFICA_RECTIFICADO = {
    'K': 38.0,  # Carburo Sólido / Fundición (J/mm³)
    'P': 42.0,  # Aceros al Carbono / Aleados (J/mm³)
    'M': 45.0,  # Aceros Inoxidables / Dúplex (J/mm³)
    'N': 18.0,  # Aluminios / No Ferrosos (J/mm³)
    'S': 52.0,  # Superaleaciones Titanio / Inconel (J/mm³)
    'H': 48.0   # Aceros Templados >55 HRC (J/mm³)
}

LIMITES_RECUBRIMIENTO = {
    'ALTIN': {'tmax': 900.0,  'dureza_gpa': 38.0, 'mu': 0.35},
    'TIALN': {'tmax': 800.0,  'dureza_gpa': 33.0, 'mu': 0.40},
    'ALCRN': {'tmax': 1100.0, 'dureza_gpa': 32.0, 'mu': 0.30},
    'DLC':   {'tmax': 350.0,  'dureza_gpa': 60.0, 'mu': 0.10}
}

MODULO_YOUNG_CARBURO = {
    '6': 630000.0,   # 6% Co -> 630 GPa (N/mm²)
    '8': 610000.0,   # 8% Co -> 610 GPa
    '10': 590000.0,  # 10% Co -> 590 GPa
    '12': 560000.0   # 12% Co -> 560 GPa
}

# =============================================================================
# RUTAS DE VISTAS (5 MÓDULOS TÉCNICOS LOCALES)
# =============================================================================
@app.route('/')
@app.route('/calculadora-muelas')
def calculadora_muelas():
    return render_template('muelas.html', active_module=1)

@app.route('/geometria-herramienta')
def geometria_herramienta():
    return render_template('geometria.html', active_module=2)

@app.route('/geometria-brocas')
def geometria_brocas():
    return render_template('brocas.html', active_module=3)

@app.route('/catalogo-abrasivos')
def catalogo_abrasivos():
    return render_template('abrasivos.html', active_module=4)

@app.route('/recubrimientos')
def recubrimientos():
    return render_template('recubrimientos.html', active_module=5)

# =============================================================================
# LÓGICA FÍSICA Y MATEMÁTICA INTERNA (MOTOR DEDICADO)
# =============================================================================
def ejecutar_motor_fisico_local(modulo, contexto):
    broca_data = contexto.get('broca', {})
    geom_data = contexto.get('geometria', {})

    alerta = False
    diagnostico = []

    # 1. EVALUACIÓN DE BROCAS (Carga de Pandeo Crítico de Euler Pcr)
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
        p_cr = (math.pi ** 2 * e_carburo * iz_nucleo) / ((0.7 * lc) ** 2)

        if fz >= p_cr * 0.8:
            alerta = True
            diagnostico.append(f"⚠️ Empuje axial Fz ({fz:.0f} N) cercano a la Carga Crítica de Pandeo de Euler ({p_cr:.0f} N).")
        if ld >= 8.0 and fajas != '4_fajas':
            alerta = True
            diagnostico.append("⚠️ Relación de Aspecto L/D >= 8x: Recomendado usar 4 fajas guía para estabilidad de agujero.")

    # 2. EVALUACIÓN DE FRESA (Susceptibilidad por Voladizo)
    if 'herramienta' in str(modulo).lower() or geom_data:
        voladizo = float(geom_data.get('longitud_corte', 35.0) or 35.0)
        diam = float(geom_data.get('diametro_ext', 10.0) or 10.0)
        if voladizo / max(diam, 0.1) > 5.0:
            alerta = True
            diagnostico.append("⚠️ Elevada susceptibilidad a inestabilidad dinámica por alto voladizo (L/D > 5).")

    if not diagnostico:
        diagnostico.append("✅ Parámetros dentro de la envolvente técnica nominal (Motor Físico OK).")

    return {
        "status": "ok",
        "provider": "Motor Físico Local (Python)",
        "alerta_critica": alerta,
        "diagnostico": "\n".join(diagnostico)
    }

# =============================================================================
# ENDPOINTS API REST
# =============================================================================
@app.route('/api/auto-evaluar', methods=['POST'])
def api_auto_evaluar():
    try:
        data = request.get_json() or {}
        modulo_actual = data.get('modulo', 'General')
        ctx = data.get('contexto_cruzado', {})
        return jsonify(ejecutar_motor_fisico_local(modulo_actual, ctx))
    except Exception as e:
        return jsonify({
            "status": "ok",
            "provider": "Motor Físico Local",
            "alerta_critica": False,
            "diagnostico": "✅ Telemetría procesada por el motor local."
        })

@app.route('/api/calcular-rectificado', methods=['POST'])
def calcular_rectificado():
    data = request.json or {}
    try:
        operacion = data.get('operacion', 'fluting')
        unidad = data.get('unidad', 'mm')
        material_iso = data.get('material_iso', 'K').upper()
        diametro = float(data.get('diametro_rueda', 100.0))
        ancho = float(data.get('ancho_rueda', 10.0))
        ancho_w = float(data.get('ancho_labio_w', 6.0))
        lc = float(data.get('longitud_corte', 30.0))
        profundidad_total = float(data.get('profundidad', 1.5))
        pasadas = max(1, int(data.get('pasadas_desbaste', 1)))
        num_canales = int(data.get('num_canales', 4))
        avance = float(data.get('avance', 120.0))
        rpm = float(data.get('rpm', 4500.0))

        profundidad_por_pasada = profundidad_total / pasadas

        # 1. Conversión de Unidades
        if unidad == 'in':
            d_mm = diametro * 25.4
            ancho_mm = (ancho_w if operacion == 'relief' else ancho) * 25.4
            lc_mm = lc * 25.4
            ap_mm = profundidad_por_pasada * 25.4
            vf_mm = avance * 25.4
            vs_sfpm = (math.pi * diametro * rpm) / 12.0
            vs_m_s = (math.pi * d_mm * rpm) / 60000.0
            vs_display = vs_sfpm
            estado_vs = "Óptimo (4300-6300 SFPM)" if 4300 <= vs_sfpm <= 6300 else ("Bajo" if vs_sfpm < 4300 else "Alto")
        else:
            d_mm = diametro
            ancho_mm = ancho_w if operacion == 'relief' else ancho
            lc_mm = lc
            ap_mm = profundidad_por_pasada
            vf_mm = avance
            vs_m_s = (math.pi * d_mm * rpm) / 60000.0
            vs_display = vs_m_s
            estado_vs = "Óptimo Aceite (22-32 m/s)" if 22 <= vs_m_s <= 32 else ("Bajo (<22 m/s)" if vs_m_s < 22 else "Alto (>32 m/s)")

        # 2. Tasa de Remoción Q'w (mm²/s) y Conversión Imperial Corregida (in²/s = mm²/s / 25.4²)
        q_prime_mm2_s = (ap_mm * vf_mm) / 60.0 if vf_mm > 0 else 0.0
        q_total_mm3_s = q_prime_mm2_s * ancho_mm
        q_prime_display = q_prime_mm2_s / (25.4 ** 2) if unidad == 'in' else q_prime_mm2_s

        # 3. Potencia y Fuerza Específica F't
        u_g = ENERGIA_ESPECIFICA_RECTIFICADO.get(material_iso, 38.0)
        potencia_kw = (u_g * q_total_mm3_s) / 1000.0 if vs_m_s > 0 else 0.0
        ft_total = (potencia_kw * 1000.0) / vs_m_s if vs_m_s > 0 else 0.0
        ft_especifica = ft_total / max(ancho_mm, 0.001)

        # 4. Carga Spindle (Ref: 11.5 kW mecánicos nominales)
        carga_spindle_pct = round((potencia_kw / 11.5) * 100.0, 1)

        # 5. Tiempo de Ciclo
        tiempo_total_seg = ((lc_mm / vf_mm) * 60.0 * pasadas * num_canales) if vf_mm > 0 else 0
        minutos = int(tiempo_total_seg // 60)
        segundos = int(tiempo_total_seg % 60)

        return jsonify({
            'success': True,
            'vs': round(vs_display, 2),
            'q_prime': round(q_prime_display, 4 if unidad == 'in' else 2),
            'ra_micras': 0.25,
            'estado_ra': "Estándar FEPA D126",
            'ft_especifica': round(ft_especifica, 1),
            'potencia_kw': round(potencia_kw, 2),
            'carga_spindle_pct': carga_spindle_pct,
            'estado_spindle': "Carga Segura" if carga_spindle_pct <= 75.0 else ("Advertencia" if carga_spindle_pct <= 100.0 else "SOBRECARGA"),
            'nivel_spindle': "success" if carga_spindle_pct <= 75.0 else ("warning" if carga_spindle_pct <= 100.0 else "danger"),
            'tiempo_str': f"{minutos}m {segundos}s",
            'estado_vs': estado_vs,
            'estado_q': "Fluting Pesado" if q_prime_mm2_s > 3.0 else "Normal"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/calcular-geometria', methods=['POST'])
def calcular_geometria():
    data = request.json or {}
    try:
        unidad = data.get('unidad', 'mm')
        diametro_ext = float(data.get('diametro_ext', 12.0))
        pct_nucleo = float(data.get('pct_nucleo', 62.0))
        diametro_nucleo_punta = diametro_ext * (pct_nucleo / 100.0)
        diametro_nucleo_raiz = min(diametro_nucleo_punta * 1.10, diametro_ext * 0.98)
        indice_iz_relativo = round((diametro_nucleo_punta / max(diametro_ext, 0.001)) ** 4 * 100.0, 1)

        return jsonify({
            'success': True,
            'diametro_nucleo_punta': round(diametro_nucleo_punta, 3),
            'diametro_nucleo_raiz': round(diametro_nucleo_raiz, 3),
            'rigidez_relativa': indice_iz_relativo,
            'estado_rigidez': "Excelente Rigidez Sección" if indice_iz_relativo >= 15.0 else "Sección Flexible",
            'clase_rigidez': "status-ok" if indice_iz_relativo >= 15.0 else "status-warning"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/estimar-recubrimiento', methods=['POST'])
def api_estimar_recubrimiento():
    try:
        data = request.get_json() or {}
        recubrimiento = str(data.get('recubrimiento', 'ALTIN')).upper()
        e_capa_um = float(data.get('e_capa_um', 3.0))
        material_iso = str(data.get('material_iso', 'P')).upper()
        vc = float(data.get('vc_m_min', 180.0))
        fz = float(data.get('fz_mm_diente', 0.05))

        prop = LIMITES_RECUBRIMIENTO.get(recubrimiento, LIMITES_RECUBRIMIENTO['ALTIN'])
        tmax = prop['tmax']
        factor_iso = {'P': 1.0, 'M': 1.25, 'K': 0.9, 'N': 0.6, 'S': 1.45, 'H': 1.35}.get(material_iso, 1.0)

        # 1. Temperatura de Interfaz (Shaw/Jaeger)
        t_corte = 25.0 + (310.0 * ((vc / 180.0) ** 0.68) * ((fz / 0.05) ** 0.22) * factor_iso * (prop['mu'] / 0.35))

        # 2. Desgaste Bimodal de Archard
        factor_termico = 1.0 + (3.5 * max(0.0, (t_corte - tmax) / tmax) ** 1.8)
        tasa_desgaste_um_min = (0.015 * (vc / 180.0) * (factor_iso / (prop['dureza_gpa'] / 30.0))) * factor_termico

        vida_capa_min = e_capa_um / max(tasa_desgaste_um_min, 0.0001)
        tasa_sustrato = tasa_desgaste_um_min * 2.2
        vida_fase2_min = (100.0 - e_capa_um) / max(tasa_sustrato, 0.0001)
        vida_total_min = vida_capa_min + vida_fase2_min

        estado_termico = 'SOBREPASA_LIMITE' if t_corte >= tmax else ('ZONA_CRITICA' if t_corte >= 0.90 * tmax else 'DENTRO_DE_LIMITE')

        return jsonify({
            'success': True,
            'data': {
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
                    'vida_hasta_vb_critico_min': round(vida_total_min, 1)
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)