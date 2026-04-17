# -*- coding: utf-8 -*-
import re
import unicodedata
import pandas as pd
from rapidfuzz import fuzz, process

# ----------------------------
# 0. Utilities xử lý văn bản
# ----------------------------
INVISIBLE_CHARS = [
    "\u200b", "\u200c", "\u200d", "\ufeff", "\u2060", "\u00A0"
]

def strip_invisible(s: str) -> str:
    if not s:
        return ""
    for ch in INVISIBLE_CHARS:
        s = s.replace(ch, " ")
    return s

def normalize_text(text: str) -> str:
    """
    Chuẩn hoá "mềm": hạ chữ thường, NFC -> NFD -> bỏ dấu, loại ký tự ko chữ/số,
    dồn khoảng trắng. Dùng cho so khớp. KHÔNG dùng để hiển thị.
    """
    if text is None:
        return ""
    text = str(text)
    # normalize unicode & loại kí tự vô hình
    text = unicodedata.normalize("NFC", text)
    text = strip_invisible(text).strip()
    text = text.lower()
    # chuyển sang NFD để tách dấu rồi bỏ dấu
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # chuẩn hoá một số ký hiệu phổ biến
    text = text.replace("–", "-").replace("—", "-").replace("–", "-")
    text = text.replace("/", " ").replace("\\", " ")
    # bỏ ký tự không phải chữ/số/space/_
    text = re.sub(r"[^\w\s-]", " ", text)
    # dồn khoảng trắng
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def normalize_for_display(text: str) -> str:
    """
    Chuẩn hoá "nhẹ" để hiển thị/ghi file: loại kí tự vô hình, dồn space, giữ nguyên dấu.
    """
    if text is None:
        return ""
    text = str(text)
    text = unicodedata.normalize("NFC", text)
    text = strip_invisible(text).strip()
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ----------------------------
# 1. Chuẩn hoá ĐVT
# ----------------------------
UNIT_MAP = {
    # phổ biến
    "cai": "cái", "cái": "cái",
    "bo": "bộ", "bô": "bộ", "bộ": "bộ",
    "kg": "kg", "kilogram": "kg", "kilôgam": "kg",
    "g": "g", "gram": "g", "gam": "g",
    "lit": "lít", "l": "lít", "lít": "lít",
    "m": "m", "met": "m", "mét": "m",
    "mm": "mm", "cm": "cm",
    "m2": "m²", "m^2": "m²", "m²": "m²",
    "m3": "m³", "m^3": "m³", "m³": "m³",
    "thung": "thùng", "thùng": "thùng",
    "chai": "chai", "hop": "hộp", "hộp": "hộp",
    "thietbi": "thiết bị", "tb": "thiết bị",
    "bo doi": "bộ",  # phòng hờ
}

def normalize_unit(u: str) -> str:
    if not u:
        return ""
    u_disp = normalize_for_display(u).lower()
    u_key = normalize_text(u)  # bỏ dấu để tìm map
    u_key = u_key.replace(".", "").replace("-", " ")
    u_key = re.sub(r"\s+", " ", u_key).strip()
    if u_key in UNIT_MAP:
        return UNIT_MAP[u_key]
    # các pattern m2/m3
    rep = u_disp.replace("^2", "²").replace("^3", "³")
    rep = rep.replace("m2", "m²").replace("m3", "m³")
    return rep

# ----------------------------
# 2. Chuẩn hoá/Filter TSKT
# ----------------------------
NOISE_PATTERNS = [
    r"^na$", r"^n/a$", r"^khong ro$", r"^khong co$", r"^trong$",
    r"^none$", r"^null$", r"^$", r"^.$"
]
NOISE_REGEXES = [re.compile(p) for p in NOISE_PATTERNS]

def is_noise_text(norm_text: str) -> bool:
    if not norm_text:
        return True
    t = norm_text.strip()
    for rx in NOISE_REGEXES:
        if rx.match(t):
            return True
    return False

UNIT_INSIDE_TEXT_MAP = {
    r"\bm\^2\b": "m²",
    r"\bm\^3\b": "m³",
    r"\bm2\b": "m²",
    r"\bm3\b": "m³",
    r"\bl\b": "lít",
}

def standardize_tskt(ts: str) -> str:
    """
    Chuẩn hoá thông số kỹ thuật: loại noise, chuẩn hoá các đơn vị viết trong chuỗi.
    """
    ts = normalize_for_display(ts)
    ts_norm = normalize_text(ts)

    if is_noise_text(ts_norm):
        return ""

    # thay đơn vị trong chuỗi
    out = ts
    for pat, repl in UNIT_INSIDE_TEXT_MAP.items():
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)

    # gom khoảng trắng
    out = re.sub(r"\s+", " ", out).strip()
    return out

# ----------------------------
# 3. Làm sạch DataFrame master Excel
# ----------------------------
REQUIRED_COLS = {
    "Mã vật tư": "Ma",
    "Tên vật tư": "Ten",
    "Mã hiệu/Thông số kỹ thuật": "TSKT",
    "ĐVT": "DVT",
}

def validate_and_align_columns(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLS.keys() if c not in df.columns]
    if missing:
        raise ValueError(f"Thiếu cột bắt buộc trong Excel: {missing}")
    # chỉ chọn các cột cần để tránh rác
    return df[list(REQUIRED_COLS.keys())].copy()

def build_full_norm(ten: str, tskt: str) -> str:
    t = normalize_text(ten)
    s = normalize_text(tskt)
    return normalize_text(f"{t} {s}").strip()

def clean_master_df(df_raw: pd.DataFrame, log=print, fuzzy_dedup=True, fuzzy_threshold=92):
    """
    Trả về df đã làm sạch + cột Full_Norm, giảm trùng lặp.
    """
    df = validate_and_align_columns(df_raw)

    # Chuẩn hoá hiển thị cơ bản
    for col in df.columns:
        df[col] = df[col].astype(str).map(normalize_for_display)

    # Chuẩn hoá sâu
    df["DVT"] = df["ĐVT"].map(normalize_unit)
    df["Ten"] = df["Tên vật tư"].map(lambda x: re.sub(r"\s+", " ", x).strip())
    df["TSKT"] = df["Mã hiệu/Thông số kỹ thuật"].map(standardize_tskt)

    # Loại dòng trống tên
    df = df[df["Ten"].str.len() > 0].copy()

    # Full_Norm
    df["Full_Norm"] = df.apply(lambda r: build_full_norm(r["Ten"], r["TSKT"]), axis=1)

    # Dedup 1: theo Mã vật tư (nếu có mã)
    if "Mã vật tư" in df.columns:
        before = len(df)
        df = df.sort_values(by=["Mã vật tư", "Ten", "TSKT"]).drop_duplicates(subset=["Mã vật tư"], keep="first")
        after = len(df)
        if before != after:
            log(f"🧹 Đã loại {before - after} dòng trùng theo 'Mã vật tư'.")

    # Dedup 2: theo (Ten + TSKT)
    before = len(df)
    df = df.drop_duplicates(subset=["Ten", "TSKT"], keep="first")
    after = len(df)
    if before != after:
        log(f"🧹 Đã loại {before - after} dòng trùng theo (Tên, TSKT).")

    # Dedup 3 (tuỳ chọn): fuzzy cluster theo Full_Norm
    if fuzzy_dedup and len(df) > 1:
        log("🔎 Đang gom cụm gần giống (fuzzy) để giảm trùng…")
        # tạo danh sách
        norms = df["Full_Norm"].tolist()
        # chọn seed theo thứ tự, loại phần tử có similarity cao > threshold
        kept_idx = []
        removed = set()
        for i, base in enumerate(norms):
            if i in removed:
                continue
            kept_idx.append(i)
            # so với phần sau
            candidates = process.extract(base, norms[i+1:], scorer=fuzz.token_set_ratio, limit=50)
            for (cand, score, rel_idx) in candidates:
                j = i + 1 + rel_idx
                if score >= fuzzy_threshold:
                    removed.add(j)
        mask = [idx in kept_idx for idx in range(len(norms))]
        before = len(df)
        df = df[mask].copy().reset_index(drop=True)
        after = len(df)
        if after < before:
            log(f"🧹 Fuzzy dedup loại {before - after} bản ghi gần giống (ngưỡng {fuzzy_threshold}).")

    # Chuẩn hoá lại cột hiển thị cuối
    df["Ma"] = df["Mã vật tư"].astype(str).map(normalize_for_display)
    df["DVT"] = df["DVT"].map(normalize_for_display)
    df["Ten"] = df["Ten"].map(normalize_for_display)
    df["TSKT"] = df["TSKT"].map(normalize_for_display)

    # Giữ các cột cần thiết
    out = df[["Ma", "Ten", "TSKT", "DVT", "Full_Norm"]].copy()
    out = out.reset_index(drop=True)
    return out

# ----------------------------
# 4. Làm sạch danh sách items (tách từ Word)
# ----------------------------
def clean_items(items: list, log=print):
    """
    items: list[ {stt, ten, tskt, dvt} ]
    Trả ra danh sách đã được làm sạch + loại rỗng.
    """
    cleaned = []
    for it in items:
        stt = normalize_for_display(it.get("stt", ""))
        ten_raw = it.get("ten", "")
        tskt_raw = it.get("tskt", "")
        dvt_raw = it.get("dvt", "")

        ten = normalize_for_display(ten_raw)
        tskt = standardize_tskt(tskt_raw)
        dvt = normalize_unit(dvt_raw)

        # Bỏ dòng thiếu tên
        if not ten.strip():
            continue

        cleaned.append({
            "stt": stt,
            "ten": ten,
            "tskt": tskt,
            "dvt": dvt,
            "query_norm": build_full_norm(ten, tskt)
        })

    # Dedup items theo (ten, tskt) để tránh khớp lặp vô ích (không bắt buộc)
    seen = set()
    deduped = []
    for it in cleaned:
        key = (normalize_text(it["ten"]), normalize_text(it["tskt"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(it)

    removed = len(cleaned) - len(deduped)
    if removed > 0:
        log(f"🧹 Loại {removed} dòng vật tư lặp (trích từ Word).")

    return deduped