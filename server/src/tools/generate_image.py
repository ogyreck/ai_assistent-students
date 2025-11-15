from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import Field

from service.llm_client import LLMClient

if TYPE_CHECKING:
    from context.research_context import ResearchContext

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GenerateSchemaTool:
    """Generates a structured schema or diagram description from unstructured content.
    Outputs in Mermaid, JSON Schema, or plain hierarchical format.
    Useful for visualizing systems, data models, or workflows.

    Use for: System design, data modeling, process mapping, knowledge structuring
    Returns: Schema in specified format (default: Mermaid flowchart)
    Best for: Documentation, onboarding, technical planning

    Usage:
        - Provide clear topic and desired output format
        - Mention key entities, relationships, or steps
    """

    reasoning: str = Field(description="Why a schema is needed")
    topic: str = Field(description="Topic to model (e.g., 'User Authentication Flow')")
    format: str = Field(default="mermaid", description="Output format: 'mermaid', 'json', 'hierarchy'")
    content_hint: str = Field(description="Key elements or description to base schema on")

    def __init__(self, **data):
        super().__init__(**data)
        self._llm = LLMClient()

    async def __call__(self, context: ResearchContext) -> str:
        format_instruction = {
            "mermaid": "Generate a Mermaid.js flowchart (graph TD) with clear nodes and arrows.",
            "json": "Output a valid JSON Schema object describing the structure.",
            "hierarchy": "Use indented bullet points to show parent-child relationships.",
        }.get(self.format, "Use a clear structured format.")

        prompt = (
            f"Create a {self.format} schema for: '{self.topic}'\n"
            f"Based on: {self.content_hint}\n\n"
            f"{format_instruction}\n"
            f"Return only the schema, no explanations."
        )

        logger.info(f"📐 Generating schema for: '{self.topic}' in {self.format} format")
        schema_output = await self._llm.generate(prompt)

        context.artifacts.append({
            "type": "generated_schema",
            "topic": self.topic,
            "format": self.format,
            "schema": schema_output.strip(),
            "timestamp": datetime.now(),
        })

        formatted = f"Schema for '{self.topic}' ({self.format.upper()}):\n\n```{self.format}\n{schema_output.strip()}\n```"
        logger.debug(formatted)
        return formatted