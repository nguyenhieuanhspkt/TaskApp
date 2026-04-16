import pandas as pd
from PyQt5.QtWidgets import QMessageBox, QFileDialog

class FeatureMergeLogic:
    def __init__(self, main_window):
        """
        Khởi tạo logic cho Tính năng 1.
        :param main_window: Đối tượng ExcelProcessor (chứa các widget UI)
        """
        self.mw = main_window
        self.all_collected_dfs = []  # Danh sách lưu các DataFrame đã 'Kết chuyển'
        self.current_preview_df = None # DataFrame vừa được 'Preview' xong

    def process_and_preview(self):
        """
        Lấy cấu hình mapping từ giao diện, đọc file Excel và hiển thị 20 dòng đầu.
        """
        if not hasattr(self.mw, 'file_path') or not self.mw.file_path:
            QMessageBox.warning(self.mw, "Lỗi", "Vui lòng chọn file Excel trước!")
            return

        try:
            # 1. Đọc dữ liệu gốc từ Excel
            df_origin = pd.read_excel(
                self.mw.file_path, 
                sheet_name=self.mw.combo_sheet.currentText(), 
                header=self.mw.spin_header.value()
            )

            final_data = {}
            
            # 2. Duyệt qua danh sách Barem để lấy dữ liệu từ các cột tương ứng
            for barem_name in self.mw.current_barem:
                # Lấy tên cột Excel đang được chọn trong ComboBox
                excel_col = self.mw.mapping_combos[barem_name].currentText()
                # Lấy kiểu dữ liệu đang chọn
                data_type = self.mw.type_combos[barem_name].currentText()
                
                if excel_col != "-- Bỏ qua --":
                    series = df_origin[excel_col]
                    
                    # Xử lý ép kiểu dữ liệu dựa trên lựa chọn của user
                    if data_type == "Số (Number)":
                        series = pd.to_numeric(series, errors='coerce')
                    elif data_type == "Ngày tháng (Date)":
                        series = pd.to_datetime(series, errors='coerce').dt.strftime('%d/%m/%Y')
                    else: # Mặc định là Text
                        series = series.astype(str).replace('nan', '')
                        
                    final_data[barem_name] = series
                else:
                    # Nếu bỏ qua, tạo cột trống
                    final_data[barem_name] = [""] * len(df_origin)

            # 3. Tạo DataFrame kết quả và hiển thị
            self.current_preview_df = pd.DataFrame(final_data)
            
            # Gọi hàm hiển thị bảng dùng chung ở main.py
            self.mw.display_table(self.mw.table_preview, self.current_preview_df.head(20))
            
        except Exception as e:
            QMessageBox.critical(self.mw, "Lỗi xử lý Preview", f"Chi tiết lỗi: {str(e)}")

    def transfer_data(self):
        """
        Lưu tạm dữ liệu vừa Preview vào 'Giỏ hàng' (danh sách chờ gộp).
        """
        if self.current_preview_df is None:
            QMessageBox.warning(self.mw, "Lưu ý", "Bạn cần bấm 'Preview' để kiểm tra dữ liệu trước khi kết chuyển!")
            return

        # Thêm bản sao vào danh sách thu thập
        self.all_collected_dfs.append(self.current_preview_df.copy())
        
        # Cập nhật thông tin lên ListWidget (danh sách chờ)
        file_name = self.mw.file_path.split('/')[-1]
        row_count = len(self.current_preview_df)
        self.mw.list_pending.addItem(f"Lần {len(self.all_collected_dfs)}: {file_name} ({row_count} dòng)")
        
        # Reset preview để tránh bấm nhầm 2 lần cùng 1 dữ liệu
        self.current_preview_df = None
        QMessageBox.information(self.mw, "Thành công", "Đã đưa dữ liệu vào danh sách chờ gộp!")

    def combine_data(self):
        """
        Nối tất cả các phần đã kết chuyển và lưu ra file Excel duy nhất.
        """
        if not self.all_collected_dfs:
            QMessageBox.warning(self.mw, "Lỗi", "Danh sách chờ đang trống! Hãy kết chuyển dữ liệu trước.")
            return

        try:
            # 1. Nối (Append) các DataFrame
            combined_df = pd.concat(self.all_collected_dfs, ignore_index=True)
            
            # 2. Hiển thị bảng tổng lên preview cho user xem lần cuối
            self.mw.display_table(self.mw.table_preview, combined_df)
            
            # 3. Hộp thoại lưu file
            save_path, _ = QFileDialog.getSaveFileName(
                self.mw, "Lưu file tổng hợp", "", "Excel Files (*.xlsx)"
            )
            
            if save_path:
                combined_df.to_excel(save_path, index=False)
                QMessageBox.information(self.mw, "Hoàn tất", f"Đã gộp thành công {len(self.all_collected_dfs)} phần vào file!")
                
                # 4. Reset trạng thái sau khi lưu thành công
                self.all_collected_dfs = []
                self.mw.list_pending.clear()
                
        except Exception as e:
            QMessageBox.critical(self.mw, "Lỗi khi gộp file", f"Lỗi: {str(e)}")