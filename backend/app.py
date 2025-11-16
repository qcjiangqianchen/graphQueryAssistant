from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging

from config import settings
from neo4j_client import Neo4jClient
from openai_client import OpenAIClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Knowledge Graph Query Assistant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Neo4j client and OpenAI client
neo4j_client = Neo4jClient(
    uri=settings.neo4j_uri,
    username=settings.neo4j_user,
    password=settings.neo4j_password
)
openai_client = OpenAIClient()

#=========== Request/Response models ===========
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    use_rag: bool = True

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: Optional[List[dict]] = None

class DocumentUpload(BaseModel):
    content: str
    metadata: Optional[dict] = None
    


#=========== API Endpoints ===========#
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "BNP AI Chatbot API",
        "version": "1.0.0"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint that processes user messages through Neo4j and OpenAI

    Args:
        request: ChatRequest containing message and optional conversation_id

    Returns:
        ChatResponse with AI-generated response and graph data sources
    """
    try:
        logger.info(f"Processing chat request: {request.message[:50]}...")

        # Query Neo4j knowledge graph if enabled
        context = ""
        sources = []

        if request.use_rag:
            logger.info("Querying Neo4j knowledge graph...")
            graph_results = neo4j_client.natural_language_query(request.message)
            
            # Format graph results as context for OpenAI
            if graph_results.get("results"):
                context = f"Graph Query Results ({graph_results['intent']}):\\n"
                context += f"{graph_results['summary']}\\n\\n"
                
                # Format results based on intent
                for idx, result in enumerate(graph_results["results"][:5], 1):
                    context += f"{idx}. {result}\\n"
                
                sources = [{"type": "graph_query", "data": graph_results}]

        # Generate response using OpenAI with graph context
        logger.info("Generating response with OpenAI...")
        ai_response = await openai_client.generate_response(
            user_message=request.message,
            context=context,
            conversation_id=request.conversation_id
        )

        return ChatResponse(
            response=ai_response["response"],
            conversation_id=ai_response["conversation_id"],
            sources=sources if sources else None
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/summary")
async def get_graph_summary():
    """Get summary statistics about the knowledge graph"""
    try:
        logger.info("Fetching graph summary...")
        summary = neo4j_client.get_graph_summary()
        return {
            "status": "success",
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting graph summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/servers")
async def get_servers(limit: int = 50):
    """Get list of all servers"""
    try:
        logger.info(f"Fetching servers (limit: {limit})...")
        servers = neo4j_client.query_servers(limit=limit)
        return {
            "status": "success",
            "count": len(servers),
            "servers": servers
        }
    except Exception as e:
        logger.error(f"Error getting servers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/applications")
async def get_applications(limit: int = 50):
    """Get list of all applications"""
    try:
        logger.info(f"Fetching applications (limit: {limit})...")
        applications = neo4j_client.query_applications(limit=limit)
        return {
            "status": "success",
            "count": len(applications),
            "applications": applications
        }
    except Exception as e:
        logger.error(f"Error getting applications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/server/{server_id}")
async def get_server_details(server_id: str):
    """Get detailed information about a specific server"""
    try:
        logger.info(f"Fetching details for server: {server_id}...")
        details = neo4j_client.query_server_details(server_id)
        if not details:
            raise HTTPException(status_code=404, detail=f"Server {server_id} not found")
        return {
            "status": "success",
            "server": details
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting server details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
