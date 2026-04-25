# arXiv Agent & NASA ADS Toolkit

Conjunto de herramientas para un astrónomo especializado en supernovas, transientes, ML/DL y multimodalidad. Cubre monitoreo automático de papers y construcción de matrices de literatura.

---

## Estructura del proyecto

```
arxiv-agent/
├── main.py            # Agente diario arXiv → WhatsApp
├── fetcher.py         # Consulta API de arXiv y filtra papers
├── notifier.py        # Traduce abstracts y envía por WhatsApp
├── digester.py        # Genera digest diario en HTML (digests/)
├── config.py          # Keywords, categorías y configuración
├── run.sh             # Wrapper para el cron job (con bridge check)
├── app.py             # Interfaz web Flask (todas las herramientas ADS)
├── run_web.sh         # Script para arrancar la interfaz web (con bridge check)
├── templates/
│   └── index.html     # Frontend de la app web (dark/light, ES/EN)
├── digests/           # Digest HTML diario (digest_YYYY-MM-DD.html)
├── summary.html       # Documentación HTML generada desde este archivo
├── utils.py           # Utilidades compartidas: is_arxiv_id, pubdate_filter
├── ads_search.py      # Buscar papers por autor en NASA ADS
├── ads_topics.py      # Buscar papers por concepto/frase
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

Todas las herramientas NASA ADS están disponibles desde un navegador. Incluye modo oscuro/claro, interfaz en español e inglés, y traducción de abstracts al español con un clic.

### Iniciar la app

```bash
/home/jurados/arxiv-agent/run_web.sh
# → http://localhost:5000
```

### Funcionalidades

| Característica | Detalle |
|---|---|
| Herramientas disponibles | ads-search, ads-topics, ads-references, ads-citations, ads-similar, ads-chain, ads-download |
| Modo oscuro / claro | Toggle en la barra superior |
| Idioma ES / EN | Toggle instantáneo sin recargar |
| Traducir abstract | Botón 🌐 en cada resultado (Google Translate, sin API key) |
| Selección de papers | Checkboxes por paper + "Seleccionar todos" |
| Exportar CSV | Solo papers seleccionados; descarga `literatura.csv` |
| Exportar BibTeX | Solo papers seleccionados; descarga `references.bib` vía NASA ADS |
| Descargar PDF | El PDF se descarga directamente desde el navegador |
| Paginación | 20 papers por página con navegación anterior/siguiente |
| Ordenar por año | Botones ↑ / ↓ en cualquier resultado; preserva selección al cambiar página |
| Badge de citas | Número de citas de NASA ADS mostrado en cada tarjeta |
| Badge arXiv | ID de arXiv detectado desde bibcode o campo `identifier`; enlaza a arxiv.org |
| Badge DOI | DOI del paper (campo `doi` de ADS); enlaza a doi.org |
| Paper-to-Code | Detección automática de repositorios (GitHub/GitLab/PyPI) en abstracts y comentarios |
| Grafo de cadena | Visualización interactiva de la cadena de referencias con vis.js |
| Digests guardados | Lista de digests HTML diarios accesibles desde el panel del agente |
| Panel de configuración | Editar categorías, keywords, hours_back y max_results sin tocar el código |
| Restaurar valores por defecto | Botón en el panel de configuración que restablece las keywords originales |
| Panel Comparar (⚖️) | Compara dos papers: referencias comunes, citaciones cruzadas, totales |
| Editor número WhatsApp | Cambiar el número destinatario del agente directamente desde la UI |
| arXiv → ADS | El dry-run resuelve cada paper arXiv en NASA ADS: bibcode, citas, PDF directo |
| Scroll-to-top | Botón flotante que aparece al bajar; vuelve al inicio del panel `.main` |
| Footer de paper | Orden: Traducir → PDF → Code → Bibcode → DOI → Refs → Citas → arXiv |

### Rutas de la API

| Ruta | Método | Descripción |
|---|---|---|
| `/` | GET | Interfaz web principal |
| `/api/search` | POST | ads-search |
| `/api/topics` | POST | ads-topics |
| `/api/references` | POST | ads-references |
| `/api/citations` | POST | ads-citations |
| `/api/similar` | POST | ads-similar (modo bibcode o texto) |
| `/api/chain` | POST | ads-chain (devuelve papers + edges para el grafo) |
| `/api/download` | POST | ads-download (devuelve el PDF) |
| `/api/download_batch` | POST | Descarga batch con metadata en una sola llamada a ADS |
| `/api/compare` | POST | Compara dos papers: refs/citas comunes (paralelo con ThreadPoolExecutor) |
| `/api/translate` | POST | Traduce un texto al español |
| `/api/export_csv` | POST | CSV de papers seleccionados |
| `/api/export_bibtex` | POST | BibTeX de papers seleccionados vía NASA ADS |
| `/api/arxiv/resolve` | POST | Resuelve IDs arXiv a bibcodes de ADS (batch) |
| `/api/arxiv/bibtex_arxiv` | GET | BibTeX de un paper directamente desde arXiv |
| `/api/arxiv/dryrun` | GET | Dry-run del agente; retorna `hours_back` y lista de papers |
| `/api/config` | GET | Lee `config.py` y devuelve sus valores |
| `/api/config/save` | POST | Escribe `config.py` y recarga el módulo en caliente |
| `/api/config/whatsapp` | POST | Actualiza `WHATSAPP_NUMBER` en `config.py` |
| `/api/arxiv/digests` | GET | Lista los digests HTML guardados en `digests/` |
| `/api/arxiv/digest` | GET | Sirve el contenido de un digest específico |

---

## Alias disponibles (después de `source ~/.bashrc`)

| Comando | Descripción |
|---|---|
| `ads-search` | Buscar papers por autor |
| `ads-topics` | Buscar papers por concepto o frase |
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

Los rangos de año son gestionados centralmente por `utils.pubdate_filter()`, compartido por todos los módulos `ads_*.py`.

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

**Ejemplos reales:**
```bash
ads-search "Forster, Francisco" --year 2022 --first-author
# → 2 resultado(s) | solo primer autor
# [01] DELIGHT: Deep Learning Identification of Galaxy Hosts...
```

---

### `ads-topics` — Buscar por concepto o frase

Busca la frase de forma exacta en título y/o abstract. Frases muy largas pueden dar 0 resultados — usar menos palabras.

```bash
ads-topics "supernova classification"
ads-topics "kilonova" --year 2024
ads-topics "supernova classification" --year 2024-2026 --rows 10
ads-topics "core collapse" --field abstract --rows 30
ads-topics "multimodal astronomy" --field title --export matriz.csv
```

**Opciones exclusivas:** `--field title|abstract|all` (dónde buscar, default: `all`)

---

### `ads-references` — Extraer referencias de un paper

Dado un bibcode o ID de arXiv, muestra todos los papers que ese trabajo cita.

```bash
ads-references "2022AJ....164..195F"              # bibcode
ads-references "2301.07688"                       # arXiv ID
ads-references "2022AJ....164..195F" --year 2018-2022
ads-references "2022AJ....164..195F" --export matriz.csv
```

---

### `ads-citations` — Ver quién cita un paper

Inverso de `ads-references`: muestra los papers que citan al trabajo dado.

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

Dos modos: similitud semántica real de ADS (por bibcode) o búsqueda por keywords extraídos de un texto.

```bash
# Modo bibcode — similitud semántica de ADS
ads-similar --bibcode "2022AJ....164..195F"
ads-similar --bibcode "2022AJ....164..195F" --year 2020-2026 --rows 15

# Modo texto — pega un párrafo de tu paper
ads-similar --text "We use a recurrent neural network to classify supernovae light curves"
ads-similar --text "tu párrafo aquí" --year 2022-2026 --rows 20

# Modo archivo — escribe tu abstract en un .txt
ads-similar --file mi_abstract.txt --export matriz.csv
```

---

### `ads-chain` — Cadena de referencias multinivel

Rastrea las referencias de un paper nivel por nivel. Útil para mapear el árbol genealógico de una idea.

**Advertencia:** crece exponencialmente. Usar `--max-per-level` para controlarlo.

```bash
ads-chain "2022AJ....164..195F"                                   # 2 niveles (default)
ads-chain "2022AJ....164..195F" --levels 3
ads-chain "2022AJ....164..195F" --levels 4 --max-per-level 5
ads-chain "2022AJ....164..195F" --levels 3 --year 2018-2026
ads-chain "2022AJ....164..195F" --levels 3 --export cadena.csv
```

**Opciones exclusivas:**

| Opción | Default | Descripción |
|---|---|---|
| `--levels` | 2 | Niveles de profundidad |
| `--max-per-level` | 10 | Máx. papers a expandir por nivel |
| `--rows` | 30 | Máx. referencias a buscar por paper |

**Guía de parámetros:**

| Objetivo | `--levels` | `--max-per-level` |
|---|---|---|
| Vista rápida | 2 | 5 |
| Revisión estándar | 2 | 20 |
| Búsqueda profunda | 3 | 10 |
| Árbol completo | 4+ | 5 |

El CSV generado incluye una columna `level` para saber a qué profundidad se encontró cada paper.

---

## Exportación CSV — Matriz de Literatura

Todos los scripts de NASA ADS aceptan `--export archivo.csv`. Las búsquedas se acumulan en el mismo archivo sin duplicar papers.

### Columnas del CSV

| Columna | Fuente | Descripción |
|---|---|---|
| `bibcode` | NASA ADS | Identificador único |
| `title` | NASA ADS | Título del paper |
| `year` | NASA ADS | Año de publicación |
| `doctype` | NASA ADS | Tipo (article, thesis, book) |
| `first_author` | NASA ADS | Primer autor |
| `url` | NASA ADS | Enlace web en ADS |
| `method` | tú | Técnica o método usado |
| `key_finding` | tú | Hallazgo principal |
| `relevance` | tú | Relevancia para tu paper |
| `notes` | tú | Notas libres |
| `level` | ads-chain | Nivel de profundidad (solo en cadena) |

### Flujo típico para construir una matriz

```bash
source ~/.bashrc

# 1. Papers de un autor clave
ads-search "Apellido, Nombre" --year 2018-2026 --export mi_matriz.csv

# 2. Papers sobre el tema central
ads-topics "mi concepto principal" --rows 30 --export mi_matriz.csv

# 3. Referencias de un paper seminal
ads-references "bibcode_seminal" --export mi_matriz.csv

# 4. Quién cita ese paper (trabajos recientes)
ads-citations "bibcode_seminal" --year 2022-2026 --export mi_matriz.csv

# 5. Papers similares a tu abstract
ads-similar --file mi_abstract.txt --export mi_matriz.csv

# 6. Árbol de referencias en profundidad
ads-chain "bibcode_seminal" --levels 3 --export mi_matriz.csv

# Abrir en Excel / Google Sheets y completar las columnas vacías
```

---

### `ads-download` — Descargar PDFs de acceso abierto

Dado un bibcode o ID de arXiv, descarga el PDF usando los links de acceso abierto de NASA ADS. Prioriza arXiv (siempre gratuito) sobre otras fuentes. También puede descargar todos los papers de un CSV.

```bash
# Paper individual por bibcode
ads-download "2022AJ....164..195F"

# Paper individual por arXiv ID
ads-download "2208.04310"

# Elegir directorio de descarga
ads-download "2022AJ....164..195F" --dir ~/papers

# Descargar todos los papers de la matriz
ads-download --from-csv mi_matriz.csv

# Descargar matriz en un directorio específico
ads-download --from-csv mi_matriz.csv --dir ~/papers/matriz
```

**Prioridad de fuentes (de más a menos confiable):**

| Fuente | Tipo | Acceso |
|---|---|---|
| `EPRINT_PDF` | arXiv PDF | Siempre gratuito |
| `ADS_PDF` | PDF alojado en ADS | Gratuito |
| `ADS_SCAN` | Escaneo digitalizado | Gratuito |
| `PUB_PDF` | PDF del publisher | Puede requerir suscripción |

**Nombre de archivo generado:** `YYYY_PrimerApellido_PrimeraPalabraTitulo.pdf`

---

## Credenciales requeridas (`.env`)

```
ADS_TOKEN=tu_token_nasa_ads
```

- **NASA ADS token** (gratuito): `https://ui.adsabs.harvard.edu/user/settings/token`
