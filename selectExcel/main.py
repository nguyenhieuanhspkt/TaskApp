# main.py
import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableWidgetItem, QLabel, QComboBox, QPushButton
from ui_design import ExcelMapperUI
from ui_design_config import DATA_TYPES, DEFAULT_BAREM_CONFIG, PREVIEW_ROWS

class ExcelProcessor(ExcelMapperUI):
    def __init__(self):
        super().__init__()
        # Khởi tạo danh sách barem từ cấu hình (lấy phần tên cột)
        self.current_barem = [item[0] for item in DEFAULT_BAREM_CONFIG]
        # Tạo từ điển lưu kiểu dữ liệu mặc định để tra cứu
        self.default_types = dict(DEFAULT_BAREM_CONFIG)
        self.file_path = ""
        self.excel_columns = ["-- Bỏ qua --"]
        self.refresh_mapping_ui()
        self.current_preview_df = None # Lưu DF vừa preview xong
        self.all_collected_dfs = []    # Danh sách các DF đã bấm Kết chuyển
        # Kết nối sự kiện
        # btn_open.clicked: Mở hộp thoại chọn file Excel từ máy tính và nạp danh sách các Sheet vào ứng dụng.
        # combo_sheet.currentIndexChanged: Tự động cập nhật danh sách tên cột mới khi người dùng thay đổi việc chọn Sheet.
        # spin_header.valueChanged: Cập nhật lại danh sách tiêu đề cột ngay khi người dùng thay đổi số dòng làm Header.
        # btn_add_col.clicked: Lấy tên từ ô nhập liệu để tạo thêm một dòng Mapping mới vào danh sách Barem hiện tại.
        # btn_preview.clicked: Thu thập toàn bộ dữ liệu đã Mapping để lọc và hiển thị kết quả lên bảng xem trước.

        self.btn_open.clicked.connect(self.open_file_logic) 
        self.combo_sheet.currentIndexChanged.connect(self.update_excel_columns)
        self.spin_header.valueChanged.connect(self.update_excel_columns)
        self.btn_add_col.clicked.connect(self.add_new_barem_column)
        self.btn_preview.clicked.connect(self.process_and_preview)
        self.btn_transfer.clicked.connect(self.transfer_data)
        self.btn_combine.clicked.connect(self.combine_data)

    def refresh_mapping_ui(self):
        """Vẽ lại giao diện Mapping với kiểu dữ liệu mặc định"""
        for i in reversed(range(self.mapping_layout.count())): 
            self.mapping_layout.itemAt(i).widget().setParent(None)
        
        self.mapping_combos = {}
        self.type_combos = {}

        for i, col_name in enumerate(self.current_barem):
            # 1. Tên trường Barem
            self.mapping_layout.addWidget(QLabel(f"<b>{col_name}</b>"), i, 0)
            
            # 2. Chọn cột từ Excel
            c_excel = QComboBox()
            c_excel.addItems(self.excel_columns)
            self.mapping_layout.addWidget(c_excel, i, 1)
            self.mapping_combos[col_name] = c_excel
            
            # 3. Chọn kiểu dữ liệu
            c_type = QComboBox()
            c_type.addItems(DATA_TYPES)
            
            # Lấy kiểu dữ liệu mặc định từ config, nếu không có thì mặc định là Text
            default_type = self.default_types.get(col_name, "Text")
            index = c_type.findText(default_type)
            if index >= 0:
                c_type.setCurrentIndex(index)
                
            self.mapping_layout.addWidget(c_type, i, 2)
            self.type_combos[col_name] = c_type
            
            # 4. Nút xóa
            btn_del = QPushButton("❌")
            btn_del.setFixedWidth(30)
            btn_del.clicked.connect(lambda ch, name=col_name: self.remove_barem_column(name))
            self.mapping_layout.addWidget(btn_del, i, 3)

    def add_new_barem_column(self):
        new_name = self.txt_new_col.text().strip()
        if new_name and new_name not in self.current_barem:
            self.current_barem.append(new_name)
            self.txt_new_col.clear()
            self.refresh_mapping_ui()

    def remove_barem_column(self, name):
        if name in self.current_barem:
            self.current_barem.remove(name)
            self.refresh_mapping_ui()

    def open_file_logic(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file Excel", "", "Excel (*.xlsx *.xls)")
        if path:
            self.file_path = path
            self.lbl_file.setText(path.split('/')[-1])
            xl = pd.ExcelFile(self.file_path)
            self.combo_sheet.clear()
            self.combo_sheet.addItems(xl.sheet_names)
    def update_excel_columns(self):
        if not self.file_path: return
        try:
            df = pd.read_excel(self.file_path, sheet_name=self.combo_sheet.currentText(), 
                               header=self.spin_header.value(), nrows=0)
            self.excel_columns = ["-- Bỏ qua --"] + [str(c) for c in df.columns]
            self.refresh_mapping_ui() # Vẽ lại để update list cột Excel vào các combo
        except: pass

    def process_and_preview(self):
        if not self.file_path: return
        try:
            df_origin = pd.read_excel(self.file_path, sheet_name=self.combo_sheet.currentText(), 
                                      header=self.spin_header.value())
            final_data = {}
            
            for barem_name in self.current_barem:
                excel_col = self.mapping_combos[barem_name].currentText()
                data_type = self.type_combos[barem_name].currentText()
                
                if excel_col != "-- Bỏ qua --":
                    series = df_origin[excel_col]
                    
                    # Xử lý ép kiểu dữ liệu
                    if data_type == "Số (Number)":
                        series = pd.to_numeric(series, errors='coerce')
                    elif data_type == "Ngày tháng (Date)":
                        series = pd.to_datetime(series, errors='coerce').dt.strftime('%d/%m/%Y')
                    else: # Text
                        series = series.astype(str).replace('nan', '')
                        
                    final_data[barem_name] = series
                else:
                    final_data[barem_name] = [""] * len(df_origin)

            df_final = pd.DataFrame(final_data)
            self.display_table(df_final.head(20))
            self.current_preview_df = df_final # Lưu DF vừa preview xong
        except Exception as e:
            QMessageBox.critical(self, "Lỗi xử lý", f"Lỗi: {str(e)}")
        
    def display_table(self, df):
        self.table_preview.setRowCount(df.shape[0])
        self.table_preview.setColumnCount(len(df.columns))
        self.table_preview.setHorizontalHeaderLabels(df.columns)
        for i in range(len(df)):
            for j in range(len(df.columns)):
                val = df.iloc[i, j]
                self.table_preview.setItem(i, j, QTableWidgetItem(str(val) if pd.notna(val) else ""))
        self.table_preview.resizeColumnsToContents()
    def transfer_data(self):
        """Đẩy dữ liệu từ Preview sang danh sách chờ"""
        if self.current_preview_df is None:
            QMessageBox.warning(self, "Lưu ý", "Chưa có dữ liệu Preview để kết chuyển!")
            return

        # Lưu bản sao vào danh sách
        self.all_collected_dfs.append(self.current_preview_df.copy())
        
        # Hiển thị thông báo lên text box bên phải (ListWidget)
        file_name = self.file_path.split('/')[-1] if self.file_path else "Data"
        row_count = len(self.current_preview_df)
        self.list_pending.addItem(f"Lần {len(self.all_collected_dfs)}: {file_name} ({row_count} dòng)")
        
        # Xóa preview để tránh bấm kết chuyển nhầm 2 lần cùng 1 dữ liệu (tùy chọn)
        self.current_preview_df = None
        QMessageBox.information(self, "Thành công", "Đã đưa vào danh sách chờ gộp!")
    def combine_data(self):
        """Nối tất cả DataFrame trong danh sách chờ thành 1 file duy nhất"""
        if not self.all_collected_dfs:
            QMessageBox.warning(self, "Lỗi", "Danh sách chờ đang trống!")
            return

        try:
            # Thực hiện nối dài (Append) các DataFrame
            combined_df = pd.concat(self.all_collected_dfs, ignore_index=True)
            
            # Hiển thị bảng tổng lên preview để user xem lần cuối
            self.display_table(combined_df)
            
            # Hỏi user chỗ lưu file
            from PyQt5.QtWidgets import QFileDialog
            save_path, _ = QFileDialog.getSaveFileName(self, "Lưu file gộp", "", "Excel Files (*.xlsx)")
            
            if save_path:
                combined_df.to_excel(save_path, index=False)
                QMessageBox.information(self, "Xong!", f"Đã gộp {len(self.all_collected_dfs)} phần và lưu thành công!")
                
                # Reset danh sách sau khi đã gộp xong
                self.all_collected_dfs = []
                self.list_pending.clear()
                
        except Exception as e:
            QMessageBox.critical(self, "Lỗi khi gộp", str(e))
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ExcelProcessor()
    window.show()
    sys.exit(app.exec_())