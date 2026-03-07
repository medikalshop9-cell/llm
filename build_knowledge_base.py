"""
rag/build_knowledge_base.py
AfriLearn — Build ChromaDB vector knowledge base from curriculum PDFs.

Indexes all curriculum documents from data/curriculum/nigeria/ and data/curriculum/ghana/
into a local ChromaDB instance. No internet required after build.

The RAG chain in api/main.py queries this knowledge base at inference time to
provide the model with curriculum-grounded context before generating a response.

Usage:
  python rag/build_knowledge_base.py \
    --curriculum-dir data/curriculum/ \
    --output afrilearn_knowledge_base/

Dependencies:
  langchain, langchain-community, chromadb, pypdf, sentence-transformers
"""

import argparse
from pathlib import Path
import sys

from loguru import logger

try:
    from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
except ImportError:
    logger.error("LangChain not installed. Run: pip install -r requirements.txt")
    sys.exit(1)


EMBEDDING_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"  # 80MB — runs fully offline
CHUNK_SIZE        = 500
CHUNK_OVERLAP     = 50
SUPPORTED_SOURCES = ["nigeria", "ghana"]


def load_curriculum_documents(curriculum_dir: Path) -> list:
    """Load all PDFs from nigeria/ and ghana/ subdirectories."""
    all_docs = []

    for country in SUPPORTED_SOURCES:
        country_dir = curriculum_dir / country
        if not country_dir.exists():
            logger.warning(f"No curriculum directory found for {country}: {country_dir}")
            continue

        pdf_files = list(country_dir.glob("**/*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {country_dir}. Add curriculum PDFs and rebuild.")
            continue

        logger.info(f"Loading {len(pdf_files)} PDF(s) from {country_dir}...")

        for pdf_path in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_path))
                docs   = loader.load()
                # Tag each document chunk with its country source
                for doc in docs:
                    doc.metadata["country"]  = country
                    doc.metadata["filename"] = pdf_path.name
                all_docs.extend(docs)
                logger.info(f"  Loaded: {pdf_path.name} ({len(docs)} pages)")
            except Exception as e:
                logger.error(f"  Failed to load {pdf_path.name}: {e}")

    return all_docs


def build_knowledge_base(curriculum_dir: Path, output_dir: str):
    logger.info("Loading curriculum documents...")
    documents = load_curriculum_documents(curriculum_dir)

    if not documents:
        logger.error(
            "No documents loaded. Ensure PDF files are present in:\n"
            "  data/curriculum/nigeria/\n"
            "  data/curriculum/ghana/\n"
            "Download Ghana NaCCA PDFs from: https://nacca.gov.gh/learning-areas-subjects/new-standards-based-curriculum-2019/"
        )
        sys.exit(1)

    logger.info(f"Loaded {len(documents)} pages total. Splitting into chunks...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"Split into {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    logger.info("First run downloads ~80MB. Subsequent runs use local cache.")
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},      # CPU inference — sufficient for retrieval
        encode_kwargs={"normalize_embeddings": True},
    )

    logger.info(f"Building ChromaDB vector store at {output_dir}...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=output_dir,
    )
    vectorstore.persist()

    logger.success(
        f"Knowledge base built successfully.\n"
        f"  Total chunks indexed: {len(chunks)}\n"
        f"  Output directory:     {output_dir}\n"
        f"\nNext step: python api/main.py  (or uvicorn api.main:app --host 0.0.0.0 --port 8000)"
    )


def main():
    parser = argparse.ArgumentParser(description="AfriLearn RAG knowledge base builder")
    parser.add_argument("--curriculum-dir", default="data/curriculum/", type=Path)
    parser.add_argument("--output",         default="afrilearn_knowledge_base",  type=str)
    args = parser.parse_args()

    build_knowledge_base(args.curriculum_dir, args.output)


if __name__ == "__main__":
    main()
