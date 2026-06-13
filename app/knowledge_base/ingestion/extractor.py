import asyncio
import instructor

from google import genai
from google.genai import types
from dataclasses import dataclass
from collections.abc import AsyncIterator

from app.core.settings import settings
from app.knowledge_base.state import GraphState
from app.knowledge_base.schemas import KnowledgeGraphExtraction
from app.knowledge_base.prompts import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_TASK_PROMPT


@dataclass
class BatchedResult:
    chunks: list[str]
    embeddings: list[list[float]]
    extraction: KnowledgeGraphExtraction
    

class ExtractionService:
    def __init__(self, graph_state: GraphState, embed_dim: int = 768):
        self._state = graph_state
        self._embed_dim = embed_dim
        self._raw_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._instructor_client = instructor.from_genai(client=self.raw_client, async_client = True)
        self._extraction_model = settings.EXTRACT_MODEL
        self._embedding_model = settings.EMBED_MODEL


    async def process_batches(self, batches: list[list[str]]) ->AsyncIterator[BatchedResult]:
        for batch in batches:
            result = await self._process_single_batch(batch)
            if result is not None:
                yield result


    async def _process_single_batch(self, batch: list[str])-> BatchedResult | None:
        extraction, embeddings = asyncio.gather(
            self._extract_with_retry(batch),
            self._embed_chunks(batch),
            return_exceptions=False,
        )

        if extraction is None or embeddings is None:
            #Need a new exception for this
            return None
        
        return BatchedResult(chunks=batch, embeddings=embeddings, extraction=extraction)
    

    def _build_prompt(self, chunk_batch: list[str])-> str:
        node_types = ", ".join(self._state.node_types.keys()) or "None yet"
        edge_types = ", ".join(self.state.edge_types.keys()) or "None yet"
        existing_nodes = ", ".join(self.state.nodes) or "None yet"

        batched_chunks_text = "".join(
            f'<chunk id="chunk_id">\n{chunk_text}\n</chunk>'
            for chunk_id, chunk_text in enumerate(chunk_batch)
        )

        return EXTRACTION_TASK_PROMPT.format(
            preferred_node_types=node_types,
            preferred_edge_types=edge_types,
            existing_nodes=existing_nodes,
            batched_chunk_text=batched_chunks_text
        )
    

    async def _extract_with_retry(self, batch: list[str], retries: int = 2)->KnowledgeGraphExtraction | None:
        prompt = self._build_prompt(batch)
        last_exc = Exception | None = None

        for attempt in range(retries):
            try:
                return await self._instructor_client.create(
                    model=self._extraction_model,
                    response_model=KnowledgeGraphExtraction,
                    messages=[
                        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ]
                )
            except Exception as exc:
                last_exc = exc
                if attempt < retries:
                    await asyncio.sleep(2**attempt)

        print(f"[EXTRACTION SERVICE] Extraction failed after {retries + 1} attempts: {last_exc}")
        return None



    async def _embed_chunks(self, chunks: list[str])-> list[list[float]] | None:
        try:
            response = await self._raw_client.aio.models.embed_content(
                model=self._embedding_model,
                contents=chunks,
                config=types.EmbeddingContentConfig(
                    output_dimensionality=self._embed_dim
                )
            )
            return [embedding.values for embedding in response.embeddings]
        except Exception as exc:
            print(f"[EXTRACTION SERVICE] Embedding failed: {exc}")
            return None