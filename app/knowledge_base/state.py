# Responsible to maintain in memory state of graph.

from app.core.exceptions import NotInitializedError, NodeConflictError
from app.knowledge_base.db.engine import AsyncSessionLocal
from app.knowledge_base.db.queries import EDGE_TYPES, NODE_TYPES, NODES

class GraphState:
    def __init__(self)-> None:
        self.nodes: set[str] = set() #nodes need to be unique
        #For node and edge types, keeping a counter, for frequency based truncation
        self.node_types: dict[str, int] = {}
        self.edge_types: dict[str, int] = {}
        self.is_initialized: bool = False


    async def initialize(self):
        """
            Initialize the grapg state from the database.
        """
        if self.is_initialized:
            return
        
        async with AsyncSessionLocal() as session:
            node_result = await session.execute(NODES)
            for (node_name,) in node_result.fetchall():
                self.nodes.add(node_name)

            node_type_results = await session.execute(NODE_TYPES)
            for node_type, type_count in node_type_results.fetchall():
                self.node_types[node_type] = type_count

            edge_type_result = await session.execute(EDGE_TYPES)
            for edge_type, edge_count in edge_type_result.fetchall():
                self.edge_types[edge_type] = edge_count

        self.is_initialized = True

    
    def manual_intialize(self, node_types: dict[str, int], edge_types: dict[str, int]):
        """
            Initialize the type manually, to limit the types when no data exits.
        """
        if self.is_initialized:
            return
        
        self.node_types = node_types
        self.edge_types = edge_types

        self.is_initialized = True
    

    def update_nodes(self, node_name):
        self._assert_initialized()
        
        if node_name in self.nodes:
            raise NodeConflictError(f"Node Conflict: {node_name} already exists.")
        self.nodes.add(node_name)


    def update_node_types(self, node_type):
        self._assert_initialized()
        self.node_types[node_type] = self.node_types.get(node_type, 0) + 1


    def update_edge_types(self, edge_type):
        self._assert_initialized()
        self.edge_types[edge_type] = self.edge_types.get(edge_type, 0) + 1


    def _assert_initialized(self):
        if not self.is_initialized:
            raise NotInitializedError("Graph state must be intialized.")