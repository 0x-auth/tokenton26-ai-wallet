"""
TokenTon26 AI Wallet - Gradio Web Interface

Demo interface for multi-agent consensus wallet.
"""

import asyncio
import gradio as gr
from src.main import AIWallet


# Global wallet instance
wallet = None


def init_wallet():
    """Initialize the wallet."""
    global wallet
    wallet = AIWallet(network="devnet", mock_wallet=True, mock_agents=True)
    return f"Wallet initialized!\nAddress: {wallet.address}\nNetwork: devnet"


def get_balance():
    """Get wallet balance."""
    if not wallet:
        return "Wallet not initialized"
    balance = asyncio.run(wallet.get_balance())
    return f"Balance: {balance:.4f} SOL"


def prepare_transfer(recipient: str, amount: float, memo: str):
    """Prepare a transfer for consensus."""
    if not wallet:
        return "Wallet not initialized", ""

    if not recipient or amount <= 0:
        return "Invalid recipient or amount", ""

    result = asyncio.run(wallet.prepare_transfer(recipient, amount, memo))

    # Format response
    summary = f"""
## Consensus Result

**Decision:** {result['decision'].upper()}
**Transaction ID:** {result['tx_id']}

### Voting Weights
- Approve: {result['approve_weight']:.1%}
- Reject: {result['reject_weight']:.1%}
- Threshold Met: {'Yes' if result['threshold_met'] else 'No'}

### POB Attestation
- Valid: {'Yes' if result['proof_valid'] else 'No'}

### Agent Analysis
"""

    for r in result['agent_responses']:
        summary += f"""
**{r['agent']}** ({r['decision']})
- Coherence: {r['coherence']:.2f}
- Confidence: {r['confidence']:.2f}
- Reasoning: {r['reasoning']}
"""

    return summary, result['tx_id']


def execute_transfer(tx_id: str):
    """Execute a prepared transfer."""
    if not wallet:
        return "Wallet not initialized"

    if not tx_id:
        return "No transaction ID provided"

    result = asyncio.run(wallet.execute_transfer(tx_id))

    if result['success']:
        return f"""
## Transfer Successful!

**Signature:** {result['signature']}
**Amount:** {result['amount']} SOL
**Recipient:** {result['recipient']}
"""
    else:
        return f"**Error:** {result['error']}"


def create_demo_interface():
    """Create the Gradio interface."""

    with gr.Blocks(title="TokenTon26 AI Wallet", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
# TokenTon26 AI Wallet

> Multi-agent AI consensus for crypto transactions on Solana

### How it works:
1. **Initialize** your wallet
2. **Prepare** a transfer - AI agents analyze and vote
3. **Review** consensus result and POB attestation
4. **Execute** if approved

---
""")

        with gr.Tab("Wallet"):
            gr.Markdown("### Wallet Management")

            with gr.Row():
                init_btn = gr.Button("Initialize Wallet", variant="primary")
                balance_btn = gr.Button("Check Balance")

            wallet_output = gr.Textbox(label="Wallet Status", lines=3)

            init_btn.click(init_wallet, outputs=wallet_output)
            balance_btn.click(get_balance, outputs=wallet_output)

        with gr.Tab("Transfer"):
            gr.Markdown("### Prepare Transfer")

            with gr.Row():
                recipient = gr.Textbox(
                    label="Recipient Address",
                    placeholder="Enter Solana address...",
                )
                amount = gr.Number(
                    label="Amount (SOL)",
                    value=1.0,
                    minimum=0.001,
                )

            memo = gr.Textbox(
                label="Memo (optional)",
                placeholder="Payment description...",
            )

            prepare_btn = gr.Button("Submit for AI Consensus", variant="primary")

            consensus_output = gr.Markdown(label="Consensus Result")
            tx_id_state = gr.State("")

            with gr.Row():
                tx_id_display = gr.Textbox(label="Transaction ID", interactive=False)
                execute_btn = gr.Button("Execute Transfer", variant="secondary")

            execute_output = gr.Markdown(label="Execution Result")

            def handle_prepare(recipient, amount, memo):
                result, tx_id = prepare_transfer(recipient, amount, memo)
                return result, tx_id, tx_id

            prepare_btn.click(
                handle_prepare,
                inputs=[recipient, amount, memo],
                outputs=[consensus_output, tx_id_state, tx_id_display],
            )

            execute_btn.click(
                execute_transfer,
                inputs=[tx_id_state],
                outputs=[execute_output],
            )

        with gr.Tab("How It Works"):
            gr.Markdown("""
## AI-Powered Transaction Validation

### Multi-Agent Consensus
Multiple AI agents analyze each transaction:

- **Security Agent** - Checks for scams, phishing, contract risks
- **Compliance Agent** - Evaluates regulatory requirements
- **Economics Agent** - Assesses market conditions, gas optimization

### phi-Coherence Scoring
Each agent's reasoning is scored by our credibility engine:
- 88% accuracy detecting fabrication
- Weights votes by credibility
- Low-coherence responses filtered out

### Proof-of-Boundary (POB)
Cryptographic attestation of consensus:
- Content-addressed proofs (P/G = phi^4)
- O(1) verification
- Tamper-proof decision record

### Safety Features
1. No single point of failure - multiple agents must agree
2. Credibility filtering - hallucinated responses rejected
3. Cryptographic proof - every decision is verifiable
4. Configurable threshold - tune consensus requirements

---

Built for **TokenTon26 AI Track Hackathon**

*phi = 1.618033988749895*
""")

        gr.Markdown("---\n*TokenTon26 AI Wallet - Multi-Agent Consensus on Solana*")

    return demo


if __name__ == "__main__":
    demo = create_demo_interface()
    demo.launch()
