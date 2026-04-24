# arXiv Agent & NASA ADS Toolkit

Conjunto de herramientas para un astrónomo especializado en supernovas, transientes, ML/DL y multimodalidad. Cubre monitoreo automático de papers y construcción de matrices de literatura.

---

## Estructura del proyecto

```
arxiv-agent/
├── main.py            # Agente diario arXiv → WhatsApp
├── fetcher.py         # Consulta API de arXiv y filtra papers
├── notifier.py        # Traduce abstracts y envía por WhatsApp
├── config.py          # Keywords, categorías y configuración
├── run.sh             # Wrapper para el cron job
├── ads_search.py      # Buscar papers por autor en NASA ADS
├── ads_topics.py      # Buscar papers por concepto/frase
├── ads_references.py  # Extraer referencias de un paper
├── ads_citations.py   # Ver quién cita un paper
├── ads_similar.py     # Encontrar papers similares
├── ads_chain.py       # Cadena de referencias multinivel
├── ads_download.py    # Descargar PDFs de acceso abierto
├── exporter.py        # Módulo compartido de exportación CSV
├── requirements.txt   # Dependencias Python
├── .env               # API keys (privado, nunca subir a git)
├── .gitignore         # Excluye .env y venv/
└── venv/              # Entorno virtual Python aislado
```

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

## 1. Agente diario de arXiv → WhatsApp

Todos los días busca papers nuevos en arXiv y los envía por WhatsApp con el abstract traducido al español.

### Categorías monitoreadas

| Código | Descripción |
|---|---|
| `astro-ph.HE` | High Energy Astrophysical Phenomena (supernovas, GRBs) |
| `astro-ph.SR` | Solar and Stellar Astrophysics |
| `astro-ph.IM` | Instrumentation and Methods for Astrophysics |
| `cs.LG` | Machine Learning |

### Palabras clave

**Supernovas:** `supernova`, `supernovae`, `core-collapse`, `Type Ia`, `SN Ia`, `SLSN`, `superluminous supernova`

**Transientes:** `transient`, `fast transient`, `kilonova`, `GRB`, `gamma-ray burst`, `FBOT`

**ML/DL:** `machine learning supernova`, `deep learning supernova`, `neural network transient`, `classification transient`

**Multimodalidad:** `multimodal astronomy`, `multimodal astrophysics`, `foundation model astronomy`

### Formato del mensaje de WhatsApp

```
🔭 arXiv Daily — 2026-04-24
📄 6 paper(s) nuevo(s) en supernovas, transientes y ML
──────────────────────────────

*[1/6] Título original en inglés*

Abstract traducido al español...

👥 Autor 1, Autor 2, Autor 3
📅 2026-04-23 15:06 UTC
🔗 http://arxiv.org/abs/2604.21759v1
```

### Programación (cron job)

Corre dos veces al día. Si el envío de las 10:00 fue exitoso, el de las 15:00 se omite. Si el PC estaba apagado a las 10:00, el de las 15:00 actúa como respaldo.

```
0 14 * * *  /home/jurados/arxiv-agent/run.sh >> agent.log 2>&1   # 10:00 AM Chile
0 19 * * *  /home/jurados/arxiv-agent/run.sh >> agent.log 2>&1   # 15:00 PM Chile
```

El archivo `.last_run` registra la fecha del último envío para evitar duplicados.

### Ejecución manual

```bash
/home/jurados/arxiv-agent/venv/bin/python main.py --dry-run  # sin enviar
/home/jurados/arxiv-agent/venv/bin/python main.py            # real
cat /home/jurados/arxiv-agent/agent.log                      # ver logs
```

### Personalización

Edita `config.py` para cambiar `WHATSAPP_NUMBER`, `KEYWORDS`, `CATEGORIES` u `HOURS_BACK`.

---

## 2. Herramientas NASA ADS

Todas requieren `ADS_TOKEN` en `.env`. Token gratuito en `https://ui.adsabs.harvard.edu/user/settings/token`.

Todas aceptan `--export archivo.csv` para acumular resultados en una matriz de literatura.

### Opciones comunes

| Opción | Aplica a | Descripción |
|---|---|---|
| `--year 2023` | todos | Filtrar por año exacto |
| `--year 2020-2023` | todos | Filtrar por rango de años |
| `--export matriz.csv` | todos | Exportar resultados a CSV |
| `--rows N` | todos | Número máximo de resultados |

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

Ejemplo: `2022_Frster_DELIGHT.pdf`

**Verificación de paywall:** si la respuesta no empieza con `%PDF`, el archivo se descarta (evita guardar páginas HTML de error).

**Opciones:**

| Opción | Default | Descripción |
|---|---|---|
| `--dir` | `~/Downloads` | Directorio de descarga |
| `--from-csv` | — | Descargar todos los papers de un CSV |

**Ejemplos reales:**
```bash
ads-download "2022AJ....164..195F"
# Directorio de descarga: /home/jurados/Downloads
#   ↓ [EPRINT_PDF] DELIGHT: Deep Learning Identification of Galaxy Hosts o
#   ✓ Guardado: 2022_Förster_DELIGHT.pdf (2276 KB)

ads-download "2301.07688" --dir /tmp/papers
#   ↓ [EPRINT_PDF] The Eighteenth Data Release of the Sloan Digital Sky Su
#   ✓ Guardado: 2023_Almeida_Eighteenth.pdf (2581 KB)
```

---

## Credenciales requeridas (`.env`)

```
ADS_TOKEN=tu_token_nasa_ads
```

- **NASA ADS token** (gratuito): `https://ui.adsabs.harvard.edu/user/settings/token`
