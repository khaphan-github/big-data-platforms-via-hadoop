import requests
import json

NIFI_API = "http://localhost:8161/nifi-api"

def inspect():
    root_id = requests.get(f"{NIFI_API}/process-groups/root").json()["id"]
    procs = requests.get(f"{NIFI_API}/flow/process-groups/{root_id}").json()["processGroupFlow"]["flow"]["processors"]
    
    for p in procs:
        p_id = p["id"]
        name = p["component"]["name"]
        
        # Query processor detail
        resp = requests.get(f"{NIFI_API}/processors/{p_id}")
        resp.raise_for_status()
        comp = resp.json()["component"]
        
        print(f"\n======================================")
        print(f"Processor: {name} ({comp['type']})")
        print(f"======================================")
        print("Property Descriptors:")
        for prop_name, desc in comp["config"]["descriptors"].items():
            print(f"  Key: '{prop_name}'")
            print(f"    Display Name: '{desc['displayName']}'")
            print(f"    Required: {desc.get('required')}")
            
if __name__ == "__main__":
    inspect()
