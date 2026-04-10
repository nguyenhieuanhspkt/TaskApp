import os
import shutil
import subprocess
import ctypes

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def get_size(path):
    """Tính dung lượng của một file hoặc thư mục (Bytes)"""
    total_size = 0
    try:
        if os.path.isfile(path):
            return os.path.getsize(path)
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
    except: pass
    return total_size

def format_bytes(size):
    """Chuyển đổi Bytes sang MB hoặc GB cho dễ đọc"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024: return f"{size:.2f} {unit}"
        size /= 1024

def clean_c_drive():
    if not is_admin():
        print("!!! VUI LÒNG CHẠY BẰNG QUYỀN ADMINISTRATOR !!!")
        return

    print("=== HỆ THỐNG DỌN DẸP & BÁO CÁO - HIẾU NGUYỄN ===")
    
    # Lấy dung lượng trống của ổ C trước khi dọn
    usage_before = shutil.disk_usage("C:/").free
    
    total_files_deleted = 0
    total_size_deleted = 0

    user_path = os.path.expanduser("~")
    paths_to_clean = [
        os.environ.get('TEMP'),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'),
        os.path.join(user_path, ".cache"),
        os.path.join(os.environ.get('LOCALAPPDATA'), 'CrashDumps'),
        os.path.join(os.environ.get('LOCALAPPDATA'), 'npm-cache'),
        os.path.join(os.environ.get('LOCALAPPDATA'), 'pip', 'cache'),
    ]

    print("\n[!] Đang tiến hành quét và xóa...")

    for path in paths_to_clean:
        if path and os.path.exists(path):
            current_path_size = get_size(path)
            files_in_path = 0
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    try:
                        if os.path.isfile(item_path) or os.path.islink(item_path):
                            os.unlink(item_path)
                            files_in_path += 1
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                            files_in_path += 1
                    except: continue
                
                total_files_deleted += files_in_path
                print(f"    - Đã dọn: {path} ({format_bytes(current_path_size)})")
            except: continue

    # Chạy các lệnh hệ thống
    print("\n[!] Đang thực thi các lệnh hệ thống (Powercfg, Pip, NPM)...")
    subprocess.run(["pip", "cache", "purge"], capture_output=True)
    subprocess.run(["npm", "cache", "clean", "--force"], shell=True, capture_output=True)
    subprocess.run(["powercfg", "-h", "off"], capture_output=True)

    # Tính toán kết quả cuối cùng
    usage_after = shutil.disk_usage("C:/").free
    gain = usage_after - usage_before

    print("\n" + "="*45)
    print("                BÁO CÁO DỌN DẸP")
    print("="*45)
    print(f"[*] Tổng số mục đã xử lý:  {total_files_deleted} files/folders")
    print(f"[*] Dung lượng lấy lại được: ~ {format_bytes(gain)}")
    print(f"[*] Trạng thái ổ C hiện tại: {format_bytes(usage_after)} trống")
    print("="*45)

if __name__ == "__main__":
    clean_c_drive()
    input("\nNhấn Enter để đóng...")