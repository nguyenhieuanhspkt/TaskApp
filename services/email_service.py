from PyQt5.QtCore import QThread, pyqtSignal
from exchangelib import Account, Credentials, Configuration, DELEGATE
import warnings
from ui.common_imports import *

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

            self.progress.emit("⏳ Đang load 30 email...")
            # messages = list(folder.all().order_by('-datetime_received')[:6])

            batch_size = 30
            filtered = []

            all_messages = folder.all().only('subject', 'datetime_received', 'sender')[:batch_size]
            messages = list(all_messages)
            self.finished.emit(messages)

            # self.finished.emit(messages)


        except Exception as e:
            self.error.emit(str(e))
    def cancel(self):
        self._cancel = True