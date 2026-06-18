import os

from app.knowledge_base.ingestion import Chunker, DocumentReader

if __name__=="__main__":
    print("Starting chunker and reader test...")
    test_chunker = Chunker(chunk_size=200)
    test_reader = DocumentReader()
    print("Chunker and Reader initialized successfully")

    os.makedirs("tests/result", exist_ok=True)
    
    with open("tests/results/chunker.txt", "w+") as file:
        for root, dirs, files in os.walk("tests/test_data"):
            for filename in files:
                file.write(f"-------------------------------{filename}-------------------------------\n")
                batch_count = 0
                filepath = os.path.join(root, filename)
                print(f"current_file: {filepath}")
                data_stream = test_reader.stream(filepath)
                chunk_stream = test_chunker.chunk(data_stream)
                for batch in test_chunker.batch(chunk_stream):
                    file.write("-------------------------------BATCH-------------------------------\n")
                    file.write("\n[CHUNK]".join(batch))
                    file.write("\n\n")
                    batch_count+=1
                    if batch_count == 3:
                         break

    
