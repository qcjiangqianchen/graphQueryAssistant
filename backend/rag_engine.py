"""
RAG (Retrieval Augmented Generation) Engine
Handles document processing, embeddings, and context retrieval
"""
import os
import uuid
import logging
from typing import List, Dict, Optional
import numpy as np

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from config import settings

# Set environment variable for OpenAI API key
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

logger = logging.getLogger(__name__)


class RAGEngine:
    """Manages document indexing and retrieval for RAG"""

    def __init__(self):
        """Initialize the RAG engine with embeddings and vector store"""
        logger.info("Initializing RAG Engine...")

        # Initialize text splitter (doesn't require API calls)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
        )

        # Lazy initialization of embeddings and vector store
        self.embeddings = None
        self.vector_store = None
        logger.info("RAG Engine initialized successfully (embeddings will be loaded on first use)")

    def _ensure_initialized(self):
        """Ensure embeddings and vector store are initialized (lazy loading)"""
        if self.embeddings is None:
            logger.info("Initializing OpenAI embeddings...")
            self.embeddings = OpenAIEmbeddings(
                model=settings.embedding_model
            )
        
        if self.vector_store is None:
            logger.info("Initializing vector store...")
            self.vector_store = self._initialize_vector_store()

    def _initialize_vector_store(self):
        """Initialize or load existing vector store"""
        persist_path = settings.persist_directory

        try:
            # Try to load existing vector store
            if os.path.exists(persist_path) and os.path.exists(
                os.path.join(persist_path, "index.faiss")
            ):
                logger.info(f"Loading existing vector store from {persist_path}")
                return FAISS.load_local(
                    persist_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                logger.info("Creating new vector store")
                # Create empty vector store with a dummy document
                dummy_doc = Document(
                    page_content="Initial setup document",
                    metadata={"type": "system"}
                )
                return FAISS.from_documents([dummy_doc], self.embeddings)

        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            # Create new vector store on error
            dummy_doc = Document(
                page_content="Initial setup document",
                metadata={"type": "system"}
            )
            return FAISS.from_documents([dummy_doc], self.embeddings)

    def add_document(self, content: str, metadata: Optional[Dict] = None) -> str:
        """
        Add a document to the RAG index

        Args:
            content: Document content as string
            metadata: Optional metadata dictionary

        Returns:
            Document ID
        """
        self._ensure_initialized()
        try:
            doc_id = str(uuid.uuid4())

            # Add document ID to metadata
            if metadata is None:
                metadata = {}
            metadata["doc_id"] = doc_id

            # Split document into chunks
            chunks = self.text_splitter.split_text(content)
            logger.info(f"Split document into {len(chunks)} chunks")

            # Create Document objects
            documents = [
                Document(
                    page_content=chunk,
                    metadata={**metadata, "chunk_index": i}
                )
                for i, chunk in enumerate(chunks)
            ]

            # Add to vector store
            self.vector_store.add_documents(documents)

            # Persist vector store
            self._persist_vector_store()

            logger.info(f"Document {doc_id} added successfully")
            return doc_id

        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            raise

    def retrieve_context(
        self, query: str, top_k: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Retrieve relevant context for a query

        Args:
            query: User query string
            top_k: Number of results to retrieve (uses settings default if None)

        Returns:
            Dictionary containing context string and source documents
        """
        self._ensure_initialized()
        try:
            if top_k is None:
                top_k = settings.top_k_results

            logger.info(f"Retrieving top {top_k} results for query: {query[:50]}...")

            # Perform similarity search
            results = self.vector_store.similarity_search_with_score(query, k=top_k)

            # Filter out the dummy document
            results = [
                (doc, score) for doc, score in results
                if doc.metadata.get("type") != "system"
            ]

            if not results:
                logger.info("No relevant documents found")
                return {"context": "", "sources": []}

            # Format context
            context_parts = []
            sources = []

            for i, (doc, score) in enumerate(results):
                context_parts.append(f"[Source {i+1}]\n{doc.page_content}\n")
                sources.append({
                    "source_id": i + 1,
                    "content": doc.page_content[:200] + "...",  # Preview
                    "score": float(score),
                    "metadata": doc.metadata
                })

            context = "\n".join(context_parts)

            logger.info(f"Retrieved {len(results)} relevant documents")

            return {
                "context": context,
                "sources": sources
            }

        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return {"context": "", "sources": []}

    def get_document_count(self) -> int:
        """Get the number of documents in the vector store"""
        self._ensure_initialized()
        try:
            # Get all documents excluding system documents
            return self.vector_store.index.ntotal - 1  # Subtract dummy document
        except Exception as e:
            logger.error(f"Error getting document count: {str(e)}")
            return 0

    def clear_documents(self):
        """Clear all documents from the vector store"""
        self._ensure_initialized()
        try:
            logger.info("Clearing all documents from vector store")

            # Recreate vector store
            dummy_doc = Document(
                page_content="Initial setup document",
                metadata={"type": "system"}
            )
            self.vector_store = FAISS.from_documents([dummy_doc], self.embeddings)

            # Persist the cleared vector store
            self._persist_vector_store()

            logger.info("All documents cleared successfully")

        except Exception as e:
            logger.error(f"Error clearing documents: {str(e)}")
            raise

    def _persist_vector_store(self):
        """Persist the vector store to disk"""
        try:
            persist_path = settings.persist_directory

            # Create directory if it doesn't exist
            os.makedirs(persist_path, exist_ok=True)

            # Save vector store
            self.vector_store.save_local(persist_path)
            logger.info(f"Vector store persisted to {persist_path}")

        except Exception as e:
            logger.error(f"Error persisting vector store: {str(e)}")
            # Don't raise exception, just log the error
