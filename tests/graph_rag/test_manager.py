import asyncio

from app.knowledge_base.state import GraphState
from app.knowledge_base.graph_manager import GraphManager

async def run_manager_test():
    test_state = GraphState()
    test_state.manual_intialize(
        node_types={"Company": 0, "Job": 0, "Skill": 0, "Incentive": 0}, 
        edge_types={"REQUIRES": 0, "GIVES": 0, "PREFERES": 0}
    )
    test_manager = GraphManager(graph_state=test_state, chunk_size=100, batch_size=4)

    await test_manager.process_document("tests/test_data/data1.pdf")

if __name__=="__main__":
    asyncio.run(run_manager_test())