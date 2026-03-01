#!/bin/bash
# TokenTon26 - Quick Token Deployment Script

set -e

echo "=============================================="
echo "TOKENTON26 - SPL TOKEN DEPLOYMENT"
echo "=============================================="

# Check if Solana CLI is installed
if ! command -v solana &> /dev/null; then
    echo "Solana CLI not found. Installing..."
    sh -c "$(curl -sSfL https://release.solana.com/stable/install)"
    export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
fi

# Check if spl-token is installed
if ! command -v spl-token &> /dev/null; then
    echo "SPL Token CLI not found. Installing..."
    cargo install spl-token-cli
fi

# Configure for devnet
echo ""
echo "Configuring for devnet..."
solana config set --url devnet

# Create or use existing keypair
KEYPAIR_PATH="$HOME/.config/solana/tokenton26.json"
if [ ! -f "$KEYPAIR_PATH" ]; then
    echo "Creating new keypair..."
    solana-keygen new --outfile "$KEYPAIR_PATH" --no-bip39-passphrase --force
fi

PUBKEY=$(solana-keygen pubkey "$KEYPAIR_PATH")
echo "Wallet: $PUBKEY"

# Request airdrop
echo ""
echo "Requesting SOL airdrop..."
solana airdrop 2 "$PUBKEY" || echo "Airdrop failed (rate limited). Try https://faucet.solana.com/"

# Check balance
echo ""
solana balance "$PUBKEY"

# Create token
echo ""
echo "Creating SPL token..."
TOKEN_OUTPUT=$(spl-token create-token --fee-payer "$KEYPAIR_PATH" 2>&1)
echo "$TOKEN_OUTPUT"

# Extract token address (the first base58 string that looks like an address)
TOKEN_ADDRESS=$(echo "$TOKEN_OUTPUT" | grep -oE '[1-9A-HJ-NP-Za-km-z]{32,44}' | head -1)

if [ -z "$TOKEN_ADDRESS" ]; then
    echo "Failed to extract token address"
    exit 1
fi

echo "Token Address: $TOKEN_ADDRESS"

# Create token account
echo ""
echo "Creating token account..."
spl-token create-account "$TOKEN_ADDRESS" --fee-payer "$KEYPAIR_PATH"

# Mint tokens (1 billion)
echo ""
echo "Minting 1,000,000,000 tokens..."
spl-token mint "$TOKEN_ADDRESS" 1000000000 --fee-payer "$KEYPAIR_PATH"

# Show supply
echo ""
echo "Token supply:"
spl-token supply "$TOKEN_ADDRESS"

# Save deployment info
echo ""
cat > deployment.json << EOF
{
  "token_address": "$TOKEN_ADDRESS",
  "wallet": "$PUBKEY",
  "network": "devnet",
  "supply": "1000000000",
  "explorer": "https://explorer.solana.com/address/$TOKEN_ADDRESS?cluster=devnet"
}
EOF

echo "Deployment info saved to deployment.json"

echo ""
echo "=============================================="
echo "DEPLOYMENT COMPLETE"
echo "=============================================="
echo "Token Address: $TOKEN_ADDRESS"
echo "Wallet: $PUBKEY"
echo "Network: devnet"
echo "Explorer: https://explorer.solana.com/address/$TOKEN_ADDRESS?cluster=devnet"
