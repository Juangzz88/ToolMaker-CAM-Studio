/* ==========================================================================
   ToolMaker CAM Studio — Modales Expertos y Troubleshooting
   ========================================================================== */

function calcCarburo() {
  const co = document.getElementById('carburo_co')?.value || '10';
  const eVal = { '6': '630 GPa', '8': '610 GPa', '10': '590 GPa', '12': '560 GPa' }[co];
  const kcVal = { '6': '3100 N/mm²', '8': '2950 N/mm²', '10': '2800 N/mm²', '12': '2600 N/mm²' }[co];
  const hvVal = { '6': '1780 HV30', '8': '1700 HV30', '10': '1620 HV30', '12': '1520 HV30' }[co];
  
  if (document.getElementById('res-carb-e')) document.getElementById('res-carb-e').textContent = eVal;
  if (document.getElementById('res-carb-kc')) document.getElementById('res-carb-kc').textContent = kcVal;
  if (document.getElementById('res-carb-hv')) document.getElementById('res-carb-hv').textContent = hvVal;
}

function calcDeflexion() {
  const D_ext = parseFloat(document.getElementById('def_D_ext')?.value) || 12.0;
  const d_nuc = parseFloat(document.getElementById('def_d')?.value) || 7.8;
  const l_vol = parseFloat(document.getElementById('def_l')?.value) || 35.0;
  const z_canales = parseInt(document.getElementById('def_z')?.value) || 4;
  const helice_deg = parseFloat(document.getElementById('def_helice')?.value) || 35.0;
  const fRad = parseFloat(document.getElementById('def_frad')?.value) || 150.0;
  const co = document.getElementById('carburo_co')?.value || '10';

  const eCarburoMap = { '6': 630000, '8': 610000, '10': 590000, '12': 560000 };
  const eCarburo = eCarburoMap[co] || 590000;
  const i_teorico = (Math.PI * Math.pow(d_nuc, 4)) / 64.0;
  const factorRanuras = 1.0 - (0.05 * z_canales) - (0.0015 * helice_deg);
  const i_efectivo = i_teorico * Math.max(factorRanuras, 0.30);
  const delta = (fRad * Math.pow(l_vol, 3)) / (3.0 * eCarburo * i_efectivo);
  const pctNucleo = (d_nuc / D_ext) * 100.0;

  const resPct = document.getElementById('res-pct-nucleo-val');
  const resIz = document.getElementById('res-iz-efectivo-val');
  const resVal = document.getElementById('res-def-val');
  const resSt = document.getElementById('res-def-status');

  if (resPct) resPct.textContent = `${pctNucleo.toFixed(1)} %`;
  if (resIz) resIz.textContent = `${i_efectivo.toFixed(2)} mm⁴`;
  if (resVal) resVal.textContent = `${delta.toFixed(4)} mm`;

  if (resSt) {
    if (delta > 0.005) {
      resSt.textContent = "⚠️ ALERTA: Deflexión crítica (> 0.005 mm). Alto riesgo de rotura o error de perfil. Usar soporte/luneta.";
      resSt.className = "small mt-2 fw-bold text-danger";
    } else {
      resSt.textContent = "✅ Proceso Estable (Sin necesidad de Luneta)";
      resSt.className = "small mt-2 fw-bold text-success";
    }
  }
}

function calcDin6535() {
  const d = document.getElementById('din_diam')?.value || '10';
  const forceMap = { '6': '> 45 Nm', '8': '> 85 Nm', '10': '> 130 Nm', '12': '> 210 Nm', '16': '> 380 Nm' };
  if (document.getElementById('res-din-force')) document.getElementById('res-din-force').textContent = forceMap[d] || '> 100 Nm';
}

const matrizTroubleshooting = {
  chipping: {
    causa: "Fuerza específica de corte o impacto mecánico excesivo al entrar al canal, o sustrato frágil.",
    acciones: [
      "Reducir la velocidad de avance entre un 15% y 20%.",
      "Dividir la profundidad agregando 1 pasada adicional de desbaste.",
      "Aumentar el contenido de Cobalto del carburo a 12% Co (Sustrato Ultra Tenaz)."
    ],
    ajustes: { factor_vf: 0.82, pasadas_extra: 1, co: '12' }
  },
  clogging: {
    causa: "Volumen de viruta remolida excesivo combinado con canal estrecho.",
    acciones: [
      "Aumentar la velocidad de husillo RPM un 10% - 15% para acelerar la evacuación.",
      "Reducir la profundidad por pasada o cambiar a Aglomerante Híbrido con grano más abierto."
    ],
    ajustes: { factor_rpm: 1.12, bond: 'hibrido' }
  },
  thermal: {
    causa: "Frotamiento elástico por muela embotada (Glazing) que genera picos térmicos.",
    acciones: [
      "Reducir la velocidad RPM de husillo un 15% para bajar la temperatura.",
      "Ejecutar un ciclo de reavivado (Dressing) en la muela."
    ],
    ajustes: { factor_rpm: 0.85, bond: 'hibrido' }
  },
  chatter: {
    causa: "Deflexión elástica o resonancia armónica entre los dientes y la muela.",
    acciones: [
      "Reducir la fuerza radial disminuyendo el avance un 15%.",
      "Aumentar las pasadas de desbaste para aligerar la carga lineal."
    ],
    ajustes: { factor_vf: 0.85, pasadas_extra: 1, bond: 'resina' }
  },
  wheel_wear: {
    causa: "Concentración baja de diamante o resistencia del aglomerante insuficiente.",
    acciones: [
      "Cambiar aglomerante a Híbrido (HB) o Metálico de mayor retención.",
      "Aumentar las RPM un 10% para aligerar la carga por grano."
    ],
    ajustes: { factor_rpm: 1.10, bond: 'hibrido' }
  }
};

let ultimoAjusteTroubleshoot = null;

function analizarFallaProceso() {
  const sintomaSelect = document.getElementById('tb_sintoma');
  const panel = document.getElementById('tb_panel_diagnostico');
  const causaTexto = document.getElementById('tb_causa_texto');
  const accionesLista = document.getElementById('tb_acciones_lista');
  
  if (!sintomaSelect) return;
  const sintoma = sintomaSelect.value;

  if (!sintoma || sintoma === 'ninguno') {
    if (panel) panel.classList.add('d-none');
    return;
  }

  const diag = matrizTroubleshooting[sintoma];
  if (!diag) return;

  if (causaTexto) causaTexto.innerHTML = diag.causa;
  if (accionesLista) {
    accionesLista.innerHTML = diag.acciones.map(a => `<li class="mb-1">🔹 ${a}</li>`).join('');
  }

  ultimoAjusteTroubleshoot = diag.ajustes;
  if (panel) {
    panel.classList.remove('d-none');
    panel.style.display = 'block';
  }
}

function aplicarSolucionTroubleshooting() {
  if (!ultimoAjusteTroubleshoot) return;
  const adj = ultimoAjusteTroubleshoot;

  if (adj.factor_vf) {
    const elVf = document.getElementById('avance');
    if (elVf) elVf.value = Math.round(parseFloat(elVf.value) * adj.factor_vf);
  }
  if (adj.factor_rpm) {
    const elRpm = document.getElementById('rpm');
    if (elRpm) elRpm.value = Math.round(parseFloat(elRpm.value) * adj.factor_rpm);
  }
  if (adj.pasadas_extra) {
    const elPasadas = document.getElementById('pasadas_desbaste');
    if (elPasadas) elPasadas.value = parseInt(elPasadas.value) + adj.pasadas_extra;
  }
  if (adj.bond) {
    const elBond = document.getElementById('aglomerante');
    if (elBond) elBond.value = adj.bond;
  }

  const modalEl = document.getElementById('modalTroubleshooting');
  if (modalEl) {
    const modalObj = bootstrap.Modal.getInstance(modalEl);
    if (modalObj) modalObj.hide();
  }

  if (typeof ejecutarCalculo === 'function') {
    ejecutarCalculo();
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const selectSintoma = document.getElementById('tb_sintoma');
  if (selectSintoma) {
    selectSintoma.addEventListener('change', analizarFallaProceso);
  }
  calcCarburo();
  calcDeflexion();
  calcDin6535();
});