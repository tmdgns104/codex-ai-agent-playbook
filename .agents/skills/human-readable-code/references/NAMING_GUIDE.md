# Naming Guide

## Principle

A name should communicate role and meaning without requiring the reader to inspect
several unrelated files.

## Prefer

```python
document_text
chunk_overlap
retrieval_results
embedding_vector
source_page

load_markdown_document()
split_document_into_chunks()
retrieve_relevant_chunks()
build_llm_context()
```

## Avoid When Meaning Is Not Obvious

```python
a
b
x1
tmp
data2
res
proc
mgr
helper
util
do_stuff()
handle()
process()
```

Short names are fine for genuinely local mathematical/index conventions such as
`i`, `j`, `x`, `y` where the meaning is conventional and obvious.

## Boolean Names

```python
is_valid
has_source
should_retry
can_write
```

## Collections

Use plural names for collections:

```python
documents
chunks
retrieval_results
```

## Units

Include units when ambiguity would be dangerous:

```python
timeout_seconds
sample_rate_hz
distance_meters
```
