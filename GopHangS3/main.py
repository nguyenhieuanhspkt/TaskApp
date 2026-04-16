# =====================================================
# FULL CODE – HOÀN CHỈNH
# GROUP ID INCREMENTAL (1,2,3,…)
# ✅ MÃ GIÁ LẤY NGUYÊN BẢN TỪ CỘT R (EXCEL)
# ✅ LỌC BỎ DÒNG TỔNG GIÁ TRỊ (CỘT O) = 0 TRƯỚC KHI GROUP ID
# =====================================================

import pandas as pd
from pathlib import Path

# ================== PATH ==================
BASE_PATH = Path(
    r"D:\onedrive_hieuna\OneDrive - EVN\Tổ Thẩm định\Năm 2026\Thẩm định 127_hieuna_3"
)
INPUT_FILE = BASE_PATH / "PL1_Dự toán Trung tu tổ máy S3 năm 2026_Phần tổ máy_492.xlsx"
OUTPUT_FILE = BASE_PATH / "PL1_5_VAT_TU_GROUPED.xlsx"
SHEET_NAME = "PL1.5 DT VẬT TƯ TM"

# ================== READ RAW ==================
df_raw = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME, header=None)

# ================== FLATTEN HEADER (ROW 4–5) ==================
header_rows = df_raw.iloc[3:5].copy()
header_rows = header_rows.ffill(axis=0).infer_objects(copy=False)

new_columns = (
    header_rows.astype(str)
    .apply(lambda c: " ".join(x.strip() for x in c if x and x.strip() != "nan"), axis=0)
)

df = df_raw.iloc[5:].copy()
df.columns = new_columns
df.reset_index(drop=True, inplace=True)
df.columns = df.columns.str.strip().str.replace(r"\s+", " ", regex=True)
df = df.loc[:, df.columns != ""]

# ================== LẤY MÃ GIÁ NGUYÊN BẢN TỪ CỘT R ==================
# Cột R = index 17 (theo Excel)
df["Mã giá"] = df_raw.iloc[5:, 17].reset_index(drop=True)

# ================== STANDARDIZE COLUMN NAMES ==================
df = df.rename(columns={
    "Tên Vật tư Tên Vật tư": "Tên vật tư",
    "ĐVT ĐVT": "Đơn vị tính",
    "Mua mới": "Số lượng",
    "Dự kiến mua mới": "Đơn giá",
    "Tổng cộng": "Tổng Giá trị (cột O)",
    "P.KTAT ghi chú": "Ghi chú",
})

# ================== AUTO FIND THÀNH TIỀN MUA SẮM MỚI ==================
tt_cols = [c for c in df.columns if "THÀNH TIỀN" in c.upper() and "DỰ KIẾN" in c.upper()]
if tt_cols:
    df = df.rename(columns={tt_cols[0]: "Thành tiền mua sắm mới"})
else:
    df["Thành tiền mua sắm mới"] = df.get("Tổng Giá trị (cột O)", 0)

# ================== SELECT FINAL COLUMNS ==================
FINAL_COLS = [
    "Tên vật tư",
    "Đơn vị tính",
    "Số lượng",
    "Đơn giá",
    "Thành tiền mua sắm mới",
    "Tổng Giá trị (cột O)",
    "Mã giá",
    "Ghi chú",
]

df_clean = df[[c for c in FINAL_COLS if c in df.columns]].copy()
df_clean = df_clean.loc[:, ~df_clean.columns.duplicated()]

# ================== CAST NUMERIC ==================
for col in ["Số lượng", "Đơn giá", "Thành tiền mua sắm mới", "Tổng Giá trị (cột O)"]:
    if col in df_clean.columns:
        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0)

# ================== LỌC BỎ TỔNG GIÁ TRỊ = 0 ==================
df_clean = df_clean[df_clean["Tổng Giá trị (cột O)"] != 0].reset_index(drop=True)

# ================== CREATE INCREMENTAL GROUP ID ==================
group_key_cols = ["Tên vật tư", "Đơn vị tính", "Đơn giá"]

df_clean["_group_key"] = (
    df_clean[group_key_cols].astype(str).agg("|".join, axis=1)
)

group_map = {k: i + 1 for i, k in enumerate(df_clean["_group_key"].drop_duplicates())}
df_clean["Group ID"] = df_clean["_group_key"].map(group_map)
df_clean.drop(columns=["_group_key"], inplace=True)

# ================== SHEET BEFORE GROUP ==================
df_before = df_clean[
    [
        "Tên vật tư",
        "Đơn vị tính",
        "Số lượng",
        "Đơn giá",
        "Thành tiền mua sắm mới",
        "Tổng Giá trị (cột O)",
        "Mã giá",
        "Ghi chú",
        "Group ID",
    ]
].copy()

# ================== SHEET AFTER GROUP ==================
group_cols = ["Group ID", "Mã giá", "Tên vật tư", "Đơn vị tính"]

df_grouped = (
    df_clean.groupby(group_cols, dropna=False)
    .agg(
        Don_gia_list=("Đơn giá", lambda x: sorted(set(x))),
        Đơn_giá=("Đơn giá", "min"),
        Số_lượng=("Số lượng", "sum"),
        Thành_tiền=("Thành tiền mua sắm mới", "sum"),
        Tổng_O=("Tổng Giá trị (cột O)", "sum"),
    )
    .reset_index()
)

df_grouped["Ghi chú"] = df_grouped["Don_gia_list"].apply(
    lambda x: "có nhiều đơn giá" if len(x) > 1 else ""
)

df_grouped = df_grouped.drop(columns=["Don_gia_list"]).rename(columns={
    "Đơn_giá": "Đơn giá",
    "Thành_tiền": "Thành tiền mua sắm mới",
    "Tổng_O": "Tổng Giá trị (cột O)",
})

# ================== CHECK TOTAL ==================
print("TOTAL BEFORE:", round(df_before["Tổng Giá trị (cột O)"].sum(), 0))
print("TOTAL AFTER :", round(df_grouped["Tổng Giá trị (cột O)"].sum(), 0))
print("DIFF        :", round(
    df_before["Tổng Giá trị (cột O)"].sum()
    - df_grouped["Tổng Giá trị (cột O)"].sum(), 0)
)

# ================== EXPORT ==================
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    df_before.to_excel(writer, sheet_name="PL1.5_ORIGINAL", index=False)
    df_grouped.to_excel(writer, sheet_name="PL1.5_GROUPED", index=False)

print("DONE:", OUTPUT_FILE)