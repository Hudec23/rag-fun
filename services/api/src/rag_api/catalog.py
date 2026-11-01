"""Fixed model catalog and file-type table (SYSTEM.md §9a, contracts/openapi/api.yaml uploadBatch)."""

# dense model -> (dims, max_tokens)
DENSE_MODELS: dict[str, tuple[int, int]] = {
    "bge-m3": (1024, 8192),
    "nomic-embed-text": (768, 8192),
    "mxbai-embed-large": (1024, 512),
    "all-minilm": (384, 256),
}
SPARSE_MODELS: list[str] = ["Qdrant/bm25", "prithivida/Splade_PP_en_v1"]
RERANK_MODELS: list[str] = ["Xenova/ms-marco-MiniLM-L-6-v2", "BAAI/bge-reranker-base"]

DEFAULT_COLLECTION = {"name": "default", "dense_model": "bge-m3", "sparse_model": "Qdrant/bm25"}
DEFAULT_SETTINGS: dict[str, object] = {
    "chat_provider": "ollama",
    "ollama": {"url": None, "chat_model": "qwen3:8b"},  # url filled from OLLAMA_URL_DEFAULT
    "anthropic": {"model": "claude-sonnet-5-5", "api_key": None},
    "openai_compatible": {"base_url": None, "model": None, "api_key": None},
    "reranker_model": "Xenova/ms-marco-MiniLM-L-6-v2",
}

MIME_BY_EXT: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".txt": "text/plain",
    ".html": "text/html",
    ".htm": "text/html",
    ".csv": "text/csv",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}

INGEST_STAGES: list[str] = ["parse", "chunk", "embed", "store"]
QUERY_STAGES: list[str] = ["transform", "retrieve", "rerank", "generate"]
# stage -> required upstream stage (must have an active version)
REQUIRED_UPSTREAM: dict[str, str | None] = {
    "parse": None,
    "chunk": "parse",
    "embed": "chunk",
    "store": "embed",
    "transform": None,
    "retrieve": None,
    "rerank": "retrieve",
    "generate": "retrieve",
}
# stage -> arq queue
QUEUE_OF: dict[str, str] = {s: "ingest" for s in INGEST_STAGES} | {s: "query" for s in QUERY_STAGES}
