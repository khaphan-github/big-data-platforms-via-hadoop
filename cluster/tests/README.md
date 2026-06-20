# HDFS CRUD Test (Python, isolated venv)

## 1) Create virtual environment
```bash
cd cluster/tests
python3 -m venv .venv
```

## 2) Activate venv
```bash
source .venv/bin/activate
```

## 3) Install dependencies
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4) Run CRUD smoke test
If you just changed cluster configs, restart first:
```bash
cd cluster
docker compose up -d --build --force-recreate namenode datanode1 datanode2
cd tests
```

From repo root:
```bash
python3 cluster/tests/hdfs_crud_test.py --namenode-http http://localhost:9870 --user hadoop
```

Or from `cluster/tests`:
```bash
python3 hdfs_crud_test.py --namenode-http http://localhost:9870 --user hadoop
```

## 5) Deactivate
```bash
deactivate
```
