# arXiv Agent & NASA ADS Toolkit

Conjunto de herramientas para un astrónomo especializado en supernovas, transientes, ML/DL y multimodalidad. Cubre monitoreo automático de papers y construcción de matrices de literatura.

---

## Estructura del proyecto

```
arxiv-agent/
├── main.py            # Agente diario arXiv → WhatsApp
├── fetcher.py         # Consulta API de arXiv y filtra papers
├── notifier.py        # Traduce abstracts y envía por WhatsApp (con reintentos)
├── digester.py        # Genera digest diario en HTML + Markdown (digests/)
├── config.py          # Keywords, categorías y configuración
├── run.sh             # Wrapper para el cron job (con bridge check)
├── app.py             # Interfaz web Flask (todas las herramientas ADS)
├── run_web.sh         # Script para arrancar la interfaz web (con bridge check)
├── utils.py           # Módulo central: ADS_TOKEN, ADS_API, STOP_WORDS,
│                      #   fetch_arxiv_doc, arxiv_to_bibcode, is_arxiv_id,
│                      #   pubdate_filter
├── templates/
│   └── index.html     # Frontend de la app web (dark/light, ES/EN, favicon SVG)
├── digests/           # Digests diarios (digest_YYYY-MM-DD.html + .md)
├── summary.md         # Este archivo — documentación técnica completa
├── summary.html       # Versión HTML de la documentación
├── ads_search.py      # Buscar papers por autor en NASA ADS
├── ads_topics.py      # Buscar papers por concepto/frase/ID/título completo
├── ads_references.py  # Extraer referencias de un paper
├── ads_citations.py   # Ver quién cita un paper
├── ads_similar.py     # Encontrar papers similares
├── ads_chain.py       # Cadena de referencias multinivel
├── ads_download.py    # Descargar PDFs + get_papers_metadata_batch
├── exporter.py        # Módulo compartido de exportación CSV
├── requirements.txt   # Dependencias Python
├── .env               # API keys (privado, nunca subir a git)
├── .gitignore         # Excluye .env y venv/
└── venv/              # Entorno virtual Python aislado
```

---

## 0. Interfaz web (app.py)

Todas las herramientas NASA ADS están disponibles desde un navegador. Incluye modo oscuro/claro, interfaz en español e inglés, favicon SVG personalizado y traducción de abstracts al español con un clic.

### Iniciar la app

```bash
/home/jurados/arxiv-agent/run_web.sh
# → http://localhost:5000
```

### Funcionalidades

| Característica | Detalle |
|---|---|
| Herramientas disponibles | ads-search, ads-topics, ads-references, ads-citations, ads-similar, ads-chain, ads-download |
| Modo oscuro / claro | Toggle en la barra superior, persiste en localStorage |
| Idioma ES / EN | Toggle instantáneo sin recargar, persiste en localStorage |
| Favicon | SVG personalizado incrustado (orbital azul, sin archivos externos) |
| Traducir abstract | Botón 🌐 en cada resultado (Google Translate, sin API key) |
| Selección de papers | Checkboxes por paper + "Seleccionar todos" |
| Exportar CSV | Solo papers seleccionados; descarga `literatura.csv` |
| Exportar BibTeX | Descarga o copia al portapapeles (arXiv o ADS) sin necesidad de guardar archivo |
| Descargar PDF | El PDF se descarga directamente desde el navegador |
| Descarga batch | Hasta 15 papers a la vez; muestra advertencia si hay más seleccionados |
| Paginación | 20 papers por página con navegación anterior/siguiente |
| Ordenar por citas | Botones ↑ / ↓ en cualquier resultado; preserva selección al cambiar página |
| Badge de citas | Número de citas de NASA ADS mostrado en cada tarjeta |
| Badge arXiv | ID de arXiv detectado; enlaza directamente a arxiv.org |
| Badge DOI | DOI del paper; enlaza a doi.org |
| Paper-to-Code | Detección automática de repositorios (GitHub/GitLab/PyPI) en abstracts |
| Grafo de cadena | Visualización interactiva de la cadena de referencias con vis.js |
| Navegación cruzada | Botones → Refs, → Citas, ≈ Similar en cada tarjeta para saltar de panel |
| Digests guardados | Lista de digests HTML + MD diarios accesibles desde el panel del agente |
| Borrar digest | Botón 🗑 por digest; elimina .html y .md simultáneamente |
| Panel de configuración | Editar categorías, keywords, hours_back y max_results sin tocar el código |
| Restaurar valores | Botón en el panel de configuración que restablece las keywords originales |
| Panel Comparar (⚖️) | Compara dos papers: referencias comunes, citaciones cruzadas, totales |
| Editor número WhatsApp | Cambiar el número destinatario del agente directamente desde la UI |
| arXiv → ADS | El dry-run resuelve cada paper arXiv en NASA ADS: bibcode, citas, PDF directo |
| Scroll-to-top | Botón flotante que aparece al bajar; vuelve al inicio del panel |
| Búsqueda por autor desde tarjeta | Click en el nombre de un autor busca todos sus papers |

### Rutas de la API

| Ruta | Método | Descripción |
|---|---|---|
| `/` | GET | Interfaz web principal |
| `/api/search` | POST | ads-search (por autor) |
| `/api/topics` | POST | ads-topics (por concepto, título, identificador) |
| `/api/references` | POST | ads-references |
| `/api/citations` | POST | ads-citations |
| `/api/similar` | POST | ads-similar (modo bibcode o texto) |
| `/api/chain` | POST | ads-chain (devuelve papers + edges para el grafo) |
| `/api/download` | POST | ads-download (devuelve el PDF) |
| `/api/download_batch` | POST | Descarga batch con metadata; header `X-Truncated` si >15 |
| `/api/compare` | POST | Compara dos papers: refs/citas comunes (paralelo con ThreadPoolExecutor) |
| `/api/translate` | POST | Traduce un texto al español |
| `/api/export_csv` | POST | CSV de papers seleccionados |
| `/api/export_bibtex` | POST | BibTeX de papers seleccionados vía NASA ADS |
| `/api/arxiv/bibtex_arxiv` | GET | BibTeX de un paper directamente desde arXiv |
| `/api/arxiv/resolve` | POST | Resuelve IDs arXiv a bibcodes de ADS (batch, usa `fetch_arxiv_doc`) |
| `/api/arxiv/dryrun` | GET | Dry-run del agente; retorna `hours_back` y lista de papers |
| `/api/config` | GET | Lee `config.py` y devuelve sus valores |
| `/api/config/save` | POST | Escribe `config.py` y recarga el módulo en caliente |
| `/api/config/whatsapp` | POST | Actualiza `WHATSAPP_NUMBER` en `config.py` |
| `/api/arxiv/digests` | GET | Lista digests con `{name, has_md}` |
| `/api/arxiv/digest` | GET | Sirve el contenido de un digest (HTML o MD con `?fmt=md`) |
| `/api/arxiv/digest` | DELETE | Elimina un digest (.html y .md si existe) |
| `/api/arxiv/status` | GET | Estado del agente (último envío, keywords, categorías) |
| `/api/arxiv/logs` | GET | Últimas líneas del log del agente |
| `/api/matrix` | GET | Carga un CSV como matriz de literatura |
| `/api/matrix/save` | POST | Guarda cambios de la matriz en disco |
| `/api/shutdown` | POST | Apaga el servidor Flask |

---

## Módulo central: `utils.py`

Único punto de verdad para las constantes y funciones compartidas por todos los módulos `ads_*.py` y `app.py`.

```python
from utils import (
    ADS_TOKEN,        # Bearer token de NASA ADS
    ADS_API,          # URL base de la API ADS
    STOP_WORDS,       # Set de ~100 palabras vacías (gramaticales + científicas genéricas)
    fetch_arxiv_doc,  # Resuelve arXiv ID → dict ADS (fl configurable)
    arxiv_to_bibcode, # Wrapper: arXiv ID → bibcode (verbose=False para uso silencioso)
    is_arxiv_id,      # Detecta si un string tiene formato arXiv (YYMM.NNNNN)
    pubdate_filter,   # Convierte año/"2020-2023"/"2020-" a filtro ADS pubdate:[...]
)
```

**`fetch_arxiv_doc(arxiv_id, fl="bibcode,title")`** — función base que hace la llamada HTTP a ADS; `arxiv_to_bibcode` la usa internamente. `api_arxiv_resolve` también la usa directamente con `fl="bibcode,citation_count"`.

---

## Alias disponibles (después de `source ~/.bashrc`)

| Comando | Descripción |
|---|---|
| `ads-search` | Buscar papers por autor |
| `ads-topics` | Buscar papers por concepto, frase, título completo o identificador |
| `ads-references` | Extraer referencias de un paper |
| `ads-citations` | Ver quién cita un paper |
| `ads-similar` | Encontrar papers similares |
| `ads-chain` | Cadena de referencias multinivel |
| `ads-download` | Descargar PDFs de acceso abierto |

---

## 1. Herramientas NASA ADS

Todas requieren `ADS_TOKEN` en `.env`. Token gratuito en `https://ui.adsabs.harvard.edu/user/settings/token`.

Todas aceptan `--export archivo.csv` para acumular resultados en una matriz de literatura.

### Opciones comunes

| Opción | Aplica a | Descripción |
|---|---|---|
| `--year 2023` | todos | Filtrar por año exacto |
| `--year 2020-2023` | todos | Filtrar por rango cerrado |
| `--year 2022-` | todos | Desde 2022 en adelante (rango abierto) |
| `--year -2020` | todos | Hasta 2020 (rango abierto) |
| `--export matriz.csv` | todos | Exportar resultados a CSV |
| `--rows N` | todos | Número máximo de resultados |

Los rangos de año son gestionados centralmente por `utils.pubdate_filter()`.

---

### `ads-search` — Buscar por autor

```bash
ads-search "Apellido, Nombre"
ads-search "Apellido, Nombre" --year 2023
ads-search "Apellido, Nombre" --year 2020-2023
ads-search "Apellido, Nombre" --first-author
ads-search "Apellido, Nombre" --year 2022 --first-author --export matriz.csv
```

**Opciones exclusivas:** `--first-author` (solo papers donde es primer autor)

---

### `ads-topics` — Buscar por concepto, frase o identificador

Busca en título y/o abstract. Soporta cinco modos de campo (`--field`):

| Modo | Descripción |
|---|---|
| `all` (default) | Frase exacta en título **o** abstract |
| `title` | Frase exacta solo en título |
| `abstract` | Frase exacta solo en abstract |
| `title-words` | Términos individuales en título (ignora stopwords; útil para títulos completos) |
| `identifier` | Lookup directo: arXiv ID, DOI (`10.xxxx/...`) o bibcode ADS |

```bash
ads-topics "supernova classification"
ads-topics "kilonova" --year 2024
ads-topics "supernova classification" --year 2024-2026 --rows 10
ads-topics "core collapse" --field abstract --rows 30
ads-topics "multimodal astronomy" --field title --export matriz.csv

# Buscar por título completo (evita 0 resultados por stopwords en modo phrase)
ads-topics "Optical and Ultraviolet Observations of the Very Young Type IIP SN 2014cx" --field title-words

# Buscar por identificador
ads-topics "2301.07688" --field identifier          # arXiv ID
ads-topics "2022AJ....164..195F" --field identifier  # bibcode ADS
ads-topics "10.3847/1538-3881/ac8a9b" --field identifier  # DOI
```

---

### `ads-references` — Extraer referencias de un paper

```bash
ads-references "2022AJ....164..195F"              # bibcode
ads-references "2301.07688"                       # arXiv ID
ads-references "2022AJ....164..195F" --year 2018-2022
ads-references "2022AJ....164..195F" --export matriz.csv
```

---

### `ads-citations` — Ver quién cita un paper

```bash
ads-citations "2022AJ....164..195F"
ads-citations "2022AJ....164..195F" --year 2024-2026
ads-citations "2022AJ....164..195F" --rows 50 --export matriz.csv
```

```
ads-references  →  ¿en qué se basó este paper?   (hacia atrás)
ads-citations   →  ¿quién construyó sobre él?     (hacia adelante)
```

---

### `ads-similar` — Encontrar papers similares

Dos modos. En modo texto, `extract_keywords` preserva acrónimos en mayúsculas (GRB, SLSN, ZTF, FBOT…) antes de normalizar el texto, mejorando la precisión de la búsqueda.

```bash
# Modo bibcode — similitud semántica real de ADS
ads-similar --bibcode "2022AJ....164..195F"
ads-similar --bibcode "2022AJ....164..195F" --year 2020-2026 --rows 15

# Modo texto — extrae keywords del párrafo
ads-similar --text "We use a recurrent neural network to classify supernovae light curves"
ads-similar --text "GRB afterglow classification using ZTF photometry" --year 2022-2026

# Modo archivo
ads-similar --file mi_abstract.txt --export matriz.csv
```

El paper semilla se excluye automáticamente de los resultados en modo bibcode.

---

### `ads-chain` — Cadena de referencias multinivel

```bash
ads-chain "2022AJ....164..195F"                                   # 2 niveles (default)
ads-chain "2022AJ....164..195F" --levels 3
ads-chain "2022AJ....164..195F" --levels 4 --max-per-level 5
ads-chain "2022AJ....164..195F" --levels 3 --export cadena.csv
```

| Opción | Default | Descripción |
|---|---|---|
| `--levels` | 2 | Niveles de profundidad |
| `--max-per-level` | 10 | Máx. papers a expandir por nivel |
| `--rows` | 30 | Máx. referencias a buscar por paper |

| Objetivo | `--levels` | `--max-per-level` |
|---|---|---|
| Vista rápida | 2 | 5 |
| Revisión estándar | 2 | 20 |
| Búsqueda profunda | 3 | 10 |
| Árbol completo | 4+ | 5 |

---

### `ads-download` — Descargar PDFs de acceso abierto

```bash
ads-download "2022AJ....164..195F"              # bibcode
ads-download "2208.04310"                       # arXiv ID
ads-download "2022AJ....164..195F" --dir ~/papers
ads-download --from-csv mi_matriz.csv
ads-download --from-csv mi_matriz.csv --dir ~/papers/matriz
```

| Fuente | Tipo | Acceso |
|---|---|---|
| `EPRINT_PDF` | arXiv PDF | Siempre gratuito |
| `ADS_PDF` | PDF alojado en ADS | Gratuito |
| `ADS_SCAN` | Escaneo digitalizado | Gratuito |
| `PUB_PDF` | PDF del publisher | Puede requerir suscripción |

**Nombre de archivo generado:** `YYYY_PrimerApellido_PrimeraPalabraTitulo.pdf`

---

## Exportación CSV — Matriz de Literatura

Todos los scripts aceptan `--export archivo.csv`. Las búsquedas se acumulan en el mismo archivo sin duplicar bibcodes.

### Columnas del CSV

| Columna | Fuente | Descripción |
|---|---|---|
| `bibcode` | NASA ADS | Identificador único |
| `title` | NASA ADS | Título del paper |
| `year` | NASA ADS | Año de publicación |
| `doctype` | NASA ADS | Tipo (article, thesis, book) |
| `first_author` | NASA ADS | Primer autor |
| `url` | NASA ADS | Enlace web en ADS |
| `method` | usuario | Técnica o método usado |
| `key_finding` | usuario | Hallazgo principal |
| `relevance` | usuario | Relevancia para tu paper |
| `notes` | usuario | Notas libres |
| `level` | ads-chain | Nivel de profundidad (solo en cadena) |

### Flujo típico para construir una matriz

```bash
source ~/.bashrc

ads-search "Apellido, Nombre" --year 2018-2026 --export mi_matriz.csv
ads-topics "mi concepto" --rows 30 --export mi_matriz.csv
ads-references "bibcode_seminal" --export mi_matriz.csv
ads-citations "bibcode_seminal" --year 2022-2026 --export mi_matriz.csv
ads-similar --file mi_abstract.txt --export mi_matriz.csv
ads-chain "bibcode_seminal" --levels 3 --export mi_matriz.csv
# Abrir en Excel / Google Sheets y completar las columnas vacías
```

---

## 2. Agente arXiv Diario

Busca papers nuevos en arXiv, genera un digest HTML + Markdown y los envía por WhatsApp.

### Ejecución

```bash
python main.py             # ejecución normal
python main.py --dry-run   # muestra papers sin enviar nada
/home/jurados/arxiv-agent/run.sh  # usado por cron
```

### Flujo

1. `fetcher.py` consulta la API de arXiv para las categorías en `config.py`
2. Filtra por keywords (sin límite; usa `MAX_RESULTS` como tope de resultados)
3. `digester.py` genera `digests/digest_YYYY-MM-DD.html` y `.md`
4. `notifier.py` traduce y envía por WhatsApp (3 reintentos con 2 s de pausa)
5. Guarda fecha en `.last_run` para no reenviar el mismo día

### Configuración (`config.py`)

```python
CATEGORIES  = ["astro-ph.HE", "astro-ph.SR", "astro-ph.IM", "cs.LG"]
KEYWORDS    = ["supernova", "GRB", "kilonova", "SLSN", ...]
MAX_RESULTS = 50    # tope de papers por ejecución
HOURS_BACK  = 72    # ventana de búsqueda en horas
```

Editable desde la interfaz web (panel Configuración) sin tocar el código.

---

## Credenciales requeridas (`.env`)

```
ADS_TOKEN=tu_token_nasa_ads
```

- **NASA ADS token** (gratuito): `https://ui.adsabs.harvard.edu/user/settings/token`
