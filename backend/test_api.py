import urllib.request
import urllib.parse
import json

base_url = "http://localhost:8000"

def call_endpoint(method, path, data=None):
    url = base_url + path
    try:
        req = urllib.request.Request(url, method=method)
        if data:
            json_data = json.dumps(data).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
            req.data = json_data
            
        with urllib.request.urlopen(req) as response:
            res_code = response.getcode()
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            print(f"[{method}] {path} -> {res_code} OK")
            return res_json
    except urllib.error.HTTPError as e:
        print(f"[{method}] {path} -> {e.code} ERROR")
        print(e.read().decode('utf-8'))
        return None
    except Exception as e:
        print(f"[{method}] {path} -> ERROR: {e}")
        return None

def run_tests():
    print("Testing APIs...\n")
    
    # 1. Health
    call_endpoint("GET", "/health")
    
    # 2. Models
    call_endpoint("GET", "/models")
    
    # 3. Components
    comps_res = call_endpoint("GET", "/components")
    
    cid = "UNKNOWN"
    if comps_res and "results" in comps_res and len(comps_res["results"]) > 0:
        cid = comps_res["results"][0]["component_id"]
        
    # 4. Component ID
    if cid != "UNKNOWN":
        call_endpoint("GET", f"/component/{cid}")
        
    # 5. Lot ID
    call_endpoint("GET", "/lot/LOT-2026-091")
    
    # 6. Predict
    predict_payload = {
        "component_id": "TEST-01",
        "Iddq_uA_0h": 12.8,
        "Iddq_uA_24h": 12.9,
        "Leakage_nA_0h": 540.0,
        "Leakage_nA_24h": 542.0,
        "PropDelay_ns_0h": 3.35,
        "PropDelay_ns_24h": 3.36
    }
    call_endpoint("POST", "/predict", predict_payload)
    
    # 7. Screen
    screen_payload = {
        "component_id": "TEST-02",
        "lot_id": "LOT-2026-091",
        "device_type": "XYZ-IC",
        "station": "ST-01",
        "temperature": "125°C",
        "voltage": "3.3V",
        "Iddq_uA_0h": 12.8,
        "Iddq_uA_24h": 12.9,
        "Leakage_nA_0h": 540.0,
        "Leakage_nA_24h": 542.0,
        "PropDelay_ns_0h": 3.35,
        "PropDelay_ns_24h": 3.36
    }
    call_endpoint("POST", "/screen", screen_payload)
    
    # 8. Batch Screen (using JSON upload mode, which expects a list or {records: [...]})
    batch_payload = {
        "records": [screen_payload]
    }
    # Wait, the batch-screen endpoint supports JSON upload, but let's test it
    call_endpoint("POST", "/batch-screen", batch_payload)

if __name__ == "__main__":
    run_tests()
