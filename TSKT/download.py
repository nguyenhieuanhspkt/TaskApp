import os
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QPushButton, QVBoxLayout
from huggingface_hub import snapshot_download
class DownloadWorker(QThread):
    # Định nghĩa các tín hiệu để gửi dữ liệu về giao diện
    progress_sig = pyqtSignal(str)  # Gửi dòng chữ thông báo
    finished_sig = pyqtSignal(str)  # Gửi đường dẫn thư mục khi xong

    def __init__(self, dest_folder):
        super().__init__()
        self.dest_folder = dest_folder

    def run(self):
        try:
            self.progress_sig.emit("📡 Đang kết nối tới Hugging Face...")
            
            # Tải mô hình BGE-M3
            snapshot_download(
                repo_id="BAAI/bge-m3",
                local_dir=self.dest_folder,
                local_dir_use_symlinks=False
            )
            
            self.finished_sig.emit(self.dest_folder)
        except Exception as e:
            self.progress_sig.emit(f"❌ Lỗi: {str(e)}")