import math

def calcular_geometria_fresa(data):
    """
    Cálculo cinemático y geométrico avanzado de fresas de carburo.
    Integra el paso de hélice (Lead Ph), indexado simétrico/asimétrico,
    diámetros de núcleo en punta/raíz y rigidez elástica Iz.
    """
    unidad = str(data.get('unidad', 'mm')).lower()
    diametro_ext = float(data.get('diametro_ext', 12.0))
    longitud_corte = float(data.get('longitud_corte', 35.0))
    pct_nucleo = float(data.get('pct_nucleo', 62.0))
    num_dientes = max(1, int(data.get('num_dientes', 4)))
    angulo_helice = float(data.get('angulo_helice', 35.0))
    tipo_punta = str(data.get('tipo_punta', 'plana')).lower()
    radio_esquina = float(data.get('radio_esquina', 0.0))
    taper_deg = float(data.get('taper_deg', 1.5))  # Ángulo de conicidad del núcleo

    # 1. Paso de Hélice (Lead Ph = pi * D / tan(lambda))
    rad_helice = math.radians(angulo_helice)
    if rad_helice > 0:
        paso_helice = (math.pi * diametro_ext) / math.tan(rad_helice)
    else:
        paso_helice = 0.0

    # 2. Indexado Angular Teórico (360° / Z)
    angulo_indexado = 360.0 / num_dientes

    # 3. Núcleo Real en Punta y Raíz (Ecuación Geométrica con Taper)
    d_nucleo_punta = diametro_ext * (pct_nucleo / 100.0)
    
    # Si la broca/fresa tiene conicidad de núcleo (taper):
    taper_rad = math.radians(taper_deg)
    d_nucleo_raiz = d_nucleo_punta + (2.0 * longitud_corte * math.sin(taper_rad))
    # Limitar para que el núcleo en la raíz nunca supere el diámetro exterior
    d_nucleo_raiz = min(d_nucleo_raiz, diametro_ext * 0.98)

    # 4. Inercia Flexional Iz y Rigidez Relativa (%)
    # Factor de reducción por tipo de herramienta (Fresa Esférica vs Plana)
    factor_esferica = 0.75 if tipo_punta == 'esferica' else 1.0
    
    i_teorico = (math.pi * (d_nucleo_punta ** 4)) / 64.0
    i_efectivo = i_teorico * factor_esferica
    
    indice_iz_relativo = round((i_efectivo / ((math.pi * (diametro_ext ** 4)) / 64.0)) * 100.0, 1)

    # 5. Geometría de Punta (Dish Angle / Chaflán / Radio)
    if tipo_punta == 'toroidal':
        esquina_str = f"R {radio_esquina:.2f} {unidad}"
        dish_angle = "2.0°"
    elif tipo_punta == 'esferica':
        esquina_str = f"R {(diametro_ext / 2.0):.2f} {unidad} (Ball Nose)"
        dish_angle = "0.0° (Esférica)"
    else:
        esquina_str = "Plana (Sin Radio)"
        dish_angle = "1.5° (Estándar)"

    # Formateo de respuesta para el frontend
    unit_str = "in" if unidad == "in" else "mm"

    return {
        'success': True,
        'diametro_nucleo_punta': round(d_nucleo_punta, 3),
        'diametro_nucleo_raiz': round(d_nucleo_raiz, 3),
        'rigidez_relativa': indice_iz_relativo,
        'paso_helice_val': round(paso_helice, 2),
        'paso_helice_str': f"{paso_helice:.2f} {unit_str}/vuelta",
        'indexado_str': f"{angulo_indexado:.1f}° ({num_dientes} Dientes Simétricos)",
        'esquina_str': esquina_str,
        'dish_angle': dish_angle,
        'rake_radial': "8.0° (Geometría Positiva)",
        'estado_rigidez': "Rigidez Sección OK" if indice_iz_relativo >= 12.0 else "Sección Alta Flexibilidad",
        'clase_rigidez': "status-ok" if indice_iz_relativo >= 12.0 else "status-warning"
    }