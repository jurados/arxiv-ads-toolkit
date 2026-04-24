# Número de WhatsApp que recibirá los mensajes (sin + ni espacios)
WHATSAPP_NUMBER = "56934202808"

# Categorías de arXiv a monitorear
# astro-ph.HE = High Energy Astrophysical Phenomena (supernovas, GRBs, etc.)
# astro-ph.SR = Solar and Stellar Astrophysics
# astro-ph.IM = Instrumentation and Methods for Astrophysics
# cs.LG      = Machine Learning
CATEGORIES = ["astro-ph.HE", "astro-ph.SR", "astro-ph.IM", "cs.LG"]

# Palabras clave para filtrar papers relevantes
# Se buscan en el título O en el abstract
KEYWORDS = [
    # Supernovas
    "supernova", "supernovae", "core-collapse",
    "Type Ia", "SN Ia", "SLSN", "superluminous supernova",
    # Transientes
    "transient", "fast transient", "kilonova",
    "GRB", "gamma-ray burst", "FBOT",
    # ML/DL aplicado
    "machine learning supernova", "deep learning supernova",
    "neural network transient", "classification transient",
    # Multimodalidad
    "multimodal astronomy", "multimodal astrophysics",
    "foundation model astronomy",
]

# Cuántos papers máximo traer por consulta
MAX_RESULTS = 50

# Cuántas horas hacia atrás buscar papers nuevos (24 = papers del último día)
HOURS_BACK = 24
