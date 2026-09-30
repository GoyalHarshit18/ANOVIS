import subprocess
import requests
import time
import sys
import os

BASE_URL = "http://localhost:8000"

def run_tests():
    print("Starting backend subprocess...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.abspath(".")
    )
    
    print("Waiting for backend to start...")
    retries = 30
    started = False
    for i in range(retries):
        try:
            res = requests.get(f"{BASE_URL}/docs")
            if res.status_code == 200:
                print("Backend started successfully!")
                started = True
                break
        except Exception as e:
            time.sleep(2)
            
    if not started:
        print("Backend failed to start in time.")
        backend.terminate()
        print(backend.stderr.read().decode())
        return

    print("Uploading LOT_00.csv...")
    file_path = "LOT_00.csv"
    with open(file_path, "rb") as f:
        res = requests.post(
            f"{BASE_URL}/upload",
            files={"file": ("LOT_00.csv", f, "text/csv")}
        )
    
    if res.status_code != 200:
        print(f"Upload failed: {res.text}")
        backend.terminate()
        return
        
    data = res.json()
    run_id = data.get("run_id")
    print(f"FINAL E2E RUN ID: {run_id}")
    
    print("Running Module A...")
    requests.post(f"{BASE_URL}/screening-runs/{run_id}/module-a")
    print("Running Anomaly Analysis...")
    requests.post(f"{BASE_URL}/screening-runs/{run_id}/anomaly-analysis")
    print("Running Module B...")
    requests.post(f"{BASE_URL}/screening-runs/{run_id}/module-b")
    print("Running Risk Fusion...")
    requests.post(f"{BASE_URL}/screening-runs/{run_id}/risk-fusion")
    
    # Check components
    res = requests.get(f"{BASE_URL}/components")
    components_data = res.json()
    components = components_data.get("components", [])
    print(f"Total components in DB: {len(components)}")
    
    # Get details for 5 components
    sample_components = [c for c in components if c['lot'] == 'LOT_00'][:5]
    for comp in sample_components:
        comp_id = comp['component_id']
        detail_res = requests.get(f"{BASE_URL}/component/{comp_id}")
        if detail_res.status_code == 200:
            print(f"Component {comp_id} fetched successfully.")
            c = detail_res.json()
            print(f"  A_SCORE: {c.get('a_score')}, prediction_risk: {c.get('prediction_risk')}, fusion_score: {c.get('evidence', {}).get('fusion_state', {}).get('fusion_score')}")
        else:
            print(f"Failed to fetch component {comp_id}: {detail_res.text}")
            
    # Export CSV
    print("Testing CSV Export...")
    csv_res = requests.get(f"{BASE_URL}/screening-runs/{run_id}/export/csv")
    if csv_res.status_code == 200:
        print(f"CSV Export successful, Size: {len(csv_res.content)} bytes")
    else:
        print(f"CSV Export failed: {csv_res.status_code} - {csv_res.text}")
        
    # Export PDF
    print("Testing PDF Export...")
    pdf_res = requests.get(f"{BASE_URL}/screening-runs/{run_id}/export/pdf")
    if pdf_res.status_code == 200:
        print(f"PDF Export successful, Size: {len(pdf_res.content)} bytes")
    else:
        print(f"PDF Export failed: {pdf_res.status_code} - {pdf_res.text}")
        
    print("\n--- Testing Edge Cases ---")
    unknown_run = requests.get(f"{BASE_URL}/screening-runs/unknown_run_123/export/csv")
    print(f"Unknown run CSV export status: {unknown_run.status_code}")
    
    unknown_comp = requests.get(f"{BASE_URL}/component/comp_unknown_999")
    print(f"Unknown component fetch status: {unknown_comp.status_code}")
    
    backend.terminate()
    print("Done")
    
if __name__ == "__main__":
    run_tests()
