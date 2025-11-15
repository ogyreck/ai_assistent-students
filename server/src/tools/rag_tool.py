from __future__ import annotations

import logging
from typing import TYPE_CHECKING
import httpx

from pydantic import Field

if TYPE_CHECKING:
    from context.research_context import ResearchContext

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

RAG_BASE_URL = "http://147.45.224.7:6500"


class RAGSearchTool:
    """Search for information in the RAG knowledge base.
    Use this tool when you need to find specific information that was previously uploaded to the knowledge base.

    Use for: Finding stored documents, retrieving specific information from knowledge base
    Returns: Answer from RAG system based on stored documents
    Best for: Questions about previously uploaded content, specific facts from knowledge base

    Usage:
        - Ask specific questions about stored information
        - Query should be clear and focused
        - Tool will return relevant answer from knowledge base
    """

    reasoning: str = Field(description="Why RAG search is needed")
    question: str = Field(description="Question to ask the RAG system")

    async def __call__(self, context: ResearchContext) -> str:
        logger.info(f"🔍 RAG search: '{self.question}'")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{RAG_BASE_URL}/api/get_answer",
                    params={"user_question": self.question}
                )
                response.raise_for_status()
                data = response.json()
                answer = data.get("answer", "No answer found")

                logger.info(f"✓ RAG answer received: {answer[:100]}...")
                return f"RAG Answer: {answer}"

        except Exception as e:
            error_msg = f"RAG search failed: {str(e)}"
            logger.error(error_msg)
            return error_msg


class RAGUploadTool:
    """Upload text to the RAG knowledge base.
    Use this tool when you need to store new information in the knowledge base for future retrieval.

    Use for: Storing documents, saving important information for later use
    Returns: Confirmation of successful upload
    Best for: Adding new content to knowledge base

    Usage:
        - Provide text content to store
        - Add descriptive title for the content
        - Content will be available for future RAG searches
    """

    reasoning: str = Field(description="Why this text needs to be uploaded")
    text: str = Field(description="Text content to upload to RAG")
    title: str = Field(description="Title or description of the content")

    async def __call__(self, context: ResearchContext) -> str:
        logger.info(f"📤 Uploading to RAG: '{self.title}'")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{RAG_BASE_URL}/api/upload_text",
                    json={"text": self.text, "title": self.title}
                )
                response.raise_for_status()

                logger.info(f"✓ Text uploaded successfully: {self.title}")
                return f"Successfully uploaded '{self.title}' to RAG knowledge base. This information is now available for future searches."

        except Exception as e:
            error_msg = f"RAG upload failed: {str(e)}"
            logger.error(error_msg)
            return error_msg