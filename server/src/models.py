from pydantic import BaseModel, Field


class SourceData(BaseModel):
    """Data about a research source."""

    number: int = Field(description="Citation number")
    title: str | None = Field(default="Untitled", description="Page title")
    url: str = Field(description="Source URL")
    snippet: str = Field(default="", description="Search snippet or summary")
    full_content: str = Field(default="", description="Full scraped content")
    char_count: int = Field(default=0, description="Character count of full content")

    def __str__(self):
        return f"[{self.number}] {self.title or 'Untitled'} - {self.url}"

class ResearchContext(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    current_step_reasoning: Any = None
    execution_result: str | None = None

    state: AgentStatesEnum = Field(default=AgentStatesEnum.INITED, description="Current research state")
    iteration: int = Field(default=0, description="Current iteration number")

    searches: list[SearchResult] = Field(default_factory=list, description="List of performed searches")
    sources: dict[str, SourceData] = Field(default_factory=dict, description="Dictionary of found sources")

    searches_used: int = Field(default=0, description="Number of searches performed")

    clarifications_used: int = Field(default=0, description="Number of clarifications requested")
    clarification_received: asyncio.Event = Field(
        default_factory=asyncio.Event, description="Event for clarification synchronization"
    )

    def agent_state(self) -> dict:
        return self.model_dump(exclude={"searches", "sources", "clarification_received"})