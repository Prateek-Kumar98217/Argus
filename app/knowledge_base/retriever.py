#Responsible for everything from retrieval of information, to before the context injection.

from google import genai
from google.genai import types

from app.core.settings import settings
from app.core.exceptions import NoContextError
from app.knowledge_base.state import GraphState
from app.knowledge_base.db.engine import AsyncSessionLocal
from app.knowledge_base.db.queries import SEED_NODE_QUERY, RECURSIVE_TRAVERSAL_QUERY

class Retriever:
    def __init__(self, graph_state: GraphState, embed_dim: int = 768, limit: int = 3, max_depth: int = 2):
        self.state = graph_state
        self.embedding_model = settings.EMBED_MODEL
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.embed_dim = embed_dim
        self.is_initialized = False
        #defines the max seed chunks got from vector search
        self.limit = limit
        #defines the max hops from each seed node during traversal
        self.max_depth = max_depth


    async def retrieve(self, query: str) -> tuple[list[float], str]:
        """
            Returns the graph rag context, also returns the query_vector for caching.
        """
        query_vector = await self._emebed_query(query)
        context = await self._fetch_context(query_vector)
        return query_vector, context


    async def _emebed_query(self, query: str) -> list[float]:
        response = await self.client.aio.models.embed_content(
            model= self.embedding_model,
            contents=query,
            config=types.EmbedContentConfig(output_dimensionality=self.embed_dim)
        )

        return response.embeddings[0].values
    
    async def _fetch_context(self, query_vector: list[float])->str:
        async with AsyncSessionLocal() as session:
            seed_result = session.execute(
                SEED_NODE_QUERY,
                {"query_vector": str(query_vector), "limit": self.limit}
            )
            seed_node_ids = [row[0] for row in seed_result.fetchall()]

            if not seed_node_ids:
                raise NoContextError("No starting node found for the query.")
            
            traversal_result = session.execute(
                RECURSIVE_TRAVERSAL_QUERY,
                {"seed_node_ids": [str(nid) for nid in seed_node_ids], "max_depth": self.max_depth}
            )

            chunks = [row[0] for row in traversal_result]

            return "\n\n".join(chunks)