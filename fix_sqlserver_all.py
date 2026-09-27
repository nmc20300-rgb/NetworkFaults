from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
UI = ROOT / "ui"
BACKUP = ROOT / "sqlserver_backup_before_bulk_fix"
BACKUP.mkdir(parents=True, exist_ok=True)

changed = []

def patch_file(path, transform):
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    new = transform(text)
    if new != text:
        rel = path.relative_to(ROOT)
        target = BACKUP / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        path.write_text(new, encoding="utf-8")
        changed.append(str(rel))

def common_fix(text):
    text = text.replace(" COLLATE NOCASE", "")
    text = text.replace("date(m.created_at)", "CONVERT(date, m.created_at)")
    text = text.replace("date(faults.entry_date)", "CONVERT(date, faults.entry_date)")
    text = text.replace("datetime(faults.entry_date)", "faults.entry_date")
    text = text.replace(
        "SELECT id FROM buildings WHERE name = ? LIMIT 1",
        "SELECT TOP 1 id FROM buildings WHERE name = ?"
    )
    text = text.replace(
        "SELECT 1 FROM faults WHERE fault_number = ? LIMIT 1",
        "SELECT TOP 1 1 FROM faults WHERE fault_number = ?"
    )
    text = re.sub(
        r"SELECT\s+(id\s+FROM\s+devices\s+WHERE\s+device_name\s*=\s*\?\s+AND\s+is_archived\s*=\s*0\s+AND\s+building_id\s*=\s*\?)\s+LIMIT\s+1",
        r"SELECT TOP 1 \1", text, flags=re.IGNORECASE
    )
    text = re.sub(
        r"SELECT\s+(id\s+FROM\s+devices\s+WHERE\s+device_name\s*=\s*\?\s+AND\s+is_archived\s*=\s*0)\s+LIMIT\s+1",
        r"SELECT TOP 1 \1", text, flags=re.IGNORECASE
    )
    text = re.sub(
        r"SELECT\s+(id,\s*spare_part_id,\s*quantity\s+FROM\s+spare_part_movements\s+WHERE\s+movement_type\s*=\s*'صرف'\s+AND\s+notes\s*=\s*\?\s+ORDER BY\s+id\s+DESC)\s+LIMIT\s+1",
        r"SELECT TOP 1 \1", text, flags=re.IGNORECASE
    )
    return text

for path in UI.glob("*.py"):
    patch_file(path, common_fix)

spare = UI / "spare_parts_page.py"
if spare.exists():
    def spare_fix(text):
        text = common_fix(text)
        pattern = re.compile(
            r"def ensure_spare_parts_tables\(\):.*?(?=\nclass\s+StatCard\b)",
            re.DOTALL
        )
        replacement = (
            "def ensure_spare_parts_tables():\n"
            "    # جداول قطع الغيار موجودة بالفعل في SQL Server.\n"
            "    return\n\n\n"
        )
        text2, n = pattern.subn(replacement, text, count=1)
        return text2 if n else text
    patch_file(spare, spare_fix)

for name in ("faults_page.py", "faults_page_excel_import.py"):
    fault = UI / name
    if fault.exists():
        def fault_fix(text):
            text = common_fix(text)
            old = '''        cursor.execute(
            "INSERT INTO buildings (name) VALUES (?)",
            (building_name.strip(),)
        )
        return cursor.lastrowid'''
            new = '''        cursor.execute(
            "INSERT INTO buildings (name) VALUES (?)",
            (building_name.strip(),)
        )
        cursor.execute(
            "SELECT TOP 1 id FROM buildings WHERE name = ? ORDER BY id DESC",
            (building_name.strip(),)
        )
        result = cursor.fetchone()
        return result["id"] if result else None'''
            return text.replace(old, new)
        patch_file(fault, fault_fix)

print("SQL Server bulk compatibility fix completed.")
print("Files changed:", len(changed))
for x in changed:
    print(" -", x)
print("Backup folder:", BACKUP)
