/* ==========================================================================
   ToolMaker CAM Studio — Core JS (Contexto y Control de Dock)
   ========================================================================== */

const TM_CONTEXT_KEY = 'TM_GLOBAL_TOOL_CONTEXT';

function toggleIADock() {
  const dock = document.getElementById('iaDockWidget');
  const btnText = document.getElementById('dock-toggle-btn');
  if (dock) {
    dock.classList.toggle('expanded');
    if (btnText) {
      btnText.textContent = dock.classList.contains('expanded') ? '▼ Colapsar' : '▲ Ampliar';
    }
  }
}

/* Extrae el primer número de un texto (respeta signo negativo y decimales).
   Devuelve NaN si no hay ningún número. */
function extraerNumero(texto) {
  const m = String(texto).replace(/,/g, '').match(/-?\d+(\.\d+)?/);
  return m ? parseFloat(m[0]) : NaN;
}

function capturarYGuardarContextoLocal() {
  try {
    const rutaActual = window.location.pathname;
    let memoriaGlobal = JSON.parse(localStorage.getItem(TM_CONTEXT_KEY) || '{}');

    const radioUnidad = document.querySelector('input[name="unidad"]:checked');
    const unidadReal = radioUnidad ? radioUnidad.value : (window.currentUnit || 'mm');

    const inputs = document.querySelectorAll('input, select');
    let datosModulo = { unidad: unidadReal };

    inputs.forEach(i => {
      const clave = i.id || i.name;
      if (!clave || i.disabled) return;
      if (['file', 'password', 'button', 'submit'].includes(i.type)) return;
      if (i.name === 'unidad' || i.id === 'unit_mm' || i.id === 'unit_in') return;
      // Un grupo de radios comparte name: solo cuenta el seleccionado
      if (i.type === 'radio' && !i.checked) return;
      if (i.value !== "") datosModulo[clave] = i.value;
    });

    const spansResultados = ['res-fz', 'res-mc', 'res-def-val', 'res-iz-efectivo-val'];
    spansResultados.forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        const valNum = extraerNumero(el.textContent);
        if (!isNaN(valNum)) datosModulo[id.replace(/-/g, '_')] = valNum;
      }
    });

    if (rutaActual.includes('geometria-herramienta')) {
      memoriaGlobal.geometria = Object.assign({}, memoriaGlobal.geometria || {}, datosModulo);
    } else if (rutaActual.includes('recubrimientos')) {
      memoriaGlobal.recubrimiento = Object.assign({}, memoriaGlobal.recubrimiento || {}, datosModulo);
    } else if (rutaActual.includes('calculadora-muelas') || rutaActual === '/') {
      memoriaGlobal.operacion = Object.assign({}, memoriaGlobal.operacion || {}, datosModulo);
    } else if (rutaActual.includes('geometria-brocas')) {
      memoriaGlobal.broca = Object.assign({}, memoriaGlobal.broca || {}, datosModulo);
    } else if (rutaActual.includes('catalogo-abrasivos')) {
      memoriaGlobal.abrasivo = Object.assign({}, memoriaGlobal.abrasivo || {}, datosModulo);
    } else {
      console.warn('[TM-Local] Ruta sin módulo asociado, contexto no guardado:', rutaActual);
    }

    localStorage.setItem(TM_CONTEXT_KEY, JSON.stringify(memoriaGlobal));
  } catch (err) {
    console.error("[TM-Local] Error capturando contexto:", err);
  }
}

/* Borra el contexto guardado entre módulos (útil para evitar datos viejos).
   Puedes llamarlo desde un botón: onclick="reiniciarContextoLocal()" */
function reiniciarContextoLocal() {
  try {
    localStorage.removeItem(TM_CONTEXT_KEY);
    console.info('[TM-Local] Contexto reiniciado.');
  } catch (err) {
    console.error("[TM-Local] Error reiniciando contexto:", err);
  }
}