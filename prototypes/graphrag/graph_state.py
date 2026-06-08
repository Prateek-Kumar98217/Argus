import psycopg2

class GraphState:
    def __init__(self, db_uri: str):
        self.db_uri = db_uri
        self.nodes = set()
        self.node_types = set()
        self.edge_types = set()
        self.refresh_from_db()

    def refresh_from_db(self) -> None:
        with psycopg2.connect(self.db_uri) as conn:
            with conn.cursor() as cur:
                #load existing nodes and types(intialize if db empty)
                cur.execute("SELECT name from nodes;")
                self.nodes = {row[0] for row in cur.fetchall()}
                cur.execute("SELECT DISTINCT type FROM nodes;")
                self.node_types = {row[0] for row in cur.fetchall()}
                #load types of edges(intialize if db empty)
                cur.execute("SELECT DISTINCT relationship_type FROM edges;")
                self.edge_types = {row[0] for row in cur.fetchall()}
    