# Scala

- Installation

```bash
curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | sudo gpg --dearmor -o /etc/apt/keyrings/scalasbt.gpg
echo "deb [signed-by=/etc/apt/keyrings/scalasbt.gpg] https://repo.scala-sbt.org/scalasbt/debian all main" | sudo tee /etc/apt/sources.list.d/sbt.list
sudo apt-get update
sudo apt-get install sbt

sbt run
sbt clean compile
sbt assembly
# Firewall: allow executors (Docker bridge subnet) to reach driver port 7078
# sudo ufw allow from 172.0.0.0/8 to any port 7078

```

## Generate mock data

```bash
./script/generate_mock_data.sh ./mock_data 10
./script/upload_to_hdfs.sh ./mock_data
```
