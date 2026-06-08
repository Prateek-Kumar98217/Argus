import os
import instructor
import psycopg2
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from prototypes.graphrag.graph_state import GraphState

DB_URI = "postgresql://admin:localpassword123@localhost:5432/graphrag_db"

graph_state = GraphState(DB_URI)

#pydanctic classes for structured output
class NodeExtraction(BaseModel):
    name: str = Field(..., description="Unique name of the entity, normalized to Title Case (e.g., 'Cloudflare Worker').")
    type: str = Field(..., description=f"Category of the entity. Try to use one of these if applicable: {list(graph_state.node_types)}, if not possible create new.")
    description: str = Field(..., description="A clear, brief summary of what this entity does based strictly on the text.")

class EdgeExtraction(BaseModel):
    source: str = Field(..., description="The name of the origin entity (must match a node name exactly).")
    target: str = Field(..., description="The name of the destination entity (must match a node name exactly).")
    relationship_type: str = Field(..., description=f"The type of relationship between the source and target. Try to use one of these if applicable: {list(graph_state.edge_types)}, if not possible create new")
    description: str = Field(..., description="A sentence explaining why or how these entities connect.")

class KnowledgeGraphExtraction(BaseModel):
    nodes: list[NodeExtraction] = Field(default_factory=list, description="List of all unique entities found in the text.")
    edges: list[EdgeExtraction] = Field(default_factory=list, description="List of all directed relationships between the found entities.")

#instructor client(enviroment variables to be given from terminal for now)
client = instructor.from_provider("google/gemini-3.5-flash")
embedding_client = genai.Client()

def extract_and_store(text_context:str):
    print("Processing chunk...")
    extracted_data: KnowledgeGraphExtraction = client.create(
        response_model=KnowledgeGraphExtraction,
        messages=[
            {"role": "system", "content":"You are a senior systems engineer extracting functional architecture graphs."},
            {"role": "user", "content": f"fAnalyze this text chunk and extract all relevant system entities and structural relationships:\n\n{text_context}"}
        ]
    )
    #get embedding of chunks
    embedding = embedding_client.models.embed_content(
        model="gemini-embedding-2",
        contents=text_context,
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    #update the graph state in memory
    for node in extracted_data.nodes:
        if node.name not in graph_state.nodes:
            graph_state.nodes.add(node.name)
        if node.type not in graph_state.node_types:
            graph_state.node_types.add(node.type)
    for edge in extracted_data.edges:
        if edge.relationship_type not in graph_state.edge_types:
            graph_state.edge_types.add(edge.relationship_type)

    print(f"Extraction successful: {len(extracted_data.nodes)}nodes and {len(extracted_data.edges)} edges.")

    #add data into the database
    with psycopg2.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            # add chunks to the db
            cur.execute(
                "INSERT INTO chunks (context, embedding) VALUES (%s, %s) RETURNING id;",
                (text_context, embedding.embeddings[0].values)
            )
            chunk_id = cur.fetchone()[0]

            #upsert nodes
            node_name_to_id={}
            for node in extracted_data.nodes:
                cur.execute(
                    """
                    INSERT INTO nodes (name, type, description, source_chunk_id) 
                    VALUES(%s, %s, %s, %s) 
                    ON CONFLICT (name) DO UPDATE SET 
                        description = EXCLUDED.description 
                    RETURNING id;
                    """,
                    (node.name, node.type, node.description, chunk_id)
                )
                node_name_to_id[node.name] = cur.fetchone()[0]
            
            #upset edges
            for edge in extracted_data.edges:
                source_id = node_name_to_id.get(edge.source)
                target_id = node_name_to_id.get(edge.target)
                cur.execute(
                    """
                    INSERT INTO edges (source_node_id, target_node_id, relationship_type, description) 
                    VALUES(%s, %s, %s, %s) 
                    ON CONFLICT (source_node_id, target_node_id, relationship_type) DO NOTHING;
                    """,
                    (source_id, target_id, edge.relationship_type, edge.description)
                )
            conn.commit()
            print("Translation to graph completed.")

if __name__ == "__main__":
    sample_docs = [
        "The API Gateway is the single entry point for all incoming client traffic. It is built using a custom Rust-based reverse proxy that handles TLS termination and rate limiting. To optimize downstream routing, the API Gateway passes all authenticated requests directly to the User Authentication Service over a high-throughput gRPC channel.",
        "The User Authentication Service handles session validation, token signing, and permission checks. To maintain high availability and sub-millisecond validation speeds, the User Authentication Service relies entirely on a Distributed Session Cache. This cache layer is deployed on an Upstash Redis cluster utilizing aggressive key eviction policies.",
        "The Distributed Session Cache stores ephemeral user claims and OAuth state tokens. If a cache miss occurs within this Redis layer, the system performs a fallback read query to the Primary User Database to re-hydrate the cache.",
        "The Primary User Database is the absolute source of truth for user profiles, hashed credentials, and account metadata. It is hosted on a highly available PostgreSQL 16 instance using physical streaming replication to a read replica."]
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: Please set the GEMINI_API_KEY environment variable.")
    else:
        for doc in sample_docs:
            extract_and_store(doc)
        