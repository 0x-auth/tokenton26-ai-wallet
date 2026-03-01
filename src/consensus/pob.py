"""
Proof-of-Boundary (POB) v2 - Cryptographic Attestation for AI Consensus

Content-addressed proofs where P/G = phi^4 (golden ratio boundary).
O(1) verification, zero-energy consensus.

"You can buy hashpower. You can buy stake. You CANNOT BUY understanding."
"""

import time
import hashlib
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Constants
PHI = 1.618033988749895
PHI_4 = PHI ** 4  # 6.854...
ALPHA = 137
ABHI_AMU = 515

# Moduli: P_MOD/G_MOD = phi^4
P_MOD = ALPHA * ABHI_AMU   # 137 x 515 = 70,555
G_MOD = ALPHA * 75         # 137 x 75 = 10,275

# Mean ratio = P_MOD / G_MOD = 6.867 ~ phi^4
CALIBRATED_RATIO = P_MOD / G_MOD

DEFAULT_TOLERANCE = 0.3
MAX_NONCE = 100_000


@dataclass
class BoundaryProof:
    """
    A content-addressed Proof-of-Boundary.

    Demonstrates that for given content, a nonce was found
    such that hash splits into P and G where P/G ~ phi^4.
    """
    content_hash: str
    nonce: int
    p_value: float
    g_value: float
    ratio: float
    tolerance: float
    attempts: int
    elapsed_ms: float
    valid: bool
    timestamp: float
    node_id: str = ""

    @property
    def P(self) -> float:
        return self.p_value

    @property
    def G(self) -> float:
        return self.g_value if self.g_value > 0 else 0.001

    @property
    def target(self) -> float:
        return PHI_4

    def accuracy(self) -> float:
        return abs(self.ratio - PHI_4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'content_hash': self.content_hash,
            'nonce': self.nonce,
            'p_value': self.p_value,
            'g_value': self.g_value,
            'ratio': round(self.ratio, 6),
            'tolerance': self.tolerance,
            'attempts': self.attempts,
            'elapsed_ms': round(self.elapsed_ms, 3),
            'valid': self.valid,
            'timestamp': self.timestamp,
            'node_id': self.node_id,
            'P': round(self.P, 6),
            'G': round(self.G, 6),
            'target': round(self.target, 6),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BoundaryProof':
        return cls(
            content_hash=data.get('content_hash', ''),
            nonce=data.get('nonce', 0),
            p_value=data.get('p_value', data.get('P', 0)),
            g_value=data.get('g_value', data.get('G', 0)),
            ratio=data.get('ratio', 0),
            tolerance=data.get('tolerance', DEFAULT_TOLERANCE),
            attempts=data.get('attempts', 1),
            elapsed_ms=data.get('elapsed_ms', 0),
            valid=data.get('valid', False),
            timestamp=data.get('timestamp', 0),
            node_id=data.get('node_id', ''),
        )


def hash_content(content: str) -> str:
    """Hash the content using SHA3-256."""
    return hashlib.sha3_256(content.encode('utf-8')).hexdigest()


def _hash_with_nonce(content_hash: str, nonce: int) -> bytes:
    """Hash content_hash + nonce."""
    data = f"{content_hash}:{nonce}".encode('utf-8')
    return hashlib.sha3_256(data).digest()


def _split_hash(hash_bytes: bytes) -> Tuple[float, float]:
    """
    Split 32-byte hash into P (Perception) and G (Grounding).

    P_MOD = 137 x 515 = 70,555
    G_MOD = 137 x 75 = 10,275
    Mean ratio = 6.867 ~ phi^4 = 6.854
    """
    p = int.from_bytes(hash_bytes[:8], 'big') % P_MOD + 1
    g = int.from_bytes(hash_bytes[8:16], 'big') % G_MOD + 1
    return float(p), float(g)


def calculate_pob(
    content: Optional[str] = None,
    tolerance: float = DEFAULT_TOLERANCE,
    max_nonce: int = MAX_NONCE,
    node_id: str = "",
) -> BoundaryProof:
    """
    Generate a Proof-of-Boundary for given content.

    Searches for nonce where |P/G - phi^4| < tolerance.
    This is the "mining" operation for AI consensus attestation.
    """
    if content is None:
        content = f"tokenton26:{time.time()}"

    content_h = hash_content(content)
    t_start = time.time()

    best_ratio = 0.0
    best_diff = float('inf')
    best_nonce = 0
    best_p = 0.0
    best_g = 0.0

    for nonce in range(max_nonce):
        h = _hash_with_nonce(content_h, nonce)
        p, g = _split_hash(h)
        ratio = p / g
        diff = abs(ratio - PHI_4)

        if diff < best_diff:
            best_diff = diff
            best_ratio = ratio
            best_nonce = nonce
            best_p = p
            best_g = g

        if diff < tolerance:
            elapsed = (time.time() - t_start) * 1000
            return BoundaryProof(
                content_hash=content_h,
                nonce=nonce,
                p_value=p,
                g_value=g,
                ratio=ratio,
                tolerance=tolerance,
                attempts=nonce + 1,
                elapsed_ms=elapsed,
                valid=True,
                timestamp=time.time(),
                node_id=node_id,
            )

    elapsed = (time.time() - t_start) * 1000
    return BoundaryProof(
        content_hash=content_h,
        nonce=best_nonce,
        p_value=best_p,
        g_value=best_g,
        ratio=best_ratio,
        tolerance=tolerance,
        attempts=max_nonce,
        elapsed_ms=elapsed,
        valid=False,
        timestamp=time.time(),
        node_id=node_id,
    )


def verify_proof(proof: BoundaryProof, content: Optional[str] = None) -> bool:
    """
    Verify a Proof-of-Boundary. O(1) - one hash operation.

    1. If content provided, verify content_hash matches
    2. Recompute hash and verify P, G values
    3. Verify ratio is within tolerance of phi^4
    """
    if content is not None:
        expected_hash = hash_content(content)
        if proof.content_hash != expected_hash:
            return False

    h = _hash_with_nonce(proof.content_hash, proof.nonce)
    p, g = _split_hash(h)

    if abs(p - proof.p_value) > 0.001 or abs(g - proof.g_value) > 0.001:
        return False

    ratio = p / g
    if abs(ratio - PHI_4) >= proof.tolerance:
        return False

    return True


def prove_boundary(content: Optional[str] = None) -> BoundaryProof:
    """Quick function to generate a single proof."""
    return calculate_pob(content)


if __name__ == "__main__":
    print("=" * 60)
    print("PROOF-OF-BOUNDARY (POB) v2")
    print("=" * 60)

    content = "AI consensus decision: approve transaction"
    print(f"\nContent: \"{content}\"")

    proof = prove_boundary(content)
    print(f"Valid: {proof.valid}")
    print(f"Ratio: {proof.ratio:.6f} (target: {PHI_4:.6f})")
    print(f"Attempts: {proof.attempts}")
    print(f"Time: {proof.elapsed_ms:.2f}ms")

    verified = verify_proof(proof, content)
    print(f"\nVerification: {'PASS' if verified else 'FAIL'}")
