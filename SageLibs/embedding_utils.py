from .utilities import count_tokens
from .config import TOKEN_CONTEXT_WINDOW_EMBEDDINGS as WINDOW_SIZE, get_setting

def chunk_content(content, overlap_tokens=None):
    if overlap_tokens is None:
        overlap_tokens = get_setting('chunk_overlap_tokens', 200)

    lines = content.splitlines(keepends=True)
    chunks = []
    current = ""
    overlap_buffer = []

    for line in lines:
        if count_tokens(current + line) > WINDOW_SIZE:
            if current:
                chunks.append(current)

            if overlap_tokens > 0 and overlap_buffer:
                overlap_text = ""
                for buf_line in reversed(overlap_buffer):
                    test_overlap = buf_line + overlap_text
                    if count_tokens(test_overlap) <= overlap_tokens:
                        overlap_text = test_overlap
                    else:
                        break
                current = overlap_text + line
            else:
                current = line

            overlap_buffer = [line]
        else:
            current += line
            overlap_buffer.append(line)

            while len(overlap_buffer) > 50:
                overlap_buffer.pop(0)

    if current:
        chunks.append(current)

    return chunks
