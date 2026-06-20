import requests
import json

NIFI_API = "http://localhost:8161/nifi-api"

def find_controller_service_types():
    resp = requests.get(f"{NIFI_API}/flow/controller-service-types")
    resp.raise_for_status()
    types = resp.json()["controllerServiceTypes"]
    
    dbcp_info = None
    for t in types:
        name = t["type"]
        if "DBCPConnectionPool" in name:
            dbcp_info = t
            break
            
    print("DBCPConnectionPool info:")
    print(json.dumps(dbcp_info, indent=2))

if __name__ == "__main__":
    find_controller_service_types()
