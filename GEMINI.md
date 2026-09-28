
# TOOLMAKER CAM STUDIO - REGLAS DE CONTEXTO Y DESARROLLO LOCAL

## 1. IDENTIDAD Y VISIÓN DEL PROYECTO

- **Nombre:** ToolMaker CAM Studio
- **Propósito:** Software de nivel industrial PWA/Flask para ingenieros y operadores CNC (fresado, rectificado, brocas de carburo, muelas FEPA y recubrimientos PVD/CVD).
- **Filosofía Operativa:** 100% LOCAL, LIVIANO, DETERMINISTA Y OFFLINE.
- **Entorno de Red:** NO depende de APIs externas de IA ni llamadas a la nube. Toda evaluación o telemetría la procesa el **Motor Físico Interno en Python** (Kienzle, Taylor, Jaeger, Q'w, Iz, deflexión).

---

## 2. REGLAS ABSOLUTAS DE CODIFICACIÓN (DIRECTIVAS OBLIGATORIAS)

1. **CÓDIGO SIEMPRE COMPLETO:**

   - Queda estrictamente prohibido entregar snippets parciales, bloques con `// ... resto del código ...`, o funciones aisladas.
   - Cada respuesta que modifique un archivo debe entregar el **código íntegro y completo** del archivo afectado para copiar y reemplazar directamente.
2. **PROTECCIÓN DE LA LÓGICA FÍSICA Y MATEMÁTICA:**

   - Las ecuaciones físicas (fuerzas Kienzle, temperatura Shaw/Jaeger, tasa Q'w, inercia Iz, deflexión elástica) y los límites tolerados son intocables.
   - La estructura de respuesta de las APIs (`/api/calcular-rectificado`, `/api/calcular-geometria`, `/api/estimar-recubrimiento`, `/api/auto-evaluar`) debe mantener sus claves JSON exactas.
3. **CONSERVACIÓN RIGUROSA DEL DOM E IDENTIFICADORES:**

   - NUNCA renombrar ni eliminar `id`, `name`, variables JS, listeners ni selectores CSS existentes. Si se agregan funcionalidades, deben reutilizar o complementar la estructura previa.
4. **ESTÁNDAR VISUAL SLATE CYAN:**

   - Paleta industrial oscura basada en variables CSS de `base.html`:
     - `--slate-bg`: `#0b1120`
     - `--panel-bg`: `#111a36`
     - `--border-color`: `#334155`
     - `--cyan-accent`: `#38bdf8`
     - `--cyan-glow`: `#00f2fe`
5. **ARQUITECTURA DE 5 MÓDULOS ACTIVOS:**

   - La suite consta **exclusivamente de 5 módulos**:
     1. `/calculadora-muelas` (Módulo 1: Operaciones & Muelas)
     2. `/geometria-herramienta` (Módulo 2: Geometría de Fresas)
     3. `/geometria-brocas` (Módulo 3: Brocas de Carburo DIN 1412-C)
     4. `/catalogo-abrasivos` (Módulo 4: Biblioteca FEPA)
     5. `/recubrimientos` (Módulo 5: Recubrimientos PVD/CVD)
   - Está prohibido reintroducir el "Módulo 6", botones hacia librerías de OpenAI/Claude o menús obsoletos.

---

## 3. ARQUITECTURA TÉCNICA DEL PROYECTO

- **Servidor:** Python 3.10+ | Flask 3.0.0
- **Puerto Local:** `http://127.0.0.1:5001`
- **Plantillas:** Jinja2 + Bootstrap 5 + Chart.js + Three.js
- **Estructura de Carpetas:**
  ```text
  CNC-Master-toolmaker-v1/
  ├── GEMINI.md
  ├── app.py
  ├── requirements.txt
  ├── static/
  └── templates/
      ├── base.html
      ├── muelas.html
      ├── geometria.html
      ├── brocas.html
      ├── abrasivos.html
      └── recubrimientos.html
  ```
