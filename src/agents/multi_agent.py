"""
Multi-Agent Consensus Engine for TokenTon26

Multiple AI agents analyze transactions:
1. Each agent provides decision + reasoning
2. Reasoning scored by phi-coherence for credibility
3. Votes weighted by coherence scores
4. Decision attested via Proof-of-Boundary (POB)
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .base import Agent, AgentResponse, AgentDecision, AgentRole
from ..consensus.phi_coherence import score as phi_score
from ..consensus.pob import calculate_pob, verify_proof, BoundaryProof


@dataclass
class ConsensusResult:
    """Result of multi-agent consensus."""
    final_decision: AgentDecision
    approve_weight: float
    reject_weight: float
    abstain_weight: float
    threshold_met: bool
    agent_responses: List[AgentResponse]
    proof: Optional[BoundaryProof]
    consensus_data: str  # JSON of all agent responses

    def to_dict(self) -> Dict[str, Any]:
        return {
            'final_decision': self.final_decision.value,
            'approve_weight': round(self.approve_weight, 4),
            'reject_weight': round(self.reject_weight, 4),
            'abstain_weight': round(self.abstain_weight, 4),
            'threshold_met': self.threshold_met,
            'agent_count': len(self.agent_responses),
            'proof_valid': self.proof.valid if self.proof else False,
            'proof_ratio': round(self.proof.ratio, 6) if self.proof else None,
        }


class MultiAgentConsensus:
    """
    Multi-agent consensus engine with phi-coherence weighting.

    Flow:
    1. All agents analyze transaction in parallel
    2. Each response scored by phi-coherence (credibility)
    3. Votes weighted by coherence * confidence
    4. Decision determined by threshold
    5. Decision attested via POB
    """

    def __init__(
        self,
        agents: List[Agent],
        approval_threshold: float = 0.6,
        min_coherence: float = 0.40,
    ):
        self.agents = agents
        self.approval_threshold = approval_threshold
        self.min_coherence = min_coherence

    async def analyze(self, transaction: Dict[str, Any]) -> ConsensusResult:
        """
        Run multi-agent consensus on a transaction.
        """
        # 1. Get all agent responses in parallel
        tasks = [agent.analyze(transaction) for agent in self.agents]
        responses = await asyncio.gather(*tasks)

        # 2. Score each response by phi-coherence
        for response in responses:
            coherence = phi_score(response.reasoning)
            response.phi_coherence = coherence

        # 3. Calculate weighted votes
        approve_weight = 0.0
        reject_weight = 0.0
        abstain_weight = 0.0
        total_weight = 0.0

        for response in responses:
            # Skip low-coherence responses
            if response.phi_coherence < self.min_coherence:
                continue

            # Weight = coherence * confidence
            weight = response.phi_coherence * response.confidence
            total_weight += weight

            if response.decision == AgentDecision.APPROVE:
                approve_weight += weight
            elif response.decision == AgentDecision.REJECT:
                reject_weight += weight
            else:
                abstain_weight += weight

        # Normalize weights
        if total_weight > 0:
            approve_weight /= total_weight
            reject_weight /= total_weight
            abstain_weight /= total_weight

        # 4. Determine final decision
        if approve_weight >= self.approval_threshold:
            final_decision = AgentDecision.APPROVE
            threshold_met = True
        elif reject_weight >= self.approval_threshold:
            final_decision = AgentDecision.REJECT
            threshold_met = True
        else:
            # No consensus - default to abstain
            final_decision = AgentDecision.ABSTAIN
            threshold_met = False

        # 5. Create consensus data for POB attestation
        consensus_data = json.dumps({
            'transaction': transaction,
            'decision': final_decision.value,
            'approve_weight': round(approve_weight, 4),
            'reject_weight': round(reject_weight, 4),
            'agent_responses': [r.to_dict() for r in responses],
        }, sort_keys=True)

        # 6. Generate POB attestation
        proof = calculate_pob(consensus_data)

        return ConsensusResult(
            final_decision=final_decision,
            approve_weight=approve_weight,
            reject_weight=reject_weight,
            abstain_weight=abstain_weight,
            threshold_met=threshold_met,
            agent_responses=responses,
            proof=proof,
            consensus_data=consensus_data,
        )

    def verify_consensus(self, result: ConsensusResult) -> bool:
        """Verify a consensus result's POB attestation."""
        if not result.proof:
            return False
        return verify_proof(result.proof, result.consensus_data)


def create_default_agents() -> List[Agent]:
    """Create a default set of agents for demo."""
    from .base import MockAgent

    return [
        MockAgent("security_1", AgentRole.SECURITY),
        MockAgent("compliance_1", AgentRole.COMPLIANCE),
        MockAgent("economics_1", AgentRole.ECONOMICS),
    ]


async def demo():
    """Demo the multi-agent consensus."""
    print("=" * 60)
    print("MULTI-AGENT CONSENSUS DEMO")
    print("=" * 60)

    # Create agents
    agents = create_default_agents()
    consensus = MultiAgentConsensus(agents)

    # Test transaction
    transaction = {
        'type': 'transfer',
        'amount': 5.0,
        'recipient': 'ABC123...',
        'memo': 'Payment for services',
    }

    print(f"\nTransaction: {transaction}")
    print("\nRunning consensus...")

    result = await consensus.analyze(transaction)

    print(f"\n--- RESULT ---")
    print(f"Decision: {result.final_decision.value}")
    print(f"Approve weight: {result.approve_weight:.2%}")
    print(f"Reject weight: {result.reject_weight:.2%}")
    print(f"Threshold met: {result.threshold_met}")
    print(f"\nAgent responses:")
    for r in result.agent_responses:
        print(f"  - {r.agent_id}: {r.decision.value} "
              f"(coherence: {r.phi_coherence:.2f}, confidence: {r.confidence:.2f})")

    print(f"\nPOB Attestation:")
    print(f"  Valid: {result.proof.valid}")
    print(f"  Ratio: {result.proof.ratio:.6f} (target: {result.proof.target:.6f})")
    print(f"  Attempts: {result.proof.attempts}")

    # Verify
    verified = consensus.verify_consensus(result)
    print(f"\nVerification: {'PASS' if verified else 'FAIL'}")


if __name__ == "__main__":
    asyncio.run(demo())
