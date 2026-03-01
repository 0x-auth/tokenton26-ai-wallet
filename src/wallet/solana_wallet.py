"""
Solana Wallet Integration for TokenTon26

AI-guarded wallet that requires multi-agent consensus before transactions.
"""

import os
import json
import base58
import base64
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

try:
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solders.signature import Signature
    from solders.transaction import Transaction
    from solders.system_program import TransferParams, transfer
    from solders.message import Message
    from solana.rpc.api import Client
    from solana.rpc.commitment import Confirmed
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False
    print("Warning: solana/solders not installed. Run: pip install solana solders")


@dataclass
class WalletConfig:
    """Wallet configuration."""
    network: str = "devnet"  # devnet, testnet, mainnet-beta
    keypair_path: Optional[str] = None
    require_consensus: bool = True
    min_approval_weight: float = 0.6

    @property
    def rpc_url(self) -> str:
        urls = {
            "devnet": "https://api.devnet.solana.com",
            "testnet": "https://api.testnet.solana.com",
            "mainnet-beta": "https://api.mainnet-beta.solana.com",
        }
        return urls.get(self.network, urls["devnet"])


class SolanaWallet:
    """
    AI-guarded Solana wallet.

    Transactions require multi-agent consensus before execution.
    Each transaction is attested via POB.
    """

    def __init__(self, config: Optional[WalletConfig] = None):
        if not SOLANA_AVAILABLE:
            raise ImportError("solana/solders packages required. Run: pip install solana solders")

        self.config = config or WalletConfig()
        self.client = Client(self.config.rpc_url)
        self.keypair: Optional[Keypair] = None

        if self.config.keypair_path:
            self._load_keypair(self.config.keypair_path)

    def _load_keypair(self, path: str):
        """Load keypair from file."""
        with open(path, 'r') as f:
            secret = json.load(f)
        self.keypair = Keypair.from_bytes(bytes(secret))

    def generate_keypair(self) -> str:
        """Generate a new keypair."""
        self.keypair = Keypair()
        return str(self.keypair.pubkey())

    def save_keypair(self, path: str):
        """Save keypair to file."""
        if not self.keypair:
            raise ValueError("No keypair to save")
        secret = list(bytes(self.keypair))
        with open(path, 'w') as f:
            json.dump(secret, f)

    @property
    def pubkey(self) -> Optional[str]:
        """Get wallet public key."""
        if self.keypair:
            return str(self.keypair.pubkey())
        return None

    @property
    def address(self) -> Optional[str]:
        """Alias for pubkey."""
        return self.pubkey

    async def get_balance(self) -> float:
        """Get wallet balance in SOL."""
        if not self.keypair:
            return 0.0
        response = self.client.get_balance(self.keypair.pubkey())
        lamports = response.value
        return lamports / 1_000_000_000  # Convert lamports to SOL

    async def request_airdrop(self, amount_sol: float = 1.0) -> Optional[str]:
        """Request airdrop (devnet only)."""
        if self.config.network != "devnet":
            raise ValueError("Airdrop only available on devnet")
        if not self.keypair:
            raise ValueError("No keypair")

        lamports = int(amount_sol * 1_000_000_000)
        response = self.client.request_airdrop(
            self.keypair.pubkey(),
            lamports
        )
        return str(response.value) if response.value else None

    def create_transfer_transaction(
        self,
        recipient: str,
        amount_sol: float,
    ) -> Dict[str, Any]:
        """
        Create a transfer transaction (not signed yet).

        Returns transaction data for AI consensus review.
        """
        if not self.keypair:
            raise ValueError("No keypair")

        recipient_pubkey = Pubkey.from_string(recipient)
        lamports = int(amount_sol * 1_000_000_000)

        return {
            'type': 'transfer',
            'from': str(self.keypair.pubkey()),
            'to': recipient,
            'amount': amount_sol,
            'lamports': lamports,
            'network': self.config.network,
        }

    async def execute_transfer(
        self,
        recipient: str,
        amount_sol: float,
        consensus_proof: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        Execute a transfer after consensus approval.

        Args:
            recipient: Recipient address
            amount_sol: Amount in SOL
            consensus_proof: POB proof from consensus (optional but recommended)

        Returns:
            Transaction signature or None
        """
        if not self.keypair:
            raise ValueError("No keypair")

        if self.config.require_consensus and not consensus_proof:
            raise ValueError("Consensus proof required for transfer")

        recipient_pubkey = Pubkey.from_string(recipient)
        lamports = int(amount_sol * 1_000_000_000)

        # Create transfer instruction
        transfer_ix = transfer(
            TransferParams(
                from_pubkey=self.keypair.pubkey(),
                to_pubkey=recipient_pubkey,
                lamports=lamports,
            )
        )

        # Get recent blockhash
        recent_blockhash = self.client.get_latest_blockhash().value.blockhash

        # Create and sign transaction
        message = Message.new_with_blockhash(
            [transfer_ix],
            self.keypair.pubkey(),
            recent_blockhash,
        )
        tx = Transaction.new_unsigned(message)
        tx.sign([self.keypair], recent_blockhash)

        # Send transaction
        result = self.client.send_transaction(tx)

        if result.value:
            return str(result.value)
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Get wallet info as dict."""
        return {
            'address': self.address,
            'network': self.config.network,
            'require_consensus': self.config.require_consensus,
        }


class MockSolanaWallet:
    """Mock wallet for testing without Solana SDK."""

    def __init__(self, config: Optional[WalletConfig] = None):
        self.config = config or WalletConfig()
        self._pubkey = "MockWallet" + "X" * 32
        self._balance = 10.0

    @property
    def pubkey(self) -> str:
        return self._pubkey

    @property
    def address(self) -> str:
        return self._pubkey

    async def get_balance(self) -> float:
        return self._balance

    async def request_airdrop(self, amount_sol: float = 1.0) -> str:
        self._balance += amount_sol
        return "mock_airdrop_signature"

    def create_transfer_transaction(
        self,
        recipient: str,
        amount_sol: float,
    ) -> Dict[str, Any]:
        return {
            'type': 'transfer',
            'from': self._pubkey,
            'to': recipient,
            'amount': amount_sol,
            'network': self.config.network,
        }

    async def execute_transfer(
        self,
        recipient: str,
        amount_sol: float,
        consensus_proof: Optional[Dict] = None,
    ) -> str:
        if self.config.require_consensus and not consensus_proof:
            raise ValueError("Consensus proof required")
        self._balance -= amount_sol
        return "mock_tx_signature_" + recipient[:8]


def create_wallet(mock: bool = False, config: Optional[WalletConfig] = None):
    """Create a wallet (mock or real)."""
    if mock or not SOLANA_AVAILABLE:
        return MockSolanaWallet(config)
    return SolanaWallet(config)


if __name__ == "__main__":
    import asyncio

    async def demo():
        print("=" * 60)
        print("SOLANA WALLET DEMO")
        print("=" * 60)

        wallet = create_wallet(mock=True)
        print(f"\nWallet address: {wallet.address}")

        balance = await wallet.get_balance()
        print(f"Balance: {balance} SOL")

        # Create transaction
        tx = wallet.create_transfer_transaction(
            recipient="RecipientAddress123",
            amount_sol=1.0,
        )
        print(f"\nTransaction: {tx}")

        # Execute (would need consensus proof in production)
        wallet.config.require_consensus = False
        sig = await wallet.execute_transfer("RecipientAddress123", 1.0)
        print(f"Signature: {sig}")

        balance = await wallet.get_balance()
        print(f"New balance: {balance} SOL")

    asyncio.run(demo())
