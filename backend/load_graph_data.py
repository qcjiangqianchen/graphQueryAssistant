"""
Load CSV data from relations folder into Neo4j graph database
"""
import csv
import logging
from pathlib import Path
from neo4j_client import Neo4jClient
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphDataLoader:
    """Loads CSV files into Neo4j knowledge graph"""
    
    def __init__(self, neo4j_client: Neo4jClient):
        self.client = neo4j_client
        self.relations_dir = Path(__file__).parent / "relations"
    
    def clear_database(self):
        """Clear all nodes and relationships from the database"""
        logger.info("Clearing existing data from Neo4j...")
        query = "MATCH (n) DETACH DELETE n"
        self.client.execute_query(query)
        logger.info("Database cleared")
    
    def create_constraints(self):
        """Create unique constraints for node IDs"""
        logger.info("Creating constraints...")
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Server) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Application) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (os:OS) REQUIRE os.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (loc:Location) REQUIRE loc.id IS UNIQUE"
        ]
        for constraint in constraints:
            try:
                self.client.execute_query(constraint)
            except Exception as e:
                logger.warning(f"Constraint may already exist: {e}")
        logger.info("Constraints created")
    
    def load_servers(self):
        """Load servers from CSV"""
        logger.info("Loading servers...")
        csv_path = self.relations_dir / "servers (1).csv"
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            servers = list(reader)
        
        query = """
        UNWIND $servers AS server
        MERGE (s:Server {id: server.id})
        SET s.name = server.name
        """
        self.client.execute_query(query, {"servers": servers})
        logger.info(f"Loaded {len(servers)} servers")
    
    def load_applications(self):
        """Load applications from CSV"""
        logger.info("Loading applications...")
        csv_path = self.relations_dir / "applications (1).csv"
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            applications = list(reader)
        
        query = """
        UNWIND $applications AS app
        MERGE (a:Application {id: app.id})
        SET a.name = app.name
        """
        self.client.execute_query(query, {"applications": applications})
        logger.info(f"Loaded {len(applications)} applications")
    
    def load_operating_systems(self):
        """Load operating systems from CSV"""
        logger.info("Loading operating systems...")
        csv_path = self.relations_dir / "oses.csv"
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            oses = list(reader)
        
        query = """
        UNWIND $oses AS os
        MERGE (o:OS {id: os.id})
        SET o.name = os.name
        """
        self.client.execute_query(query, {"oses": oses})
        logger.info(f"Loaded {len(oses)} operating systems")
    
    def load_locations(self):
        """Create location nodes from located_in relationships"""
        logger.info("Loading locations...")
        csv_path = self.relations_dir / "located_in.csv"
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            locations = set(row['end'] for row in reader)
        
        query = """
        UNWIND $locations AS loc_id
        MERGE (l:Location {id: loc_id})
        SET l.name = loc_id
        """
        self.client.execute_query(query, {"locations": list(locations)})
        logger.info(f"Loaded {len(locations)} locations")
    
    def load_runs_on_relationships(self):
        """Load RUNS_ON relationships (Server -> OS)"""
        logger.info("Loading RUNS_ON relationships...")
        csv_path = self.relations_dir / "runs_on.csv"
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            relationships = list(reader)
        
        query = """
        UNWIND $rels AS rel
        MATCH (s:Server {id: rel.start})
        MATCH (os:OS {id: rel.end})
        MERGE (s)-[:RUNS_ON]->(os)
        """
        self.client.execute_query(query, {"rels": relationships})
        logger.info(f"Loaded {len(relationships)} RUNS_ON relationships")
    
    def load_hosts_relationships(self):
        """Load HOSTS relationships (Server -> Application)"""
        logger.info("Loading HOSTS relationships...")
        csv_path = self.relations_dir / "hosts (1).csv"
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            relationships = list(reader)
        
        query = """
        UNWIND $rels AS rel
        MATCH (s:Server {id: rel.start})
        MATCH (a:Application {id: rel.end})
        MERGE (s)-[:HOSTS]->(a)
        """
        self.client.execute_query(query, {"rels": relationships})
        logger.info(f"Loaded {len(relationships)} HOSTS relationships")
    
    def load_located_in_relationships(self):
        """Load LOCATED_IN relationships (Server -> Location)"""
        logger.info("Loading LOCATED_IN relationships...")
        csv_path = self.relations_dir / "located_in.csv"
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            relationships = list(reader)
        
        query = """
        UNWIND $rels AS rel
        MATCH (s:Server {id: rel.start})
        MATCH (l:Location {id: rel.end})
        MERGE (s)-[:LOCATED_IN]->(l)
        """
        self.client.execute_query(query, {"rels": relationships})
        logger.info(f"Loaded {len(relationships)} LOCATED_IN relationships")
    
    def load_all(self, clear_first: bool = True):
        """Load all data into Neo4j"""
        logger.info("Starting full data load...")
        
        if clear_first:
            self.clear_database()
        
        self.create_constraints()
        
        # Load nodes first
        self.load_servers()
        self.load_applications()
        self.load_operating_systems()
        self.load_locations()
        
        # Load relationships
        self.load_runs_on_relationships()
        self.load_hosts_relationships()
        self.load_located_in_relationships()
        
        # Get summary
        summary = self.client.get_graph_summary()
        logger.info(f"Data load complete! Summary: {summary}")
        
        return summary


def main():
    """Main function to load data"""
    logger.info("Connecting to Neo4j...")
    
    # Initialize Neo4j client
    neo4j_client = Neo4jClient(
        uri=settings.neo4j_uri,
        username=settings.neo4j_user,
        password=settings.neo4j_password
    )
    
    try:
        # Load data
        loader = GraphDataLoader(neo4j_client)
        summary = loader.load_all(clear_first=True)
        
        logger.info("=" * 50)
        logger.info("Data loading completed successfully!")
        logger.info(f"Servers: {summary.get('servers', 0)}")
        logger.info(f"Applications: {summary.get('apps', 0)}")
        logger.info(f"Operating Systems: {summary.get('oses', 0)}")
        logger.info(f"Total Relationships: {summary.get('relationships', 0)}")
        logger.info("=" * 50)
        
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    main()
