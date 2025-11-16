# Knowledge Graph Query Assistant

## Overview

This project implements a knowledge graph-powered AI chatbot that:
- Uses Neo4j graph database for infrastructure knowledge management
- Implements natural language queries over structured graph data
- Integrates with OpenAI's GPT-4o-mini for intelligent responses
- Provides FastAPI backend with RESTful endpoints
- React frontend with modern chat interface
- Fully dockerized with docker-compose for easy deployment

## Architecture

```
graphQueryAssistant/
├── docker-compose.yml          # Service orchestration
├── backend/
│   ├── Dockerfile             # Backend containerization
│   ├── app.py                 # FastAPI application
│   ├── config.py              # Configuration
│   ├── neo4j_client.py        # Graph database operations
│   ├── openai_client.py       # OpenAI integration
│   ├── load_graph_data.py     # CSV data loader
│   ├── requirements.txt       # Dependencies
│   └── relations/             # CSV data files
│       ├── servers.csv
│       ├── applications.csv
│       ├── oses.csv
│       ├── runs_on.csv
│       ├── hosts.csv
│       └── located_in.csv
└── frontend/
    └── src/
        └── components/
            └── ChatInterface.tsx  # React chat UI
```

## Running the application

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd graphQueryAssistant
```

2. **Set up environment variables**
- Create a `.env` file in the root directory:
```bash
OPENAI_API_KEY=your-openai-api-key-here
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Load graph data**
- Execute command when running for the first time to initialise DB with data from the csv files
```bash
docker-compose exec backend python load_graph_data.py
```

5. **Start the frontend**
```bash
npm install
npm run start
```

6. **Access services**
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (neo4j/password123)
- **Frontend**: http://localhost:3000


### API Documentation

Once running, access the API documentation using swagger at:
- Swagger UI: `http://localhost:8000/docs`

### Subsequent running of application
```bash
# start frontend
npm run start

# start backend service + db
docker compose up --build -d
```

## Usage Examples

### 1. Check Graph Summary
```powershell
curl http://localhost:8000/graph/summary
# Returns: {"status":"success","summary":{"servers":10,"apps":20,"oses":5,"relationships":40}}
```

### 2. List All Servers
```powershell
curl http://localhost:8000/graph/servers
```

### 3. Get Server Details
```powershell
curl http://localhost:8000/graph/server/server1
```

### 4. Chat with Graph Database
```powershell
$body = @{
    message = "What servers run Ubuntu?"
    use_rag = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -Body $body -ContentType "application/json"
```

### 5. Chat without Graph (General AI)
```powershell
$body = @{
    message = "What is artificial intelligence?"
    use_rag = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -Body $body -ContentType "application/json"
```

## Configuration

Key configuration options in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `OPENAI_MODEL` | GPT model to use | gpt-4o-mini |
| `OPENAI_TEMPERATURE` | Response randomness (0-1) | 0.7 |
| `OPENAI_MAX_TOKENS` | Max token usage | 1000 |


## License

This project is developed as part of a BNP interview assessment.

