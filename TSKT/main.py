import sys
import os
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QFont
from huggingface_hub import snapshot_download

# Import từ file engine.py của bạn
from engine import WorkerThread 

class DownloadWorker(QThread):
    progress_sig = pyqtSignal(str)
    finished_sig = pyqtSignal(bool, str)

    def __init__(self, dest_folder):
        super().__init__()
        self.dest_folder = dest_folder

    def run(self):
        try:
            self.progress_sig.emit("📡 Đang tải bộ não AI BGE-M3 (2.3GB)... Vui lòng xem tiến trình tại Console.")
            snapshot_download(
                repo_id="BAAI/bge-m3",
                local_dir=self.dest_folder,
                local_dir_use_symlinks=False
            )
            self.finished_sig.emit(True, self.dest_folder)
        except Exception as e:
            self.finished_sig.emit(False, str(e))

class AuditApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Audit Vật Tư Professional - BGE-M3")
        self.resize(1300, 850)
        
        # Lưu cấu hình ứng dụng (Nhớ đường dẫn AI)
        self.settings = QSettings("AI_Audit_Tool", "AuditApp")
        self.model_path = self.settings.value("last_model_path", "")
        
        self.initUI()
        self.check_initial_ai()

    def initUI(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # --- PHẦN 1: CẤU HÌNH AI ---
        ai_group = QGroupBox("Cài đặt Hệ thống AI")
        ai_group.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; }")
        ai_lay = QHBoxLayout()
        
        self.btn_setup_ai = QPushButton("🧠 Cài đặt / Chọn Thư mục AI")
        self.btn_setup_ai.setMinimumHeight(40)
        self.btn_setup_ai.setStyleSheet("background-color: #8e44ad; color: white; border-radius: 5px;")
        
        self.lbl_ai_status = QLabel("Chưa thiết lập AI")
        self.lbl_ai_status.setStyleSheet("color: #7f8c8d; font-style: italic;")
        
        ai_lay.addWidget(self.btn_setup_ai, 1)
        ai_lay.addWidget(self.lbl_ai_status, 3)
        ai_group.setLayout(ai_lay)
        main_layout.addWidget(ai_group)

        # --- PHẦN 2: CHỌN FILE DỮ LIỆU ---
        file_lay = QHBoxLayout()
        self.btn_e = QPushButton("📁 Chọn Excel Kho")
        self.btn_w = QPushButton("📝 Chọn Word Hồ Sơ")
        for b in [self.btn_e, self.btn_w]:
            b.setMinimumHeight(40)
            file_lay.addWidget(b)
        main_layout.addLayout(file_lay)

        # --- PHẦN 3: ĐIỀU KHIỂN CHÍNH ---
        ctrl_lay = QHBoxLayout()
        self.btn_run = QPushButton("🚀 BẮT ĐẦU THẨM ĐỊNH")
        self.btn_run.setMinimumHeight(50)
        self.btn_run.setStyleSheet("background-color: #2c3e50; color: white; font-size: 14px; font-weight: bold;")
        
        self.btn_abort = QPushButton("🛑 DỪNG")
        self.btn_abort.setEnabled(False)
        self.btn_abort.setMinimumHeight(50)
        self.btn_abort.setStyleSheet("background-color: #c0392b; color: white;")
        
        ctrl_lay.addWidget(self.btn_run, 4)
        ctrl_lay.addWidget(self.btn_abort, 1)
        main_layout.addLayout(ctrl_lay)

        # --- PHẦN 4: TIẾN TRÌNH & TRẠNG THÁI ---
        self.pbar = QProgressBar()
        self.pbar.setStyleSheet("QProgressBar { border: 1px solid grey; border-radius: 5px; text-align: center; } "
                                "QProgressBar::chunk { background-color: #3498db; }")
        main_layout.addWidget(self.pbar)
        
        self.lbl_status = QLabel("Sẵn sàng xử lý")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_status)

        # --- PHẦN 5: BẢNG KẾT QUẢ ---
        self.table = QTableView()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Không cho sửa bảng
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.model = QStandardItemModel()
        self.table.setModel(self.model)
        main_layout.addWidget(self.table)

        # --- Connections ---
        self.btn_setup_ai.clicked.connect(self.handle_ai_setup)
        self.btn_e.clicked.connect(self.select_excel)
        self.btn_w.clicked.connect(self.select_word)
        self.btn_run.clicked.connect(self.run_process)
        self.btn_abort.clicked.connect(self.abort_process)

    # --- LOGIC AI ---
    def is_model_valid(self, path):
        if not path or not os.path.exists(path): return False
        return os.path.exists(os.path.join(path, "pytorch_model.bin"))

    def check_initial_ai(self):
        if self.is_model_valid(self.model_path):
            self.lbl_ai_status.setText(f"✅ AI Sẵn sàng: {self.model_path}")
            self.lbl_ai_status.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.model_path = ""
            self.lbl_ai_status.setText("❌ Chưa có AI. Vui lòng Chọn thư mục hoặc Tải về.")

    def handle_ai_setup(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa AI")
        if not folder: return

        if self.is_model_valid(folder):
            self.save_ai_path(folder)
        else:
            res = QMessageBox.question(self, "Tải AI", "Thư mục trống. Tải bộ não AI BGE-M3 (2.3GB) về đây?", 
                                       QMessageBox.Yes|QMessageBox.No)
            if res == QMessageBox.Yes:
                self.btn_setup_ai.setEnabled(False)
                self.dl_worker = DownloadWorker(folder)
                self.dl_worker.progress_sig.connect(self.lbl_status.setText)
                self.dl_worker.finished_sig.connect(self.on_dl_finished)
                self.dl_worker.start()

    def save_ai_path(self, path):
        self.model_path = path
        self.settings.setValue("last_model_path", path)
        self.lbl_ai_status.setText(f"✅ AI Sẵn sàng: {path}")
        self.lbl_ai_status.setStyleSheet("color: #27ae60; font-weight: bold;")

    def on_dl_finished(self, success, result):
        self.btn_setup_ai.setEnabled(True)
        if success:
            self.save_ai_path(result)
            QMessageBox.information(self, "Thành công", "Đã tải xong Bộ não AI!")
        else:
            QMessageBox.critical(self, "Lỗi", f"Tải AI thất bại: {result}")

    # --- LOGIC XỬ LÝ FILE ---
    def select_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn Excel Kho", "", "Excel (*.xlsx)")
        if path: 
            self.epath = path
            self.btn_e.setText(f"✔ {os.path.basename(path)}")
            self.btn_e.setStyleSheet("background-color: #d5f5e3;")

    def select_word(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn Word Hồ Sơ", "", "Word (*.docx)")
        if path: 
            self.wpath = path
            self.btn_w.setText(f"✔ {os.path.basename(path)}")
            self.btn_w.setStyleSheet("background-color: #d5f5e3;")

    def run_process(self):
        if not self.model_path:
            return QMessageBox.warning(self, "Thiếu AI", "Vui lòng cài đặt Bộ não AI trước!")
        if not hasattr(self, 'epath') or not hasattr(self, 'wpath'):
            return QMessageBox.warning(self, "Thiếu file", "Vui lòng chọn đủ 2 file Excel và Word!")
        
        self.btn_run.setEnabled(False)
        self.btn_abort.setEnabled(True)
        self.model.clear()
        self.pbar.setValue(0)
        
        self.worker = WorkerThread(self.epath, self.wpath, self.model_path)
        self.worker.progress.connect(self.pbar.setValue)
        self.worker.log_signal.connect(self.lbl_status.setText)
        self.worker.result_ready.connect(self.show_table)
        self.worker.finished.connect(self.cleanup)
        self.worker.start()

    def abort_process(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.requestInterruption()
            self.lbl_status.setText("🛑 Đang dừng hệ thống...")

    def cleanup(self):
        self.btn_run.setEnabled(True)
        self.btn_abort.setEnabled(False)
        self.lbl_status.setText("✅ Hoàn thành thẩm định")

    def show_table(self, df):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(df.columns)
        
        for _, row in df.iterrows():
            items = [QStandardItem(str(v)) for v in row]
            
            # Logic tô màu thông minh
            score_str = str(row["Điểm"]).replace('%', '')
            try: score_val = float(score_str)
            except: score_val = 0

            if "❌" in str(row["Trạng thái"]):
                color = QColor("#e74c3c") # Đỏ: Lệch
            elif score_val < 80:
                color = QColor("#f39c12") # Cam: Nghi ngờ (Cần check tay)
            else:
                color = QColor("#27ae60") # Xanh: Khớp tốt

            # Áp dụng màu cho cột Trạng thái và Điểm
            items[1].setForeground(color)
            items[3].setForeground(color)
            
            # Làm đậm các mục quan trọng
            font = QFont(); font.setBold(True)
            items[1].setFont(font)
            
            self.model.appendRow(items)
            
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Set style chung cho chuyên nghiệp
    app.setStyle("Fusion")
    win = AuditApp(); win.show()
    sys.exit(app.exec_())