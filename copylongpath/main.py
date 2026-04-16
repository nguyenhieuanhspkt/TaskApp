import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import threading

class CopyTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Công cụ Copy Network Siêu cấp - Robocopy GUI")
        self.root.geometry("650x450")

        # --- Giao diện chọn đường dẫn ---
        tk.Label(root, text="Thư mục nguồn (Source):", font=('Segoe UI', 10, 'bold')).pack(pady=(10, 0), anchor="w", padx=20)
        self.src_ent = tk.Entry(root, width=70)
        self.src_ent.pack(side="top", pady=5, padx=20)
        tk.Button(root, text="Chọn Nguồn", command=self.browse_src).pack(anchor="e", padx=20)

        tk.Label(root, text="Thư mục đích (Network/Drive):", font=('Segoe UI', 10, 'bold')).pack(pady=(10, 0), anchor="w", padx=20)
        self.dst_ent = tk.Entry(root, width=70)
        self.dst_ent.pack(side="top", pady=5, padx=20)
        tk.Button(root, text="Chọn Đích", command=self.browse_dst).pack(anchor="e", padx=20)

        # --- Khu vực hiển thị Log ---
        tk.Label(root, text="Tiến độ thực hiện:", font=('Segoe UI', 10)).pack(pady=(10, 0), anchor="w", padx=20)
        self.log_area = scrolledtext.ScrolledText(root, width=75, height=10, font=('Consolas', 9))
        self.log_area.pack(pady=5, padx=20)

        # --- Nút điều khiển ---
        self.start_btn = tk.Button(root, text="BẮT ĐẦU COPY", bg="#2ecc71", fg="white", 
                                   font=('Segoe UI', 12, 'bold'), command=self.start_thread)
        self.start_btn.pack(pady=20)

    def browse_src(self):
        path = filedialog.askdirectory()
        if path: self.src_ent.delete(0, tk.END); self.src_ent.insert(0, path)

    def browse_dst(self):
        path = filedialog.askdirectory()
        if path: self.dst_ent.delete(0, tk.END); self.dst_ent.insert(0, path)

    def run_copy(self):
        src = self.src_ent.get()
        dst = self.dst_ent.get()

        if not src or not dst:
            messagebox.showerror("Lỗi", "Vui lòng chọn đầy đủ nguồn và đích!")
            return

        self.start_btn.config(state="disabled", text="Đang Copy...")
        self.log_area.insert(tk.END, f"Đang khởi tạo Robocopy...\nNguồn: {src}\nĐích: {dst}\n{'-'*40}\n")
        
        # Lệnh Robocopy tối ưu cho Network và Long Path
        # /NDL: Không liệt kê tên thư mục trong log (cho nhanh)
        # /TEE: Vừa ghi file vừa hiển thị ra màn hình
        command = ["robocopy", src, dst, "/E", "/Z", "/MT:16", "/R:3", "/W:5", "/TS", "/FP"]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                   text=True, shell=True, bufsize=1)

        for line in process.stdout:
            self.log_area.insert(tk.END, line)
            self.log_area.see(tk.END) # Tự động cuộn xuống dưới
            self.root.update_idletasks()

        process.wait()
        self.start_btn.config(state="normal", text="BẮT ĐẦU COPY")
        messagebox.showinfo("Hoàn tất", "Quá trình copy đã kết thúc!")

    def start_thread(self):
        # Chạy trong thread riêng để không làm treo giao diện
        thread = threading.Thread(target=self.run_copy)
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = CopyTool(root)
    root.mainloop()