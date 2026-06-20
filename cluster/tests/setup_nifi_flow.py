import requests
import json
import time

NIFI_API = "http://localhost:8161/nifi-api"

# Bundle definitions discovered
BUNDLE_STANDARD = {
    "group": "org.apache.nifi",
    "artifact": "nifi-standard-nar",
    "version": "1.27.0"
}
BUNDLE_AVRO = {
    "group": "org.apache.nifi",
    "artifact": "nifi-avro-nar",
    "version": "1.27.0"
}
BUNDLE_HADOOP = {
    "group": "org.apache.nifi",
    "artifact": "nifi-hadoop-nar",
    "version": "1.27.0"
}
BUNDLE_DBCP = {
    "group": "org.apache.nifi",
    "artifact": "nifi-dbcp-service-nar",
    "version": "1.27.0"
}

def get_root_pg_id():
    resp = requests.get(f"{NIFI_API}/process-groups/root")
    resp.raise_for_status()
    return resp.json()["id"]

def create_dbcp_pool(root_id):
    # Check if Connection Pool already exists
    resp = requests.get(f"{NIFI_API}/flow/process-groups/{root_id}")
    resp.raise_for_status()
    resp = requests.get(f"{NIFI_API}/flow/process-groups/{root_id}/controller-services")
    resp.raise_for_status()
    services = resp.json().get("controllerServices", [])
    for svc in services:
        if svc["component"]["name"] == "MySQL Connection Pool":
            print("MySQL Connection Pool already exists.")
            return svc["id"], svc["revision"]
            
    # Create it
    payload = {
        "revision": {"version": 0},
        "component": {
            "type": "org.apache.nifi.dbcp.DBCPConnectionPool",
            "bundle": BUNDLE_DBCP,
            "name": "MySQL Connection Pool",
            "properties": {
                "Database Connection URL": "jdbc:mysql://ingest-mysql:3306/rss_ingest",
                "Database Driver Class Name": "com.mysql.cj.jdbc.Driver",
                "Database User": "root",
                "Password": "rss_password"
            }
        }
    }
    resp = requests.post(f"{NIFI_API}/process-groups/{root_id}/controller-services", json=payload)
    resp.raise_for_status()
    svc = resp.json()
    print("Created MySQL Connection Pool.")
    return svc["id"], svc["revision"]

def enable_dbcp_pool(svc_id, revision):
    # Enable it
    payload = {
        "revision": revision,
        "state": "ENABLED"
    }
    resp = requests.put(f"{NIFI_API}/controller-services/{svc_id}/run-status", json=payload)
    resp.raise_for_status()
    print("Enabled MySQL Connection Pool.")
    return resp.json()["revision"]

def create_processor(root_id, proc_type, bundle, name, x, y, properties, auto_terminate_rels=None):
    payload = {
        "revision": {"version": 0},
        "component": {
            "type": proc_type,
            "bundle": bundle,
            "name": name,
            "position": {"x": x, "y": y},
            "config": {
                "properties": properties
            }
        }
    }
    if auto_terminate_rels:
        payload["component"]["config"]["autoTerminatedRelationships"] = auto_terminate_rels
        
    resp = requests.post(f"{NIFI_API}/process-groups/{root_id}/processors", json=payload)
    resp.raise_for_status()
    proc = resp.json()
    print(f"Created Processor {name} (ID: {proc['id']}).")
    return proc["id"], proc["revision"]

def create_connection(root_id, source_id, dest_id, relationships):
    payload = {
        "revision": {"version": 0},
        "component": {
            "source": {
                "id": source_id,
                "groupId": root_id,
                "type": "PROCESSOR"
            },
            "destination": {
                "id": dest_id,
                "groupId": root_id,
                "type": "PROCESSOR"
            },
            "selectedRelationships": relationships
        }
    }
    resp = requests.post(f"{NIFI_API}/process-groups/{root_id}/connections", json=payload)
    if resp.status_code != 201 and resp.status_code != 200:
        print(f"Error creating connection: {resp.status_code} {resp.text}")
    resp.raise_for_status()
    conn = resp.json()
    print(f"Connected {source_id} to {dest_id} via {relationships}.")
    return conn["id"]

def start_processor(proc_id, revision):
    payload = {
        "revision": revision,
        "state": "RUNNING"
    }
    resp = requests.put(f"{NIFI_API}/processors/{proc_id}/run-status", json=payload)
    resp.raise_for_status()
    print(f"Started Processor {proc_id}.")

def reset_flow(root_id):
    # 1. Stop all processors
    resp = requests.get(f"{NIFI_API}/process-groups/{root_id}/processors")
    resp.raise_for_status()
    procs = resp.json().get("processors", [])
    for p in procs:
        p_id = p["id"]
        version = p["revision"]["version"]
        try:
            requests.put(f"{NIFI_API}/processors/{p_id}/run-status", json={
                "revision": {"version": version},
                "state": "STOPPED"
            }).raise_for_status()
        except Exception:
            pass
            
    # Wait a bit for processors to stop
    time.sleep(2)
    
    # 2. Delete all connections
    resp = requests.get(f"{NIFI_API}/process-groups/{root_id}/connections")
    resp.raise_for_status()
    conns = resp.json().get("connections", [])
    for c in conns:
        c_id = c["id"]
        version = c["revision"]["version"]
        try:
            requests.delete(f"{NIFI_API}/connections/{c_id}", params={"version": version}).raise_for_status()
        except Exception as e:
            print(f"Error deleting connection {c_id}: {e}")
        
    # 3. Delete all processors
    resp = requests.get(f"{NIFI_API}/process-groups/{root_id}/processors")
    resp.raise_for_status()
    procs = resp.json().get("processors", [])
    for p in procs:
        p_id = p["id"]
        version = p["revision"]["version"]
        try:
            requests.delete(f"{NIFI_API}/processors/{p_id}", params={"version": version}).raise_for_status()
        except Exception as e:
            print(f"Error deleting processor {p_id}: {e}")
        
    print("Cleaned up existing processors and connections in root process group.")

def main():
    print("Connecting to NiFi API...")
    root_id = get_root_pg_id()
    print(f"Root Process Group ID: {root_id}")
    
    # Clean up canvas first
    reset_flow(root_id)
    
    # 1. Create and Enable DBCP Pool
    svc_id, revision = create_dbcp_pool(root_id)
    time.sleep(1)
    # Enable service if not already enabled
    try:
        revision = enable_dbcp_pool(svc_id, revision)
    except Exception as e:
        print(f"Connection pool might already be enabled: {e}")
        
    # Categories config
    categories = [
        {
            "key": "giai_tri",
            "name_vn": "Giải Trí",
            "view": "v_articles_giai_tri",
            "hdfs_dir": "/raw_zone/giai_tri",
            "x_offset": 0
        },
        {
            "key": "cong_nghe",
            "name_vn": "Công Nghệ",
            "view": "v_articles_cong_nghe",
            "hdfs_dir": "/raw_zone/cong_nghe",
            "x_offset": 450
        },
        {
            "key": "suc_khoe",
            "name_vn": "Sức Khỏe",
            "view": "v_articles_suc_khoe",
            "hdfs_dir": "/raw_zone/suc_khoe",
            "x_offset": 900
        }
    ]
    
    for cat in categories:
        q_name = f"Query_{cat['key'].upper()}"
        conv_name = f"ConvertAvroToJSON_{cat['key'].upper()}"
        put_name = f"PutHDFS_{cat['key'].upper()}"
        
        print(f"\nCreating pipeline for {cat['name_vn']}...")
        
        # 1. QueryDatabaseTable
        q_props = {
            "Database Connection Pooling Service": svc_id,
            "db-fetch-db-type": "MySQL",
            "Table Name": cat["view"],
            "Maximum-value Columns": "id"
        }
        q_id, q_rev = create_processor(
            root_id=root_id,
            proc_type="org.apache.nifi.processors.standard.QueryDatabaseTable",
            bundle=BUNDLE_STANDARD,
            name=q_name,
            x=100 + cat["x_offset"],
            y=100,
            properties=q_props
        )
        
        # 2. ConvertAvroToJSON
        conv_props = {
            "JSON container options": "none",
            "Wrap Single Record": "false"
        }
        conv_id, conv_rev = create_processor(
            root_id=root_id,
            proc_type="org.apache.nifi.processors.avro.ConvertAvroToJSON",
            bundle=BUNDLE_AVRO,
            name=conv_name,
            x=100 + cat["x_offset"],
            y=300,
            properties=conv_props,
            auto_terminate_rels=["failure"]
        )
        
        # 3. PutHDFS
        put_props = {
            "Hadoop Configuration Resources": "/opt/nifi-1.25.0/conf/core-site.xml,/opt/nifi-1.25.0/conf/hdfs-site.xml",
            "Directory": cat["hdfs_dir"],
            "Conflict Resolution Strategy": "append"
        }
        put_id, put_rev = create_processor(
            root_id=root_id,
            proc_type="org.apache.nifi.processors.hadoop.PutHDFS",
            bundle=BUNDLE_HADOOP,
            name=put_name,
            x=100 + cat["x_offset"],
            y=500,
            properties=put_props,
            auto_terminate_rels=["success", "failure"]
        )
        
        # Connect processors
        create_connection(root_id, q_id, conv_id, ["success"])
        create_connection(root_id, conv_id, put_id, ["success"])
        
        # Start processors
        time.sleep(1)
        start_processor(q_id, q_rev)
        start_processor(conv_id, conv_rev)
        start_processor(put_id, put_rev)

    print("\nNiFi automated configuration completed successfully!")

if __name__ == "__main__":
    main()
