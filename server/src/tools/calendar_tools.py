from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from server.src.context.research_context import ResearchContext

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CalendarTool:
    """Provides calendar-related information and date calculations.
    Can return current date, compute deadlines, suggest timelines, or format dates.

    Use for: Scheduling, deadline tracking, time estimation, date formatting
    Returns: Human-readable date info or timeline suggestions
    Best for: Planning research phases, setting reminders, contextual time references

    Usage:
        - Request current date/time
        - Ask for date X days from now
        - Request timeline for multi-step tasks
    """

    reasoning: str = Field(description="Why calendar info is needed")
    action: str = Field(
        description="Action to perform: 'current_date', 'add_days', 'timeline_suggestion'"
    )
    days_offset: int = Field(default=0, ge=-365, le=365, description="Days to add/subtract from today")
    task_description: str | None = Field(default=None, description="Task for timeline suggestion")

    async def __call__(self, context: ResearchContext) -> str:
        now = datetime.now()
        logger.info(f"📅 Calendar action: {self.action}")

        if self.action == "current_date":
            result = f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        elif self.action == "add_days":
            target = now + timedelta(days=self.days_offset)
            result = (
                f"{abs(self.days_offset)} day{'s' if abs(self.days_offset) != 1 else ''} "
                f"{'from' if self.days_offset >= 0 else 'before'} today ({now.strftime('%Y-%m-%d')}) "
                f"is: {target.strftime('%Y-%m-%d')}"
            )
        elif self.action == "timeline_suggestion" and self.task_description:
            # Simple heuristic: 3 phases over 7–14 days
            start = now.strftime('%Y-%m-%d')
            mid = (now + timedelta(days=5)).strftime('%Y-%m-%d')
            end = (now + timedelta(days=12)).strftime('%Y-%m-%d')
            result = (
                f"Suggested timeline for: '{self.task_description}'\n"
                f"- Planning & Research: {start} – {mid}\n"
                f"- Execution & Drafting: {mid} – {end}\n"
                f"- Review & Finalize: by {end}"
            )
        else:
            result = "Invalid calendar action or missing parameters."

        context.artifacts.append({
            "type": "calendar_info",
            "action": self.action,
            "result": result,
            "timestamp": datetime.now(),
        })

        logger.debug(result)
        return result