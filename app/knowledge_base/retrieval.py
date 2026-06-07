#Responsible for everything from retrieval of information, to before the context injection.

from google import genai
from google.genai import types

from app.knowledge_base.state import GraphState
from app.knowledge_base.db.queries import SEED_NODE_QUERY, RECURSIVE_TRAVERSAL_QUERY
from app.knowledge_base.db.engine import AsyncSessionLocal
from app.core.settings import settings
from app.core.exceptions import NoContextError

class Retriever:
    def __init__(self, graph_state: GraphState, embed_dim: int = 768, limit: int = 3, max_depth: int = 2):
        self.state = graph_state
        self.embedding_model = settings.EMBED_MODEL
        self.client = genai.Client()
        self.embed_dim = embed_dim
        self.is_initialized = False
        #limit defines the max intial chunks got from vector search
        self.limit = limit
        #max_depth defines the max "hops" in the graph traversal
        self.max_depth = max_depth

    async def retrieve(self, query):
        """
            Returns the graph rag context, also returns the query_vector for caching.
        """
        embedding = await self.client.aio.models.embed_content(
            model= self.embedding_model,
            contents=query,
            config=types.EmbedContentConfig(output_dimensionality=self.embed_dim)
        )
        
        query_vector = embedding.embeddings[0].values
        
        async with AsyncSessionLocal() as session:
            seed_nodes = await session.execute(SEED_NODE_QUERY, {"query_vector": str(query_vector), "limit_chunks": self.limit})

            seed_node_ids = [row[0] for row in seed_nodes.fetchall()]

            if not seed_node_ids:
                raise NoContextError("No starting nodes found for the query")
            
            str_seed_ids = [str(seed_node) for seed_node in seed_node_ids]
            
            context_chunks= await session.execute(RECURSIVE_TRAVERSAL_QUERY, {"seed_node_ids": str_seed_ids, "max_depth": self.max_depth})

            chunks = [row[0] for row in context_chunks.fetchall()]

            context = "\n\n".join(chunks)

            return query_vector, context