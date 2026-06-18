import os
import json
import asyncio
import dataclasses

from app.knowledge_base.state import GraphState
from app.knowledge_base.ingestion import Chunker, DocumentReader, ExtractionService

async def run_extraction_test():
    print("Initializing required componenets...")
    test_reader = DocumentReader()
    test_state = GraphState()
    # Yeah I am definately using job descriptions for testing
    test_state.manual_intialize(
        node_types={"Company": 0, "Job": 0, "Skill": 0, "Incentive": 0}, 
        edge_types={"REQUIRES": 0, "GIVES": 0, "PREFERES": 0}
    )
    test_chunker = Chunker(chunk_size=100)
    test_extraction = ExtractionService(graph_state=test_state)

    data_stream = test_reader.stream("tests/test_data/data1.pdf")
    chunk_stream = test_chunker.chunk(text_stream = data_stream)

    batches = list(batch for batch in test_chunker.batch(chunk_stream))

    os.makedirs("tests/results", exist_ok=True)

    print("Starting Extraction process...")

    with open("tests/results/extraction.txt", "w+") as file:
        async for result in test_extraction.process_batches(batches):
            content = f" result: {result.model_dump_json(exclude={"embeddings"}, indent=2)}"
            file.write(f"[BATCH]\n\n{content}\n")
            print("Batch written to file")

if __name__=="__main__":
    asyncio.run(run_extraction_test())