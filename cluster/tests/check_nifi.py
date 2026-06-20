import requests
import json

NIFI_API = "http://localhost:8161/nifi-api"

def check_status():
    root_id = requests.get(f"{NIFI_API}/process-groups/root").json()["id"]
    
    # Get processors
    procs = requests.get(f"{NIFI_API}/flow/process-groups/{root_id}").json()["processGroupFlow"]["flow"]["processors"]
    print("NiFi Processors:")
    for p in procs:
        comp = p["component"]
        status = p["status"]
        print(f"  Name: {comp['name']}")
        print(f"    State: {status.get('runStatus')}")
        print(f"    Validation Errors: {comp.get('validationErrors', [])}")
        # print(json.dumps(p, indent=2)) # uncomment if needed
        
    # Get connections
    conns = requests.get(f"{NIFI_API}/flow/process-groups/{root_id}").json()["processGroupFlow"]["flow"]["connections"]
    print("\nNiFi Connections:")
    for c in conns:
        comp = c["component"]
        status = c["status"]
        print(f"  Connection: {comp.get('name', 'unnamed')} ({comp['source']['name']} -> {comp['destination']['name']})")
        print(f"    Queued: {status['aggregateSnapshot']['queued']}")

if __name__ == "__main__":
    check_status()
