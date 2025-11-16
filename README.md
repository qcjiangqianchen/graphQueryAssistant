# BNP AI Chatbot

An intelligent chatbot system powered by **Neo4j Graph Database**, **OpenAI GPT**, and **FastAPI**. 

## Overview

This project implements a knowledge graph-powered AI chatbot that:
- Uses **Neo4j** graph database for infrastructure knowledge management
- Implements natural language queries over structured graph data
- Integrates with **OpenAI's GPT-4o-mini** for intelligent responses
- Provides **FastAPI** backend with RESTful endpoints
- Includes **React** frontend with modern chat interface
- Fully **dockerized** with docker-compose for easy deployment

## Architecture

```
bnp_aichatbot/
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
│       ├── servers (1).csv
│       ├── applications (1).csv
│       ├── oses.csv
│       ├── runs_on.csv
│       ├── hosts (1).csv
│       └── located_in.csv
└── frontend/
    └── src/
        └── components/
            └── ChatInterface.tsx  # React chat UI
```

## Features

### Core Functionality
- **Graph-Powered Chat**: Natural language queries over Neo4j knowledge graph
- **Infrastructure Knowledge**: Query servers, applications, and their relationships
- **AI Responses**: GPT-4o-mini provides intelligent, context-aware answers
- **Conversation History**: Maintains context across multiple messages
- **Graph Visualization**: Neo4j Browser for visual data exploration

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/chat` | Send message and get AI response with graph context |
| GET | `/graph/summary` | Get knowledge graph statistics |
| GET | `/graph/servers` | List all servers |
| GET | `/graph/applications` | List all applications |
| GET | `/graph/server/{id}` | Get detailed server information |

## 🚀 Quick Start with Docker

### Prerequisites
- Docker and Docker Compose
- OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd bnp_aichatbot
```

2. **Set up environment variables**
Create a `.env` file in the root directory:
```bash
OPENAI_API_KEY=your-openai-api-key-here
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Load graph data**
```bash
docker-compose exec backend python load_graph_data.py
```

5. **Access services**
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (neo4j/password123)
- **Frontend**: http://localhost:3000

### Local Development (Without Docker)

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

### API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

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
| `CHUNK_SIZE` | Text chunk size for RAG | 1000 |
| `TOP_K_RESULTS` | Number of results to retrieve | 3 |
| `PERSIST_DIRECTORY` | Vector store location | ./vector_store |

## Project Components

### RAG Engine (`rag_engine.py`)
- Document chunking and embedding
- FAISS vector store management
- Similarity search and context retrieval
- Document persistence

### OpenAI Client (`openai_client.py`)
- Chat completion handling
- Conversation history management
- System prompt construction
- Token usage tracking

### Configuration (`config.py`)
- Environment variable management
- Settings validation with Pydantic
- Centralized configuration access

## Development

### Running in Development Mode
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Testing the API
Use the Swagger UI at `http://localhost:8000/docs` for interactive testing.

### Logging
The application uses Python's logging module. Logs are output to console with INFO level by default.

## Production Considerations

For production deployment:

1. **Security**
   - Update CORS origins in `app.py`
   - Use environment-specific configuration
   - Implement API authentication

2. **Performance**
   - Use Redis for conversation history
   - Implement request rate limiting
   - Add caching layer

3. **Storage**
   - Use PostgreSQL with pgvector for production vector store
   - Implement proper backup strategies
   - Use cloud storage for document persistence

4. **Monitoring**
   - Add application monitoring
   - Implement error tracking
   - Set up logging aggregation

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure you're in the `backend` directory and virtual environment is activated
2. **OpenAI API errors**: Verify your API key is valid and has credits
3. **Vector store errors**: Check write permissions for `PERSIST_DIRECTORY`
4. **Memory issues**: Reduce `CHUNK_SIZE` or use fewer documents

## License

This project is developed as part of a BNP interview assessment.

## Contact

For questions or issues, please contact the development team.
