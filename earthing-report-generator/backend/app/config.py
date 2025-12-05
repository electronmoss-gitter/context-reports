"""
Global configuration for the earthing report generator
"""
import os
from pathlib import Path

# ============================================================
# EMBEDDING MODEL - Set this once, used everywhere
# ============================================================
# Options:
#   - "sentence-transformers/all-mpnet-base-v2" (768 dims, high quality)
#   - "sentence-transformers/all-MiniLM-L6-v2" (384 dims, faster, lower memory)
#   - "sentence-transformers/all-small-MiniLM-L12-v2" (384 dims, smallest)
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-mpnet-base-v2"
)

# ============================================================
# INGESTION SETTINGS
# ============================================================
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

# ============================================================
# VECTOR STORE SETTINGS
# ============================================================
VECTOR_STORE_PATH = os.getenv(
    "VECTOR_STORE_PATH",
    "./chroma_db"
)
VECTOR_STORE_COLLECTION = os.getenv(
    "VECTOR_STORE_COLLECTION",
    "earthing_reports"
)

# ============================================================
# DATA PATHS
# ============================================================
HISTORICAL_REPORTS_PATH = os.getenv(
    "HISTORICAL_REPORTS_PATH",
    "./data/historical_reports"
)
STANDARDS_PATH = os.getenv(
    "STANDARDS_PATH",
    "./data/standards"
)

# ============================================================
# LLM SETTINGS
# ============================================================
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

# ============================================================
# LOGGING
# ============================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")