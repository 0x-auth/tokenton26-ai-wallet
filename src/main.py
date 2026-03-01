"""
TokenTon26 AI Wallet - Main Application

AI-powered multi-agent consensus wallet on Solana.
"""

import asyncio
import json
from typing import Optional, Dict, Any

from .agents.base import MockAgent, AgentRole
from .agents.multi_agent import MultiAgentConsensus, ConsensusResult
from .wallet.solana_wallet import create_wallet, WalletConfig
from .consensus.pob import verify_proof


class AIWallet:
    """
    TokenTon26 AI Wallet

    An intelligent crypto wallet that uses multi-agent AI consensus
    to validate transactions before execution.
    """

    def __init__(
        self,
        network: str = "devnet",
        mock_wallet: bool = True,
        mock_agents: bool = True,
    ):
        # Wallet configuration
        self.wallet_config = WalletConfig(
            network=network,
            require_consensus=True,
            min_approval_weight=0.6,
        )
        self.wallet = create_wallet(mock=mock_wallet, config=self.wallet_config)

        # Create agents
        if mock_agents:
            agents = [
                MockAgent("security_agent", AgentRole.SECURITY),
                MockAgent("compliance_agent", AgentRole.COMPLIANCE),
                MockAgent("economics_agent", AgentRole.ECONOMICS),
            ]
        else:
            # Use real agents (requires API keys)
            from .agents.base import OpenAIAgent, AnthropicAgent
            agents = [
                OpenAIAgent("security_agent", AgentRole.SECURITY),
                AnthropicAgent("compliance_agent", AgentRole.COMPLIANCE),
                OpenAIAgent("economics_agent", AgentRole.ECONOMICS),
            ]

        self.consensus = MultiAgentConsensus(
            agents=agents,
            approval_threshold=self.wallet_config.min_approval_weight,
        )

        self.pending_transactions: Dict[str, Dict] = {}

    @property
    def address(self) -> Optional[str]:
        return self.wallet.address

    async def get_balance(self) -> float:
        return await self.wallet.get_balance()

    async def request_airdrop(self, amount: float = 1.0) -> Optional[str]:
        return await self.wallet.request_airdrop(amount)

    async def prepare_transfer(
        self,
        recipient: str,
        amount: float,
        memo: str = "",
    ) -> Dict[str, Any]:
        """
        Prepare a transfer for AI consensus review.

        Returns transaction data and consensus result.
        """
        # Create transaction
        transaction = self.wallet.create_transfer_transaction(recipient, amount)
        transaction['memo'] = memo

        # Run consensus
        result = await self.consensus.analyze(transaction)

        # Store for execution
        tx_id = result.proof.content_hash[:16] if result.proof else "no_proof"
        self.pending_transactions[tx_id] = {
            'transaction': transaction,
            'consensus': result,
        }

        return {
            'tx_id': tx_id,
            'transaction': transaction,
            'decision': result.final_decision.value,
            'approve_weight': result.approve_weight,
            'reject_weight': result.reject_weight,
            'threshold_met': result.threshold_met,
            'proof_valid': result.proof.valid if result.proof else False,
            'agent_responses': [
                {
                    'agent': r.agent_id,
                    'decision': r.decision.value,
                    'coherence': r.phi_coherence,
                    'confidence': r.confidence,
                    'reasoning': r.reasoning,
                }
                for r in result.agent_responses
            ],
        }

    async def execute_transfer(self, tx_id: str) -> Dict[str, Any]:
        """
        Execute a prepared transfer after consensus approval.
        """
        if tx_id not in self.pending_transactions:
            return {'error': 'Transaction not found', 'success': False}

        pending = self.pending_transactions[tx_id]
        result: ConsensusResult = pending['consensus']
        transaction = pending['transaction']

        # Check consensus
        if result.final_decision.value != 'approve':
            return {
                'error': f'Transaction rejected by consensus: {result.final_decision.value}',
                'success': False,
            }

        # Verify POB
        if result.proof and not verify_proof(result.proof, result.consensus_data):
            return {'error': 'POB verification failed', 'success': False}

        # Execute
        try:
            signature = await self.wallet.execute_transfer(
                recipient=transaction['to'],
                amount_sol=transaction['amount'],
                consensus_proof=result.proof.to_dict() if result.proof else None,
            )

            # Clean up
            del self.pending_transactions[tx_id]

            return {
                'success': True,
                'signature': signature,
                'amount': transaction['amount'],
                'recipient': transaction['to'],
            }

        except Exception as e:
            return {'error': str(e), 'success': False}

    def get_wallet_info(self) -> Dict[str, Any]:
        """Get wallet information."""
        return {
            'address': self.address,
            'network': self.wallet_config.network,
            'require_consensus': self.wallet_config.require_consensus,
            'min_approval_weight': self.wallet_config.min_approval_weight,
            'agent_count': len(self.consensus.agents),
        }


async def demo():
    """Demo the AI wallet."""
    print("=" * 70)
    print("TOKENTON26 AI WALLET - DEMO")
    print("=" * 70)

    # Create wallet
    wallet = AIWallet(network="devnet", mock_wallet=True, mock_agents=True)

    print(f"\nWallet address: {wallet.address}")
    print(f"Network: {wallet.wallet_config.network}")

    # Get balance
    balance = await wallet.get_balance()
    print(f"Balance: {balance} SOL")

    # Prepare transfer
    print("\n--- PREPARING TRANSFER ---")
    result = await wallet.prepare_transfer(
        recipient="RecipientAddress123456789",
        amount=2.5,
        memo="Payment for services",
    )

    print(f"Transaction ID: {result['tx_id']}")
    print(f"Decision: {result['decision']}")
    print(f"Approve weight: {result['approve_weight']:.2%}")
    print(f"Threshold met: {result['threshold_met']}")
    print(f"POB valid: {result['proof_valid']}")

    print("\nAgent responses:")
    for r in result['agent_responses']:
        print(f"  - {r['agent']}: {r['decision']} "
              f"(coherence: {r['coherence']:.2f}, confidence: {r['confidence']:.2f})")
        print(f"    Reasoning: {r['reasoning'][:60]}...")

    # Execute if approved
    if result['decision'] == 'approve':
        print("\n--- EXECUTING TRANSFER ---")
        exec_result = await wallet.execute_transfer(result['tx_id'])
        if exec_result['success']:
            print(f"Success! Signature: {exec_result['signature']}")
        else:
            print(f"Failed: {exec_result['error']}")
    else:
        print(f"\nTransfer rejected: {result['decision']}")

    # Final balance
    balance = await wallet.get_balance()
    print(f"\nFinal balance: {balance} SOL")


if __name__ == "__main__":
    asyncio.run(demo())
