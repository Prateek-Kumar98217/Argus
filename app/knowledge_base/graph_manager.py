import uuid

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.knowledge_base.state import GraphState
from app.knowledge_base.db.engine import AsyncSessionLocal
from app.knowledge_base.db.models import Chunk, Node, Edge, NodeToChunks
from app.knowledge_base.ingestion import Chunker, DocumentReader, ExtractionService
from app.knowledge_base.ingestion.extractor import BatchedResult


class GraphManager:
    def __init__(self, graph_state: GraphState, chunk_size: int = 100, batch_size: int = 5, embed_dim: int = 768)-> None:
        self._state = graph_state
        self._reader = DocumentReader()
        self._chunker = Chunker(chunk_size=chunk_size)
        self._extractor = ExtractionService(graph_state=graph_state, embed_dim=embed_dim)
        self._batch_size = batch_size


    async def process_document(self, filepath)->None:
        text_stream = self._reader.stream(filepath)
        chunk_stream = self._chunker.chunk(text_stream)
        batches = list(self._chunker.batch(chunk_stream, self._batch_size))

        async for result in self._extractor.process_batches(batches):
            await self._persist(result)
            self._apply_to_state(result)

    
    async def _persist(self, result: BatchedResult):
        async with AsyncSessionLocal() as session:
            try:
                chunk_uuids = await self._insert_chunks(session, result)
                node_name_to_uuid = await self._upsert_nodes(session, result, chunk_uuids)
                await self._upsert_edges(session, result, node_name_to_uuid)
                await session.commit()
                self._check_state()
            except Exception as exc:
                await session.rollback()
                raise RuntimeError(
                    f"[Graph Manager] Batch persistence failed, transaction rollbacked: {exc}"
                )from exc


    async def _insert_chunks(self, session, result: BatchedResult)->list[uuid.UUID]:
        chunk_uuids:list[uuid.UUID] = []
        for chunk, embedding in zip(result.chunks, result.embeddings):
            chunk_uuid = uuid.uuid4()
            session.add(
                Chunk(
                    id=chunk_uuid,
                    context=chunk,
                    embedding=embedding,
                )
            )

            chunk_uuids.append(chunk_uuid)

        await session.flush()
        return chunk_uuids


    async def _upsert_nodes(self, session, result: BatchedResult, chunk_uuids: list[uuid.UUID])->dict[str, uuid.UUID]:
        node_name_to_uuid: dict[str, uuid.UUID] = {}
        for chunk in result.extraction.extracted_batches:
            for node in chunk.nodes:
                stmt=(
                    pg_insert(Node).values(
                        id=uuid.uuid4(),
                        name=node.name,
                        type=node.type,
                        description=node.description,
                    ).on_conflict_do_update(
                        index_elements=["name"],
                        set_ = {"description": node.description}
                    ).returning(Node.id)
                )

                result_row = await session.execute(stmt)
                node_name_to_uuid[node.name] = result_row.scalar_one()
        return node_name_to_uuid


    async def _upsert_edges(self, session, result: BatchedResult, node_name_to_uuid: list[uuid.UUID])->None:
        for chunk in result.extraction.extracted_batches:
            for edge in chunk.edges:
                source_node_uuid = node_name_to_uuid.get(edge.source_node)
                target_node_uuid = node_name_to_uuid.get(edge.target_node)

                if not source_node_uuid or not target_node_uuid:
                    print(f"[Graph Manager] Skipping edge '{edge.source_node}' -> '{edge.target_node}': One or both nodes not yet persisted")
                    continue

                stmt = pg_insert(Edge).values(
                    id=uuid.uuid4(),
                    source_node_id = source_node_uuid,
                    target_node_id = target_node_uuid,
                    relationship_type = edge.type,
                    description = edge.description,
                ).on_conflict_do_nothing(index_elements=["source_node_id", "target_node_id", "relationship_type"])

                await session.execute(stmt)


    def _apply_to_state(self, result: BatchedResult):
        for batch in result.extraction.extracted_batches:
            for node in batch.nodes:
                self._state.update_nodes(node.name)
                self._state.update_node_types(node.type)

        for batch in result.extraction.extracted_batches:
            for edge in batch.edges:
                self._state.update_edge_types(edge.type)

    def _check_state(self):
        print(f"NODES: {self._state.nodes}")
        print(f"NODE TYPES: {self._state.node_types}")
        print(f"EDGE_TYPES: {self._state.edge_types}")