# gui_main.py

import sys
from typing import Optional

import pandas as pd

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox,
    QTextEdit, QTableView, QHeaderView, QAbstractItemView, QGroupBox, QSizePolicy
)

from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant

from tskt_parser.processor import TSKTProcessor
from common.docx_reader import docx_single_table_to_df
from common.excel_exporter import export_to_excel


# ================= DataFrame Model =================
class DataFrameModel(QAbstractTableModel):

    def __init__(self, df: pd.DataFrame = pd.DataFrame()):
        super().__init__()
        self._df = df

    def setDataFrame(self, df: pd.DataFrame):
        self.beginResetModel()
        self._df = df.copy()
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._df)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            val = self._df.iat[index.row(), index.column()]
            return "" if pd.isna(val) else str(val)
        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):

        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Horizontal:
            return self._df.columns[section]

        return section + 1


# ================= GUI =================
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.processor = TSKTProcessor()

        self.df_raw: Optional[pd.DataFrame] = None
        self.df_eval: Optional[pd.DataFrame] = None

        self.setWindowTitle("TSKT Parser")
        self.resize(1100, 700)

        self.init_ui()

    def init_ui(self):

        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)

        # ---------- FILE ----------
        grp_file = QGroupBox("Tệp dữ liệu")

        file_layout = QHBoxLayout(grp_file)

        self.txt_docx = QLineEdit()
        btn_docx = QPushButton("Chọn DOCX")
        btn_docx.clicked.connect(self.choose_docx)

        self.txt_excel = QLineEdit()
        btn_excel = QPushButton("Chọn Excel")
        btn_excel.clicked.connect(self.choose_excel)

        file_layout.addWidget(QLabel("DOCX"))
        file_layout.addWidget(self.txt_docx)
        file_layout.addWidget(btn_docx)

        file_layout.addSpacing(20)

        file_layout.addWidget(QLabel("Output"))
        file_layout.addWidget(self.txt_excel)
        file_layout.addWidget(btn_excel)

        # ---------- ACTION ----------
        action_layout = QHBoxLayout()

        btn_preview = QPushButton("Preview")
        btn_preview.clicked.connect(self.preview)

        btn_run = QPushButton("Process")
        btn_run.clicked.connect(self.process)

        action_layout.addStretch()
        action_layout.addWidget(btn_preview)
        action_layout.addWidget(btn_run)

        # ---------- TABLE ----------
        self.table = QTableView()
        self.model = DataFrameModel(pd.DataFrame())

        self.table.setModel(self.model)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        # ---------- SUMMARY ----------
        self.txt_summary = QTextEdit()
        self.txt_summary.setReadOnly(True)

        layout.addWidget(grp_file)
        layout.addLayout(action_layout)
        layout.addWidget(self.table, 4)
        layout.addWidget(self.txt_summary, 1)

    # -----------------------------
    def choose_docx(self):

        path, _ = QFileDialog.getOpenFileName(self, "DOCX", "", "*.docx")

        if path:
            self.txt_docx.setText(path)

    def choose_excel(self):

        path, _ = QFileDialog.getSaveFileName(self, "Excel", "", "*.xlsx")

        if path:
            self.txt_excel.setText(path)

    # -----------------------------
    def preview(self):

        path = self.txt_docx.text()

        df = docx_single_table_to_df(path)

        self.df_raw = df

        self.model.setDataFrame(df.head(50))

        self.txt_summary.setText("Preview 50 rows")

    # -----------------------------
    def process(self):

        if self.df_raw is None:
            QMessageBox.warning(self, "Error", "Load DOCX first")
            return

        df_eval, summary = self.processor.process_dataframe(self.df_raw)

        self.df_eval = df_eval

        self.model.setDataFrame(df_eval.head(100))

        export_to_excel(df_eval, summary, self.txt_excel.text())

        self.txt_summary.setText(summary.to_string())


# ================= ENTRY =================
def main():

    app = QApplication(sys.argv)

    win = MainWindow()

    win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()