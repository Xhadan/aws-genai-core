import re

def markdown_chunking(markdown_text, max_tokensP0):
    """Chunk markdown preserving header hierarchy."""
    # Split by headers while keeping header with content
    sections = re.split(r'(^#{1,6}\s+.+$)', markdown_text, flags=re.MULTILINE)

    chunks = []
    current_chunk = ""
    current_header = ""

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Check if this is a header
        if re.match(r'^#{1,6}\s+', section):
            current_header = section
        else:
            # This is content - combine with header
            full_section = f"{current_header}\n\n{section}" if current_header else section

            # Check token count (approximate: 1 token = 4 chars)
            estimated_tokens = len(full_section) // 4

            if estimated_tokens <= max_tokens:
                chunks.append({
                    'text': full_section,
                    'header': current_header,
                    'estimated_tokens': estimated_tokens
                })
            else:
                # Split large sections by paragraphs
                paragraphs = section.split('\n\n')
                for para in paragraphs:
                    para_text = f"{current_header}\n\n{para}" if current_header else para
                    chunks.append({
                        'text': para_text,
                        'header': current_header,
                        'estimated_tokens': len(para_text) // 4
                    })

    return chunks