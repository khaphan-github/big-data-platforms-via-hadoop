import requests
import time

NIFI_API = "http://localhost:8161/nifi-api"

def get_processors():
    root_id = requests.get(f"{NIFI_API}/process-groups/root").json()["id"]
    procs = requests.get(f"{NIFI_API}/flow/process-groups/{root_id}").json()["processGroupFlow"]["flow"]["processors"]
    return procs

def stop_processor(proc_id, revision):
    payload = {
        "revision": revision,
        "state": "STOPPED"
    }
    resp = requests.put(f"{NIFI_API}/processors/{proc_id}/run-status", json=payload)
    resp.raise_for_status()
    print(f"Stopped Processor {proc_id}")
    return resp.json()["revision"]

def clear_processor_state(proc_id):
    resp = requests.post(f"{NIFI_API}/processors/{proc_id}/state/clear-requests")
    resp.raise_for_status()
    print(f"Cleared state for Processor {proc_id}")

def start_processor(proc_id, revision):
    payload = {
        "revision": revision,
        "state": "RUNNING"
    }
    resp = requests.put(f"{NIFI_API}/processors/{proc_id}/run-status", json=payload)
    resp.raise_for_status()
    print(f"Started Processor {proc_id}")

def main():
    procs = get_processors()
    query_procs = [p for p in procs if p["component"]["name"].startswith("Query_")]
    
    # 1. Stop query processors
    for p in query_procs:
        p_id = p["id"]
        rev = p["revision"]
        # Stop
        try:
            new_rev = stop_processor(p_id, rev)
            p["revision"] = new_rev
        except Exception as e:
            print(f"Error stopping {p_id}: {e}")
            
    # Wait for processors to stop
    time.sleep(2)
    
    # 2. Clear state
    for p in query_procs:
        p_id = p["id"]
        try:
            clear_processor_state(p_id)
        except Exception as e:
            print(f"Error clearing state for {p_id}: {e}")
            
    # 3. Restart processors
    for p in query_procs:
        p_id = p["id"]
        rev = p["revision"]
        try:
            # We fetch the latest revision to be safe
            latest_proc = requests.get(f"{NIFI_API}/processors/{p_id}").json()
            latest_rev = latest_proc["revision"]
            start_processor(p_id, latest_rev)
        except Exception as e:
            print(f"Error starting {p_id}: {e}")

if __name__ == "__main__":
    main()
