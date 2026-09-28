"""
Aplica correcciones puntuales a templates/base.html y templates/muelas.html.

Uso (desde la raíz del proyecto):
    python parche_templates.py

- Antes de modificar un archivo guarda una copia en _backup_parche/
- Cada parche verifica que el texto a cambiar exista EXACTAMENTE una vez.
  Si no, lo omite y te lo dice (no rompe nada).
- Se puede ejecutar más de una vez: los parches ya aplicados se detectan.
"""
import pathlib
import re
import shutil

BACKUP = pathlib.Path("_backup_parche")


def leer(ruta):
    return ruta.read_text(encoding="utf-8")


def guardar(ruta, texto):
    copia = BACKUP / ruta
    if not copia.exists():
        copia.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ruta, copia)
    ruta.write_text(texto, encoding="utf-8")


def literal(texto, nombre, viejo, nuevo, marcador):
    if marcador in texto:
        print(f"  [YA APLICADO] {nombre}")
        return texto
    n = texto.count(viejo)
    if n != 1:
        print(f"  [NO APLICADO] {nombre}: se esperaba 1 coincidencia y hay {n}")
        return texto
    print(f"  [OK] {nombre}")
    return texto.replace(viejo, nuevo)


def regex(texto, nombre, patron, nuevo, marcador):
    if marcador in texto:
        print(f"  [YA APLICADO] {nombre}")
        return texto
    n = len(list(re.finditer(patron, texto, flags=re.S)))
    if n != 1:
        print(f"  [NO APLICADO] {nombre}: se esperaba 1 coincidencia y hay {n}")
        return texto
    print(f"  [OK] {nombre}")
    return re.sub(patron, lambda m: nuevo, texto, count=1, flags=re.S)


# ---------------------------------------------------------------------------
# base.html
# ---------------------------------------------------------------------------
BLOQUE_SCRIPTS_BASE = """</script>
  <script src="{{ url_for('static', filename='css/js/core.js') }}"></script>
  <script src="{{ url_for('static', filename='css/js/evaluator.js') }}"></script>
  <script>
  """


def parchar_base():
    ruta = pathlib.Path("templates/base.html")
    print(f"\n{ruta}")
    if not ruta.exists():
        print("  [ERROR] No existe el archivo")
        return
    texto = leer(ruta)

    # B1: quitar las funciones duplicadas del <script> embebido y cargar los JS externos
    if "css/js/core.js" in texto:
        print("  [YA APLICADO] B1 scripts externos")
    else:
        ini = texto.find("let autoAiTimer = null;")
        fin = texto.find("function calcCarburo() {")
        if ini == -1 or fin == -1 or fin < ini:
            print("  [NO APLICADO] B1 scripts externos: no se encontraron los marcadores")
        else:
            texto = texto[:ini] + BLOQUE_SCRIPTS_BASE + texto[fin:]
            print("  [OK] B1 scripts externos (core.js y evaluator.js ahora sí se cargan)")

    # B2: el ajuste de Cobalto del asistente de fallas nunca se aplicaba
    texto = literal(
        texto, "B2 aplicar ajuste de Cobalto",
        "const modalEl = document.getElementById('modalTroubleshooting');",
        "if (adj.co) {\n"
        "      const elCo = document.getElementById('carburo_co');\n"
        "      if (elCo) elCo.value = adj.co;\n"
        "    }\n\n"
        "    const modalEl = document.getElementById('modalTroubleshooting');",
        "if (adj.co)",
    )
    guardar(ruta, texto)


# ---------------------------------------------------------------------------
# muelas.html
# ---------------------------------------------------------------------------
def parchar_muelas():
    ruta = pathlib.Path("templates/muelas.html")
    print(f"\n{ruta}")
    if not ruta.exists():
        print("  [ERROR] No existe el archivo")
        return
    texto = leer(ruta)

    # M1: el gráfico de pasadas buscaba un id que no existe
    texto = literal(
        texto, "M1 id del gráfico de pasadas",
        "getElementById('pasadasChartCanvas')",
        "getElementById('chartPasadasCanvas')",
        "getElementById('chartPasadasCanvas')",
    )

    # M2: exportar PNG salía vacío (canvas temporal fuera del DOM medía 0x0)
    texto = regex(
        texto, "M2 exportar PNG",
        r"const rect = canvas\.getBoundingClientRect\(\);\s*const dpr = window\.devicePixelRatio \|\| 1;",
        "const enDom = canvas.isConnected;\n"
        "    const rect = enDom ? canvas.getBoundingClientRect() : { width: width, height: height };\n"
        "    const dpr = enDom ? (window.devicePixelRatio || 1) : 1;",
        "canvas.isConnected",
    )

    # M3: mostrar Ancho de Labio (W) en Relief y ocultar pasadas cuando no es Fluting
    texto = literal(
        texto, "M3 campos según operación",
        "function actualizarVisibilidadControlesRueda() {",
        "function actualizarVisibilidadControlesRueda() {\n"
        "    // Relief usa Ancho de Labio (W); las demás operaciones usan Ancho de Rueda.\n"
        "    // Las pasadas de desbaste solo aplican al ranurado (fluting).\n"
        "    const opActual = getValStr('operacion', 'fluting');\n"
        "    const esRelief = (opActual === 'relief');\n"
        "    document.getElementById('group-ancho-w')?.classList.toggle('d-none', !esRelief);\n"
        "    document.getElementById('group-ancho')?.classList.toggle('d-none', esRelief);\n"
        "    document.getElementById('group-pasadas')?.classList.toggle('d-none', opActual !== 'fluting');",
        "const esRelief",
    )

    # M4: colorear Vs según su estado (antes siempre verde, incluso en "Alto")
    texto = regex(
        texto, "M4 color de velocidad Vs",
        r"if \(document\.getElementById\('est-vs'\)\) document\.getElementById\('est-vs'\)\.textContent = \"Estado: \" \+ json\.estado_vs;",
        "const estVsEl = document.getElementById('est-vs');\n"
        "        if (estVsEl) {\n"
        "            estVsEl.textContent = \"Estado: \" + json.estado_vs;\n"
        "            // Verde: en rango | Amarillo: bajo | Rojo: alto\n"
        "            const colorVs = /^Alto/.test(json.estado_vs) ? '#ff1744' : (/^Bajo/.test(json.estado_vs) ? '#ffea00' : '#4ade80');\n"
        "            estVsEl.style.setProperty('color', colorVs, 'important');\n"
        "            const resVsEl = document.getElementById('res-vs');\n"
        "            if (resVsEl) resVsEl.style.setProperty('color', colorVs, 'important');\n"
        "        }",
        "colorVs",
    )

    # M5: un campo vacío mandaba NaN y aparecía "Límite Físico Excedido"
    texto = literal(
        texto, "M5 no calcular con campos vacíos",
        "const res = await fetch('/api/calcular-rectificado', {",
        "const criticos = ['diametro_rueda', 'ancho_rueda', 'profundidad', 'avance', 'rpm'];\n"
        "        if (criticos.some(k => !Number.isFinite(data[k]))) return; // campo vacío: esperar\n\n"
        "        const res = await fetch('/api/calcular-rectificado', {",
        "criticos.some",
    )

    # M6: sincronizar contexto y evaluador tras cada cálculo
    texto = literal(
        texto, "M6 sincronizar contexto tras calcular",
        "actualizarGraficoPasadas(kw, pasadasVal, pct);",
        "actualizarGraficoPasadas(kw, pasadasVal, pct);\n\n"
        "        // Mantener el contexto y el evaluador al día aunque el valor lo haya cambiado el código\n"
        "        if (typeof capturarYGuardarContextoLocal === 'function') {\n"
        "            capturarYGuardarContextoLocal();\n"
        "            triggerAutoAI();\n"
        "        }",
        "capturarYGuardarContextoLocal === 'function'",
    )

    # M7: el canvas mostraba cursor "grab" pero no se podía arrastrar
    texto = literal(
        texto, "M7 arrastrar (pan) en el canvas",
        "document.getElementById('form-calc')?.addEventListener('submit', function(e) {",
        "(function habilitarPanM1() {\n"
        "    const cv = document.getElementById('wheelCanvas');\n"
        "    if (!cv) return;\n"
        "    let arrastrando = false, ultimoX = 0, ultimoY = 0;\n"
        "    cv.addEventListener('pointerdown', e => {\n"
        "        arrastrando = true; ultimoX = e.clientX; ultimoY = e.clientY;\n"
        "        cv.style.cursor = 'grabbing'; cv.setPointerCapture(e.pointerId);\n"
        "    });\n"
        "    cv.addEventListener('pointermove', e => {\n"
        "        if (!arrastrando) return;\n"
        "        panXM1 += e.clientX - ultimoX; panYM1 += e.clientY - ultimoY;\n"
        "        ultimoX = e.clientX; ultimoY = e.clientY;\n"
        "        renderWheelCanvas();\n"
        "    });\n"
        "    const soltar = () => { arrastrando = false; cv.style.cursor = 'grab'; };\n"
        "    cv.addEventListener('pointerup', soltar);\n"
        "    cv.addEventListener('pointercancel', soltar);\n"
        "})();\n\n"
        "document.getElementById('form-calc')?.addEventListener('submit', function(e) {",
        "habilitarPanM1",
    )
    guardar(ruta, texto)


if __name__ == "__main__":
    parchar_base()
    parchar_muelas()
    print("\nListo. Copias originales en _backup_parche/  |  Recarga el navegador con Ctrl+F5.")