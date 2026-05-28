# Cluster Notes

## Check status
```bash
docker exec hadoop-namenode hdfs dfsadmin -report
```

## Python HDFS CRUD smoke test (with venv)
```bash
cd cluster/tests
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python hdfs_crud_test.py --namenode-http http://localhost:9870 --user hadoop
```

Chi tiet: `cluster/tests/README.md`
