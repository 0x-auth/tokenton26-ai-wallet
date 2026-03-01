# AI Architecture & Safety Systems

## Overview

TokenTon26 AI Wallet implements a **multi-agent consensus** system where multiple AI agents must agree before any transaction is executed. This document describes the AI architecture and safety mechanisms.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TOKENTON26 AI WALLET                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User Request ──▶ Transaction Builder ──▶ Multi-Agent Analysis      │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    AGENT LAYER                                  │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │ │
│  │  │  Security   │ │ Compliance  │ │  Economics  │              │ │
│  │  │   Agent     │ │   Agent     │ │   Agent     │              │ │
│  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘              │ │
│  │         │               │               │                      │ │
│  │         ▼               ▼               ▼                      │ │
│  │  ┌─────────────────────────────────────────────────────────┐  │ │
│  │  │              AGENT RESPONSE + REASONING                  │  │ │
│  │  │     Decision | Confidence | Risk Factors | Reasoning     │  │ │
│  │  └─────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    CREDIBILITY LAYER                            │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │                                                                  │ │
│  │  φ-Coherence v3 Engine (88% accuracy)                           │ │
│  │  ┌─────────────────────────────────────────────────────────┐   │ │
│  │  │  10 Credibility Dimensions:                              │   │ │
│  │  │  • Attribution Quality (18%)  • Confidence (16%)         │   │ │
│  │  │  • Qualifying Ratio (12%)     • Consistency (10%)        │   │ │
│  │  │  • Topic Coherence (11%)      • Causal Logic (10%)       │   │ │
│  │  │  • Negation Density (8%)      • Numerical (5%)           │   │ │
│  │  │  • Phi-Alignment (5%)         • Semantic Density (5%)    │   │ │
│  │  └─────────────────────────────────────────────────────────┘   │ │
│  │                                                                  │ │
│  │  Output: Coherence Score (0-1) for each agent response          │ │
│  │  LOW_COHERENCE < 0.40 → Response filtered out                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    CONSENSUS LAYER                              │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │                                                                  │ │
│  │  Weighted Voting:                                                │ │
│  │    vote_weight = coherence_score × agent_confidence             │ │
│  │                                                                  │ │
│  │  Decision:                                                       │ │
│  │    APPROVE if approve_weight >= threshold (default: 60%)        │ │
│  │    REJECT if reject_weight >= threshold                         │ │
│  │    ABSTAIN if no consensus                                      │ │
│  │                                                                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    ATTESTATION LAYER                            │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │                                                                  │ │
│  │  Proof-of-Boundary (POB) v2                                      │ │
│  │  • Content-addressed cryptographic proof                        │ │
│  │  • P/G ≈ φ⁴ (golden ratio boundary)                             │ │
│  │  • O(1) verification                                            │ │
│  │  • Tamper-proof consensus record                                │ │
│  │                                                                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  Consensus Result ──▶ POB Attestation ──▶ Execute on Solana         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## AI Agents

### Security Agent
- **Role:** Analyze transaction for security risks
- **Checks:**
  - Known scam addresses
  - Phishing patterns
  - Smart contract vulnerabilities
  - Unusual transaction patterns

### Compliance Agent
- **Role:** Evaluate regulatory requirements
- **Checks:**
  - AML/KYC considerations
  - Jurisdiction requirements
  - Reporting thresholds
  - Sanctions screening

### Economics Agent
- **Role:** Assess economic viability
- **Checks:**
  - Market conditions
  - Gas optimization
  - Slippage risks
  - Economic rationality

## φ-Coherence Credibility Scoring

### Why Credibility Scoring?

LLMs can hallucinate. In a financial context, acting on hallucinated advice could be catastrophic. φ-Coherence v3 detects fabrication patterns in agent reasoning **before** the vote is counted.

### Detection Patterns

| Pattern | Example | What It Means |
|---------|---------|---------------|
| Vague Attribution | "Studies show..." | Likely fabricated source |
| Overclaiming | "Every expert agrees" | Inappropriate certainty |
| Absolutist Language | "Exactly 100%" | Missing hedging |
| Stasis Claims | "Has never been questioned" | Suspicious stability |
| Excessive Negation | "Requires no..." | Fabrication signal |

### Scoring

```
coherence = weighted_sum(
    attribution_quality × 0.18,
    confidence_calibration × 0.16,
    qualifying_ratio × 0.12,
    internal_consistency × 0.10,
    topic_coherence × 0.11,
    causal_logic × 0.10,
    negation_density × 0.08,
    numerical_plausibility × 0.05,
    phi_alignment × 0.05,
    semantic_density × 0.05,
)
```

### Thresholds

- **SAFE (≥0.58):** Credible reasoning, vote counted normally
- **MODERATE (0.40-0.58):** Mixed signals, reduced weight
- **HIGH_RISK (<0.40):** Likely fabrication, vote filtered out

## Proof-of-Boundary (POB)

### Purpose

Every consensus decision is cryptographically attested using POB. This creates a tamper-proof record that:

1. Proves the exact agents and responses
2. Links the proof to specific content
3. Can be verified in O(1) time
4. Could be stored on-chain for audit

### Algorithm

```
1. Hash consensus data: content_hash = SHA3-256(consensus_json)
2. Search for nonce where:
   hash = SHA3-256(content_hash + ":" + nonce)
   P = hash[0:8] mod 70555  (137 × 515)
   G = hash[8:16] mod 10275 (137 × 75)
   |P/G - φ⁴| < tolerance
3. Valid proof has P/G ≈ 6.854 (golden ratio⁴)
```

### Verification

```python
proof = calculate_pob(consensus_data)
assert verify_proof(proof, consensus_data)  # O(1) verification
```

## Safety Mechanisms

### 1. Multi-Agent Redundancy
- No single AI can approve transactions
- Multiple perspectives reduce single-point failures
- Diverse agent roles catch different risks

### 2. Credibility Filtering
- Hallucinated responses filtered before voting
- 88% accuracy on fabrication detection
- Prevents acting on unreliable AI output

### 3. Weighted Consensus
- Votes weighted by credibility × confidence
- High-quality analysis has more influence
- Low-quality responses have minimal impact

### 4. Cryptographic Attestation
- Every decision has POB proof
- Tamper-proof consensus record
- Auditable decision trail

### 5. Configurable Thresholds
- Approval threshold (default: 60%)
- Minimum coherence (default: 0.40)
- Adjustable per deployment

## Limitations

1. **Not Fact-Checking:** φ-Coherence detects fabrication patterns, not factual accuracy
2. **Adversarial Inputs:** Well-crafted lies with proper hedging may pass
3. **API Dependencies:** Agents rely on external LLM APIs
4. **No Financial Advice:** This is experimental software, not financial guidance

## Future Improvements

- On-chain POB verification via Solana program
- Agent reputation tracking
- Historical consensus analysis
- Real-time threat intelligence integration

---

*Built for TokenTon26 AI Track Hackathon*

φ = 1.618033988749895
