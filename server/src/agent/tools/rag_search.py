from langchain.tools import tool
from service.QdrantService import QdrantService
from utils.logger import get_logger

logger = get_logger(__name__)

qdrant_service = QdrantService()


@tool
def search_in_documents(query: str) -> str:
    """
    Search for information in uploaded documents using RAG.
    Use this tool when the user asks to find information in their documents or PDFs.

    Args:
        query: The search query to find relevant information in documents

    Returns:
        Relevant text passages from the documents
    """
    try:
        logger.info(f"Searching documents with query: {query}")

        results = qdrant_service.search_similar(query)

        if not results:
            logger.info("No results found in documents")
            return "No relevant information found in the uploaded documents."

        context_parts = []
        for i, result in enumerate(results[:5], 1):
            context_parts.append(f"[Source {i}] {result['text']}")

        context = "\n\n".join(context_parts)
        logger.info(f"Found {len(results)} results, returning top 5")

        return context

    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        return f"Error searching documents: {str(e)}"