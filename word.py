import sys, re
import numpy as np
import pandas as pd
from pathlib import Path
from docx import Document

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QProgressBar, QTextEdit, QMessageBox, QCheckBox, QSpinBox
)

# =========================
# 0) CORE: SMART SEARCH (CHẶT)
# =========================
STOPWORDS = set("""
vong dem lam kin su dung cho loai bo pos item no ban ve dinh kem
model hang nsx hoac tuong duong kich thuoc vat lieu
gasket bonnet seat packing phut chan bui gioang
""".split())

def norm(s: str) -> str:
    s = str(s).lower().replace("đ", "d")
    s = re.sub(r"[^a-z0-9\s\-\./x%]", " ", s)   # giữ chữ/số/-,.,/,x,%
    s = re.sub(r"\s+", " ", s).strip()
    return s

def norm_uom(s: str) -> str:
    return norm(s).replace(" ", "")

def tokens_filtered(text: str):
    t = norm(text)
    toks = [x for x in t.split() if x not in STOPWORDS and len(x) > 1]
    return set(toks)

def extract_model_tokens(text: str):
    t = norm(text)
    tokens = set(t.split())
    # token kiểu model: có chữ+số hoặc số+chữ
    return [tok for tok in tokens if re.search(r"[a-z]+\d|\d+[a-z]", tok)]

def extract_dim_tokens(text: str):
    t = norm(text)
    dims = re.findall(r"\b\d+(?:\.\d+)?\s*(?:mm|ml|l|kg|g|vac|vdc|bar|rpm|x)\b", t)
    return [norm(d) for d in dims]

def overlap_score(q_tokens, t_tokens):
    if not q_tokens:
        return 0.0
    return len(q_tokens & t_tokens) / len(q_tokens)

def classify_and_explain_strict(word_row, erp_row, score_val, th_strong=0.55, th_med=0.45):
    query = f"{word_row['Word_Tên']} {word_row['Word_Thông số']}"
    model_tokens = extract_model_tokens(query)
    dim_tokens = extract_dim_tokens(query)

    erp_comp = norm(" ".join([
        str(erp_row.get("Mã vật tư", "")),
        str(erp_row.get("Tên vật tư (NXT)", "")),
        str(erp_row.get("Thông số kỹ thuật", "")),
        str(erp_row.get("Diễn Giải", "")),
        str(erp_row.get("Đơn vị tính", "")),
    ]))

    model_hit = any(m in erp_comp.split() for m in model_tokens) if model_tokens else False
    dim_hit = any(d in erp_comp for d in dim_tokens) if dim_tokens else False

    if score_val < th_med:
        return ("Tạo mã mới",
                f"Điểm khớp thấp ({score_val:.2f} < {th_med}). Dù đã lọc ĐVT/model/dims, vẫn không đủ tương đồng để dùng lại mã ERP.")

    if model_tokens:
        if model_hit and score_val >= th_strong:
            return ("Khớp theo Model/Hãng",
                    "Đã lọc theo ĐVT + model; model/hãng xuất hiện trong dòng ERP và điểm khớp cao.")
        return ("Tương đương chức năng (cần duyệt)",
                "Có model trong Word nhưng điểm chưa đủ cao để chốt. Cần kiểm tra lại model/part-no/hãng trước khi dùng mã ERP.")

    if dim_tokens:
        if dim_hit and score_val >= th_strong:
            return ("Khớp theo Quy cách/Thông số",
                    "Đã lọc theo ĐVT + dims; thông số/kích thước trùng và điểm khớp cao.")
        return ("Tương đương chức năng (cần duyệt)",
                "Có thông số trong Word nhưng điểm chưa đủ cao để chốt. Cần đối chiếu lại kích thước/vật liệu/ứng dụng.")

    common = sorted(list(tokens_filtered(query) & tokens_filtered(erp_comp)))[:12]
    return ("Tương đương chức năng (cần duyệt)",
            "Không có model/dims rõ ràng; chỉ khớp theo nhóm/tên. Bắt buộc duyệt. Từ khóa trùng: " + ", ".join(common))

# =========================
# 1) WORKER THREAD
# =========================
class MappingWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, erp_path, word_path, out_path, strict=True, topk=3, th_strong=0.55, th_med=0.45):
        super().__init__()
        self.erp_path = erp_path
        self.word_path = word_path
        self.out_path = out_path
        self.strict = strict
        self.topk = topk
        self.th_strong = th_strong
        self.th_med = th_med

    def run(self):
        try:
            self.log.emit("Đang đọc file ERP Excel...")
            erp_df = pd.read_excel(self.erp_path, engine="openpyxl")
            self.log.emit(f"ERP rows: {erp_df.shape[0]}")

            self.log.emit("Đang đọc file Word...")
            doc = Document(self.word_path)

            items = []
            for table in doc.tables:
                for row in table.rows[1:]:
                    cells = [c.text.strip() for c in row.cells]
                    if len(cells) >= 4:
                        stt, ten, tskt, dvt = cells[0], cells[1], cells[2], cells[3]
                        if ten.strip() == "0" and tskt.strip() == "0":
                            continue
                        items.append({"Stt": stt, "Word_Tên": ten, "Word_Thông số": tskt, "Word_ĐVT": dvt})

            word_df = pd.DataFrame(items)
            if word_df.empty:
                raise ValueError("Không tìm thấy dòng vật tư hợp lệ trong file Word.")

            # Build corpus
            text_cols = [c for c in [
                "Mã vật tư", "Tên vật tư (NXT)", "Thông số kỹ thuật",
                "Diễn Giải", "Đơn vị tính", "Số Hợp Đồng/QĐ", "Kho"
            ] if c in erp_df.columns]

            if not text_cols:
                raise ValueError("File ERP không có các cột text để tìm kiếm (Mã vật tư/Tên vật tư/Thông số...).")

            self.log.emit("Đang tạo chỉ mục tìm kiếm (tokenize)...")
            erp_text = erp_df[text_cols].astype(str).agg(" ".join, axis=1).map(norm).to_numpy()
            erp_tokens = [set(t.split()) for t in erp_text]
            erp_tokens_f = [set([x for x in t.split() if x not in STOPWORDS and len(x) > 1]) for t in erp_text]

            # UoM
            uom_col = "Đơn vị tính" if "Đơn vị tính" in erp_df.columns else None
            erp_uom_norm = erp_df[uom_col].astype(str).map(norm_uom).to_numpy() if uom_col else None

            def best_match_strict(query: str, word_uom: str):
                q_tokens = tokens_filtered(query)
                model_tokens = extract_model_tokens(query)
                dim_tokens = extract_dim_tokens(query)

                n = len(erp_df)
                cand = np.arange(n)

                # FILTER UOM
                wu = norm_uom(word_uom)
                if erp_uom_norm is not None and wu:
                    cand = cand[erp_uom_norm[cand] == wu]

                # FILTER MODEL
                if model_tokens:
                    cand = np.array([i for i in cand if any(m in erp_tokens[i] for m in model_tokens)], dtype=int)

                # FILTER DIMS
                if dim_tokens:
                    cand = np.array([i for i in cand if any(d in erp_text[i] for d in dim_tokens)], dtype=int)

                if cand.size == 0:
                    return [], []

                scores = []
                for i in cand:
                    ov = overlap_score(q_tokens, erp_tokens_f[i])
                    model_bonus = 0.25 if (model_tokens and any(m in erp_tokens[i] for m in model_tokens)) else 0.0
                    dim_bonus = 0.15 if (dim_tokens and any(d in erp_text[i] for d in dim_tokens)) else 0.0
                    scores.append(ov + model_bonus + dim_bonus)

                scores = np.array(scores, dtype=float)
                order = scores.argsort()[::-1][: self.topk]
                top_idx = cand[order].tolist()
                top_sc = scores[order].tolist()
                return top_idx, top_sc

            def best_match_loose(query: str):
                # (Nếu bạn muốn chế độ thoáng sau này) — hiện không dùng
                q_tokens = tokens_filtered(query)
                model_tokens = extract_model_tokens(query)
                scores = np.zeros(len(erp_df), dtype=float)
                for i in range(len(erp_df)):
                    ov = overlap_score(q_tokens, erp_tokens_f[i])
                    bonus = 0.15 if model_tokens and any(m in erp_tokens[i] for m in model_tokens) else 0.0
                    scores[i] = ov + bonus
                best_i = int(scores.argmax())
                return [best_i], [float(scores[best_i])]

            rows = []
            total = len(word_df)

            for idx, w in word_df.iterrows():
                query = f"{w['Word_Tên']} {w['Word_Thông số']}"

                if self.strict:
                    top_idx, top_sc = best_match_strict(query, w["Word_ĐVT"])
                else:
                    top_idx, top_sc = best_match_loose(query)

                if not top_idx:
                    rows.append({
                        **w.to_dict(),
                        "ERP_Mã vật tư": "",
                        "ERP_Tên vật tư": "",
                        "ERP_Thông số": "",
                        "ERP_ĐVT": "",
                        "Điểm khớp": 0.00,
                        "Phân loại": "Tạo mã mới",
                        "Giải thích khớp": "Không có candidate thỏa điều kiện CHẶT (ĐVT + model nếu có + dims nếu có).",
                        "Top3_Gợi ý": ""
                    })
                else:
                    best_i = top_idx[0]
                    best_score = float(top_sc[0])
                    er = erp_df.iloc[best_i]

                    category, reason = classify_and_explain_strict(
                        w, er, best_score, th_strong=self.th_strong, th_med=self.th_med
                    )

                    top3_txt = []
                    for i, sc in zip(top_idx, top_sc):
                        r = erp_df.iloc[i]
                        top3_txt.append(f"{r.get('Mã vật tư','')} | {r.get('Tên vật tư (NXT)','')} | score={sc:.2f}")
                    top3_txt = "\n".join(top3_txt)

                    if category == "Tạo mã mới":
                        rows.append({
                            **w.to_dict(),
                            "ERP_Mã vật tư": "",
                            "ERP_Tên vật tư": "",
                            "ERP_Thông số": "",
                            "ERP_ĐVT": "",
                            "Điểm khớp": round(best_score, 2),
                            "Phân loại": category,
                            "Giải thích khớp": reason,
                            "Top3_Gợi ý": top3_txt
                        })
                    else:
                        rows.append({
                            **w.to_dict(),
                            "ERP_Mã vật tư": str(er.get("Mã vật tư", "")),
                            "ERP_Tên vật tư": str(er.get("Tên vật tư (NXT)", "")),
                            "ERP_Thông số": str(er.get("Thông số kỹ thuật", "")),
                            "ERP_ĐVT": str(er.get("Đơn vị tính", "")),
                            "Điểm khớp": round(best_score, 2),
                            "Phân loại": category,
                            "Giải thích khớp": reason,
                            "Top3_Gợi ý": top3_txt
                        })

                # progress
                pct = int((idx + 1) * 100 / total)
                self.progress.emit(pct)

            map_df = pd.DataFrame(rows)
            summary = map_df.groupby("Phân loại").size().reset_index(name="Số dòng")

            self.log.emit("Đang ghi file Excel output...")
            out_path = Path(self.out_path)
            with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
                map_df.to_excel(writer, index=False, sheet_name="Mapping")
                summary.to_excel(writer, index=False, sheet_name="Summary")

            self.finished.emit(str(out_path))

        except Exception as e:
            self.failed.emit(str(e))

# =========================
# 2) GUI
# =========================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mapping Word ↔ ERP (PyQt5) - CHẾ ĐỘ CHẶT")
        self.resize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # ERP file
        self.erp_edit = QLineEdit()
        btn_erp = QPushButton("Chọn ERP Excel...")
        btn_erp.clicked.connect(self.pick_erp)
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("ERP Excel (.xlsx):"))
        row1.addWidget(self.erp_edit)
        row1.addWidget(btn_erp)
        layout.addLayout(row1)

        # Word file
        self.word_edit = QLineEdit()
        btn_word = QPushButton("Chọn Word (.docx)...")
        btn_word.clicked.connect(self.pick_word)
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Word (.docx):"))
        row2.addWidget(self.word_edit)
        row2.addWidget(btn_word)
        layout.addLayout(row2)

        # Output
        self.out_edit = QLineEdit()
        btn_out = QPushButton("Chọn nơi lưu...")
        btn_out.clicked.connect(self.pick_out)
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Output (.xlsx):"))
        row3.addWidget(self.out_edit)
        row3.addWidget(btn_out)
        layout.addLayout(row3)

        # Options
        opt = QHBoxLayout()
        self.strict_cb = QCheckBox("Chế độ CHẶT (khuyến nghị)")
        self.strict_cb.setChecked(True)

        opt.addWidget(self.strict_cb)
        opt.addWidget(QLabel("Top gợi ý:"))
        self.topk_spin = QSpinBox()
        self.topk_spin.setRange(1, 10)
        self.topk_spin.setValue(3)
        opt.addWidget(self.topk_spin)

        opt.addWidget(QLabel("Ngưỡng chốt (STRONG):"))
        self.th_strong = QLineEdit("0.55")
        self.th_strong.setFixedWidth(60)
        opt.addWidget(self.th_strong)

        opt.addWidget(QLabel("Ngưỡng loại (MED):"))
        self.th_med = QLineEdit("0.45")
        self.th_med.setFixedWidth(60)
        opt.addWidget(self.th_med)

        opt.addStretch(1)
        layout.addLayout(opt)

        # Run
        self.run_btn = QPushButton("Chạy Mapping")
        self.run_btn.clicked.connect(self.run_mapping)
        layout.addWidget(self.run_btn)

        # Progress + log
        self.pb = QProgressBar()
        self.pb.setRange(0, 100)
        layout.addWidget(self.pb)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)

        self.worker = None

    def append_log(self, msg):
        self.log_box.append(msg)

    def pick_erp(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn ERP Excel", "", "Excel (*.xlsx)")
        if path:
            self.erp_edit.setText(path)

    def pick_word(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn Word", "", "Word (*.docx)")
        if path:
            self.word_edit.setText(path)

    def pick_out(self):
        path, _ = QFileDialog.getSaveFileName(self, "Lưu Output", "Mapping_Word_ERP.xlsx", "Excel (*.xlsx)")
        if path:
            if not path.lower().endswith(".xlsx"):
                path += ".xlsx"
            self.out_edit.setText(path)

    def run_mapping(self):
        erp_path = self.erp_edit.text().strip()
        word_path = self.word_edit.text().strip()
        out_path = self.out_edit.text().strip()

        if not erp_path or not Path(erp_path).exists():
            QMessageBox.warning(self, "Thiếu file", "Vui lòng chọn file ERP Excel hợp lệ.")
            return
        if not word_path or not Path(word_path).exists():
            QMessageBox.warning(self, "Thiếu file", "Vui lòng chọn file Word hợp lệ.")
            return
        if not out_path:
            QMessageBox.warning(self, "Thiếu output", "Vui lòng chọn nơi lưu output.")
            return

        try:
            th_strong = float(self.th_strong.text().strip())
            th_med = float(self.th_med.text().strip())
        except:
            QMessageBox.warning(self, "Sai ngưỡng", "Ngưỡng phải là số (vd 0.55 và 0.45).")
            return

        strict = self.strict_cb.isChecked()
        topk = int(self.topk_spin.value())

        self.pb.setValue(0)
        self.log_box.clear()
        self.append_log("Bắt đầu chạy mapping...")

        self.run_btn.setEnabled(False)

        self.worker = MappingWorker(
            erp_path=erp_path,
            word_path=word_path,
            out_path=out_path,
            strict=strict,
            topk=topk,
            th_strong=th_strong,
            th_med=th_med
        )
        self.worker.progress.connect(self.pb.setValue)
        self.worker.log.connect(self.append_log)
        self.worker.finished.connect(self.on_done)
        self.worker.failed.connect(self.on_fail)
        self.worker.start()

    def on_done(self, out_path):
        self.append_log(f"✅ Hoàn tất! Output: {out_path}")
        QMessageBox.information(self, "Xong", f"Đã xuất file:\n{out_path}")
        self.run_btn.setEnabled(True)

    def on_fail(self, err):
        self.append_log(f"❌ Lỗi: {err}")
        QMessageBox.critical(self, "Lỗi", err)
        self.run_btn.setEnabled(True)

# =========================
# 3) MAIN
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())