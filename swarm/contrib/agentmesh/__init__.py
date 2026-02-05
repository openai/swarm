# Copyright (c) Agent-Mesh Contributors. All rights reserved.
# Licensed under the MIT License.
"""Agent-Mesh Trust Layer for OpenAI Swarm.

Provides trusted handoffs between Swarm agents.
"""

from .trusted_handoff import (
    TrustedAgent,
    TrustPolicy,
    TrustedSwarm,
    HandoffVerifier,
    TrustViolationError,
)

__all__ = [
    "TrustedAgent",
    "TrustPolicy",
    "TrustedSwarm",
    "HandoffVerifier",
    "TrustViolationError",
]

__version__ = "0.1.0"
