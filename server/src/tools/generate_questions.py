from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import Field

from server.src.config.Config import CONFIG
from server.src.service.llm_client import LLMClient

if TYPE_CHECKING:
    from server.src.context.research_context import ResearchContext

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GenerateWorkQuestionsTool:
    """Generates thoughtful, context-aware questions about a given work (e.g., article, paper, report).
    Useful for deepening understanding, preparing discussions, or guiding further research.
    Questions cover factual, analytical, and critical thinking aspects.

    Use for: Academic papers, technical reports, news articles, documentation
    Returns: List of 3–5 well-formulated questions
    Best for: Active learning, peer review prep, knowledge validation

    Usage:
        - Provide clear work title and summary/content
        - Specify desired question type if needed (e.g., 'critical', 'factual')
    """

    reasoning: str = Field(description="Why generating questions is needed")
    work_title: str = Field(description="Title or name of the work")
    work_summary: str = Field(description="Brief summary or key points of the work")
    question_count: int = Field(default=5, ge=1, le=10, description="Number of questions to generate")

    def __init__(self, **data):
        super().__init__(**data)
        self._llm = LLMClient()

    async def __call__(self, context: ResearchContext) -> str:
        prompt = (
            f"Based on the following work titled '{self.work_title}' with summary:\n"
            f"\"{self.work_summary}\"\n\n"
            f"Generate exactly {self.question_count} insightful questions that help explore, "
            f"analyze, or critically evaluate this work. "
            f"Return only the questions, numbered, one per line."
        )

        logger.info(f"❓ Generating questions for work: '{self.work_title}'")
        response = await self._llm.generate(prompt, max_tokens=300)

        timestamp = datetime.now()
        context.artifacts.append({
            "type": "generated_questions",
            "work_title": self.work_title,
            "questions": response.strip(),
            "timestamp": timestamp,
        })

        formatted = f"Generated Questions for '{self.work_title}':\n\n{response.strip()}"
        logger.debug(formatted)
        return formatted