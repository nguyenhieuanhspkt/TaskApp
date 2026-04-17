class EmailLoaderThread(QThread):
    progress = pyqtSignal(str)        # gửi message debug về UI
    finished = pyqtSignal(list)       # danh sách email hợp lệ
    error = pyqtSignal(str)           # lỗi

    def __init__(self, email, password, ews_url):
        super().__init__()
        self.email = email
        self.password = password
        self.ews_url = ews_url
        self._cancel = False

    def run(self):
        try:
            warnings.filterwarnings("ignore", category=UserWarning)
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter

            self.progress.emit("⏳ Tạo credentials...")
            creds = Credentials(username=self.email, password=self.password)
            config = Configuration(service_endpoint=self.ews_url, credentials=creds)

            self.progress.emit("⏳ Kết nối account EWS...")
            account = Account(
                primary_smtp_address=self.email,
                credentials=creds,
                autodiscover=False,
                config=config,
                access_type=DELEGATE,
            )

            self.progress.emit("⏳ Truy cập folder ThamDinh...")
            try:
                folder = account.inbox / "ThamDinh"
                if folder.folder_class != 'IPF.Note':
                    self.finished.emit([])
                    return
            except Exception as e:
                self.error.emit(f"Không tìm thấy folder ThamDinh: {e}")
                return

            self.progress.emit("⏳ Đang load email...")
            # messages = list(folder.all().order_by('-datetime_received')[:6])

            batch_size = 50
            filtered = []

            all_messages = folder.all().only('subject', 'datetime_received', 'sender')[:batch_size]
            messages = list(all_messages)

            # for msg in messages:  # không cần islice nữa
            #     if self._cancel:
            #         self.finished.emit([])
            #         return
            #     if msg.sender and msg.sender.email_address.lower() == "hoangbh@vinhtan4tpp.evn.vn":
            #         filtered.append(msg)
            self.finished.emit(messages)

            # self.finished.emit(messages)


        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        self._cancel = True

# ----------------------------- #
#   ⚙️  Cấu hình hộp thoại email   #
# ----------------------------- #

class EmailDialog(QDialog):
    def __init__(self, table: QTableWidget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chọn email")
        self.selected_item = None
        self.table = table
        layout = QVBoxLayout()
        # Thêm table vào layout
        layout.addWidget(self.table)
        # Nút chọn
        btn = QPushButton("Chọn")
        btn.clicked.connect(self.choose)
        layout.addWidget(btn)
        
        self.setLayout(layout)
        self.resize(800, 400) 
        self.list_widget = QListWidget()
        self.list_widget.setWordWrap(True)  # wrap text dài
    def choose(self):
        row = self.table.currentRow()
        if 0 <= row < self.table.rowCount():
            # Lấy dữ liệu từ các cột
            subject_item = self.table.item(row, 0)
            sender_item = self.table.item(row, 1)
            date_item = self.table.item(row, 2)

            self.selected_item = {
                'subject': subject_item.text() if subject_item else '',
                'sender': sender_item.text() if sender_item else '',
                'date': date_item.text() if date_item else ''
            }
            self.accept()
        else:
            QMessageBox.warning(self, "Lỗi", "Bạn chưa chọn email.")

