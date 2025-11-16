"""
Neo4j Client for Knowledge Graph queries
Handles connections and Cypher query execution
"""
import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Manages connections and queries to Neo4j graph database"""

    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize Neo4j client
        
        Args:
            uri: Neo4j connection URI (e.g., bolt://localhost:7687)
            username: Neo4j username
            password: Neo4j password
        """
        logger.info(f"Initializing Neo4j client to {uri}...")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            # Verify connectivity
            self.driver.verify_connectivity()
            logger.info("Neo4j client connected successfully")
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise

    def close(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results
        
        Args:
            query: Cypher query string
            parameters: Optional query parameters
            
        Returns:
            List of result records as dictionaries
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    def query_servers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all servers with their properties"""
        query = """
        MATCH (s:Server)
        RETURN s.id AS id, s.name AS name
        LIMIT $limit
        """
        return self.execute_query(query, {"limit": limit})

    def query_applications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all applications"""
        query = """
        MATCH (a:Application)
        RETURN a.id AS id, a.name AS name
        LIMIT $limit
        """
        return self.execute_query(query, {"limit": limit})

    def query_server_details(self, server_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific server including:
        - Operating system it runs on
        - Applications it hosts
        - Location
        """
        query = """
        MATCH (s:Server {id: $server_id})
        OPTIONAL MATCH (s)-[:RUNS_ON]->(os:OS)
        OPTIONAL MATCH (s)-[:HOSTS]->(app:Application)
        OPTIONAL MATCH (s)-[:LOCATED_IN]->(loc:Location)
        RETURN s.id AS server_id, 
               s.name AS server_name,
               os.name AS operating_system,
               collect(DISTINCT app.name) AS applications,
               loc.id AS location
        """
        results = self.execute_query(query, {"server_id": server_id})
        return results[0] if results else {}

    def query_applications_by_os(self, os_name: str) -> List[Dict[str, Any]]:
        """Find all applications running on servers with a specific OS"""
        query = """
        MATCH (s:Server)-[:RUNS_ON]->(os:OS)
        WHERE os.name CONTAINS $os_name
        MATCH (s)-[:HOSTS]->(app:Application)
        RETURN DISTINCT app.id AS app_id, app.name AS app_name, 
               s.name AS server_name, os.name AS os_name
        """
        return self.execute_query(query, {"os_name": os_name})

    def query_servers_by_location(self, location_id: str) -> List[Dict[str, Any]]:
        """Find all servers in a specific location"""
        query = """
        MATCH (s:Server)-[:LOCATED_IN]->(loc:Location {id: $location_id})
        OPTIONAL MATCH (s)-[:RUNS_ON]->(os:OS)
        OPTIONAL MATCH (s)-[:HOSTS]->(app:Application)
        RETURN s.id AS server_id, s.name AS server_name,
               os.name AS operating_system,
               collect(app.name) AS applications
        """
        return self.execute_query(query, {"location_id": location_id})

    def natural_language_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process natural language queries and convert to appropriate Cypher
        
        Args:
            user_query: User's natural language question
            
        Returns:
            Dictionary with query results and context
        """
        query_lower = user_query.lower()
        
        # Detect query intent and execute appropriate query
        if "server" in query_lower and any(word in query_lower for word in ["list", "show", "all", "what"]):
            results = self.query_servers(limit=50)
            return {
                "intent": "list_servers",
                "results": results,
                "summary": f"Found {len(results)} servers"
            }
        
        elif "application" in query_lower and any(word in query_lower for word in ["list", "show", "all"]):
            results = self.query_applications(limit=50)
            return {
                "intent": "list_applications",
                "results": results,
                "summary": f"Found {len(results)} applications"
            }
        
        elif "ubuntu" in query_lower or "windows" in query_lower or "centos" in query_lower or "linux" in query_lower:
            # Extract OS name from query
            os_keywords = ["ubuntu", "windows", "centos", "linux", "rhel"]
            os_name = next((word for word in os_keywords if word in query_lower), "")
            results = self.query_applications_by_os(os_name.capitalize())
            return {
                "intent": "query_by_os",
                "results": results,
                "summary": f"Found {len(results)} applications on {os_name} servers"
            }
        
        elif "location" in query_lower or "loc" in query_lower:
            # Try to extract location ID
            import re
            loc_match = re.search(r'loc\d+', query_lower)
            if loc_match:
                location_id = loc_match.group(0)
                results = self.query_servers_by_location(location_id)
                return {
                    "intent": "query_by_location",
                    "results": results,
                    "summary": f"Found {len(results)} servers in {location_id}"
                }
        
        # If specific server mentioned
        import re
        server_match = re.search(r'server\d+', query_lower)
        if server_match:
            server_id = server_match.group(0)
            result = self.query_server_details(server_id)
            return {
                "intent": "server_details",
                "results": [result],
                "summary": f"Details for {server_id}"
            }
        
        # Default: return general graph statistics
        stats_query = """
        MATCH (s:Server) WITH count(s) as server_count
        MATCH (a:Application) WITH server_count, count(a) as app_count
        MATCH (os:OS) WITH server_count, app_count, count(os) as os_count
        RETURN server_count, app_count, os_count
        """
        stats = self.execute_query(stats_query)
        return {
            "intent": "general_info",
            "results": stats,
            "summary": "Graph database statistics"
        }

    def get_graph_summary(self) -> Dict[str, Any]:
        """Get summary statistics about the knowledge graph"""
        query = """
        MATCH (s:Server) WITH count(s) as servers
        MATCH (a:Application) WITH servers, count(a) as apps
        MATCH (os:OS) WITH servers, apps, count(os) as oses
        MATCH ()-[r]->() WITH servers, apps, oses, count(r) as relationships
        RETURN servers, apps, oses, relationships
        """
        result = self.execute_query(query)
        return result[0] if result else {}
