from ui.common_imports import *
from services.firebase_services import get_db

class TaskService(QObject):
    def __init__(self,parent=None):
        super().__init__(parent)  
        self.tasks = {}  # dict lưu tất cả task
        # Load cấu hình email một lần
        self.email = os.getenv("MYEMAIL")
        self.password = os.getenv("MYPASSEMAIL")
        self.ews_url = os.getenv("EWS_URL")
        
        self.tasks = {}
        self.db = get_db()  # lấy db đã init

    # ---------------- LOAD / SAVE (firebase) ----------------
    def load_tasks(self):
        """
        Load task từ Firebase LIST (root /)
        Convert sang dict: {id: task}
        """
        ref = self.db.reference("/")   # ⚠ root, không phải /tasks
        data = ref.get()

        tasks_dict = {}

        if isinstance(data, list):
            for index, task in enumerate(data):
                if not task:
                    continue

                task_id = task.get("id", index)
                task["id"] = task_id
                task["_fb_index"] = index  # 🔥 lưu index Firebase để edit/delete
                tasks_dict[task_id] = task

        elif isinstance(data, dict):
            # phòng trường hợp lỡ có dict
            for k, v in data.items():
                if isinstance(v, dict):
                    task_id = v.get("id", int(k))
                    v["id"] = task_id
                    v["_fb_index"] = int(k)
                    tasks_dict[task_id] = v

        self.tasks = tasks_dict
        print(f"[DEBUG] Load {len(self.tasks)} tasks")
        return self.tasks


    def add_or_edit_task(self, task_data, edit_mode=False, edit_index=None):
        ref = self.db.reference("/tasks")

        # --- Chỉnh sửa task ---
        if edit_mode and edit_index in self.tasks:
            print(f"[DEBUG] Edit task id={edit_index}")
            # Cập nhật local dict
            self.tasks[edit_index].update(task_data)
            # Update Firebase
            ref.child(str(edit_index)).update(task_data)
            print(f"[DEBUG] Task id={edit_index} đã được cập nhật")
            return edit_index

        # --- Thêm task mới ---
        else:
            existing_ids = set(self.tasks.keys())
            # Tìm ID trống ≥62
            new_id = next((i for i in range(62, 10000) if i not in existing_ids), None)
            if new_id is None:
                raise ValueError("Không còn ID trống!")

            # Thêm thông tin bổ sung
            task_data_full = {
                "id": new_id,
                "folder": f"Thẩm định {new_id}",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "edited_at": "",
                **task_data
            }

            # Cập nhật local dict
            self.tasks[new_id] = task_data_full
            
            # Lưu lên Firebase
            ref.child(str(new_id)).set(task_data_full)
            print(f"[DEBUG] Task id={new_id} đã được lưu")
            return new_id
    
    def save_task_by_id(self, task_obj):
        """
        Lưu 1 task cụ thể lên Firebase
        task_obj: dict, phải có key 'id'
        """
        try:
            from firebase_admin import db

            # Kiểm tra task hợp lệ
            if not isinstance(task_obj, dict) or "id" not in task_obj:
                print("[DEBUG] Task không hợp lệ:", task_obj)
                return

            task_id = task_obj["id"]

            # Lưu task lên Firebase
            ref = db.reference(f'/tasks/{task_id}')
            ref.set(task_obj)
            print(f"[DEBUG] Lưu thành công task id={task_id} lên Firebase")

            # Cập nhật local dict
            self.tasks[task_id] = task_obj

        except Exception as fb_err:
            print("[DEBUG] Không lưu được task:", fb_err)
            
  
    def delete_task(self, task_id):
        if task_id in self.tasks:
            try:
                from firebase_admin import db

                # Xóa task trên Firebase
                ref = db.reference(f'/tasks/{task_id}')
                ref.delete()
                print(f"[DEBUG] Xóa thành công task id={task_id} trên Firebase")

                # Xóa task khỏi dict local
                del self.tasks[task_id]

            except Exception as fb_err:
                print("[DEBUG] Không xóa được task:", fb_err) 
          
    
  
            
            
            
            
    def fetch_emails(self, email, password, ews_url):
        """Kết nối server, tải danh sách email và trả về list."""
        from services.email_service import EmailLoaderThread

        thread = EmailLoaderThread(email, password, ews_url)
        return thread  # để UI gắn signal và start thread
    def star_load_email(self):
        # --- Lấy thông tin đăng nhập email từ .env ---
        MYEMAIL = os.getenv("MYEMAIL")
        MYPASS = os.getenv("MYPASSEMAIL")
        EWS_URL = os.getenv("EWS_URL")
        if not all([MYEMAIL, MYPASS, EWS_URL]):
            QMessageBox.warning(self, "Thiếu thông tin", "Chưa cấu hình đầy đủ thông tin email.")
            return
          # --- Lấy thông tin đăng nhập email từ .env ---
        
    def returnThread(self):
        # --- Lấy thông tin đăng nhập email từ .env ---
        MYEMAIL = os.getenv("MYEMAIL")
        MYPASS = os.getenv("MYPASSEMAIL")
        EWS_URL = os.getenv("EWS_URL")
        thread = self.fetch_emails(MYEMAIL, MYPASS, EWS_URL)
        self.email_thread = thread
        return thread
        
    def create_task_from_email(self, msg, author):
        existing_ids = [t.get("id", 0) for t in self.tasks]
        new_id = max(existing_ids + [61]) + 1

        new_task = {
            "id": new_id,
            "folder": f"Thẩm định {new_id}",
            "title": msg.get('subject', "(Không có tiêu đề)"),
            "start_date": msg.get('date', "").split()[0],
            "due_date": "",
            "deadline": "",
            "status": "doing",
            "author": author,
            "content": "",
            "created_at": msg.get('date', ""),
            "edited_at": "",
        }

        self.tasks.append(new_task)
        self.save_tasks()

        return new_task
    
    