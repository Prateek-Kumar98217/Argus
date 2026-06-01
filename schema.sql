CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nodes(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(100),
    description TEXT,
    source_chunk_id UUID REFERENCES chunks(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS edges(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_node_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    target_node_id UUID REFERENCES nodes(id) on DELETE CASCADE,
    relationship_type VARCHAR(100),
    DESCRIPTION TEXT,
    UNIQUE( source_node_id, target_node_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_node_name ON nodes(name);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_node_id);

CREATE INDEX IF NOT EXISTS idx_embedding_chunk_hnsw ON chunks USING hnsw(embedding vector_cosine_ops);