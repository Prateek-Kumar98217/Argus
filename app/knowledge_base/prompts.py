# app/knowledge_base/prompts.py

EXTRACTION_SYSTEM_PROMPT = """
You are an expert systems architecture analyzer responsible for extracting key entities and their interconnected relationships into a clean, abstract knowledge graph.
"""

EXTRACTION_TASK_PROMPT = """
Analyze the provided chunks of data and extract key entities (nodes) and relationships (edges).

PREFERRED NODE TYPES:
{preferred_node_types}

PREFERRED EDGE TYPES:
{preferred_edge_types}

EXISTING ALREADY KNOWN NODES (Use these names if they match semantically to prevent duplicate aliases):
{existing_nodes}

INSTRUCTIONS:
1. Read each <chunk> carefully.
2. Extract nodes and edges specific to that chunk.
3. Map your response back to the specific chunk ID attribute.
4. Try to use the preferred node and edge types as much as possible.
5. If the preferred types are insufficient, create new ones. Keep them highly abstract to minimize total category sprawl.
6. If no explicit relationship exists between entities, do not force edge creation.
7. Deduplicate entities aggressively: Do not create separate nodes for 'Postgres' and 'postgres db'. Map them both to a single canonical node name like 'PostgreSQL'.

TEXT CHUNKS TO PROCESS:
{batched_chunk_text}
"""