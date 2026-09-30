import sqlite3, json
conn = sqlite3.connect('sih26170_lot00_e2e.db')
cursor = conn.cursor()
row1 = cursor.execute("SELECT decision_basis FROM risk_fusion_results WHERE final_decision='REVIEW_REQUIRED' LIMIT 1").fetchone()
if row1:
    print("REVIEW_REQUIRED:", json.dumps(json.loads(row1[0]), indent=2))
row3 = cursor.execute("SELECT evidence, warnings FROM screening_results WHERE stage='MODULE_A' LIMIT 1").fetchone()
if row3:
    print("MODULE_A EVIDENCE:", row3[0])
    print("MODULE_A WARNINGS:", row3[1])
