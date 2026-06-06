#Raw queries related to retrieval, injestion dont need raw queries


from sqlalchemy import text

SEED_NODE_QUERY=text(
    """
        SELECT DISTINCT id 
        FROM nodes 
        WHERE source_chunk_id IN (
            SELECT id 
            FROM chunks 
            ORDER BY embedding <=> :query_vector::vector 
            LIMIT :limit_chunks
        );
    """
)
#parateters: query_vector, limit_chunks

RECURSIVE_TRAVERSAL_QUERY=text(
    """
        WITH RECURSIVE graph_traversal AS (
            SELECT id, name, description, 0 AS depth, ARRAY[id] AS visited 
            FROM nodes
            WHERE id = ANY(:seed_node_ids::uuid[])

            UNION ALL

            SELECT n.id, n.name, n.description, gt.depth + 1, gt.visited || n.id
            FROM graph_traversal gt
            JOIN edges e ON gt.id = e.source_node_id
            JOIN nodes n ON e.target_node_id = n.id
            WHERE gt.depth < :max_depth
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
)
#parameters: seed_node_ids, max_depth