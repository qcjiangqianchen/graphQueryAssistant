# 🚀 BNP AI Chatbot Deployment Guide

## Quick Start with Docker Compose

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key

### Step 1: Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
OPENAI_API_KEY=your-openai-api-key-here
```

### Step 2: Start Services

```bash
# Start Neo4j and Backend
docker-compose up -d

# Check status
docker-compose ps
```

Services will be available at:
- **Backend API**: http://localhost:8000
- **Neo4j Browser**: http://localhost:7474 (username: neo4j, password: password123)
- **API Docs**: http://localhost:8000/docs

### Step 3: Load Graph Data

```bash
# Access backend container
docker-compose exec backend bash

# Load CSV data into Neo4j
python load_graph_data.py

# Exit container
exit
```

### Step 4: Test the API

```bash
curl http://localhost:8000/graph/summary
```

## 📦 What's Included

### Services
- **Neo4j**: Graph database (ports 7474, 7687)
- **Backend**: FastAPI application (port 8000)

### Data
Your CSV files in `backend/relations/` are automatically mounted and loaded:
- `servers (1).csv` - Server nodes
- `applications (1).csv` - Application nodes
- `oses.csv` - Operating system nodes
- `runs_on.csv` - Server-OS relationships
- `hosts (1).csv` - Server-Application relationships
- `located_in.csv` - Server-Location relationships

## 🛠️ Development

### Local Development (Without Docker)

1. **Start Neo4j**:
```bash
docker run --name neo4j-bnp -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 -d neo4j:latest
```

2. **Install Dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

3. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

4. **Load Data**:
```bash
python load_graph_data.py
```

5. **Run Backend**:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

Frontend will open at http://localhost:3000

## 📖 API Endpoints

### Chat
- `POST /chat` - Send message to AI chatbot
  ```json
  {
    "message": "What servers run Ubuntu?",
    "use_rag": true
  }
  ```

### Graph Queries
- `GET /graph/summary` - Get graph statistics
- `GET /graph/servers` - List all servers
- `GET /graph/applications` - List all applications
- `GET /graph/server/{server_id}` - Get server details

## 🔍 Example Queries

Try asking:
- "What servers run Ubuntu?"
- "Show me all applications"
- "What is running on server1?"
- "Which servers are in location loc1?"
- "What applications run on Windows servers?"

## 🛑 Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## 📊 Monitoring

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f neo4j
```

### Neo4j Browser
1. Go to http://localhost:7474
2. Connect with:
   - URL: `bolt://localhost:7687`
   - Username: `neo4j`
   - Password: `password123`

3. Run Cypher queries:
```cypher
MATCH (n) RETURN n LIMIT 25
MATCH (s:Server)-[r]->(n) RETURN s, r, n LIMIT 50
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Restart
docker-compose restart backend
```

### Neo4j connection issues
```bash
# Wait for Neo4j to be ready (takes ~30 seconds)
docker-compose logs neo4j

# Verify connectivity
docker-compose exec backend python -c "from neo4j_client import Neo4jClient; client = Neo4jClient('bolt://neo4j:7687', 'neo4j', 'password123'); print('Connected!')"
```

### Data not loading
```bash
# Re-run data loader
docker-compose exec backend python load_graph_data.py
```

## 💰 Cost Optimization

Current configuration uses the most cost-effective OpenAI models:
- **gpt-4o-mini**: $0.150/$0.600 per 1M tokens (input/output)
- Typical query cost: ~$0.0003-0.0005

## 🔒 Security Notes

For production deployment:
1. Change Neo4j password in `docker-compose.yml`
2. Use environment variables for sensitive data
3. Enable HTTPS
4. Restrict CORS origins in `app.py`
5. Use Docker secrets for API keys

## 📝 Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │────────▶│   Backend    │────────▶│   Neo4j     │
│ (React App) │         │  (FastAPI)   │         │  (Graph DB) │
│  Port 3000  │         │  Port 8000   │         │  Port 7687  │
└─────────────┘         └──────────────┘         └─────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  OpenAI API  │
                        │  (GPT-4o)    │
                        └──────────────┘
```

## 🎯 Project Structure

```
bnp_aichatbot/
├── docker-compose.yml          # Orchestration
├── backend/
│   ├── Dockerfile             # Backend container
│   ├── app.py                 # FastAPI application
│   ├── neo4j_client.py        # Neo4j operations
│   ├── openai_client.py       # OpenAI integration
│   ├── load_graph_data.py     # Data loader
│   ├── config.py              # Configuration
│   ├── requirements.txt       # Python dependencies
│   └── relations/             # CSV data files
└── frontend/
    ├── src/
    │   ├── App.tsx
    │   └── components/
    │       └── ChatInterface.tsx
    └── package.json
```
