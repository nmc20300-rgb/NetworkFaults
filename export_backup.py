import shutil
from pathlib import Path
import pyodbc

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=master;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

backup_sql_path = r"C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQL\Backup\NetworkFaults_Export.bak"
dest_path = Path(r"c:\Users\Administrator\NetworkFaults\NetworkFaults_Export.bak")

print("[1/2] Creating SQL backup for NetworkFaults...")
conn = pyodbc.connect(conn_str, autocommit=True)
cursor = conn.cursor()
cursor.execute(f"BACKUP DATABASE [NetworkFaults] TO DISK = N'{backup_sql_path}' WITH INIT, STATS = 10")
while cursor.nextset():
    pass
cursor.close()
conn.close()
print("[OK] Backup created successfully in SQL Server.")

print("[2/2] Copying backup file to project directory...")
shutil.copy2(backup_sql_path, dest_path)
size_mb = dest_path.stat().st_size / (1024 * 1024)
print(f"[SUCCESS] Backup file ready at: {dest_path}")
print(f"File size: {size_mb:.2f} MB")
