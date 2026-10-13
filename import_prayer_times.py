from database import import_prayer_times_csv

csv_path = r"C:\Users\Administrator\NetworkFaults\alexandria_prayer_times_through_2031.csv"

count = import_prayer_times_csv(csv_path)
print(f"تم استيراد {count} يومًا")
