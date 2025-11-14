from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import Field

from server.src.service.llm_client import LLMClient

if TYPE_CHECKING:
    from server.src.context.research_context import ResearchContext

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SummarizeContentTool:
    """Creates concise, accurate summaries of long-form content.
    Preserves key facts, conclusions, and context.
    Can tailor length and focus (e.g., 'executive summary', 'technical highlights').

    Use for: Articles, reports, meeting notes, research papers
    Returns: Short summary (1–5 sentences) or bullet points
    Best for: Quick review, information distillation, report generation

    Usage:
        - Provide full or partial content
        - Specify desired length or focus area
    """

    reasoning: str = Field(description="Why summarization is needed")
    content: str = Field(description="Content to summarize")
    length: str = Field(default="short", description="Summary length: 'short', 'medium', 'bullet_points'")
    focus: str | None = Field(default=None, description="Aspect to emphasize (e.g., 'conclusions', 'methods')")

    def __init__(self, **data):
        super().__init__(**data)
        self._llm = LLMClient()

    async def __call__(self, context: ResearchContext) -> str:
        length_guide = {
            "short": "1-2 sentences",
            "medium": "3-5 sentences",
            "bullet_points": "3-5 bullet points starting with '-'",
        }.get(self.length, "brief summary")

        focus_part = f" Focus on: {self.focus}." if self.focus else ""
        prompt = (
            f"Summarize the following content in a {length_guide}.{focus_part}\n\n"
            f"Content:\n{self.content}\n\n"
            f"Return only the summary, no introduction or markdown."
        )

        logger.info(f"📝 Summarizing content (length: {self.length})")
        summary = await self._llm.generate(prompt, max_tokens=300)

        context.artifacts.append({
            "type": "summary",
            "length": self.length,
            "focus": self.focus,
            "summary": summary.strip(),
            "timestamp": datetime.now(),
        })

        formatted = f"Summary ({self.length}{f', focus: {self.focus}' if self.focus else ''}):\n\n{summary.strip()}"
        logger.debug(formatted)
        return formatted