from dataclasses import dataclass, field


@dataclass(slots=True)
class AgentConfig:
    """
    Common configuration for a SmolAgents agent.
    """

    max_steps: int = 3
    planning_interval: int | None = None
    authorized_imports: list[str] = field(default_factory=list)
    stream_outputs: bool = False
    use_structured_outputs_internally: bool = False
    max_print_outputs_length: int | None = None


def get_research_agent_config() -> AgentConfig:
    """
    Configuration used by the Research Agent.
    """
    return AgentConfig(
        max_steps=3,
        planning_interval=None,
        authorized_imports=[],
        stream_outputs=False,
        use_structured_outputs_internally=False,
        max_print_outputs_length=None,
    )