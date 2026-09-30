import sqlite3, json
conn = sqlite3.connect('sih26170_lot00_e2e.db')
cursor = conn.cursor()
events = cursor.execute("SELECT id, metadata_ FROM audit_events WHERE event_type='RISK_FUSION'").fetchall()
first_pass = []
second_pass = []
for idx, (eid, meta_str) in enumerate(events):
    meta = json.loads(meta_str)
    if idx < 173:
        first_pass.append(meta.get("final_decision"))
    else:
        second_pass.append(meta.get("final_decision"))

from collections import Counter
print("First pass:", Counter(first_pass))
print("Second pass:", Counter(second_pass))
