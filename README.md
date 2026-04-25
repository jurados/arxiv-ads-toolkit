# arXiv Agent & NASA ADS Toolkit

Conjunto de herramientas avanzadas para la automatización de la literatura científica y construcción de matrices bibliográficas. Diseñado para investigadores especializados en **supernovas, transientes, Machine Learning/Deep Learning aplicado y multimodalidad**.

Esta herramienta centraliza la potencia de la API de **NASA ADS** en una interfaz web moderna y una potente suite de comandos (CLI), permitiendo el monitoreo diario de **arXiv** y la gestión inteligente de bibliografía.

---

## 🚀 Funcionalidades Principales

### 🌐 Interfaz Web (app.py)
Una aplicación Flask completa para gestionar toda tu investigación desde el navegador:
- **Modo Oscuro/Claro** y soporte bilingüe (**Español/Inglés**).
- **Traducción instantánea** de abstracts (vía Google Translate).
- **Visualización interactiva de grafos**: Mapeo visual de cadenas de referencias con `vis.js`.
- **Gestión de Descargas**: Descarga directa de PDFs de acceso abierto.
- **Paper-to-Code**: Detección automática de repositorios de código (GitHub, GitLab, PapersWithCode, PyPI) analizando abstracts, comentarios y agradecimientos.
- **Exportación flexible**: Generación de matrices en **CSV** y archivos **BibTeX** listos para LaTeX.
- **Configuración en caliente**: Edita palabras clave y categorías directamente desde la interfaz, con botón "Restaurar valores por defecto".
- **Panel de Comparación (⚖️)**: Compara dos papers en paralelo — referencias comunes, citaciones cruzadas y diferencias de impacto.
- **Badges DOI y arXiv**: Cada tarjeta muestra el DOI (enlace a doi.org) y el ID de arXiv (enlace a arxiv.org) detectados automáticamente.
- **Botón scroll-to-top**: Aparece al bajar en la página y vuelve al inicio con un clic.
- **Número de WhatsApp editable**: Cambia el destinatario del agente diario directamente desde la interfaz sin tocar el código.

### 🤖 Agente Diario (arXiv → WhatsApp)
- Monitoreo automático de nuevos papers en arXiv con envío por WhatsApp.
- Dry-run desde la interfaz web: previsualiza los papers del día con badges de año, tipo y citaciones.
- Ventana de búsqueda configurable (`hours_back`) desde el panel web.
- Generación de digest diario en HTML guardado en `digests/`.

### 🛠 Herramientas NASA ADS (CLI)
- `ads-search`: Búsquedas precisas por autor (incluyendo filtro de primer autor).
- `ads-topics`: Búsqueda semántica por conceptos o frases exactas.
- `ads-references` / `ads-citations`: Extracción de redes de citas hacia atrás y hacia adelante.
- `ads-similar`: Encuentra trabajos relacionados mediante similitud semántica de ADS o análisis de texto.
- `ads-chain`: Rastreo de referencias en múltiples niveles para mapear el "árbol genealógico" de una idea.
- `ads-download`: Automatización de descargas de PDFs (priorizando arXiv sobre paywalls), con descarga batch y metadata en una sola llamada a la API.

---

## 💻 Instalación y Configuración

### Requisitos
- Python 3.10+
- **NASA ADS Token**: Consíguelo gratis en [ADS Settings](https://ui.adsabs.harvard.edu/user/settings/token).

### Setup
```bash
git clone https://github.com/jurados/arxiv-ads-toolkit
cd arxiv-ads-toolkit
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuración
Crea un archivo `.env` en la raíz:
```env
ADS_TOKEN=tu_token_aqui
```

---

## 📖 Uso Rápido

### Lanzar Interfaz Web
```bash
./run_web.sh
# Acceso en: http://localhost:5000
```

### Construir una Matriz de Literatura (CLI)
Todas las herramientas aceptan el flag `--export` para acumular resultados en un CSV sin duplicados.
Los filtros de año soportan rangos abiertos:
```bash
# Ejemplos de filtros de año
ads-search "Forster, Francisco" --year 2022         # año exacto
ads-topics "supernova" --year 2020-2023             # rango cerrado
ads-citations "bibcode" --year 2022-                # desde 2022 en adelante
ads-references "bibcode" --year -2020               # hasta 2020

# Unir búsquedas en una sola matriz
ads-search "Forster, Francisco" --year 2022-2026 --export mi_matriz.csv
ads-topics "supernova classification" --rows 20 --export mi_matriz.csv
```

---

## 📊 Matriz de Literatura
El sistema genera un archivo `literatura.csv` con columnas pre-formateadas:
- **Datos de ADS**: bibcode, título, año, primer autor, URL.
- **Campos de Análisis**: método, hallazgo principal, relevancia, notas (para completar en Excel/Google Sheets).

---

## 📜 Licencia
MIT
