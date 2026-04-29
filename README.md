# arXiv Agent & NASA ADS Toolkit

Conjunto de herramientas para un astrónomo especializado en supernovas, transientes, ML/DL y multimodalidad. Centraliza la API de **NASA ADS** en una interfaz web moderna y una suite CLI, con monitoreo diario automático de **arXiv**.

---

## Funcionalidades principales

### Interfaz web (`app.py`)

- **11 paneles**: Search, Topics, References, Citations, Similar, Chain, Download, Compare, Matrix, Agent, Config
- Modo oscuro/claro y soporte bilingüe ES/EN (persisten en localStorage)
- Favicon SVG personalizado incrustado
- Traducción de abstracts con un clic (Google Translate, sin API key)
- Exportación en **CSV** y **BibTeX** (descarga o copia al portapapeles)
- Descarga directa de PDFs (individual o batch de hasta 15 papers)
- **Paper-to-Code**: detecta automáticamente repos GitHub/GitLab/PyPI en abstracts
- **Badges** de citas, arXiv y DOI en cada tarjeta; navegación cruzada entre paneles (→ Refs, → Citas, ≈ Similar)
- **Grafo interactivo** de cadenas de referencias (vis.js)
- **Panel Compare**: referencias y citas en común entre dos papers (paralelo con ThreadPoolExecutor)
- Digests diarios en HTML + Markdown con borrado individual desde la UI
- Configuración en caliente: keywords, categorías y horas de búsqueda sin tocar el código

### Herramientas CLI (`ads-*`)

| Comando | Descripción |
|---|---|
| `ads-search` | Buscar papers por autor (con `--first-author`) |
| `ads-topics` | Buscar por concepto, frase, título completo o identificador (arXiv/DOI/bibcode) |
| `ads-references` | Referencias de un paper (hacia atrás) |
| `ads-citations` | Quién cita un paper (hacia adelante) |
| `ads-similar` | Papers similares por bibcode o texto libre |
| `ads-chain` | Cadena de referencias multinivel con grafo |
| `ads-download` | Descargar PDFs de acceso abierto |

Todas aceptan `--year`, `--rows` y `--export archivo.csv` para acumular resultados en una **matriz de literatura** sin duplicados.

### Agente arXiv diario

Busca papers nuevos en arXiv, genera un digest HTML + Markdown y los envía por WhatsApp (3 reintentos automáticos). Ejecutado por cron; dry-run disponible desde la UI.

---

## Instalación

```bash
git clone https://github.com/jurados/arxiv-ads-toolkit
cd arxiv-ads-toolkit
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Crea `.env` en la raíz:

```env
ADS_TOKEN=tu_token_aqui
```

Token gratuito en [ui.adsabs.harvard.edu/user/settings/token](https://ui.adsabs.harvard.edu/user/settings/token).

---

## Uso rápido

```bash
# Interfaz web
./run_web.sh
# → http://localhost:5000

# CLI — construir una matriz de literatura
ads-search "Forster, Francisco" --year 2020-2026 --export mi_matriz.csv
ads-topics "supernova classification" --rows 20 --export mi_matriz.csv
ads-topics "2301.07688" --field identifier           # buscar por arXiv ID
ads-topics "Optical Observations of SN 2014cx" --field title-words  # título completo
ads-references "2022AJ....164..195F" --export mi_matriz.csv
ads-similar --file mi_abstract.txt --export mi_matriz.csv
ads-chain "2022AJ....164..195F" --levels 3 --export mi_matriz.csv

# Agente diario
python main.py --dry-run
```

---

## Módulo central `utils.py`

Único punto de verdad para todos los módulos `ads_*.py` y `app.py`:

```python
from utils import (
    ADS_TOKEN, ADS_API, STOP_WORDS,
    fetch_arxiv_doc,   # arXiv ID → dict ADS (fl configurable)
    arxiv_to_bibcode,  # arXiv ID → bibcode
    is_arxiv_id,       # detecta formato YYMM.NNNNN
    pubdate_filter,    # "2020-2023" → filtro ADS pubdate:[...]
)
```

---

## Documentación completa

Ver [`summary.md`](summary.md) o abrir [`summary.html`](summary.html) en el navegador.

---

## Licencia

MIT
