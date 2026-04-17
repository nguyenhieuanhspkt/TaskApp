import json
from datetime import datetime, timedelta

def excel_date_to_str(serial):
    try:
        # Chuyển đổi số serial Excel sang chuỗi YYYY-MM-DD
        serial = int(serial)
        date = datetime(1899, 12, 30) + timedelta(days=serial)
        return date.strftime("%Y-%m-%d")
    except:
        # Nếu đã là chuỗi "2025-07-17 00:00:00", chỉ lấy phần ngày
        return str(serial).split(' ')[0]

def normalize_task(task, target_year):
    # 1. Chuẩn hóa Year thành String
    task['year'] = str(task.get('year', target_year))
    
    # 2. Chuyển đổi done -> status (Kiểu 2026)
    if 'done' in task:
        if task['done'] is True:
            task['status'] = 'done'
        else:
            task['status'] = task.get('status', 'doing')
        del task['done'] # Xóa trường cũ

    # 3. Chuẩn hóa ngày tháng
    for date_key in ['start_date', 'due_date', 'deadline']:
        if date_key in task and task[date_key]:
            val = str(task[date_key])
            if val.isdigit() and len(val) <= 5: # Nếu là số serial Excel
                task[date_key] = excel_date_to_str(val)
            else:
                task[date_key] = val.split(' ')[0] # Lấy YYYY-MM-DD

    # 4. Đảm bảo có mảng history
    if 'history' not in task:
        task['history'] = []
        if task.get('created_at'):
            task['history'].append(f"{task['created_at']}: Tạo mới (Import)")

    return task

# TIẾN HÀNH TRỘN
with open('tasks_2025.json', 'r', encoding='utf-8') as f:
    data_2025 = json.load(f)

with open('tasks_2026.json', 'r', encoding='utf-8') as f:
    data_2026 = json.load(f)

# Chuẩn hóa từng bản ghi
merged_list = []
for item in data_2025:
    merged_list.append(normalize_task(item, "2025"))

for item in data_2026:
    merged_list.append(normalize_task(item, "2026"))

# Lưu file cuối cùng
with open('merged_tasks_firebase.json', 'w', encoding='utf-8') as f:
    json.dump(merged_list, f, ensure_ascii=False, indent=4)

print("Đã nối và chuẩn hóa thành công!")