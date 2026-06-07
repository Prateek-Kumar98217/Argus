import psycopg2
from google import genai
from google.genai import types
from yolo.graphrag.graph_state import GraphState

DB_URI = "postgresql://admin:localpassword123@localhost:5432/graphrag_db"

embedding_client = genai.Client()
graph_state = GraphState(DB_URI)

def retrieve(query: str) -> str:
    embedding = embedding_client.models.embed_content(
        model="gemini-embedding-2",
        contents=query, 
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    query_vector = embedding.embeddings[0].values

    with psycopg2.connect(graph_state.db_uri) as conn:
        with conn.cursor() as cur:

            seed_nodes_query = """
                SELECT DISTINCT id 
                FROM nodes 
                WHERE source_chunk_id IN (
                    SELECT id 
                    FROM chunks 
                    ORDER BY embedding <=> %s::vector 
                    LIMIT 1
                );
            """
            cur.execute(seed_nodes_query, (query_vector,))
            seed_node_rows = cur.fetchall()
            seed_node_ids = [row[0] for row in seed_node_rows]
            
            if not seed_node_ids:
                print("No starting nodes found matching the query vector.")
                return ""
            traversal_query = """
                WITH RECURSIVE graph_traversal AS (
                
                    SELECT id, name, description, 0 AS depth, ARRAY[id] AS visited 
                    FROM nodes
                    WHERE id = ANY(%s::uuid[])
                    
                    UNION ALL
                    
                    SELECT n.id, n.name, n.description, gt.depth + 1, gt.visited || n.id
                    FROM graph_traversal gt
                    JOIN edges e ON gt.id = e.source_node_id
                    JOIN nodes n ON e.target_node_id = n.id
                    WHERE gt.depth < 2
                        AND NOT (n.id = ANY(gt.visited))
                ),
                discovered_nodes AS (
                    SELECT DISTINCT id FROM graph_traversal
                )
                SELECT DISTINCT c.context
                FROM chunks c
                JOIN nodes n ON n.source_chunk_id = c.id
                WHERE n.id IN (SELECT id FROM discovered_nodes);
            """
            
            cur.execute(traversal_query, (seed_node_ids,))
            rows = cur.fetchall() 
            context_chunks = [row[0] for row in rows]
            
            if not context_chunks:
                print("No downstream graph context found connected to those nodes.")
            else:
                print("\n\n".join(context_chunks))

if __name__ == "__main__":
    query = "How does the API Gateway handle user session verification and where does it check if the data isn't cached?"
    retrieve(query)