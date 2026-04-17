import pyrebase
import os
FIREBASE_URL = os.getenv("FIREBASE_URL")
SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")



import os
import firebase_admin
from firebase_admin import credentials, db

def get_db():
    """
    Khởi tạo Firebase nếu chưa có và trả về module db.
    """
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            "databaseURL": os.getenv("FIREBASE_URL")
        })
    return db



# Cấu hình Firebase
firebase_config = {
    "apiKey": os.getenv("MYFIREBASEAPIKEY"),         # API key riêng nếu cần
    "authDomain": FIREBASE_URL,                     # domain dựa trên URL
    "databaseURL": FIREBASE_URL,                    # database URL
    "storageBucket": f"{FIREBASE_URL.split('//')[1].split('.')[0]}.appspot.com",
    "serviceAccount": SERVICE_ACCOUNT_PATH          # path đến JSON key
}
# firebase = pyrebase.initialize_app(firebase_config)
# db = firebase.database()

# # def firebase_get_all_tasks():
#     """
#     Lấy tất cả task từ Firebase Realtime Database
#     Trả về dict {id: task_dict}
#     """
#     print("[DEBUG] Bắt đầu lấy dữ liệu từ Firebase...")
    
#     try:
#         data = db.child("tasks").get()
#         tasks = {}
#         if data.each():
#             for item in data.each():
#                 task_id = int(item.key())  # key của Firebase
#                 task_value = item.val()    # dict chứa task data
#                 tasks[task_id] = task_value
#         return tasks
#     except Exception as e:
#         print(f"[ERROR] Lỗi khi lấy task từ Firebase: {e}")
#         return {}

