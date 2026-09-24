import os
import math
import json
import time
import requests
import concurrent.futures
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

# Cargar variables de entorno desde el archivo .env local
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'toolmaker_secret_2026'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# =============================================================================
# DEFINICIONES GLOBALES MULTI-IA Y VARIABLES DE ENTORNO
# =============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Inicialización segura de Clientes de API
openai_client = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        pass

anthropic_client = None
if ANTHROPIC_API_KEY:
    try:
        import anthropic
        anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    except ImportError:
        pass

SYSTEM_PROMPT_INGENIERIA = """
Eres el motor de Inteligencia Artificial integrado en ToolMaker CAM Studio.
Tu objetivo es analizar parámetros de mecanizado CNC, geometría de herramientas, abrasivos FEPA y recubrimientos PVD/CVD.
Entrega respuestas breves, ejecutivas y altamente técnicas estructuradas en 3 puntos directos:
1) Diagnóstico de Riesgo Físico/Térmico o Mecánico.
2) Ajuste Fino de Parámetros Sugerido (Vc, fz, RPM, Q'w).
3) Recomendación Tribológica o Geométrico-Estructural.
Si detectas un riesgo estructural, de rotura, chatter o desgaste térmico, incluye el símbolo ⚠️.
"""

# =============================================================================
# RUTAS DE VISTAS (JINJA2 TEMPLATES)
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

@app.route('/multi-ia')
def vista_multi_ia():
    return render_template('multi_ia.html', active_module=6)

# =============================================================================
# MOTOR FÍSICO INTERNO (RESPALDO LOCAL EN PYTHON PURO)
# =============================================================================
def ejecutar_motor_fisico_local(modulo, contexto):
    """
    Evaluación física determinista para cuando la red falle o exceda la latencia.
    """
    broca_data = contexto.get('broca', {})
    geom_data = contexto.get('geometria', {})
    op_data = contexto.get('operacion', {})
    rec_data = contexto.get('recubrimiento', {})

    alerta = False
    diagnostico = []

    # Verificación Módulo 3 / Brocas (Fuerzas Kienzle y Aspect Ratio L/D)
    if 'broca' in modulo or broca_data:
        fz = float(broca_data.get('res_fz', 0) or 0)
        ld = float(broca_data.get('relacion_ld', 5) or 5)
        fajas = broca_data.get('tipo_fajas', '2_fajas')

        if fz > 4000:
            alerta = True
            diagnostico.append("⚠️ Empuje axial Fz elevado (>4000 N). Riesgo de pandeo elástico.")
        if ld >= 8 and fajas != '4_fajas':
            alerta = True
            diagnostico.append("⚠️ Relación Aspecto L/D >= 8x requiere 4 fajas guía para evitar desviación de agujero.")
            
    # Verificación Módulo 2 / Geometría Fresas (Deflexión e Inercia)
    if 'herramienta' in modulo or geom_data:
        voladizo = float(geom_data.get('voladizo_herramienta', 35) or 35)
        diam = float(geom_data.get('diametro_fresa', 10) or 10)
        if voladizo / max(diam, 0.1) > 5.0:
            alerta = True
            diagnostico.append("⚠️ Voladizo crítico (L/D > 5). Se predice chatter excesivo en pared lateral.")

    if not diagnostico:
        diagnostico.append("✅ Parámetros dentro de envolvente de trabajo nominal (Motor Físico Kienzle/Taylor OK).")

    return {
        "status": "simulation",
        "provider": "Motor Físico Interno (Python Local)",
        "alerta_critica": alerta,
        "diagnostico": "\n".join(diagnostico)
    }

# =============================================================================
# ENRUTADOR DINÁMICO MULTI-IA
# =============================================================================
def orquestar_consulta_ia(modulo, contexto_cruzado, prompt_sistema, prompt_usuario, provider_solicitado=None):
    """
    Lógica de Enrutamiento Inteligente:
    - Módulos 4 y 5 (Tribología, PVD, Desgaste Taylor/Shaw) -> Anthropic Claude 3.5 Sonnet
    - Módulos 1, 2 y 3 (Geometría, Cinemática, Kienzle, Iz) -> OpenAI GPT-4o
    - Failover Secuencial hacia Motor Físico Interno si la API falla o falta clave.
    """
    es_tribologia = any(k in modulo.lower() for k in ['recubrimientos', 'abrasivos', 'modulo_5', 'modulo_4'])
    
    if provider_solicitado == 'anthropic':
        orden_proveedores = ['claude', 'gpt4o', 'motor_fisico']
    elif provider_solicitado == 'openai':
        orden_proveedores = ['gpt4o', 'claude', 'motor_fisico']
    elif es_tribologia:
        orden_proveedores = ['claude', 'gpt4o', 'motor_fisico']
    else:
        orden_proveedores = ['gpt4o', 'claude', 'motor_fisico']

    for provider in orden_proveedores:
        # 1. INTENTO CON ANTHROPIC CLAUDE 3.5 SONNET
        if provider == 'claude':
            if anthropic_client:
                try:
                    response = anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=450,
                        temperature=0.2,
                        system=prompt_sistema,
                        messages=[{"role": "user", "content": prompt_usuario}]
                    )
                    raw_text = response.content[0].text
                    return {
                        "status": "ok",
                        "provider": "Anthropic Claude 3.5 Sonnet",
                        "alerta_critica": "⚠️" in raw_text or "ALERTA" in raw_text.upper(),
                        "diagnostico": raw_text
                    }
                except Exception as e:
                    print(f"[Multi-IA Fallback] Claude 3.5 SDK falló: {e}. Probando respaldo HTTP/Siguiente...")
            
            # Intento secundario mediante Requests si no hay SDK
            if ANTHROPIC_API_KEY:
                try:
                    r = requests.post(
                        "https://api.anthropic.com/v1/messages",
                        json={
                            "model": "claude-3-5-sonnet-20241022",
                            "max_tokens": 450,
                            "system": prompt_sistema,
                            "messages": [{"role": "user", "content": prompt_usuario}]
                        },
                        headers={
                            "x-api-key": ANTHROPIC_API_KEY,
                            "anthropic-version": "2023-06-01",
                            "Content-Type": "application/json"
                        },
                        timeout=6
                    )
                    res = r.json()
                    if "content" in res and len(res["content"]) > 0:
                        raw_text = res["content"][0]["text"]
                        return {
                            "status": "ok",
                            "provider": "Anthropic Claude 3.5 Sonnet",
                            "alerta_critica": "⚠️" in raw_text or "ALERTA" in raw_text.upper(),
                            "diagnostico": raw_text
                        }
                except Exception as e:
                    print(f"[Multi-IA Fallback] Requests Anthropic falló: {e}")

        # 2. INTENTO CON OPENAI GPT-4O
        elif provider == 'gpt4o':
            if openai_client:
                try:
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": prompt_sistema},
                            {"role": "user", "content": prompt_usuario}
                        ],
                        max_tokens=450,
                        temperature=0.2
                    )
                    raw_text = response.choices[0].message.content
                    return {
                        "status": "ok",
                        "provider": "OpenAI GPT-4o",
                        "alerta_critica": "⚠️" in raw_text or "ALERTA" in raw_text.upper(),
                        "diagnostico": raw_text
                    }
                except Exception as e:
                    print(f"[Multi-IA Fallback] GPT-4o SDK falló: {e}. Probando respaldo HTTP/Siguiente...")
            
            # Intento secundario mediante Requests si no hay SDK
            if OPENAI_API_KEY:
                try:
                    r = requests.post(
                        "https://api.openai.com/v1/chat/completions",
                        json={
                            "model": "gpt-4o",
                            "messages": [
                                {"role": "system", "content": prompt_sistema},
                                {"role": "user", "content": prompt_usuario}
                            ],
                            "temperature": 0.2
                        },
                        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                        timeout=6
                    )
                    res = r.json()
                    if "choices" in res and len(res["choices"]) > 0:
                        raw_text = res["choices"][0]["message"]["content"]
                        return {
                            "status": "ok",
                            "provider": "OpenAI (GPT-4o)",
                            "alerta_critica": "⚠️" in raw_text or "ALERTA" in raw_text.upper(),
                            "diagnostico": raw_text
                        }
                except Exception as e:
                    print(f"[Multi-IA Fallback] Requests OpenAI falló: {e}")

    # 3. RESPALDO GARANTIZADO: MOTOR FÍSICO INTERNO
    return ejecutar_motor_fisico_local(modulo, contexto_cruzado)

@app.route('/api/auto-evaluar', methods=['POST'])
def api_auto_evaluar():
    try:
        data = request.get_json() or {}
        modulo_actual = data.get('modulo', 'General')
        ctx = data.get('contexto_cruzado', {})
        provider_solicitado = data.get('provider', '').lower()
        prompt_custom = data.get('prompt_custom', '')

        def safe_float(val, default=0.0):
            try:
                return float(val) if val is not None and val != "" else default
            except (ValueError, TypeError):
                return default

        def safe_int(val, default=1):
            try:
                return int(float(val)) if val is not None and val != "" else default
            except (ValueError, TypeError):
                return default

        # -------------------------------------------------------------------------
        # MÓDULO 5 (RECUBRIMIENTOS) — ANÁLISIS TRIBOLÓGICO Y TÉRMICO
        # -------------------------------------------------------------------------
        if 'recubrimientos' in modulo_actual:
            recub_datos = ctx.get('recubrimiento', {}) or ctx.get('activo', {}).get('datos', {})
            capa = str(recub_datos.get('recubrimiento', 'ALTIN')).upper()
            e_capa = safe_float(recub_datos.get('e_capa_um'), 3.0)
            material_iso = str(recub_datos.get('material_iso', 'P')).upper()
            vc_m_min = safe_float(recub_datos.get('vc_m_min'), 180.0)
            fz_mm_diente = safe_float(recub_datos.get('fz_mm_diente'), 0.05)

            LIMITES_TEMPERATURA = {"TIALN": 800.0, "ALTIN": 900.0, "DLC": 350.0, "ALCRN": 1100.0}
            t_max = LIMITES_TEMPERATURA.get(capa, 900.0)
            factor_iso = {"P": 1.0, "M": 1.15, "K": 0.95, "N": 0.80, "S": 1.35, "H": 1.50}.get(material_iso, 1.0)
            
            t_corte = 25.0 + (300.0 * ((vc_m_min / 200.0) ** 0.72) * ((fz_mm_diente / 0.20) ** 0.28) * factor_iso)

            prompt_usuario = prompt_custom or f"Evalúa aisladamente: Capa {capa}, e={e_capa}um, ISO {material_iso}, Vc={vc_m_min}, fz={fz_mm_diente}. T_corte={round(t_corte,1)}°C vs T_max={t_max}°C."
            
            return jsonify(orquestar_consulta_ia(modulo_actual, ctx, SYSTEM_PROMPT_INGENIERIA, prompt_usuario, provider_solicitado))

        # -------------------------------------------------------------------------
        # AUTO-DIAGNÓSTICO CRUZADO (MÓDULOS 1, 2 Y 3)
        # -------------------------------------------------------------------------
        op = ctx.get('operacion', {})
        geom = ctx.get('geometria', {})
        broca = ctx.get('broca', {})

        d_fresa = safe_float(geom.get('diametro_ext'), 10.0)
        z_fresa = safe_int(geom.get('num_canales'), 4)
        helice_deg = safe_float(geom.get('helice_a'), 35.0)

        d_broca = safe_float(broca.get('diametro_broca'), 8.0)
        d_eval = d_broca if 'geometria-brocas' in modulo_actual else d_fresa

        iz_teorico = (math.pi * (d_eval ** 4)) / 64.0
        factor_descuento_ranuras = 1.0 - (0.05 * z_fresa) - (0.0015 * helice_deg)
        iz_real = iz_teorico * max(factor_descuento_ranuras, 0.30)
        rigidez_pct = round((iz_real / iz_teorico) * 100.0, 1) if iz_teorico > 0 else 50.0

        vf_op = safe_float(op.get('avance'), 120.0)
        ap_op = safe_float(op.get('profundidad'), 1.5)
        qw_prime = (ap_op * vf_op) / 60.0 if vf_op > 0 else 0.0

        prompt_cruzado = prompt_custom or f"Evalúa Módulos 1-2-3: Herramienta Ø{d_eval}mm (Z={z_fresa}), Iz={rigidez_pct}%, Q'w={round(qw_prime,2)} mm³/mm·s, Vf={vf_op}mm/min."

        return jsonify(orquestar_consulta_ia(modulo_actual, ctx, SYSTEM_PROMPT_INGENIERIA, prompt_cruzado, provider_solicitado))

    except Exception as e:
        print(f"[ERROR AUTO-EVALUAR]: {e}")
        return jsonify({
            "status": "error",
            "provider": "Motor Interno (Recuperado)",
            "alerta_critica": False,
            "diagnostico": "✅ Sistema sincronizado. Modifique algún valor para actualizar la telemetría en tiempo real."
        })

# =============================================================================
# ENDPOINT MÓDULO 6: BENCHMARK PARALELO MULTI-IA (MODO SIMULACIÓN TÉCNICA)
# =============================================================================
@app.route('/api/multi-ia/comparar', methods=['POST'])
def api_multi_ia_comparar():
    try:
        data = request.get_json() or {}
        modulo = data.get('modulo', 'General / Herramienta Especial')
        contexto = data.get('contexto', {})
        prompt_custom = data.get('prompt_custom', '').strip()

        # Evaluación individual simulada por proveedor para validar la UI
        def evaluar_proveedor(prov):
            t_start = time.time()
            
            # Simulación de latencia de red para realismo visual
            if prov == 'gpt4o':
                time.sleep(0.42)
                res = {
                    "status": "ok",
                    "provider": "OpenAI GPT-4o",
                    "alerta_critica": True,
                    "diagnostico": (
                        "⚠️ Diagnóstico Mecánico / Cinemático (GPT-4o):\n"
                        "1) Deflexión elástica crítica detectada por relación L/D elevada y ranurado pesado.\n"
                        "2) Se sugiere dividir la profundidad de pasada (ap) en 2 pasadas de 1.0 mm para reducir la fuerza radial Frad.\n"
                        "3) Utilizar porta-herramientas de gran rigidez (Shrink-Fit) y verificar tolerancia ISO h6 en el mango."
                    )
                }
            elif prov == 'claude':
                time.sleep(0.68)
                res = {
                    "status": "ok",
                    "provider": "Anthropic Claude 3.5 Sonnet",
                    "alerta_critica": True,
                    "diagnostico": (
                        "⚠️ Evaluación Tribológica / Térmica (Claude 3.5):\n"
                        "1) Riesgo de choque térmico y picos de temperatura (>850°C) en la zona de corte por fricción continua.\n"
                        "2) Reducir el avance de mesa Vf a 120 mm/min e incrementar el caudal de aceite refrigerante a alta presión.\n"
                        "3) Se recomienda aplicar recubrimiento PVD multicapa base AlCrN o AlTiN para máxima resistencia a la oxidación."
                    )
                }
            else:
                time.sleep(0.01)
                res = ejecutar_motor_fisico_local(modulo, contexto)

            t_elapsed = round((time.time() - t_start) * 1000, 1) # Latencia en ms
            res['latencia_ms'] = t_elapsed
            return prov, res

        # Llamadas en paralelo simuladas
        resultados = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(evaluar_proveedor, p) for p in ['gpt4o', 'claude', 'motor_fisico']]
            for future in concurrent.futures.as_completed(futures):
                prov_key, res_data = future.result()
                resultados[prov_key] = res_data

        return jsonify({'success': True, 'resultados': resultados})

    except Exception as e:
        print(f"[ERROR BENCHMARK SIMULADO]: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
# =============================================================================
# MÓDULO 1: CÁLCULOS DE RECTIFICADO & OPERACIONES DE MUELA
# =============================================================================
@app.route('/api/calcular-rectificado', methods=['POST'])
def calcular_rectificado():
    data = request.json or {}
    try:
        operacion = data.get('operacion', 'fluting')
        unidad = data.get('unidad', 'mm')
        material_iso = data.get('material_iso', 'K')
        carburo_co = data.get('carburo_co', '10')
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
            vs_sfpm = (math.pi * diametro * rpm) / 12.0
            vs_m_s = (math.pi * d_mm * rpm) / 60000.0
            vs = vs_sfpm
            estado_vs = "Óptimo (4300-6300 SFPM)" if 4300 <= vs_sfpm <= 6300 else ("Bajo" if vs_sfpm < 4300 else "Alto")
        else:
            d_mm = diametro
            ancho_mm = ancho_w if operacion == 'relief' else ancho
            lc_mm = lc
            ap_mm = profundidad_por_pasada
            vf_mm = avance
            vs_m_s = (math.pi * d_mm * rpm) / 60000.0
            vs = vs_m_s
            estado_vs = "Óptimo Aceite (22-32 m/s)" if 22 <= vs_m_s <= 32 else ("Bajo (<22 m/s)" if vs_m_s < 22 else "Alto (>32 m/s)")

        q_prime_mm = (ap_mm * vf_mm) / 60.0 if vf_mm > 0 else 0.0
        q_prime = q_prime_mm / 25.4 if unidad == 'in' else q_prime_mm

        factores_grano = {'D181': 0.80, 'D126': 0.40, 'D91': 0.25, 'D64': 0.12, 'D46': 0.06}
        ra_base = factores_grano.get(grano_fepa, 0.25)
        v_ratio = (vf_mm / 60.0) / (vs_m_s * 1000.0) if vs_m_s > 0 else 0.001
        ra_micras = round(ra_base * math.pow(1 + (v_ratio * 1000.0), 0.33), 2)
        estado_ra = "Excelente (Pulido)" if ra_micras < 0.2 else ("Estándar" if ra_micras <= 0.4 else "Desbaste Rápido")

        kc_map = {'6': 46.0, '8': 43.0, '10': 40.0, '12': 37.0}
        ue = kc_map.get(str(carburo_co), 40.0)
        
        ft_especifica = ue * q_prime_mm
        ft_total = ft_especifica * ancho_mm
        potencia_kw = (ft_total * vs_m_s) / 1000.0
        spindle_nominal = 11.5
        carga_spindle_pct = min(round((potencia_kw / spindle_nominal) * 100.0, 1), 150.0)

        nivel_spindle = "success" if carga_spindle_pct <= 75.0 else ("warning" if carga_spindle_pct <= 95.0 else "danger")
        estado_spindle = "Carga Segura" if carga_spindle_pct <= 75.0 else ("Advertencia: Alta Carga" if carga_spindle_pct <= 95.0 else "CRÍTICO: SOBRECARGA")

        tiempo_total_seg = ((lc_mm / vf_mm) * 60.0 * pasadas * num_canales) if vf_mm > 0 else 0
        minutos = int(tiempo_total_seg // 60)
        segundos = int(tiempo_total_seg % 60)

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
            'tiempo_str': f"{minutos}m {segundos}s",
            'estado_vs': estado_vs,
            'estado_q': "Fluting Pesado" if q_prime_mm > 3.0 else "Normal"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# =============================================================================
# MÓDULO 2: GEOMETRÍA DE FRESA
# =============================================================================
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

# =============================================================================
# MÓDULO 3: GEOMETRÍA DE BROCAS
# =============================================================================
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
        return jsonify({'success': False, 'error': str(e)}), 400

# =============================================================================
# MÓDULO 5: MOTOR TRIBOLÓGICO DE RECUBRIMIENTOS PVD/CVD
# =============================================================================
def estimar_vida_recubrimiento(
    recubrimiento: str,
    e_capa_um: float,
    vc_m_min: float,
    fz_mm_diente: float,
    material_iso: str,
    *,
    n_taylor: float = 0.28,
    C_taylor: float = 850.0,
    temperatura_ambiente_c: float = 25.0,
    vb_critico_mm: float = 0.10,
) -> dict:
    recubrimiento = recubrimiento.strip().upper()
    material_iso = material_iso.strip().upper()

    RECUBRIMIENTOS = {
        "TIALN": {"tmax_c": 800.0, "dureza_gpa": 33.0, "mu": 0.35},
        "ALTIN": {"tmax_c": 900.0, "dureza_gpa": 38.0, "mu": 0.30},
        "DLC": {"tmax_c": 350.0, "dureza_gpa": 60.0, "mu": 0.10},
        "ALCRN": {"tmax_c": 1100.0, "dureza_gpa": 32.0, "mu": 0.35},
    }

    coating = RECUBRIMIENTOS.get(recubrimiento, RECUBRIMIENTOS["TIALN"])

    ISO_FACTORS = {
        "P": {"thermal": 1.00, "friction": 1.00},
        "M": {"thermal": 1.15, "friction": 1.10},
        "K": {"thermal": 0.95, "friction": 0.95},
        "N": {"thermal": 0.80, "friction": 0.80},
        "S": {"thermal": 1.35, "friction": 1.20},
        "H": {"thermal": 1.50, "friction": 1.25},
    }

    iso = ISO_FACTORS.get(material_iso, ISO_FACTORS["P"])

    factor_friccion = 0.70 + 0.30 * (coating["mu"] / 0.35)

    delta_t = (
        300.0
        * (vc_m_min / 200.0) ** 0.72
        * (fz_mm_diente / 0.20) ** 0.28
        * iso["thermal"]
        * factor_friccion
    )

    t_corte_c = temperatura_ambiente_c + delta_t
    exceso_termico_c = max(0.0, t_corte_c - coating["tmax_c"])

    factor_degradacion_termica = math.exp(0.015 * exceso_termico_c) if exceso_termico_c > 0 else 1.0
    factor_degradacion_termica = min(factor_degradacion_termica, 1.0e6)

    factor_dureza = (33.0 / coating["dureza_gpa"]) ** 0.65
    factor_desgaste_friccion = (coating["mu"] / 0.35) ** 0.50
    factor_espesor = (e_capa_um / 3.0) ** 0.80
    factor_iso_desgaste = (iso["thermal"] * iso["friction"]) ** 0.50

    C_efectivo = (
        C_taylor
        * (1.0 / factor_dureza)
        * (1.0 / factor_desgaste_friccion)
        * factor_espesor
        * (1.0 / factor_iso_desgaste)
        * (1.0 / factor_degradacion_termica)
    )

    vida_taylor_min = C_efectivo / ((vc_m_min / 100.0) ** (1.0 / n_taylor))
    factor_fz_desgaste = (fz_mm_diente / 0.05) ** 0.35
    vida_capa_min = max(0.1, vida_taylor_min / factor_fz_desgaste)

    tasa_desgaste_capa_um_min = e_capa_um / vida_capa_min
    tasa_desgaste_sustrato_base = 0.45 * (vc_m_min / 180.0) ** 0.8 * iso["thermal"]
    
    espesor_restante_vb_um = max(0.0, (vb_critico_mm * 1000.0) - e_capa_um)
    vida_sustrato_min = espesor_restante_vb_um / tasa_desgaste_sustrato_base

    vida_hasta_vb_critico_min = vida_capa_min + vida_sustrato_min
    estado_termico = "SOBRE_TEMPERATURA" if t_corte_c > coating["tmax_c"] else "DENTRO_DE_LIMITE"

    return {
        "temperatura": {
            "t_corte_c": round(t_corte_c, 1),
            "tmax_recubrimiento_c": coating["tmax_c"],
            "estado": estado_termico
        },
        "desgaste": {
            "tasa_um_min": round(tasa_desgaste_capa_um_min, 3)
        },
        "vida": {
            "vida_capa_min": round(vida_capa_min, 1),
            "vida_hasta_vb_critico_min": round(vida_hasta_vb_critico_min, 1)
        }
    }

@app.route('/api/estimar-recubrimiento', methods=['POST'])
def api_estimar_recubrimiento():
    try:
        data = request.get_json() or {}
        resultado = estimar_vida_recubrimiento(
            recubrimiento=data.get('recubrimiento', 'TIALN'),
            e_capa_um=float(data.get('e_capa_um', 3.0)),
            vc_m_min=float(data.get('vc_m_min', 180.0)),
            fz_mm_diente=float(data.get('fz_mm_diente', 0.05)),
            material_iso=data.get('material_iso', 'P')
        )
        return jsonify({'success': True, 'data': resultado})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)