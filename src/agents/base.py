"""
Base Agent Interface for TokenTon26 Multi-Agent Consensus

Each agent analyzes transactions and provides recommendations.
Responses are weighted by phi-coherence credibility scores.
"""

import os
import httpx
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum


class AgentRole(Enum):
    SECURITY = "security"      # Analyze security risks
    COMPLIANCE = "compliance"  # Check regulatory compliance
    ECONOMICS = "economics"    # Evaluate economic impact
    GENERAL = "general"        # General analysis


class AgentDecision(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass
class AgentResponse:
    """Response from an AI agent."""
    agent_id: str
    role: AgentRole
    decision: AgentDecision
    reasoning: str
    confidence: float  # 0-1
    risk_factors: List[str]
    phi_coherence: float = 0.0  # Filled by consensus engine

    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'role': self.role.value,
            'decision': self.decision.value,
            'reasoning': self.reasoning,
            'confidence': self.confidence,
            'risk_factors': self.risk_factors,
            'phi_coherence': self.phi_coherence,
        }


class Agent(ABC):
    """Abstract base class for AI agents."""

    def __init__(self, agent_id: str, role: AgentRole):
        self.agent_id = agent_id
        self.role = role

    @abstractmethod
    async def analyze(self, transaction: Dict[str, Any]) -> AgentResponse:
        """Analyze a transaction and return a recommendation."""
        pass

    def _build_prompt(self, transaction: Dict[str, Any]) -> str:
        """Build analysis prompt based on role."""
        base = f"""Analyze this Solana transaction and provide a recommendation.

Transaction Details:
- Type: {transaction.get('type', 'unknown')}
- Amount: {transaction.get('amount', 0)} SOL
- Recipient: {transaction.get('recipient', 'unknown')}
- Memo: {transaction.get('memo', '')}

Your role: {self.role.value.upper()} ANALYST

"""
        if self.role == AgentRole.SECURITY:
            base += """Focus on:
- Smart contract risks
- Phishing indicators
- Known scam addresses
- Unusual patterns"""
        elif self.role == AgentRole.COMPLIANCE:
            base += """Focus on:
- Regulatory compliance
- AML/KYC considerations
- Jurisdiction issues
- Reporting requirements"""
        elif self.role == AgentRole.ECONOMICS:
            base += """Focus on:
- Market conditions
- Gas optimization
- Slippage risks
- Economic rationality"""
        else:
            base += """Provide general analysis of risks and benefits."""

        base += """

Respond in this exact format:
DECISION: [APPROVE/REJECT/ABSTAIN]
CONFIDENCE: [0.0-1.0]
REASONING: [Your detailed analysis]
RISK_FACTORS: [comma-separated list of risks, or "none"]
"""
        return base


class OpenAIAgent(Agent):
    """Agent powered by OpenAI."""

    def __init__(self, agent_id: str, role: AgentRole, model: str = "gpt-4o-mini"):
        super().__init__(agent_id, role)
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")

    async def analyze(self, transaction: Dict[str, Any]) -> AgentResponse:
        if not self.api_key:
            return AgentResponse(
                agent_id=self.agent_id,
                role=self.role,
                decision=AgentDecision.ABSTAIN,
                reasoning="OpenAI API key not configured",
                confidence=0.0,
                risk_factors=["api_error"],
            )

        prompt = self._build_prompt(transaction)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                return AgentResponse(
                    agent_id=self.agent_id,
                    role=self.role,
                    decision=AgentDecision.ABSTAIN,
                    reasoning=f"API error: {response.status_code}",
                    confidence=0.0,
                    risk_factors=["api_error"],
                )

            content = response.json()["choices"][0]["message"]["content"]
            return self._parse_response(content)

    def _parse_response(self, content: str) -> AgentResponse:
        """Parse LLM response into structured AgentResponse."""
        lines = content.strip().split('\n')

        decision = AgentDecision.ABSTAIN
        confidence = 0.5
        reasoning = ""
        risk_factors = []

        for line in lines:
            line = line.strip()
            if line.startswith("DECISION:"):
                d = line.replace("DECISION:", "").strip().upper()
                if "APPROVE" in d:
                    decision = AgentDecision.APPROVE
                elif "REJECT" in d:
                    decision = AgentDecision.REJECT
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.replace("CONFIDENCE:", "").strip())
                except:
                    pass
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
            elif line.startswith("RISK_FACTORS:"):
                rf = line.replace("RISK_FACTORS:", "").strip()
                if rf.lower() != "none":
                    risk_factors = [r.strip() for r in rf.split(",")]

        return AgentResponse(
            agent_id=self.agent_id,
            role=self.role,
            decision=decision,
            reasoning=reasoning,
            confidence=confidence,
            risk_factors=risk_factors,
        )


class AnthropicAgent(Agent):
    """Agent powered by Anthropic Claude."""

    def __init__(self, agent_id: str, role: AgentRole, model: str = "claude-3-haiku-20240307"):
        super().__init__(agent_id, role)
        self.model = model
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

    async def analyze(self, transaction: Dict[str, Any]) -> AgentResponse:
        if not self.api_key:
            return AgentResponse(
                agent_id=self.agent_id,
                role=self.role,
                decision=AgentDecision.ABSTAIN,
                reasoning="Anthropic API key not configured",
                confidence=0.0,
                risk_factors=["api_error"],
            )

        prompt = self._build_prompt(transaction)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                return AgentResponse(
                    agent_id=self.agent_id,
                    role=self.role,
                    decision=AgentDecision.ABSTAIN,
                    reasoning=f"API error: {response.status_code}",
                    confidence=0.0,
                    risk_factors=["api_error"],
                )

            content = response.json()["content"][0]["text"]
            return self._parse_response(content)

    def _parse_response(self, content: str) -> AgentResponse:
        """Parse LLM response into structured AgentResponse."""
        lines = content.strip().split('\n')

        decision = AgentDecision.ABSTAIN
        confidence = 0.5
        reasoning = ""
        risk_factors = []

        for line in lines:
            line = line.strip()
            if line.startswith("DECISION:"):
                d = line.replace("DECISION:", "").strip().upper()
                if "APPROVE" in d:
                    decision = AgentDecision.APPROVE
                elif "REJECT" in d:
                    decision = AgentDecision.REJECT
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.replace("CONFIDENCE:", "").strip())
                except:
                    pass
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
            elif line.startswith("RISK_FACTORS:"):
                rf = line.replace("RISK_FACTORS:", "").strip()
                if rf.lower() != "none":
                    risk_factors = [r.strip() for r in rf.split(",")]

        return AgentResponse(
            agent_id=self.agent_id,
            role=self.role,
            decision=decision,
            reasoning=reasoning,
            confidence=confidence,
            risk_factors=risk_factors,
        )


class MockAgent(Agent):
    """Mock agent for testing (no API calls)."""

    def __init__(self, agent_id: str, role: AgentRole, default_decision: AgentDecision = AgentDecision.APPROVE):
        super().__init__(agent_id, role)
        self.default_decision = default_decision

    async def analyze(self, transaction: Dict[str, Any]) -> AgentResponse:
        amount = transaction.get('amount', 0)

        # Simple risk heuristics for demo
        if amount > 100:
            decision = AgentDecision.REJECT
            reasoning = f"Large transaction ({amount} SOL) requires manual review"
            risk_factors = ["high_value"]
            confidence = 0.8
        elif amount > 10:
            decision = AgentDecision.APPROVE
            reasoning = f"Medium transaction ({amount} SOL) within acceptable limits"
            risk_factors = ["moderate_value"]
            confidence = 0.7
        else:
            decision = self.default_decision
            reasoning = f"Small transaction ({amount} SOL) is low risk"
            risk_factors = []
            confidence = 0.9

        return AgentResponse(
            agent_id=self.agent_id,
            role=self.role,
            decision=decision,
            reasoning=reasoning,
            confidence=confidence,
            risk_factors=risk_factors,
        )
