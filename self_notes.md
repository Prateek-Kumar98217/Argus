
## TODO:

1. Need to revise chunking strategy for text files(need accumulator logic instead of paragraph based), and finetune the chunk_size for optimal extraction and reduced hallucination.
2. Add "Document Context" so that the extractor can route pronouns to actual nodes, instead of creating new ones.
3. Deal with a bit of pydantic hallucinations in model output.(work out a decent harness and precautions)
4. Rework the retrival to use the assiciation table.(Important cannot test retrieval until then)
5. Add proper standardized logging.


## STATUS:

1. GraphRAG: On hold(due a bit of burnout)