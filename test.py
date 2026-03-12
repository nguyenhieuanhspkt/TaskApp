import json
from pathlib import Path

path = Path("data.json")

with open(path, "r", encoding="utf-8") as f:
    old_data = json.load(f)

# Kiểm tra nếu đã có schema_version thì bỏ qua
if isinstance(old_data, dict) and "schema_version" in old_data:
    print("✅ File đã có schema_version, không cần cập nhật.")
else:
    new_data = {
        "schema_version": 1,
        "tasks": old_data
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    print("✅ Đã thêm schema_version và bọc lại dữ liệu.")
