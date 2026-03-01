"""
TokenTon26 - SPL Token Deployment Script

Deploy the AI Wallet governance token on Solana devnet.
"""

import os
import json
import subprocess
from pathlib import Path


def run_cmd(cmd: str, check: bool = True) -> str:
    """Run a shell command and return output."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        raise Exception(f"Command failed: {cmd}")
    return result.stdout.strip()


def check_solana_cli():
    """Check if Solana CLI is installed."""
    try:
        version = run_cmd("solana --version")
        print(f"Solana CLI: {version}")
        return True
    except:
        print("Solana CLI not found. Install from: https://docs.solana.com/cli/install-solana-cli-tools")
        return False


def check_spl_token_cli():
    """Check if SPL Token CLI is installed."""
    try:
        version = run_cmd("spl-token --version")
        print(f"SPL Token CLI: {version}")
        return True
    except:
        print("SPL Token CLI not found. Run: cargo install spl-token-cli")
        return False


def setup_devnet():
    """Configure Solana CLI for devnet."""
    print("\nConfiguring for devnet...")
    run_cmd("solana config set --url devnet")
    config = run_cmd("solana config get")
    print(config)


def create_or_get_keypair(name: str = "tokenton26") -> str:
    """Create or get existing keypair."""
    keypair_path = Path.home() / ".config" / "solana" / f"{name}.json"

    if keypair_path.exists():
        print(f"Using existing keypair: {keypair_path}")
    else:
        print(f"Creating new keypair: {keypair_path}")
        run_cmd(f"solana-keygen new --outfile {keypair_path} --no-bip39-passphrase --force")

    # Get pubkey
    pubkey = run_cmd(f"solana-keygen pubkey {keypair_path}")
    print(f"Wallet address: {pubkey}")

    return str(keypair_path), pubkey


def request_airdrop(pubkey: str, amount: float = 2.0):
    """Request SOL airdrop on devnet."""
    print(f"\nRequesting {amount} SOL airdrop...")
    try:
        run_cmd(f"solana airdrop {amount} {pubkey}")
        balance = run_cmd(f"solana balance {pubkey}")
        print(f"Balance: {balance}")
    except Exception as e:
        print(f"Airdrop failed (rate limited?): {e}")
        print("Try again later or use: https://faucet.solana.com/")


def create_token(keypair_path: str) -> str:
    """Create a new SPL token."""
    print("\nCreating SPL token...")

    # Create token
    output = run_cmd(f"spl-token create-token --fee-payer {keypair_path}")
    print(output)

    # Extract token address
    for line in output.split('\n'):
        if 'Creating token' in line or 'Address:' in line:
            parts = line.split()
            for part in parts:
                if len(part) > 30 and part.isalnum():
                    return part

    # Fallback: get from token accounts
    tokens = run_cmd(f"spl-token accounts --owner {keypair_path}")
    print(f"Token accounts: {tokens}")

    raise Exception("Could not extract token address")


def create_token_account(keypair_path: str, token_address: str) -> str:
    """Create token account for the wallet."""
    print(f"\nCreating token account for {token_address}...")
    output = run_cmd(f"spl-token create-account {token_address} --fee-payer {keypair_path}")
    print(output)

    # Extract account address
    for line in output.split('\n'):
        if 'Creating account' in line:
            parts = line.split()
            for part in parts:
                if len(part) > 30:
                    return part

    return ""


def mint_tokens(keypair_path: str, token_address: str, amount: int = 1000000000):
    """Mint tokens to the wallet."""
    print(f"\nMinting {amount:,} tokens...")
    output = run_cmd(f"spl-token mint {token_address} {amount} --fee-payer {keypair_path}")
    print(output)


def get_token_info(token_address: str) -> dict:
    """Get token information."""
    print(f"\nToken info for {token_address}:")
    supply = run_cmd(f"spl-token supply {token_address}")
    print(f"Supply: {supply}")

    return {
        "address": token_address,
        "supply": supply,
        "network": "devnet",
    }


def save_deployment_info(info: dict, output_path: str = "deployment.json"):
    """Save deployment information."""
    with open(output_path, 'w') as f:
        json.dump(info, f, indent=2)
    print(f"\nDeployment info saved to: {output_path}")


def main():
    print("=" * 60)
    print("TOKENTON26 - SPL TOKEN DEPLOYMENT")
    print("=" * 60)

    # Check prerequisites
    if not check_solana_cli():
        return
    if not check_spl_token_cli():
        return

    # Setup
    setup_devnet()

    # Get or create keypair
    keypair_path, pubkey = create_or_get_keypair("tokenton26")

    # Request airdrop
    request_airdrop(pubkey)

    # Create token
    try:
        token_address = create_token(keypair_path)
        print(f"\nToken created: {token_address}")

        # Create account
        create_token_account(keypair_path, token_address)

        # Mint initial supply (1 billion tokens)
        mint_tokens(keypair_path, token_address, 1_000_000_000)

        # Get info
        info = get_token_info(token_address)
        info["keypair_path"] = keypair_path
        info["wallet"] = pubkey

        # Save
        save_deployment_info(info)

        print("\n" + "=" * 60)
        print("DEPLOYMENT COMPLETE")
        print("=" * 60)
        print(f"Token Address: {token_address}")
        print(f"Wallet: {pubkey}")
        print(f"Network: devnet")
        print(f"Explorer: https://explorer.solana.com/address/{token_address}?cluster=devnet")

    except Exception as e:
        print(f"\nDeployment failed: {e}")
        print("\nManual steps:")
        print("1. solana airdrop 2")
        print("2. spl-token create-token")
        print("3. spl-token create-account <TOKEN_ADDRESS>")
        print("4. spl-token mint <TOKEN_ADDRESS> 1000000000")


if __name__ == "__main__":
    main()
