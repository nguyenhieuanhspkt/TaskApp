import json
import os
import xlsxwriter
import re
from datetime import datetime, timedelta
import config 

class WeeklyReportExporter:
    def __init__(self):
        self.json_path = config.JSON_FILE_PATH
        self.today = datetime.now().date()
        self.start_week = self.today - timedelta(days=self.today.weekday())
        self.authors_map = {"Admins": "Chị Chi", "hieuna_3": "Anh Hiếu", "tuank": "Tuấn Kiệt"}

    def clean_task_title(self, text):
        """Hàm chuẩn hóa tiêu đề hồ sơ theo yêu cầu của Anh Hiếu"""
        if not text: return ""
        
        # 1. Loại bỏ xuống dòng và khoảng trắng thừa
        text = text.replace('\n', ' ').strip()
        
        # 2. Từ điển các từ viết tắt cần thay thế
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

        # Thay thế các từ viết tắt (không phân biệt hoa thường)
        for short, long in replacements.items():
            text = re.sub(short, long, text, flags=re.IGNORECASE)

        # 3. Đảm bảo bắt đầu bằng "Thẩm định" hoặc "Thẩm tra"
        # Xóa tiền tố "Re: " hoặc các ký tự lạ ở đầu
        text = re.sub(r'^(Re:\s*|V/v\s*)', '', text, flags=re.IGNORECASE).strip()
        
        check_prefix = text.lower()
        if not (check_prefix.startswith("thẩm định") or check_prefix.startswith("thẩm tra")):
            text = "Thẩm định " + text

        # 4. Định dạng Sentence case (Viết hoa chữ đầu, còn lại viết thường)
        # Lưu ý: Giữ lại viết hoa cho các danh từ riêng như VT4, S3 nếu cần, 
        # nhưng ở đây em làm chuẩn sentence case như Anh yêu cầu.
        text = text.capitalize()
        
        return text

    def standardize_date(self, date_input):
        if not date_input or not isinstance(date_input, str): return None
        try: return datetime.strptime(date_input[:10], "%Y-%m-%d").date()
        except: pass
        try: return datetime.strptime(date_input[:10], "%d/%m/%Y").date()
        except: pass
        return None

    def calculate_efficiency(self, task):
        status = task.get('status')
        if status != "done":
            return "Đang xử lý", "Đang trong tiến độ thực hiện.", "#FFFFFF"

        final = task.get('final_report', {})
        sd_inside = final.get('start_date')
        sd_outside = task.get('start_date')
        sd = self.standardize_date(sd_inside) if sd_inside else self.standardize_date(sd_outside)
        
        if not sd: return "Thiếu dữ liệu", "Chưa xác định ngày bắt đầu.", None

        fsd = self.standardize_date(final.get('first_sent_date'))
        cpd = self.standardize_date(final.get('completion_date'))
        ed = cpd if cpd else self.today
        actual_delta = (ed - sd).days
        
        res_text, res_color, explanation = "Hoàn thành đúng hạn", "#E2EFDA", "Hoàn thành trong thời gian quy định."

        if actual_delta > 3:
            if fsd:
                work_days = (fsd - sd).days + 1
                if work_days <= 3:
                    explanation = f"Tổng thời gian xử lý thực tế {work_days} ngày (Có thời gian chờ bổ sung hồ sơ)."
                else:
                    res_text, res_color = f"Trễ hạn ({actual_delta-3} ngày)", "#FFC7CE"
                    explanation = "Hồ sơ phức tạp, cần nhiều thời gian đối chiếu quy chuẩn kỹ thuật."
            else:
                res_text, res_color = f"Trễ hạn ({actual_delta-3} ngày)", "#FFC7CE"
                explanation = "Thời gian xử lý kéo dài do rà soát kỹ các thông số kỹ thuật."
        
        return res_text, explanation, res_color

    def friendly_log(self, log_str):
        if not log_str: return "Mới nhận hồ sơ"
        match = re.search(r'(\d{2}/\d{2})', log_str)
        day_month = match.group(1) if match else self.today.strftime("%d/%m")
        date_suffix = f" ngày {day_month}/2026"
        if "Tạo mới" in log_str: return f"Vừa được đề nghị thẩm định{date_suffix}"
        if "Gửi ý kiến Zalo" in log_str: return f"Đã gửi ý kiến thẩm định{date_suffix}"
        if "Chỉnh sửa thông tin/phân loại hồ sơ" in log_str: return f"Đã chuẩn xác tên gọi công việc{date_suffix}"
        if "Chuyển: doing" in log_str: return f"Vừa cập nhật trạng thái đang xử lý sau khi nhận hồ sơ{date_suffix}"
        if "Xong - Đã rà soát báo cáo" in log_str: return f"Đã ban hành báo cáo thẩm định{date_suffix} và rà soát xong tiến độ công việc"
        return log_str

    def get_data(self):
        if not os.path.exists(self.json_path): return []
        with open(self.json_path, "r", encoding="utf-8") as f: return json.load(f)

    def is_active_this_week(self, task):
        sd = self.standardize_date(task.get('start_date'))
        if sd and sd >= self.start_week: return True
        final = task.get('final_report', {})
        for key in ['completion_date', 'final_report_date']:
            fd = self.standardize_date(final.get(key))
            if fd and fd >= self.start_week: return True
        history = task.get('history', [])
        check_days = [(self.start_week + timedelta(days=i)).strftime("%d/%m") for i in range(5)]
        for log in history:
            if any(d in log for d in check_days): return True
        return False

    def export(self):
        all_tasks = self.get_data()
        weekly_tasks = [t for t in all_tasks if self.is_active_this_week(t)]
        if not weekly_tasks: return

        weekly_tasks.sort(key=lambda x: (not (x.get('category') == config.SPECIAL_CATEGORY or not x.get('category')), -x.get('id', 0)))

        workbook = xlsxwriter.Workbook(config.OUTPUT_FILENAME)
        detail_sheet = workbook.add_worksheet('Báo cáo chi tiết')
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#1F4E78', 'font_color': 'white', 'border': 1, 'align': 'center'})
        
        headers = ["STT", "Lĩnh vực", "Chuyên viên", "Nội dung hồ sơ", "Ngày bắt đầu", "Ngày xong", "Đánh giá", "Giải trình tiến độ", "Tiến độ chi tiết"]
        for i, h in enumerate(headers): detail_sheet.write(0, i, h, header_fmt)

        for row, t in enumerate(weekly_tasks, start=1):
            eval_text, explanation, color = self.calculate_efficiency(t)
            is_special = (t.get('category') == config.SPECIAL_CATEGORY or not t.get('category'))
            fmt = workbook.add_format({'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'bg_color': '#E2EFDA' if is_special else '#FFFFFF'})
            eval_fmt = workbook.add_format({'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'bg_color': color if color else '#FFFFFF', 'bold': True})

            # CLEAN TEXT TIÊU ĐỀ TẠI ĐÂY
            clean_title = self.clean_task_title(t.get('title', ''))

            detail_sheet.write(row, 0, row, fmt)
            detail_sheet.write(row, 1, "Pháp chế/Thanh tra" if is_special else "Thẩm định", fmt)
            detail_sheet.write(row, 2, self.authors_map.get(t.get('author', ''), t.get('author', '')), fmt)
            detail_sheet.write(row, 3, clean_title, fmt) # Ghi tiêu đề đã sạch
            detail_sheet.write(row, 4, self.standardize_date(t.get('start_date')).strftime(config.DATE_FORMAT_OUT) if self.standardize_date(t.get('start_date')) else "-", fmt)
            detail_sheet.write(row, 5, self.standardize_date(t.get('final_report', {}).get('completion_date')).strftime(config.DATE_FORMAT_OUT) if self.standardize_date(t.get('final_report', {}).get('completion_date')) else "-", fmt)
            detail_sheet.write(row, 6, eval_text, eval_fmt)
            detail_sheet.write(row, 7, explanation, fmt)
            detail_sheet.write(row, 8, self.friendly_log(t.get('history', [])[-1] if t.get('history') else ""), fmt)

        detail_sheet.set_column('D:D', 50)
        detail_sheet.set_column('G:G', 22)
        detail_sheet.set_column('H:I', 50)
        workbook.close()
        os.startfile(config.OUTPUT_FILENAME)

if __name__ == "__main__":
    WeeklyReportExporter().export()