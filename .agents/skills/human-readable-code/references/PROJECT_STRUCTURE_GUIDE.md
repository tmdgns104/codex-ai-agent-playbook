# Project Structure Guide

## Goal

The project tree should mirror the major responsibilities of the system.

For example, a simple RAG application may use:

```text
src/
├── ingestion/
│   ├── document_loader.py
│   └── chunker.py
├── embedding/
│   └── embedding_service.py
├── retrieval/
│   └── retriever.py
└── generation/
    ├── context_builder.py
    └── answer_generator.py
```

A reader can infer:

`Document → Chunk → Embedding → Retrieval → Context → Answer`

before reading implementation details.

## Rules

- Group by responsibility/domain rather than arbitrary file size.
- Do not create a directory for one tiny file unless the boundary is meaningful.
- Avoid generic dumping grounds such as `utils.py` becoming unrelated code storage.
- Keep entry points obvious.
- Keep configuration discoverable.
- Keep tests structurally related to production modules when practical.
- Avoid circular responsibility boundaries.

## Abstraction Test

Before introducing an abstraction, ask:

1. Does a current requirement need it?
2. Does it make the caller simpler?
3. Does it reduce real duplication?
4. Does it clarify a boundary?
5. Can a new developer explain why it exists?

If most answers are no, keep the implementation simpler.
