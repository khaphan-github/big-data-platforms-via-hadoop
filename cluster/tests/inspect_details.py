import requests
import json

NIFI_API = "http://localhost:8161/nifi-api"

def inspect_details():
    root_id = requests.get(f"{NIFI_API}/process-groups/root").json()["id"]
    procs = requests.get(f"{NIFI_API}/flow/process-groups/{root_id}").json()["processGroupFlow"]["flow"]["processors"]
    
    # Let's find PutHDFS
    target_proc_id = None
    for p in procs:
        if "PutHDFS" in p["component"]["name"]:
            target_proc_id = p["id"]
            break
            
    if not target_proc_id:
        print("PutHDFS not found")
        return
        
    resp = requests.get(f"{NIFI_API}/processors/{target_proc_id}")
    resp.raise_for_status()
    comp = resp.json()["component"]
    
    print("PutHDFS descriptors:")
    for name, desc in comp["config"]["descriptors"].items():
        if desc.get("required"):
            print(f"\nRequired Key: {name}")
            print(f"  Default Value: {desc.get('defaultValue')}")
            if desc.get("allowableValues"):
                print("  Allowable Values:")
                for av in desc["allowableValues"]:
                    print(f"    - {av['allowableValue']['value']}")
                    
    print("\nPutHDFS current properties:")
    print(json.dumps(comp["config"]["properties"], indent=2))
    
    print("\nConvertAvroToJSON properties current values:")
    print(json.dumps(comp["config"]["properties"], indent=2))

if __name__ == "__main__":
    inspect_details()
