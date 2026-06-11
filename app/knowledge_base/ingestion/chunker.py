import re

from collections.abc import Iterator


class Chunker:
    def __init__(self, chunk_size):
        self.chunk_size = chunk_size

    
    def chunk(self, text_stream: Iterator[str]) -> Iterator[str]:
        for text in text_stream:
            yield from self._chunk_text(text)

    
    def batch(self, chunk_stream: Iterator[str], batch_size: int = 5)-> Iterator[list[str]]:
        batch: list[str] = []
        for chunk in chunk_stream:
            batch.append(chunk)
            if len(batch)==batch_size:
                yield batch
                batch = []
        if batch:
            yield batch


    def _split_sentences(self, paragraph: str)-> list[str]:
        pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s'
        return [s.strip() for s in re.split(pattern, paragraph) if s.strip()]
    

    def _chunk_text(self, text: str) -> Iterator[str]:
        paragraphs = re.split(r'\n\n+', text.strip())

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            yield from self._chunk_paragraph(paragraph)


    def _chunk_paragraph(self, paragraph: str)-> Iterator[str]:
        if len(paragraph.split()) <= self.chunk_size:
            yield paragraph
            return
        
        sentences = self._split_sentences(paragraph)
        current_chunk: list[str] = []
        current_word_count: int = 0

        for sentence in sentences:
            sentence_words = sentence.split()
            sentence_word_count = len(sentence_words)

            if sentence_word_count > self.chunk_size:
                if current_chunk:
                    yield " ".join(current_chunk)
                    current_chunk = []
                    current_word_count = 0
                yield sentence
                continue

            if current_word_count + sentence_word_count >self.chunk_size:
                if current_chunk:
                    yield " ".join(current_chunk)
                current_chunk = [sentence]
                current_word_count = sentence_word_count
                continue

            current_chunk.append(sentence)
            current_word_count += sentence_word_count
        
        if current_chunk:
            yield " ".join(current_chunk)
