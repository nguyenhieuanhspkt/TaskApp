import sys
import pandas as pd
import io
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QFileDialog, QLabel, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QHBoxLayout, QLineEdit)
from PyQt5.QtCore import Qt

class MaterialProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.df_final_grouped = None
        self.df_final_original = None

    def initUI(self):
        self.setWindowTitle('Công cụ Thẩm định Vật tư - EVN 2026')
        self.setGeometry(100, 100, 1000, 700)

        # Main Widget và Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # --- Khu vực điều khiển ---
        ctrl_layout = QHBoxLayout()
        
        self.btn_open = QPushButton('📁 Chọn File Excel')
        self.btn_open.clicked.connect(self.load_file)
        
        self.label_file = QLabel('Chưa chọn file...')
        self.label_file.setStyleSheet("color: gray;")

        self.btn_process = QPushButton('⚡ Xử lý dữ liệu')
        self.btn_process.setEnabled(False)
        self.btn_process.clicked.connect(self.process_data)

        self.btn_export = QPushButton('💾 Xuất File Excel')
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.export_file)

        ctrl_layout.addWidget(self.btn_open)
        ctrl_layout.addWidget(self.label_file, 1)
        ctrl_layout.addWidget(self.btn_process)
        ctrl_layout.addWidget(self.btn_export)
        
        layout.addLayout(ctrl_layout)

        # --- Thông số cấu hình ---
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("Tên Sheet:"))
        self.txt_sheet = QLineEdit("PL1.5 DT VẬT TƯ TM")
        config_layout.addWidget(self.txt_sheet)
        layout.addLayout(config_layout)

        # --- Bảng hiển thị kết quả (Preview) ---
        self.table = QTableWidget()
        layout.addWidget(self.table)

        # --- Thanh trạng thái ---
        self.status_label = QLabel("Sẵn sàng")
        layout.addWidget(self.status_label)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file Excel", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.input_file = file_path
            self.label_file.setText(file_path.split('/')[-1])
            self.btn_process.setEnabled(True)
            self.status_label.setText("Đã tải file. Nhấn 'Xử lý' để bắt đầu.")

    def process_data(self):
        try:
            sheet_name = self.txt_sheet.text()
            # Logic xử lý (giữ nguyên từ code gốc của bạn)
            df_raw = pd.read_excel(self.input_file, sheet_name=sheet_name, header=None)
            
            # Xử lý Header
            header_rows = df_raw.iloc[3:5].copy()
            header_rows = header_rows.ffill(axis=0).infer_objects(copy=False)
            new_columns = (header_rows.astype(str).apply(lambda c: " ".join(x.strip() for x in c if x and x.strip() != "nan"), axis=0))
            
            df = df_raw.iloc[5:].copy()
            df.columns = new_columns
            df.columns = df.columns.str.strip().str.replace(r"\s+", " ", regex=True)
            df = df.loc[:, df.columns != ""]
            
            # Lấy Mã giá cột R (index 17)
            df["Mã giá"] = df_raw.iloc[5:, 17].reset_index(drop=True)
            
            # Rename
            df = df.rename(columns={
                "Tên Vật tư Tên Vật tư": "Tên vật tư",
                "ĐVT ĐVT": "Đơn vị tính",
                "Mua mới": "Số lượng",
                "Dự kiến mua mới": "Đơn giá",
                "Tổng cộng": "Tổng Giá trị (cột O)",
            })

            # Tìm Thành tiền
            tt_cols = [c for c in df.columns if "THÀNH TIỀN" in c.upper() and "DỰ KIẾN" in c.upper()]
            if tt_cols: df = df.rename(columns={tt_cols[0]: "Thành tiền mua sắm mới"})
            else: df["Thành tiền mua sắm mới"] = df.get("Tổng Giá trị (cột O)", 0)

            # Convert Numeric & Filter
            for col in ["Số lượng", "Đơn giá", "Thành tiền mua sắm mới", "Tổng Giá trị (cột O)"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            
            df_clean = df[df["Tổng Giá trị (cột O)"] != 0].reset_index(drop=True)

            # Group ID logic
            group_key_cols = ["Tên vật tư", "Đơn vị tính", "Đơn giá"]
            df_clean["_group_key"] = df_clean[group_key_cols].astype(str).agg("|".join, axis=1)
            group_map = {k: i + 1 for i, k in enumerate(df_clean["_group_key"].drop_duplicates())}
            df_clean["Group ID"] = df_clean["_group_key"].map(group_map)
            df_clean.drop(columns=["_group_key"], inplace=True)
            
            self.df_final_original = df_clean.copy()

            # Grouping
            group_cols = ["Group ID", "Mã giá", "Tên vật tư", "Đơn vị tính"]
            df_grouped = df_clean.groupby(group_cols, dropna=False).agg(
                Don_gia_list=("Đơn giá", lambda x: sorted(set(x))),
                Đơn_giá=("Đơn giá", "min"),
                Số_lượng=("Số lượng", "sum"),
                Thành_tiền=("Thành tiền mua sắm mới", "sum"),
                Tổng_O=("Tổng Giá trị (cột O)", "sum"),
            ).reset_index()

            df_grouped["Ghi chú"] = df_grouped["Don_gia_list"].apply(lambda x: "có nhiều đơn giá" if len(x) > 1 else "")
            self.df_final_grouped = df_grouped.drop(columns=["Don_gia_list"])

            # Hiển thị lên bảng (Preview 50 dòng đầu)
            self.display_data(self.df_final_grouped.head(50))
            self.btn_export.setEnabled(True)
            self.status_label.setText(f"Xử lý xong! Tổng tiền: {df_grouped['Tổng_O'].sum():,.0f} đ")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xử lý: {str(e)}")

    def display_data(self, df):
        self.table.setRowCount(df.shape[0])
        self.table.setColumnCount(df.shape[1])
        self.table.setHorizontalHeaderLabels(df.columns)
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                self.table.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))

    def export_file(self):
        if self.df_final_grouped is None: return
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Lưu file", "Ket_qua_nhom_vat_tu.xlsx", "Excel Files (*.xlsx)")
        if save_path:
            with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
                self.df_final_original.to_excel(writer, sheet_name="PL1.5_ORIGINAL", index=False)
                self.df_final_grouped.to_excel(writer, sheet_name="PL1.5_GROUPED", index=False)
            QMessageBox.information(self, "Thành công", "Đã xuất file thành công!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MaterialProcessorApp()
    ex.show()
    sys.exit(app.exec_())