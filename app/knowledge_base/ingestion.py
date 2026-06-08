#Responsible for complete data injestion including, chunking, node and edge extraction, embedding and database management.

import re
import json
import asyncio
import instructor

from google import genai
from google.genai import types
from collections.abc import Generator

from app.core.settings import settings
from app.knowledge_base.state import GraphState
from app.knowledge_base.db.engine import AsyncSessionLocal
from app.knowledge_base.schemas import KnowledgeGraphExtraction
from app.knowledge_base.prompts import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_TASK_PROMPT

class GraphManager:
    def __init__(self, graph_state: GraphState, chunk_size: int = 300)->None:
        self.state = graph_state
        #raw client for embedding task
        self.raw_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        #instructor client for schema validation of extraction output
        self.instructor_client = instructor.from_genai(client=self.raw_client)
        self.chunk_size = chunk_size
        #specific models
        self.embedding_model = settings.EMBED_MODEL
        self.extraction_model = settings.EXTRACT_MODEL

    
    def _read_docs(self, filepath)-> str:
        pass


    def _split_sentences(self, paragraph)->list[str]:
        pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s'
        return [s.strip() for s in re.split(pattern, paragraph) if s.strip()]


    def _chunk(self, text) -> Generator[str]:
        paragraphs = re.split(r'\n\n+', text.strip())
        last_yielded_chunk = None

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            if len(paragraph.split())<= self.chunk_size:
                yield paragraph
                last_yielded_chunk = paragraph
                continue

            sentences = self._split_sentences(paragraph)
            current_chunk = []
            current_word_count = 0

            for sentence in sentences:
                sentence_words = sentence.split()
                sentence_word_count = len(sentence_words)

                if sentence_word_count > self.chunk_size:
                    if current_chunk:
                        chunk_str = " ".join(current_chunk)
                        yield chunk_str
                        last_yielded_chunk = chunk_str
                    yield sentence
                    last_yielded_chunk = sentence
                    current_chunk = []
                    current_word_count = 0
                    continue

                if current_word_count + sentence_word_count >= self.chunk_size:
                    current_chunk.append(sentence)
                    chunk_str = " ".join(current_chunk)
                    yield chunk_str
                    last_yielded_chunk = chunk_str

                    current_chunk = [sentence]
                    current_word_count = sentence_word_count
                    continue
                
                current_chunk.append(sentence)
                current_word_count += sentence_word_count

            if current_chunk:
                chunk_str = " ".join(current_chunk)
                if chunk_str != last_yielded_chunk:
                    yield chunk_str
                    last_yielded_chunk=chunk_str


    def _generate_batches(self, chunk_iterable, batch_size: int = 5) -> Generator[list[str]]:
        batch = []
        for chunk in chunk_iterable:
            batch.append(chunk)
            if len(batch) == batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    
    def _generate_extraction_prompt(self, chunk_batch: list[str]) -> str:
        preferred_node_types = ", ".join(self.state.node_types.keys()) or "None yet"
        preferred_edge_types = ", ".join(self.state.edge_types.keys()) or "None yet"
        existing_nodes = ", ".join(self.state.nodes) or "None yet"

        batched_chunks_text = ""

        for temp_id, chunk in enumerate(chunk_batch):
            batched_chunks_text += f'<chunk id="{temp_id}">\n{chunk}\n</chunk>\n\n'

        formatted_extraction_prompt = EXTRACTION_TASK_PROMPT.format(
            preferred_node_types = preferred_node_types,
            preferred_edge_types = preferred_edge_types,
            existing_nodes = existing_nodes,
            batched_chunk_text =  batched_chunks_text
        )

        return formatted_extraction_prompt
    

    async def extract_graph(self, filepath)->KnowledgeGraphExtraction:
        pass


    async def ingest(self):
        pass
