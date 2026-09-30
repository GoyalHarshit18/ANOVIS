import sqlite3
conn = sqlite3.connect('sih26170_lot00_e2e.db')
cursor = conn.cursor()
count = cursor.execute("SELECT COUNT(*) FROM screening_results WHERE stage='FINAL'").fetchone()[0]
print("FINAL count:", count)
count2 = cursor.execute("SELECT COUNT(*) FROM screening_results WHERE stage='MODULE_A'").fetchone()[0]
print("MODULE_A count:", count2)
