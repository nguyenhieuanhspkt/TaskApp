import json
import os
import xlsxwriter
import re
from datetime import datetime, timedelta
# Import tương đối file cấu hình
try:
    from . import weeklyconfig
except (ImportError, ValueError):
    import weeklyconfig

class WeeklyReportExporter:
    def __init__(self, root_path_from_manager, year):
        """
        :param root_path_from_manager: D:\onedrive_hieuna\... (đến Tổ Thẩm định)
        :param year: 2026
        """
        self.json_path = weeklyconfig.JSON_FILE_PATH
        self.today = datetime.now().date()
        # Xác định ngày thứ Hai của tuần này
        self.start_week = self.today - timedelta(days=self.today.weekday())
        
        # Bản đồ chuyển đổi tên User hiển thị trong Excel
        self.authors_map = {
            "Admins": "Chị Chi", 
            "hieuna_3": "Anh Hiếu", 
            "tuank": "Tuấn Kiệt"
        }
        
        # Lưu đường dẫn gốc để tạo Link Folder
        self.base_path = os.path.join(root_path_from_manager, f"Năm {year}")

    def clean_task_title(self, text):
        """Chuẩn hóa tiêu đề: Viết hoa chữ đầu, thay viết tắt, giữ ngoại lệ 'Thực hiện'"""
        if not text: return ""
        text = text.replace('\n', ' ').strip()
        
        # 1. Từ điển viết tắt
        replacements = {
            r"KQLCNT": "kết quả lựa chọn nhà thầu",
            r"KHLCNT": "kế hoạch lựa chọn nhà thầu",
            r"KQLC": "kết quả lựa chọn nhà thầu",
            r"E-HSMT": "hồ sơ mời thầu qua mạng",
            r"HSMT": "hồ sơ mời thầu",
            r"QTMT": "quan trắc môi trường",
            r"ATTT": "an toàn thông tin",
            r"SCTD": "sự cố tràn dầu",
            r"SCMT": "sự cố môi trường",
            r"THC": "thu hồi chì",
            r"TD": "tràn dầu",
            r"BCNCKT": "báo cáo nghiên cứu khả thi",
            r"SCL": "sửa chữa lớn",
            r"SCTX": "sửa chữa thường xuyên",
            r"CBCNV": "cán bộ công nhân viên",
            r"NM": "nhà máy",
            r"NMNĐ": "nhà máy nhiệt điện",
            r"VTSCTX": "vật tư sửa chữa thường xuyên"
        }
        for short, long in replacements.items():
            text = re.sub(short, long, text, flags=re.IGNORECASE)

        # 2. Xử lý Prefix (Ngoại lệ: Thực hiện)
        text = re.sub(r'^(Re:\s*|V/v\s*)', '', text, flags=re.IGNORECASE).strip()
        check_prefix = text.lower()
        allowed_prefixes = ("thẩm định", "thẩm tra", "thực hiện")
        
        if not check_prefix.startswith(allowed_prefixes):
            text = "Thẩm định " + text

        # 3. Sentence case
        text = text.capitalize()
        return text

    def standardize_date(self, date_input):
        """Chuyển đổi các định dạng ngày về đối tượng date"""
        if not date_input or not isinstance(date_input, str): return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(date_input[:10], fmt).date()
            except:
                continue
        return None

    def calculate_efficiency(self, task):
        """Tính toán hiệu quả và giải trình tiến độ"""
        status = task.get('status')
        if status != "done":
            return "Đang xử lý", "Đang trong tiến độ thực hiện.", "#FFFFFF"

        final = task.get('final_report', {})
        sd = self.standardize_date(final.get('start_date') or task.get('start_date'))
        if not sd: return "Thiếu dữ liệu", "Chưa xác định ngày bắt đầu.", None

        fsd = self.standardize_date(final.get('first_sent_date'))
        cpd = self.standardize_date(final.get('completion_date'))
        ed = cpd if cpd else self.today
        actual_delta = (ed - sd).days
        
        res_text, res_color, explanation = "Hoàn thành đúng hạn", "#E2EFDA", "Hoàn thành trong thời gian quy định."

        if actual_delta > 3:
            if fsd and (fsd - sd).days + 1 <= 3:
                explanation = f"Thời gian xử lý thực tế phù hợp (có chờ bổ sung hồ sơ)."
            else:
                res_text, res_color = f"Trễ hạn ({actual_delta-3} ngày)", "#FFC7CE"
                explanation = "Hồ sơ phức tạp, cần nhiều thời gian đối chiếu quy chuẩn kỹ thuật."
        
        return res_text, explanation, res_color

    def friendly_log(self, log_str):
        """Làm đẹp dòng nhật ký cuối cùng"""
        if not log_str: return "Mới nhận hồ sơ"
        match = re.search(r'(\d{2}/\d{2})', log_str)
        date_suffix = f" ngày {match.group(1)}/2026" if match else ""
        
        if "Tạo mới" in log_str: return f"Vừa được đề nghị thẩm định{date_suffix}"
        if "Xong - Đã rà soát báo cáo" in log_str: return f"Đã ban hành báo cáo thẩm định{date_suffix}"
        return log_str

    def get_data(self):
        """Đọc file tasks.json"""
        if not os.path.exists(self.json_path): return []
        with open(self.json_path, "r", encoding="utf-8") as f: 
            return json.load(f)

    def is_active_this_week(self, task):
        """Logic lọc hồ sơ: Chỉ hiện những việc thực sự làm trong tuần này"""
        final = task.get('final_report', {})
        # 1. Nếu đã có báo cáo cuối cùng
        if final:
            report_date = self.standardize_date(final.get('final_report_date'))
            completion_date = self.standardize_date(final.get('completion_date'))
            # Nếu ngày xong nằm trong tuần này thì hiện
            if (report_date and report_date >= self.start_week) or \
               (completion_date and completion_date >= self.start_week):
                return True
            return False # Đã xong từ tuần trước thì loại bỏ

        # 2. Nếu hồ sơ chưa xong (đang làm)
        sd = self.standardize_date(task.get('start_date'))
        if sd and sd >= self.start_week: return True # Mới nhận tuần này
        if task.get('status') in ['doing', 'sent']: return True # Làm từ tuần trước chưa xong

        return False

    def export(self):
        """Hàm chính thực hiện xuất file Excel"""
        all_tasks = self.get_data()
        weekly_tasks = [t for t in all_tasks if self.is_active_this_week(t)]
        if not weekly_tasks: return

        # Sắp xếp hồ sơ
        weekly_tasks.sort(key=lambda x: (not (x.get('category') == weeklyconfig.SPECIAL_CATEGORY or not x.get('category')), -x.get('id', 0)))

        workbook = xlsxwriter.Workbook(weeklyconfig.OUTPUT_FILENAME)
        sheet = workbook.add_worksheet('Báo cáo chi tiết')
        
        # Format
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#1F4E78', 'font_color': 'white', 'border': 1, 'align': 'center'})
        link_fmt = workbook.add_format({'font_color': 'blue', 'underline': True, 'border': 1, 'valign': 'vcenter'})
        
        headers = ["STT", "Lĩnh vực", "Chuyên viên", "Nội dung hồ sơ", "Ngày bắt đầu", "Ngày xong", "Đánh giá", "Giải trình tiến độ", "Link Folder"]
        for i, h in enumerate(headers): sheet.write(0, i, h, header_fmt)

        for row, t in enumerate(weekly_tasks, start=1):
            eval_text, explanation, color = self.calculate_efficiency(t)
            is_special = (t.get('category') == weeklyconfig.SPECIAL_CATEGORY or not t.get('category'))
            
            fmt = workbook.add_format({'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'bg_color': '#E2EFDA' if is_special else '#FFFFFF'})
            eval_fmt = workbook.add_format({'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'bg_color': color or '#FFFFFF', 'bold': True})

            sheet.write(row, 0, row, fmt)
            sheet.write(row, 1, "Pháp chế" if is_special else "Thẩm định", fmt)
            sheet.write(row, 2, self.authors_map.get(t.get('author', ''), t.get('author', '')), fmt)
            sheet.write(row, 3, self.clean_task_title(t.get('title', '')), fmt)
            
            d_start = self.standardize_date(t.get('start_date'))
            d_end = self.standardize_date(t.get('final_report', {}).get('completion_date'))
            
            sheet.write(row, 4, d_start.strftime(weeklyconfig.DATE_FORMAT_OUT) if d_start else "-", fmt)
            sheet.write(row, 5, d_end.strftime(weeklyconfig.DATE_FORMAT_OUT) if d_end else "-", fmt)
            sheet.write(row, 6, eval_text, eval_fmt)
            sheet.write(row, 7, explanation, fmt)

            # TẠO LINK FOLDER DỰA TRÊN USER ĐÃ CHỌN
            folder_name = t.get('folder', '')
            if self.base_path and folder_name:
                full_link = os.path.join(self.base_path, folder_name)
                # Dùng external để mở thư mục Windows Explorer
                sheet.write_url(row, 8, f"external:{full_link}", link_fmt, string="Mở thư mục")
            else:
                sheet.write(row, 8, "Không có link", fmt)

        sheet.set_column('D:D', 50)
        sheet.set_column('G:G', 22)
        sheet.set_column('H:H', 40)
        sheet.set_column('I:I', 15)
        
        workbook.close()
        os.startfile(weeklyconfig.OUTPUT_FILENAME)

if __name__ == "__main__":
    # Test nhanh (phải chạy bằng python -m weeklyreport.main)
    WeeklyReportExporter(r"D:\TestPath").export()