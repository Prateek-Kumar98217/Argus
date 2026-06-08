# app/knowledge_base/schemas.py
from pydantic import BaseModel, Field

class NodeExtraction(BaseModel):
    name: str = Field(
        description="Canonical name of the entity. Normalize variants to a single name (e.g., 'Postgres' and 'postgres db' -> 'PostgreSQL'). Use Title Case."
    )
    type: str = Field(
        description="The general domain category of the entity (e.g., 'Database', 'Microservice', 'Framework', 'Library'). Prefer existing types if provided."
    )
    description: str = Field(
        description="A concise summary of the entity's purpose or role."
    )

class EdgeExtraction(BaseModel):
    source_node: str = Field(
        description="The exact name of the source entity, matching a 'name' field in the nodes list."
    )
    target_node: str = Field(
        description="The exact name of the target entity, matching a 'name' field in the nodes list."
    )
    type: str = Field(
        description="The relationship action type in uppercase (e.g., 'QUERIES', 'DEPENDS_ON', 'AUTHENTICATES'). Keep it highly abstract."
    )
    description: str = Field(
        description="A brief, one-sentence description explaining why or how these two entities(from source to target only) are connected based on the text."
    )

class ChunkGraph(BaseModel):
    chunk_id: int = Field(
        description="The exact integer ID extracted from the surrounding <chunk id='X'> tag."
    )
    nodes: list[NodeExtraction] = Field(
        default_factory=list,
        description="List of distinct, unique entities found within this specific chunk."
    )
    edges: list[EdgeExtraction] = Field(
        default_factory=list,
        description="List of explicit, directed relationships connecting the nodes within this specific chunk."
    )

class KnowledgeGraphExtraction(BaseModel):
    extracted_batches: list[ChunkGraph] = Field(
        default_factory=list,
        description="The collection of extracted graphs, grouped sequentially by their chunk IDs."
    )