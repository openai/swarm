# Agent-Mesh Trust Layer for OpenAI Swarm

This contrib module adds **trust-verified handoffs** to OpenAI Swarm using the [Agent-Mesh](https://github.com/imran-siddique/agent-mesh) CMVK identity layer.

## The Problem

Swarm enables multi-agent orchestration through **handoffs** — when one agent transfers control to another. However, standard Swarm has no way to:

- Verify the receiving agent is trusted
- Prevent handoffs to malicious agents
- Audit handoff chains
- Protect sensitive context during handoffs

## The Solution

Agent-Mesh provides cryptographic identity verification via the **CMVK (Cryptographic Multi-party Verification Keys)** model. This integration:

1. **Assigns DIDs** to each Swarm agent (`did:swarm:xxx`)
2. **Verifies trust** before allowing handoffs
3. **Audits all handoffs** with full context logging
4. **Protects sensitive data** with elevated trust requirements

## Installation

```bash
pip install openai swarm
# Agent-Mesh integration is included in swarm/contrib/agentmesh/
```

## Quick Start

```python
from swarm import Agent
from swarm.contrib.agentmesh import TrustedSwarm, TrustPolicy

# Define your agents
triage_agent = Agent(
    name="Triage",
    instructions="Route requests to appropriate agent.",
    functions=[transfer_to_sales, transfer_to_support],
)

sales_agent = Agent(
    name="Sales",
    instructions="Handle sales inquiries.",
)

support_agent = Agent(
    name="Support",
    instructions="Handle support tickets.",
)

# Create trusted swarm with policy
policy = TrustPolicy(
    min_trust_score=0.5,
    blocked_targets={"UntrustedAgent"},
    audit_logging=True,
)

swarm = TrustedSwarm(policy=policy)

# Register agents with trust scores
swarm.register_agent(triage_agent, trust_score=0.8)
swarm.register_agent(sales_agent, trust_score=0.7)
swarm.register_agent(support_agent, trust_score=0.6)

# Run with trust verification
response = swarm.run(
    agent=triage_agent,
    messages=[{"role": "user", "content": "I want to buy something"}],
)
```

## Trust Policies

```python
from swarm.contrib.agentmesh import TrustPolicy

# Strict policy for sensitive operations
strict_policy = TrustPolicy(
    min_trust_score=0.7,
    allowed_targets={"ApprovedAgent1", "ApprovedAgent2"},
    sensitive_context_keys={"api_key", "password", "ssn"},
    sensitive_trust_score=0.9,
    audit_logging=True,
)

# Callback on violations
def handle_violation(from_agent, to_agent, reason):
    print(f"BLOCKED: {from_agent} -> {to_agent}: {reason}")

policy = TrustPolicy(
    on_violation=handle_violation,
)
```

## Sensitive Context Protection

When context variables contain sensitive keys, elevated trust is required:

```python
# Default: min_trust_score = 0.5
# With sensitive context: sensitive_trust_score = 0.8

response = swarm.run(
    agent=triage_agent,
    messages=[{"role": "user", "content": "Process my order"}],
    context_variables={
        "user_id": "12345",      # Normal - requires 0.5 trust
        "api_key": "secret123",  # Sensitive - requires 0.8 trust
    },
)
```

## Audit Trail

```python
# Get handoff audit log
log = swarm.verifier.get_handoff_log()

for record in log:
    print(f"{record.from_agent} -> {record.to_agent}")
    print(f"  Trust: {record.trust_score}")
    print(f"  Verified: {record.verified}")
    print(f"  Context keys: {record.context_keys}")
    print(f"  Time: {record.timestamp}")

# Trust report
report = swarm.get_trust_report()
print(f"Total handoffs: {report['handoff_count']}")
print(f"Violations: {report['violations']}")
```

## Dynamic Trust Updates

Trust scores can be adjusted based on agent behavior:

```python
# Increase trust after successful interactions
swarm.verifier.update_trust("Sales", delta=0.1)

# Decrease trust after issues
swarm.verifier.update_trust("Support", delta=-0.2)
```

## Integration with Agent-Mesh

For full CMVK identity management, use alongside the Agent-Mesh library:

```python
from agentmesh.identity import CMVKIdentity
from swarm.contrib.agentmesh import TrustedSwarm

# Create Agent-Mesh identity
identity = CMVKIdentity.generate()

# Use with Swarm
swarm = TrustedSwarm()
# ... DID verification integrates with Agent-Mesh
```

## API Reference

### TrustPolicy

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_trust_score` | float | 0.5 | Minimum trust for handoffs |
| `allowed_targets` | Set[str] | {} | Allowed target agents (empty = all) |
| `blocked_targets` | Set[str] | {} | Blocked target agents |
| `sensitive_context_keys` | Set[str] | {...} | Keys requiring elevated trust |
| `sensitive_trust_score` | float | 0.8 | Trust required for sensitive context |
| `audit_logging` | bool | True | Enable handoff logging |
| `on_violation` | Callable | None | Violation callback |

### TrustedSwarm

| Method | Description |
|--------|-------------|
| `register_agent(agent, trust_score)` | Register agent with trust score |
| `run(agent, messages, context)` | Run with trust verification |
| `get_trust_report()` | Get trust status report |

### HandoffVerifier

| Method | Description |
|--------|-------------|
| `verify_handoff(from, to, context)` | Verify handoff is allowed |
| `update_trust(agent, delta)` | Adjust trust score |
| `get_handoff_log()` | Get audit log |

## Why Trust Matters

In multi-agent systems, handoffs create attack vectors:

1. **Malicious agents** could intercept handoffs
2. **Compromised agents** could exfiltrate context
3. **Unauthorized agents** could receive privileged data

Trust verification ensures only vetted agents participate in your swarm.

## Related

- [Agent-Mesh](https://github.com/imran-siddique/agent-mesh) — Full trust/identity layer
- [OpenAI Swarm](https://github.com/openai/swarm) — Multi-agent orchestration
- [A2A Protocol](https://github.com/a2aproject/A2A) — Agent-to-Agent communication
