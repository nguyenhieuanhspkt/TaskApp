import os
import time
import glob
from pathlib import Path
from typing import Optional, Tuple, List

import pandas as pd
from PyQt5 import QtWidgets, QtGui, QtCore

# Cập nhật Import theo bản mới nhất của PandasAI
from pandasai import SmartDataframe
from pandasai.llm import Ollama

# --- Worker chạy nền để không treo UI khi AI đang suy nghĩ ---
class AnalysisWorker(QtCore.QThread):
    resultReady = QtCore.pyqtSignal(str)
    chartReady = QtCore.pyqtSignal(str)
    errorOccurred = QtCore.pyqtSignal(str)

    def __init__(self, df, prompt, model_name, charts_dir):
        super().__init__()
        self.df = df
        self.prompt = prompt
        self.model_name = model_name
        self.charts_dir = charts_dir

    def run(self):
        try:
            # Khởi tạo LLM theo cấu trúc module mới
            llm = Ollama(model=self.model_name, base_url="http://localhost:11434")
            
            # Cấu hình SmartDataframe
            config = {
                "llm": llm,
                "save_charts": True,
                "save_charts_path": str(self.charts_dir),
                "response_parser": None # Để mặc định cho đơn giản
            }
            
            sdf = SmartDataframe(self.df, config=config)
            response = sdf.chat(self.prompt)
            
            self.resultReady.emit(str(response))
            
            # Tìm biểu đồ mới nhất
            files = glob.glob(str(self.charts_dir / "*.png"))
            if files:
                latest = max(files, key=os.path.getmtime)
                self.chartReady.emit(latest)
                
        except Exception as e:
            self.errorOccurred.emit(str(e))

# --- Widget Module chính ---
class AIAnalysisWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.df = None
        self.charts_dir = Path.cwd() / "charts"
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        self._init_ui()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Top Bar
        top = QtWidgets.QHBoxLayout()
        self.btn_open = QtWidgets.QPushButton("📂 Mở tệp")
        self.btn_open.clicked.connect(self.open_file)
        self.lbl_file = QtWidgets.QLabel("Chưa có dữ liệu")
        self.model_input = QtWidgets.QLineEdit("mistral")
        self.model_input.setFixedWidth(100)
        
        top.addWidget(self.btn_open)
        top.addWidget(self.lbl_file, stretch=1)
        top.addWidget(QtWidgets.QLabel("Model:"))
        top.addWidget(self.model_input)
        layout.addLayout(top)

        # Body
        body = QtWidgets.QHBoxLayout()
        
        # Chat
        chat_layout = QtWidgets.QVBoxLayout()
        self.chat_view = QtWidgets.QTextEdit()
        self.chat_view.setReadOnly(True)
        self.input_box = QtWidgets.QPlainTextEdit()
        self.input_box.setFixedHeight(70)
        self.btn_send = QtWidgets.QPushButton("Gửi ▶")
        self.btn_send.clicked.connect(self.start_analysis)
        
        chat_layout.addWidget(self.chat_view)
        chat_layout.addWidget(self.input_box)
        chat_layout.addWidget(self.btn_send)

        # Chart
        self.chart_label = QtWidgets.QLabel("Biểu đồ")
        self.chart_label.setMinimumWidth(400)
        self.chart_label.setAlignment(QtCore.Qt.AlignCenter)
        self.chart_label.setStyleSheet("border: 1px dashed #ccc; background: white;")
        
        body.addLayout(chat_layout, stretch=3)
        body.addWidget(self.chart_label, stretch=2)
        layout.addLayout(body)

        # Shortcut
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self, activated=self.start_analysis)

    def open_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Mở file", "", "Data (*.csv *.xlsx)")
        if path:
            self.df = pd.read_csv(path) if path.endswith('.csv') else pd.read_excel(path)
            self.lbl_file.setText(os.path.basename(path))

    def start_analysis(self):
        prompt = self.input_box.toPlainText().strip()
        if not prompt or self.df is None: return
        
        self.chat_view.append(f"<b>Bạn:</b> {prompt}")
        self.input_box.clear()
        self.btn_send.setEnabled(False)

        # Chạy worker
        self.worker = AnalysisWorker(self.df, prompt, self.model_input.text(), self.charts_dir)
        self.worker.resultReady.connect(self.on_result)
        self.worker.chartReady.connect(self.on_chart)
        self.worker.errorOccurred.connect(self.on_error)
        self.worker.finished.connect(lambda: self.btn_send.setEnabled(True))
        self.worker.start()

    def on_result(self, text):
        self.chat_view.append(f"<span style='color:#2980b9;'><b>AI:</b> {text}</span>")

    def on_chart(self, path):
        pix = QtGui.QPixmap(path)
        self.chart_label.setPixmap(pix.scaled(self.chart_label.size(), QtCore.Qt.KeepAspectRatio))

    def on_error(self, err):
        self.chat_view.append(f"<b style='color:red;'>Lỗi:</b> {err}")