import fitz

from collections.abc import Iterator

from app.core.exceptions import FileNotSupportedError


#Number of lines to be buffered before flushing a text/markdown block.
_TEXT_PAGE_LINE_THRESHOLD = 40


class DocumentReader:
    def stream(self, filepath: str) -> Iterator[str]:
        if filepath.endswith(".pdf"):
            yield from self._stream_pdf(filepath)
        elif filepath.endswith((".txt", ".md")):
            yield from self._stream_text(filepath)
        else:
            raise FileNotSupportedError(f"Unsupported file format for ingestion: {filepath}")
        

    def _stream_pdf(self, filepath: str)->Iterator[str]:
        with fitz.open(filepath) as doc:
            for page in doc:
                text = page.get_text()
                if text.strip():
                    yield text
       
        
    def _stream_text(self, filepath: str) -> Iterator[str]:
        with open(filepath, 'r', encoding='utf-8') as fh:
            buffer: list[str] = []
            for line in fh:
                buffer.append(line)
                if line.strip=="" and len(buffer)>=_TEXT_PAGE_LINE_THRESHOLD:
                    yield "".join(buffer)
                    buffer = []
            if buffer:
                yield "".join(buffer)