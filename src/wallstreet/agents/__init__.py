"""Risk assessment agents with factory for swappable implementations."""

from wallstreet.agents.base import RiskAgent, RiskAssessment
from wallstreet.agents.risk_committee import RulesBasedRiskCommittee


def create_risk_agent(agent_type: str = "rules") -> RiskAgent:
    """Factory to create a risk assessment agent.

    Args:
        agent_type: "rules" for deterministic rules-based agent.
                    "llm" reserved for future LLM-based agent.
    """
    if agent_type == "rules":
        return RulesBasedRiskCommittee()
    raise ValueError(f"Unknown agent type: {agent_type!r}")


__all__ = ["RiskAgent", "RiskAssessment", "RulesBasedRiskCommittee", "create_risk_agent"]
