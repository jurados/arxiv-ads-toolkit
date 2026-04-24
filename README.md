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
- **Exportación flexible**: Generación de matrices en **CSV** y archivos **BibTeX** listos para LaTeX.
- **Configuración en caliente**: Edita palabras clave y categorías directamente desde la interfaz.

### 🤖 Agente Diario (arXiv → WhatsApp)
- Monitoreo automático de nuevas publicaciones en categorías seleccionadas.
- Filtrado por palabras clave inteligentes (Supernovas, Transientes, ML, Multimodalidad).
- Envío de notificaciones diarias vía **WhatsApp** con abstracts traducidos.

### 🛠 Herramientas NASA ADS (CLI)
- `ads-search`: Búsquedas precisas por autor (incluyendo filtro de primer autor).
- `ads-topics`: Búsqueda semántica por conceptos o frases exactas.
- `ads-references` / `ads-citations`: Extracción de redes de citas hacia atrás y hacia adelante.
- `ads-similar`: Encuentra trabajos relacionados mediante similitud semántica de ADS o análisis de texto.
- `ads-chain`: Rastreo de referencias en múltiples niveles para mapear el "árbol genealógico" de una idea.
- `ads-download`: Automatización de descargas de PDFs (priorizando arXiv sobre paywalls).

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
Todas las herramientas aceptan el flag `--export` para acumular resultados en un CSV sin duplicados:
```bash
# Ejemplo: Unir búsquedas de autor y tema en una sola matriz
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
