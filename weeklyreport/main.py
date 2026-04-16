import json
import os
import xlsxwriter
from datetime import datetime, timedelta
import config 

class WeeklyReportExporter:
    def __init__(self):
        self.json_path = config.JSON_FILE_PATH
        # Xác định mốc Thứ 2 tuần này (Ngày 13/04/2026)
        today = datetime.now().date()
        self.start_week = today - timedelta(days=today.weekday())

    def get_data(self):
        if not os.path.exists(self.json_path):
            print(f"LỖI: Không thấy file tại: {self.json_path}")
            return []
        with open(self.json_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"LỖI JSON: {e}")
                return []

    def is_active_this_week(self, task):
        """Lọc hồ sơ có start_date từ Thứ 2 tuần này trở đi"""
        sd_raw = task.get('start_date')
        if not sd_raw: return False
        try:
            task_date = datetime.strptime(str(sd_raw)[:10], "%Y-%m-%d").date()
            return task_date >= self.start_week
        except:
            return False

    def export(self):
        all_tasks = self.get_data()
        weekly_tasks = [t for t in all_tasks if self.is_active_this_week(t)]

        if not weekly_tasks:
            print(f"Không có hồ sơ mới từ ngày {self.start_week.strftime('%d/%m')} đến nay.")
            return

        # SẮP XẾP: Pháp chế/Thanh tra lên đầu, ID mới nhất lên đầu
        def sort_priority(t):
            cat = t.get('category')
            is_special = (cat == config.SPECIAL_CATEGORY or not cat)
            return (not is_special, -t.get('id', 0))

        weekly_tasks.sort(key=sort_priority)

        # Tạo file Excel với tên reportTuan.xlsx
        filename = config.OUTPUT_FILENAME
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet('BaoCaoTuan')

        # Định dạng bảng
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#1F4E78', 'font_color': 'white', 'border': 1, 'align': 'center'})
        special_fmt = workbook.add_format({'bg_color': '#E2EFDA', 'border': 1, 'text_wrap': True, 'valign': 'vcenter'})
        normal_fmt = workbook.add_format({'border': 1, 'text_wrap': True, 'valign': 'vcenter'})

        headers = ["STT", "Mảng công việc", "Chuyên viên", "Nội dung hồ sơ/Sản phẩm", "Ngày bắt đầu", "Trạng thái", "Tiến độ mới nhất"]
        for i, h in enumerate(headers):
            worksheet.write(0, i, h, header_fmt)

        for row, t in enumerate(weekly_tasks, start=1):
            cat = t.get('category')
            is_special = (cat == config.SPECIAL_CATEGORY or not cat)
            fmt = special_fmt if is_special else normal_fmt
            
            dept = "Pháp chế/Thanh tra" if is_special else "Thẩm định"
            st = {"doing": "Đang xử lý", "sent": "Đã trình", "done": "Hoàn thành"}.get(t.get('status'), t.get('status'))
            last_log = t.get('history', [])[-1] if t.get('history') else "Mới tiếp nhận"

            worksheet.write(row, 0, row, fmt)
            worksheet.write(row, 1, dept, fmt)
            worksheet.write(row, 2, t.get('author'), fmt)
            worksheet.write(row, 3, t.get('title', '').strip(), fmt)
            worksheet.write(row, 4, str(t.get('start_date')), fmt)
            worksheet.write(row, 5, st, fmt)
            worksheet.write(row, 6, last_log, fmt)

        # Căn chỉnh độ rộng cột
        worksheet.set_column('A:A', 4)
        worksheet.set_column('B:C', 18)
        worksheet.set_column('D:D', 50)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 14)
        worksheet.set_column('G:G', 45)
        
        workbook.close()
        print(f"Đã xuất thành công {len(weekly_tasks)} hồ sơ vào file: {filename}")
        os.startfile(filename)

if __name__ == "__main__":
    app = WeeklyReportExporter()
    app.export()