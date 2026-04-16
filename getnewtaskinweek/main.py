import win32com.client
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import config
import json
import os

# Lấy đường dẫn của thư mục chứa file main.py hiện tại (tức là thư mục getnewtaskinweek)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tạo đường dẫn đầy đủ đến file credentials.json
credentials_path = os.path.join(BASE_DIR, config.CREDENTIALS_FILE)

class GetNewTaskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GetNewTaskInWeek - Outlook to Sheets Porter")
        self.root.geometry("1000x850")
        
        self.temp_df = None  # Lưu trữ dữ liệu sau khi "Chốt" (Optimize)
        self.data = []       # Dữ liệu thô từ Outlook
        
        # --- 1. Khai báo các cột thông tin có thể lấy từ Outlook ---
        self.available_columns = {
            "Date": tk.BooleanVar(value=True),
            "Subject": tk.BooleanVar(value=True),
            "Sender": tk.BooleanVar(value=True),
            "Body Snippet": tk.BooleanVar(value=False),
            "Importance": tk.BooleanVar(value=False)
        }

        self.setup_ui()

    def setup_ui(self):
        # --- Header: Nhập tên người gửi ---
        header_frame = tk.Frame(self.root)
        header_frame.pack(pady=15, fill='x', padx=20)

        tk.Label(header_frame, text="Người gửi (Sender):", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w')
        self.sender_entry = tk.Entry(header_frame, width=35, font=('Arial', 10))
        self.sender_entry.insert(0, "BUI HUY HOANG")
        self.sender_entry.grid(row=0, column=1, padx=10)

        # --- Column Selection: Chọn cột muốn preview ---
        col_frame = tk.LabelFrame(self.root, text=" Lựa chọn thông tin Preview ", padx=10, pady=10)
        col_frame.pack(fill='x', padx=20, pady=5)
        
        for i, (col_name, var) in enumerate(self.available_columns.items()):
            tk.Checkbutton(col_frame, text=col_name, variable=var).grid(row=0, column=i, padx=10)

        # --- Button 1: Quét Outlook ---
        self.preview_btn = tk.Button(self.root, text="🔍 Bước 1: Quét Folder ThamDinh", 
                                   command=self.fetch_outlook_data, bg="#e1e1e1", 
                                   font=('Arial', 10, 'bold'), pady=8)
        self.preview_btn.pack(pady=10)

        # --- Treeview: Bảng hiển thị dữ liệu ---
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(expand=True, fill='both', padx=20)
        self.tree = ttk.Treeview(tree_frame, show='headings')
        
        # Thanh cuộn cho bảng
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side='left', expand=True, fill='both')
        scrollbar.pack(side='right', fill='y')

        # --- Debug Log: Cửa sổ thông báo tiến trình ---
        log_label = tk.Label(self.root, text="Hệ thống Debug Log:", fg="blue", font=('Arial', 9, 'italic'))
        log_label.pack(anchor='w', padx=20, pady=(10, 0))
        
        self.log_text = tk.Text(self.root, height=8, font=('Consolas', 9), state='disabled', bg="#f8f9fa")
        self.log_text.pack(fill='x', padx=20, pady=5)

        # --- Footer: Nút xuất JSON và Push Sheets ---
        footer_frame = tk.Frame(self.root)
        footer_frame.pack(pady=20)

        self.btn_json = tk.Button(footer_frame, text="📄 Bước 2: Xuất & Kiểm duyệt JSON", 
                                 command=self.handle_export_json, state='disabled', 
                                 bg="#2196F3", fg="white", font=('Arial', 10, 'bold'), padx=15, pady=8)
        self.btn_json.pack(side='left', padx=10)

        self.btn_sheets = tk.Button(footer_frame, text="🚀 Bước 3: Chốt lên Google Sheets", 
                                   command=self.push_to_sheets, state='disabled', 
                                   bg="#cccccc", fg="white", font=('Arial', 10, 'bold'), padx=15, pady=8)
        self.btn_sheets.pack(side='left', padx=10)

    def log(self, message):
        """Hàm in log ra màn hình GUI"""
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"> {message}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
        self.root.update_idletasks()

    def fetch_outlook_data(self):
        self.log("Đang khởi tạo kết nối Outlook...")
        try:
            # Xác định các cột được chọn
            selected_cols = [name for name, var in self.available_columns.items() if var.get()]
            self.tree["columns"] = selected_cols
            for col in selected_cols:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=150 if col != "Subject" else 400)

            # Truy cập Folder ThamDinh
            outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
            inbox = outlook.GetDefaultFolder(config.OUTLOOK_INBOX_ID)
            
            try:
                target_folder = inbox.Folders(config.TARGET_SUBFOLDER)
                self.log(f"Đã mở folder: {config.TARGET_SUBFOLDER}")
            except:
                self.log(f"LỖI: Không thấy folder '{config.TARGET_SUBFOLDER}' trong Inbox!")
                return

            messages = target_folder.Items
            messages.Sort("[ReceivedTime]", True)
            
            target_sender = self.sender_entry.get().strip().lower()
            self.data = []
            for item in self.tree.get_children(): self.tree.delete(item)

            self.log(f"Đang lọc email từ: '{target_sender}'...")
            
            # Duyệt tối đa 1000 mail gần nhất
            for i in range(1, min(1001, len(messages))):
                msg = messages.Item(i)
                try:
                    if msg.Class == 43 and target_sender in msg.SenderName.lower():
                        row_dict = {}
                        if self.available_columns["Date"].get(): row_dict["Date"] = msg.ReceivedTime.strftime("%Y-%m-%d %H:%M")
                        if self.available_columns["Subject"].get(): row_dict["Subject"] = msg.Subject
                        if self.available_columns["Sender"].get(): row_dict["Sender"] = msg.SenderName
                        if self.available_columns["Body Snippet"].get(): row_dict["Body Snippet"] = msg.Body[:60].strip()
                        if self.available_columns["Importance"].get(): row_dict["Importance"] = "High" if msg.Importance == 2 else "Normal"
                        
                        vals = [row_dict[c] for c in selected_cols]
                        self.data.append(row_dict)
                        self.tree.insert("", "end", values=vals)
                except: continue

            if self.data:
                self.btn_json.config(state='normal')
                self.log(f"Tìm thấy {len(self.data)} mail. Mời bạn thực hiện Bước 2.")
            else:
                self.log("Không tìm thấy email nào khớp điều kiện.")

        except Exception as e:
            self.log(f"LỖI Outlook: {str(e)}")

    def handle_export_json(self):
        self.log("Đang tối ưu dữ liệu (Làm sạch tiêu đề, xóa trùng)...")
        try:
            df = pd.DataFrame(self.data)
            # Xử lý làm sạch Subject
            if "Subject" in df.columns:
                df['Subject'] = df['Subject'].str.replace(r'^(Re:\s*|Fwd:\s*|RE:\s*|FW:\s*)', '', regex=True).str.strip()
            
            df = df.drop_duplicates()
            
            # Xuất file JSON
            output_path = os.path.abspath(config.OUTPUT_JSON_FILE)
            with open(config.OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(df.to_dict(orient='records'), f, ensure_ascii=False, indent=4)
            
            self.temp_df = df
            self.btn_sheets.config(state='normal', bg="#4CAF50")
            self.log(f"Đã xuất JSON tại: {output_path}")
            self.log(">>> NẾU HÀI LÒNG, bấm Bước 3 để đẩy lên Google Sheets.")
            messagebox.showinfo("JSON Ready", "File JSON đã sẵn sàng để kiểm tra.")
        except Exception as e:
            self.log(f"LỖI JSON: {str(e)}")

    def push_to_sheets(self):
        self.log("--- BẮT ĐẦU QUY TRÌNH PUSH SHEETS ---")
        try:
            # 1. Xác định đường dẫn credentials
            base_dir = os.path.dirname(os.path.abspath(__file__))
            credentials_path = os.path.join(base_dir, config.CREDENTIALS_FILE)
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, config.SCOPES)
            client = gspread.authorize(creds)
            
            # 2. Kiểm tra việc kết nối file
            self.log(f"Đang tìm kiếm Spreadsheet có tên: '{config.GOOGLE_SHEET_NAME}'...")
            try:
                spreadsheet = client.open(config.GOOGLE_SHEET_NAME)
                # LOG CHI TIẾT: Hiện ID của file để bạn đối chiếu trên URL trình duyệt
                self.log(f"KẾT NỐI THÀNH CÔNG!")
                self.log(f"ID file: {spreadsheet.id}")
                self.log(f"Đường dẫn file: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
            except gspread.exceptions.SpreadsheetNotFound:
                self.log(f"LỖI: Không tìm thấy file nào tên '{config.GOOGLE_SHEET_NAME}'")
                return

            # 3. Kiểm tra Tab (Worksheet)
            sheet = spreadsheet.sheet1
            self.log(f"Đang ghi vào Tab (Worksheet): '{sheet.title}'")
            
            # 4. Chuẩn bị dữ liệu
            data_to_push = [self.temp_df.columns.values.tolist()] + self.temp_df.values.tolist()
            num_rows = len(data_to_push)
            
            self.log(f"Đang chuẩn bị đẩy {num_rows} dòng dữ liệu (bao gồm header)...")
            
            # 5. Thực hiện ghi
            sheet.clear()
            # Sử dụng phương thức update với xác nhận phản hồi rõ ràng
            response = sheet.update(range_name='A1', values=data_to_push)
            
            # LOG CHI TIẾT: Phản hồi từ Google về số ô đã cập nhật
            updated_cells = response.get('updatedCells', 0)
            if updated_cells > 0:
                self.log(f"XÁC NHẬN: Đã cập nhật thành công {updated_cells} ô dữ liệu.")
                messagebox.showinfo("Thành công", f"Đã đẩy {num_rows} dòng lên Google Sheets!")
            else:
                self.log("CẢNH BÁO: API báo thành công nhưng 0 ô được cập nhật. Hãy kiểm tra lại file.")

            self.btn_sheets.config(state='disabled', bg="#cccccc")
            
        except Exception as e:
            self.log(f"LỖI HỆ THỐNG: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GetNewTaskApp(root)
    root.mainloop()