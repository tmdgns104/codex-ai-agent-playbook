# Comments and Docstrings

## Comments Explain Why

Bad:

```python
# Loop through chunks
for chunk in chunks:
    ...
```

Better:

```python
# Preserve page metadata so the final answer can cite the original PDF page.
chunk.metadata["page"] = page_number
```

Good comment topics:
- rationale
- constraint
- workaround
- invariant
- safety condition
- unusual library behavior
- performance tradeoff
- why an apparently simpler option is incorrect

## Docstrings

Document public or non-obvious functions/classes.

Example:

```python
def load_markdown_document(path: Path) -> Document:
    # Responsibility: load one Markdown file and preserve traceable source metadata.
    ...
```

Avoid enormous docstrings that duplicate the implementation line by line.
