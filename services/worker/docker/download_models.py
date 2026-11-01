"""Download every model file the worker needs at runtime into /opt/models (image build only).
Runtime is offline (HF_HUB_OFFLINE=1) except Ollama / API calls."""

import os
import subprocess
import sys

from fastembed import SparseTextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from huggingface_hub import hf_hub_download

MODELS = os.environ["MODELS_DIR"]

TOKENIZERS = [
    "BAAI/bge-m3",
    "nomic-ai/nomic-embed-text-v1.5",
    "mixedbread-ai/mxbai-embed-large-v1",
    "sentence-transformers/all-MiniLM-L6-v2",
]
SPARSE = ["Qdrant/bm25", "prithivida/Splade_PP_en_v1"]
RERANK = ["Xenova/ms-marco-MiniLM-L-6-v2", "BAAI/bge-reranker-base"]


def main() -> None:
    for repo in TOKENIZERS:
        hf_hub_download(repo, "tokenizer.json")
        print("tokenizer", repo, flush=True)
    cache = os.environ["FASTEMBED_CACHE_PATH"]
    for name in SPARSE:
        SparseTextEmbedding(name, cache_dir=cache)
        print("sparse", name, flush=True)
    for name in RERANK:
        TextCrossEncoder(name, cache_dir=cache)
        print("rerank", name, flush=True)
    import nltk

    nltk.download("punkt_tab", download_dir=os.environ["NLTK_DATA"], quiet=True)
    print("nltk punkt_tab", flush=True)
    subprocess.run(
        [
            "docling-tools",
            "models",
            "download",
            "-o",
            f"{MODELS}/docling",
            "layout",
            "tableformer",
            "easyocr",
        ],
        check=True,
    )
    print("docling models", flush=True)


if __name__ == "__main__":
    sys.exit(main())
