from pathlib import Path

# ===== Base paths =====
PROJECT_DIR = Path(__file__).resolve().parents[1]   # .../HSMT
DATA_DIR = PROJECT_DIR / "Data"

# ===== Files =====
HSMT_EXCEL_FILE = DATA_DIR / "GT39.xlsx"

# ===== Sheet names =====
SHEET_TTD = "TTD"
SHEET_TTD_FULL_SPECS = "TTD-Full-specs"