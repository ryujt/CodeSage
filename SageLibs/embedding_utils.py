from .utilities import count_tokens
from .config import TOKEN_CONTEXT_WINDOW_EMBEDDINGS as WINDOW_SIZE

def chunk_content(content):
    lines = content.splitlines(keepends=True)
    chunks = []
    current = ""
    for line in lines:
        if count_tokens(current + line) > WINDOW_SIZE:
            chunks.append(current)
            current = line
        else:
            current += line
    if current:
        chunks.append(current)
    return chunks 