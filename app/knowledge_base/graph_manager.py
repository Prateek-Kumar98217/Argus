from app.knowledge_base.state import GraphState
from app.knowledge_base.db.engine import AsyncSessionLocal
from app.knowledge_base.ingestion import Chunker, DocumentReader, ExtractionService
from app.knowledge_base.ingestion.extractor import BatchedResult


class GraphManager:
    def __init__(self, graph_state: GraphState, chunk_size: int = 300, batch_size: int = 5, embed_dim: int = 768)-> None:
        self._state = graph_state
        self._reader = DocumentReader()
        self._chunker = Chunker(chunk_size=chunk_size)
        self._extractor = ExtractionService(graph_state=graph_state, embed_dim=embed_dim)
        self._batch_size = batch_size


    async def process_document(self, filepath)->None:
        text_stream = self.reader.stream(filepath)
        chunk_stream = self.chunker.chunk(text_stream)
        batches = list(self._chunker.batch(chunk_stream, self._batch_size))

        async for result in self._extractor.process_batches(batches):
            await self._persist(result)
            self._apply_to_state(result)

    
    async def _persist(self, result: BatchedResult):
        pass


    def _apply_to_state(self, result: BatchedResult):
        for node in result.extraction.nodes:
            self._state.update_nodes(node.name)
            self._state.update_node_types(node.type)

        for edge in result.extraction.edges:
            self._state.update_edge_types(edge.type)