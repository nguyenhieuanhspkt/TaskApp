import pandas as pd
from config import (
    HSMT_EXCEL_FILE,
    SHEET_TTD,
    SHEET_TTD_FULL_SPECS,
)

def main():
    if not HSMT_EXCEL_FILE.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {HSMT_EXCEL_FILE}")

    print("✅ Đã tìm thấy file:", HSMT_EXCEL_FILE)

    # Đọc danh sách sheet
    xls = pd.ExcelFile(HSMT_EXCEL_FILE, engine="openpyxl")
    print("📄 Các sheet trong file:")
    for s in xls.sheet_names:
        print(" -", s)

    # Đọc sheet TTD
    df_ttd = pd.read_excel(HSMT_EXCEL_FILE, sheet_name=SHEET_TTD)
    print("✅ Sheet TTD:", df_ttd.shape)

    # Đọc sheet TTD-Full-specs
    df_full = pd.read_excel(
        HSMT_EXCEL_FILE,
        sheet_name=SHEET_TTD_FULL_SPECS,
        header=None
    )
    print("✅ Sheet Full specs:", df_full.shape)
    from processors.vlxd import is_vlxd

    df_full["IS_VLXD"] = df_full.apply(
        lambda r: is_vlxd(
            f"{str(r.get('Tên vật tư', ''))} {str(r.get('TSKT', ''))}"
        ),
        axis=1
    )

if __name__ == "__main__":
    
    main()