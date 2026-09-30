import requests
import json
import time
import psycopg2
import pandas as pd
import os

BASE_URL = "http://localhost:8000"
DB_URL = "postgresql://postgres.qajktpiwajlpkvdvihvn:Pratyush1909@aws-0-ap-southeast-2.pooler.supabase.com:5432/postgres"
CSV_PATH = os.path.join(os.path.dirname(__file__), "backend", "LOT_00.csv")

def print_section(title):
    print("\n" + "="*50)
    print(title)
    print("="*50)

def main():
    print_section("1. Start backend successfully")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {resp.status_code}")
    except Exception as e:
        print(f"Failed to connect to backend: {e}")
        return

    print_section("5. Upload LOT_00.csv")
    with open(CSV_PATH, "rb") as f:
        files = {"file": ("LOT_00.csv", f, "text/csv")}
        resp = requests.post(f"{BASE_URL}/upload", files=files)
    
    print(f"Upload status: {resp.status_code}")
    if resp.status_code != 200:
        print(resp.text)
        return
        
    data = resp.json()
    run_id = data.get("run_id")
    print(f"Generated run_id: {run_id}")
    
    print_section("Run ML pipelines")
    for phase in ["module-a", "anomaly-analysis", "module-b", "risk-fusion"]:
        print(f"Triggering {phase}...")
        resp = requests.post(f"{BASE_URL}/screening-runs/{run_id}/{phase}")
        print(f"{phase} status: {resp.status_code}")
        if resp.status_code != 200:
            print(resp.text)
    
    print_section("8. Verify measurements/components persist in the database")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    cur.execute("SELECT count(*) FROM components")
    comp_count = cur.fetchone()[0]
    print(f"Components persisted: {comp_count}")
    
    cur.execute("SELECT count(*) FROM screening_results")
    res_count = cur.fetchone()[0]
    print(f"Results persisted: {res_count}")
    
    print_section("11-17. Verify API results for components")
    resp = requests.get(f"{BASE_URL}/components", params={"run_id": run_id, "limit": 100})
    components_data = resp.json()
    if isinstance(components_data, dict) and "components" in components_data:
        components_list = components_data["components"]
    elif isinstance(components_data, dict) and "data" in components_data:
        components_list = components_data["data"]
    elif isinstance(components_data, dict) and "results" in components_data:
        components_list = components_data["results"]
    else:
        components_list = components_data
        
    if not components_list or not isinstance(components_list, list):
        print("No components returned by API!")
        return
        
    print(f"API returned {len(components_list)} components.")
    
    # Pick 5 components for cross-layer consistency
    test_comps = components_list[:5]
    print("\nCross-Layer Consistency Candidates:")
    for c in test_comps:
        print(f" - {c['component_id']}: Final Decision={c.get('final_decision')}, Fusion={c.get('fusion_score')}")

    print_section("20. Export CSV and PDF")
    csv_resp = requests.get(f"{BASE_URL}/screening-runs/{run_id}/export/csv")
    print(f"CSV Export: {csv_resp.status_code}, Content-Type: {csv_resp.headers.get('content-type')}")
    
    pdf_resp = requests.get(f"{BASE_URL}/screening-runs/{run_id}/export/pdf")
    print(f"PDF Export: {pdf_resp.status_code}, Content-Type: {pdf_resp.headers.get('content-type')}")
    
    print_section("FINAL DB CHECK")
    print("Database consistency:")
    cur.execute("SELECT final_decision, count(*) FROM screening_results WHERE run_id = %s GROUP BY final_decision", (run_id,))
    for row in cur.fetchall():
        print(f" - {row[0]}: {row[1]}")

if __name__ == "__main__":
    main()
