# Deployment Guide

## Prerequisites

- Python 3.8+
- Neo4j 5.0+
- Anthropic API key
- LangSmith account (optional)

## Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd john
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password

# Anthropic API Key
ANTHROPIC_API_KEY=sk-ant-your-api-key

# LangSmith (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=traffic-management-prod
```

### 5. Database Setup

```bash
python scripts/setup_database.py
```

### 6. Verify Installation

```bash
python scripts/demo.py basic
```

## Production Deployment

### Docker Deployment

1. **Create Dockerfile:**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "scripts/demo.py", "interactive"]
```

2. **Build and Run:**

```bash
docker build -t traffic-management .
docker run -e NEO4J_URI=bolt://your-neo4j:7687 \
           -e ANTHROPIC_API_KEY=your-key \
           traffic-management
```

### Kubernetes Deployment

1. **Create ConfigMap:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: traffic-config
data:
  NEO4J_URI: "bolt://neo4j-service:7687"
  NEO4J_USERNAME: "neo4j"
  LANGCHAIN_TRACING_V2: "true"
```

2. **Create Secret:**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: traffic-secrets
type: Opaque
stringData:
  NEO4J_PASSWORD: "your-password"
  ANTHROPIC_API_KEY: "your-api-key"
  LANGCHAIN_API_KEY: "your-langsmith-key"
```

3. **Create Deployment:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: traffic-management
spec:
  replicas: 3
  selector:
    matchLabels:
      app: traffic-management
  template:
    metadata:
      labels:
        app: traffic-management
    spec:
      containers:
      - name: traffic-app
        image: traffic-management:latest
        envFrom:
        - configMapRef:
            name: traffic-config
        - secretRef:
            name: traffic-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

### Cloud Deployment Options

#### AWS ECS

1. **Task Definition:**

```json
{
  "family": "traffic-management",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "traffic-app",
      "image": "your-account.dkr.ecr.region.amazonaws.com/traffic-management:latest",
      "environment": [
        {"name": "NEO4J_URI", "value": "bolt://your-neo4j:7687"}
      ],
      "secrets": [
        {"name": "ANTHROPIC_API_KEY", "valueFrom": "arn:aws:secretsmanager:region:account:secret:anthropic-key"}
      ]
    }
  ]
}
```

#### Google Cloud Run

```bash
gcloud run deploy traffic-management \
  --image gcr.io/your-project/traffic-management \
  --platform managed \
  --region us-central1 \
  --set-env-vars NEO4J_URI=bolt://your-neo4j:7687 \
  --set-secrets ANTHROPIC_API_KEY=anthropic-key:latest
```

#### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name traffic-management \
  --image your-registry.azurecr.io/traffic-management:latest \
  --environment-variables NEO4J_URI=bolt://your-neo4j:7687 \
  --secure-environment-variables ANTHROPIC_API_KEY=your-key
```

## Database Deployment

### Neo4j Cloud

1. **Create AuraDB Instance:**
   - Go to https://neo4j.com/cloud/aura/
   - Create new instance
   - Note connection details

2. **Configure Connection:**
   ```bash
   NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your-generated-password
   ```

### Self-Hosted Neo4j

1. **Docker Compose:**

```yaml
version: '3.8'
services:
  neo4j:
    image: neo4j:5.0
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/your-password
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs

volumes:
  neo4j_data:
  neo4j_logs:
```

2. **Production Configuration:**

Add to `neo4j.conf`:
```
dbms.memory.heap.initial_size=1G
dbms.memory.heap.max_size=2G
dbms.memory.pagecache.size=1G
dbms.security.auth_enabled=true
```

## Monitoring and Observability

### Logging Configuration

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('traffic_management.log'),
        logging.StreamHandler()
    ]
)
```

### Health Checks

Create health check endpoint:

```python
from flask import Flask, jsonify
from monitoring.performance_metrics import system_monitor

app = Flask(__name__)

@app.route('/health')
def health_check():
    health = system_monitor.check_system_health()
    status_code = 200 if health['status'] == 'healthy' else 503
    return jsonify(health), status_code

if __name__ == '__main__':
    app.run(port=8080)
```

### Monitoring with Prometheus

```python
from prometheus_client import Counter, Histogram, start_http_server

QUERY_COUNT = Counter('traffic_queries_total', 'Total queries processed')
QUERY_DURATION = Histogram('traffic_query_duration_seconds', 'Query duration')

# In your application
QUERY_COUNT.inc()
with QUERY_DURATION.time():
    result = process_query(query)
```

## Performance Tuning

### Database Optimization

1. **Create Indexes:**
```cypher
CREATE INDEX link_id_index FOR (l:Link) ON (l.link_id);
CREATE INDEX vms_link_index FOR (v:VMS) ON (v.LINK_ID);
```

2. **Connection Pooling:**
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    uri,
    auth=(username, password),
    max_connection_lifetime=30 * 60,  # 30 minutes
    max_connection_pool_size=50,
    connection_acquisition_timeout=30
)
```

### LLM Optimization

1. **Request Batching:**
```python
# Process multiple events in one request
batch_prompt = f"""
Process these traffic events:
Event 1: {event1}
Event 2: {event2}
Event 3: {event3}
"""
```

2. **Response Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_response(query_hash):
    return llm.invoke(query)
```

## Security Considerations

### API Key Management

1. **Use Secret Management:**
   - AWS Secrets Manager
   - Azure Key Vault
   - Google Secret Manager
   - HashiCorp Vault

2. **Environment Variables:**
```bash
# Never commit these to version control
export ANTHROPIC_API_KEY="$(aws secretsmanager get-secret-value --secret-id anthropic-key --query SecretString --output text)"
```

### Network Security

1. **Neo4j Security:**
```
# Enable encryption
dbms.connector.bolt.tls_level=REQUIRED
dbms.ssl.policy.bolt.enabled=true
```

2. **Firewall Rules:**
```bash
# Only allow specific IPs
iptables -A INPUT -p tcp --dport 7687 -s YOUR_APP_IP -j ACCEPT
iptables -A INPUT -p tcp --dport 7687 -j DROP
```

### Input Validation

```python
from src.utils.validators import sanitize_cypher_query

def safe_query_execution(user_query):
    try:
        sanitized = sanitize_cypher_query(user_query)
        return run_cypher_query(sanitized)
    except ValueError as e:
        return f"Invalid query: {e}"
```

## Backup and Recovery

### Database Backup

```bash
# Neo4j backup
neo4j-admin dump --database=neo4j --to=/backups/neo4j-backup.dump

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
neo4j-admin dump --database=neo4j --to=/backups/neo4j-$DATE.dump
aws s3 cp /backups/neo4j-$DATE.dump s3://your-backup-bucket/
```

### Configuration Backup

```bash
# Backup configuration
cp .env .env.backup
tar -czf config-backup.tar.gz .env prompts/ config/
```

## Troubleshooting

### Common Issues

1. **Connection Timeout:**
```python
# Increase timeout in config
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME, 
    password=NEO4J_PASSWORD,
    timeout=60  # Increase from 30
)
```

2. **Memory Issues:**
```bash
# Increase JVM heap for Neo4j
NEO4J_HEAP_MEMORY=2G
```

3. **LLM Rate Limits:**
```python
import time
from tenacity import retry, wait_exponential

@retry(wait=wait_exponential(multiplier=1, min=4, max=10))
def robust_llm_call(prompt):
    return llm.invoke(prompt)
```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
python scripts/demo.py basic
```

### Log Analysis

```bash
# Find errors in logs
grep ERROR traffic_management.log

# Monitor real-time logs
tail -f traffic_management.log | grep -E "(ERROR|WARNING)"
```
