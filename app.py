from flask import Flask, render_template, request, jsonify
import math

app = Flask(__name__)
app.config['SECRET_KEY'] = 'toolmaker_secret_2026'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/')
def index():
    return render_template('muelas.html', active_module=1)

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

@app.route('/api/calcular-rectificado', methods=['POST'])
def calcular_rectificado():
    data = request.json or {}
    try:
        operacion = data.get('operacion', 'fluting')
        unidad = data.get('unidad', 'mm')
        material_iso = data.get('material_iso', 'K')
        carburo_co = data.get('carburo_co', '10') # % Cobalto
        aglomerante = data.get('aglomerante', 'hibrido')
        grano_fepa = data.get('grano_fepa', 'D126')
        
        diametro = float(data.get('diametro_rueda', 100))
        ancho = float(data.get('ancho_rueda', 10))
        ancho_w = float(data.get('ancho_labio_w', 6.0))
        lc = float(data.get('longitud_corte', 30))
        profundidad_total = float(data.get('profundidad', 1.5))
        pasadas = int(data.get('pasadas_desbaste', 1))
        num_canales = int(data.get('num_canales', 4))
        avance = float(data.get('avance', 120))
        rpm = float(data.get('rpm', 4500))

        if pasadas <= 0 or operacion != 'fluting': 
            pasadas = 1
            
        profundidad_por_pasada = profundidad_total / pasadas

        if unidad == 'in':
            d_mm = diametro * 25.4
            ancho_mm = (ancho_w if operacion == 'relief' else ancho) * 25.4
            lc_mm = lc * 25.4
            ap_mm = profundidad_por_pasada * 25.4
            vf_mm = avance * 25.4

            vs = (math.pi * diametro * rpm) / 12.0
            vs_m_s = (math.pi * d_mm * rpm) / 60000.0
            q_prime = profundidad_por_pasada * avance
            q_prime_mm = (ap_mm * vf_mm) / 60.0 if vf_mm > 0 else 0.0
            
            estado_vs = "Óptimo (4300-6300 SFPM)" if 4300 <= vs <= 6300 else ("Bajo" if vs < 4300 else "Alto (Riesgo daño)")
        else:
            d_mm = diametro
            ancho_mm = ancho_w if operacion == 'relief' else ancho
            lc_mm = lc
            ap_mm = profundidad_por_pasada
            vf_mm = avance

            vs = (math.pi * diametro * rpm) / 60000.0
            vs_m_s = vs
            q_prime = (profundidad_por_pasada * avance) / 60.0 if avance > 0 else 0.0
            q_prime_mm = q_prime

            # Rango seguro de Vs para rectificado de Carburo
            if 22 <= vs <= 32:
                estado_vs = "Óptimo Aceite (22-32 m/s)"
            elif vs < 22:
                estado_vs = "Bajo (<22 m/s)"
            else:
                estado_vs = "Alto (Riesgo térmico >32 m/s)"

        if operacion == 'fluting':
            if q_prime_mm > 5.0 and aglomerante == 'resina':
                estado_q = "Advertencia: Requiere Aglomerante Híbrido"
            else:
                estado_q = "Fluting Normal (<3.0)" if q_prime_mm < 3.0 else "Fluting Pesado Óptimo"
        elif operacion == 'gashing':
            estado_q = "Gashing Estándar" if q_prime_mm <= 4.0 else "Gashing Alto"
        else:
            estado_q = "Relief Ligero (Excelente acabado)" if q_prime_mm <= 1.5 else "Relief Alto"

        # Factores de rugosidad por tipo de grano FEPA
        factores_grano = {'D181': 0.80, 'D126': 0.40, 'D91': 0.25, 'D64': 0.12, 'D46': 0.06}
        ra_base = factores_grano.get(grano_fepa, 0.25)
        ra_micras = round(ra_base * (1 + (vf_mm / 1000.0)), 2)
        estado_ra = "Excelente (Pulido Espejo)" if ra_micras < 0.2 else ("Estándar Industrial" if ra_micras <= 0.4 else "Desbaste Rápido")

        # Fuerza de corte específica para rectificado de Carburo según su % de Cobalto
        kc_map = {'6': 46.0, '8': 43.0, '10': 40.0, '12': 37.0}
        ue = kc_map.get(str(carburo_co), 40.0)
        
        ft_especifica = ue * q_prime_mm
        ft_total = ft_especifica * ancho_mm

        potencia_kw = (ft_total * vs_m_s) / 1000.0
        spindle_nominal = 11.5
        carga_spindle_pct = min(round((potencia_kw / spindle_nominal) * 100.0, 1), 150.0)

        if carga_spindle_pct <= 75.0:
            estado_spindle = "Carga Segura (Husillo OK)"
            nivel_spindle = "success"
        elif carga_spindle_pct <= 95.0:
            estado_spindle = "Advertencia: Alta Carga"
            nivel_spindle = "warning"
        else:
            estado_spindle = "CRÍTICO: SOBRECARGA SPINDLE"
            nivel_spindle = "danger"

        if operacion == 'fluting':
            tiempo_por_pasada_seg = ((lc_mm / vf_mm) * 60.0) + 2.5 if vf_mm > 0 else 0
            tiempo_total_seg = tiempo_por_pasada_seg * pasadas * num_canales
        elif operacion == 'gashing':
            tiempo_total_seg = (3.5 * num_canales) + ((ap_mm / vf_mm) * 60.0 * num_canales) if vf_mm > 0 else 0
        else:
            tiempo_total_seg = (((lc_mm / vf_mm) * 60.0) + 2.0) * num_canales if vf_mm > 0 else 0

        minutos = int(tiempo_total_seg // 60)
        segundos = int(tiempo_total_seg % 60)
        tiempo_str = f"{minutos}m {segundos}s"

        return jsonify({
            'success': True,
            'vs': round(vs, 2),
            'q_prime': round(q_prime, 3 if unidad == 'in' else 2),
            'ra_micras': ra_micras,
            'estado_ra': estado_ra,
            'ft_especifica': round(ft_especifica, 1),
            'potencia_kw': round(potencia_kw, 2),
            'carga_spindle_pct': carga_spindle_pct,
            'estado_spindle': estado_spindle,
            'nivel_spindle': nivel_spindle,
            'tiempo_str': tiempo_str,
            'estado_vs': estado_vs,
            'estado_q': estado_q
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/calcular-geometria', methods=['POST'])
def calcular_geometria():
    data = request.json or {}
    try:
        unidad = data.get('unidad', 'mm')
        tipo_herramienta = data.get('tipo_herramienta', 'plana')
        diametro_ext = float(data.get('diametro_ext', 12.0))
        diametro_d2 = float(data.get('diametro_d2', 16.0))
        num_canales = int(data.get('num_canales', 4))
        tipo_helice = data.get('tipo_helice', 'estandar')
        
        helice_a = float(data.get('helice_a', 35.0))
        helice_b = float(data.get('helice_b', 38.0))
        delta_index = float(data.get('delta_index', 2.0))
        
        pct_nucleo = float(data.get('pct_nucleo', 62.0))
        longitud_corte = float(data.get('longitud_corte', 30.0))
        core_taper_deg = float(data.get('core_taper_deg', 0.5))
        angulo_conicidad = float(data.get('angulo_conicidad', 5.0))

        tipo_esquina = data.get('tipo_esquina', 'radio')
        val_esquina = float(data.get('val_esquina', 0.5))
        dish_angle = float(data.get('dish_angle', 2.0))
        rake_radial = float(data.get('rake_radial', 12.0))

        if tipo_herramienta == 'esferica':
            radio_punta = diametro_ext / 2.0
            str_esquina = f"Esférica Completa (R{round(radio_punta, 3)})"
            diametro_nucleo_punta = diametro_ext * (pct_nucleo / 100.0) * 0.75 
        elif tipo_herramienta == 'toroidal':
            str_esquina = f"Toroidal R{round(val_esquina, 3)}"
            diametro_nucleo_punta = diametro_ext * (pct_nucleo / 100.0)
        elif tipo_herramienta == 'conica':
            str_esquina = f"Cónica {round(angulo_conicidad,1)}°/lado (D2 Raíz: {round(diametro_d2, 2)})"
            diametro_nucleo_punta = diametro_ext * (pct_nucleo / 100.0)
        else:
            if tipo_esquina == 'chaflan':
                str_esquina = f"Chaflán {round(val_esquina, 3)} x 45°"
            else:
                str_esquina = f"Plana Radio R{round(val_esquina, 3)}"
            diametro_nucleo_punta = diametro_ext * (pct_nucleo / 100.0)

        inc_taper = 2.0 * (longitud_corte * math.sin(math.radians(angulo_conicidad if tipo_herramienta == 'conica' else core_taper_deg)))
        diametro_nucleo_raiz = diametro_nucleo_punta + inc_taper
        profundidad_canal = (diametro_ext - diametro_nucleo_punta) / 2.0

        rad_hel_a = math.radians(helice_a)
        lead_a = (math.pi * diametro_ext) / math.tan(rad_hel_a) if math.tan(rad_hel_a) != 0 else 0

        if tipo_helice == 'variable':
            rad_hel_b = math.radians(helice_b)
            lead_b = (math.pi * diametro_ext) / math.tan(rad_hel_b) if math.tan(rad_hel_b) != 0 else 0
            str_lead = f"{round(lead_a, 2)} / {round(lead_b, 2)}"
        else:
            str_lead = f"{round(lead_a, 2)}"

        div_base = 360.0 / num_canales if num_canales > 0 else 90.0
        if tipo_helice == 'variable':
            ang_1 = div_base - delta_index
            ang_2 = div_base + delta_index
            str_index = f"{round(ang_1, 1)}° / {round(ang_2, 1)}°"
        else:
            str_index = f"{round(div_base, 1)}° (Simétrico)"

        landa_1 = diametro_ext * 0.06
        landa_2 = diametro_ext * 0.18
        ancho_diente_total = landa_1 + landa_2

        rigidez_relativa = round((diametro_nucleo_punta / diametro_ext) ** 4 * 100.0, 1) if diametro_ext > 0 else 0.0

        if rigidez_relativa >= 15.0:
            estado_rigidez = "Excelente Rigidez (Aceros / Inox)"
            clase_rigidez = "status-ok"
        elif rigidez_relativa >= 8.0:
            estado_rigidez = "Rigidez Estándar (Uso General)"
            clase_rigidez = "status-warning"
        else:
            estado_rigidez = "Baja Rigidez (Alta evacuación / Aluminio)"
            clase_rigidez = "status-danger"

        return jsonify({
            'success': True,
            'diametro_nucleo_punta': round(diametro_nucleo_punta, 4 if unidad == 'in' else 3),
            'diametro_nucleo_raiz': round(diametro_nucleo_raiz, 4 if unidad == 'in' else 3),
            'profundidad_canal': round(profundidad_canal, 4 if unidad == 'in' else 3),
            'paso_helice_str': str_lead,
            'indexado_str': str_index,
            'landa_1': round(landa_1, 4 if unidad == 'in' else 3),
            'landa_2': round(landa_2, 4 if unidad == 'in' else 3),
            'ancho_diente_total': round(ancho_diente_total, 4 if unidad == 'in' else 3),
            'esquina_str': str_esquina,
            'dish_angle': round(dish_angle, 1),
            'rake_radial': round(rake_radial, 1),
            'rigidez_relativa': rigidez_relativa,
            'estado_rigidez': estado_rigidez,
            'clase_rigidez': clase_rigidez
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/calcular-broca', methods=['POST'])
def calcular_broca():
    data = request.json or {}
    try:
        unidad = data.get('unidad', 'mm')
        d1 = float(data.get('diametro_broca', 8.0))
        lc = float(data.get('longitud_canal', 53.0))
        helice = float(data.get('helice_broca', 30.0))
        ang_punta = float(data.get('angulo_punta', 140.0))
        
        pct_dw = float(data.get('pct_nucleo_broca') or data.get('pct_nucleo') or 28.0)
        back_taper = float(data.get('back_taper_val') or data.get('back_taper') or 0.08)

        rad_hel = math.radians(helice)
        lead_broca = (math.pi * d1) / math.tan(rad_hel) if math.tan(rad_hel) != 0 else 0.0

        rad_half_sigma = math.radians(ang_punta / 2.0)
        altura_punta = (d1 / 2.0) / math.tan(rad_half_sigma) if math.tan(rad_half_sigma) != 0 else 0.0

        dw_punta = d1 * (pct_dw / 100.0)
        back_taper_acum = (lc / 100.0) * (back_taper * 25.4 if unidad == 'in' else back_taper)
        dw_raiz = dw_punta + back_taper_acum

        return jsonify({
            'success': True,
            'lead_broca': round(lead_broca, 2),
            'altura_punta': round(altura_punta, 4 if unidad == 'in' else 3),
            'dw_punta': round(dw_punta, 4 if unidad == 'in' else 3),
            'dw_raiz': round(dw_raiz, 4 if unidad == 'in' else 3)
        })
    except Exception as e:
        print(f"ERROR EN BROCA: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)