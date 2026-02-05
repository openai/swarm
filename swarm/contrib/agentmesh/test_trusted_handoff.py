# Copyright (c) Agent-Mesh Contributors. All rights reserved.
# Licensed under the MIT License.
"""Tests for Agent-Mesh trust layer in Swarm."""

import pytest
from datetime import timezone

from swarm.contrib.agentmesh import (
    TrustedAgent,
    TrustPolicy,
    TrustedSwarm,
    HandoffVerifier,
    TrustViolationError,
)
from swarm.contrib.agentmesh.trusted_handoff import AgentIdentity, HandoffRecord


class MockAgent:
    """Mock Swarm Agent for testing."""
    
    def __init__(self, name: str, functions=None):
        self.name = name
        self.functions = functions or []
        self.instructions = f"Mock agent {name}"


class TestAgentIdentity:
    """Tests for AgentIdentity."""
    
    def test_from_agent(self):
        """Test identity creation from agent."""
        agent = MockAgent("TestAgent")
        identity = AgentIdentity.from_agent(agent)
        
        assert identity.agent_name == "TestAgent"
        assert identity.did.startswith("did:swarm:")
        assert len(identity.public_key) == 64  # SHA256 hex
        assert identity.trust_score == 0.5
    
    def test_capabilities_from_functions(self):
        """Test capabilities extracted from functions."""
        def my_function():
            pass
        
        agent = MockAgent("TestAgent", functions=[my_function])
        identity = AgentIdentity.from_agent(agent)
        
        assert "my_function" in identity.capabilities


class TestHandoffVerifier:
    """Tests for HandoffVerifier."""
    
    def test_register_agent(self):
        """Test agent registration."""
        policy = TrustPolicy()
        verifier = HandoffVerifier(policy)
        
        agent = MockAgent("TestAgent")
        identity = verifier.register_agent(agent, trust_score=0.8)
        
        assert identity.agent_name == "TestAgent"
        assert identity.trust_score == 0.8
    
    def test_verify_handoff_success(self):
        """Test successful handoff verification."""
        policy = TrustPolicy(min_trust_score=0.5)
        verifier = HandoffVerifier(policy)
        
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        verifier.register_agent(agent1, trust_score=0.7)
        verifier.register_agent(agent2, trust_score=0.7)
        
        assert verifier.verify_handoff("Agent1", "Agent2") is True
    
    def test_verify_handoff_unregistered(self):
        """Test handoff to unregistered agent fails."""
        policy = TrustPolicy()
        verifier = HandoffVerifier(policy)
        
        agent1 = MockAgent("Agent1")
        verifier.register_agent(agent1)
        
        with pytest.raises(TrustViolationError, match="not registered"):
            verifier.verify_handoff("Agent1", "UnknownAgent")
    
    def test_verify_handoff_blocked(self):
        """Test handoff to blocked agent fails."""
        policy = TrustPolicy(blocked_targets={"BlockedAgent"})
        verifier = HandoffVerifier(policy)
        
        agent1 = MockAgent("Agent1")
        blocked = MockAgent("BlockedAgent")
        verifier.register_agent(agent1)
        verifier.register_agent(blocked)
        
        with pytest.raises(TrustViolationError, match="blocked"):
            verifier.verify_handoff("Agent1", "BlockedAgent")
    
    def test_verify_handoff_low_trust(self):
        """Test handoff fails when trust too low."""
        policy = TrustPolicy(min_trust_score=0.7)
        verifier = HandoffVerifier(policy)
        
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        verifier.register_agent(agent1, trust_score=0.8)
        verifier.register_agent(agent2, trust_score=0.5)  # Below threshold
        
        with pytest.raises(TrustViolationError, match="Trust score"):
            verifier.verify_handoff("Agent1", "Agent2")
    
    def test_sensitive_context_requires_higher_trust(self):
        """Test sensitive context requires elevated trust."""
        policy = TrustPolicy(
            min_trust_score=0.5,
            sensitive_trust_score=0.9,
            sensitive_context_keys={"api_key"},
        )
        verifier = HandoffVerifier(policy)
        
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        verifier.register_agent(agent1, trust_score=0.9)
        verifier.register_agent(agent2, trust_score=0.7)  # Above 0.5, below 0.9
        
        # Normal context works
        verifier.verify_handoff("Agent1", "Agent2", {"user_id": "123"})
        
        # Sensitive context fails
        with pytest.raises(TrustViolationError):
            verifier.verify_handoff("Agent1", "Agent2", {"api_key": "secret"})
    
    def test_update_trust(self):
        """Test trust score updates."""
        policy = TrustPolicy()
        verifier = HandoffVerifier(policy)
        
        agent = MockAgent("Agent1")
        verifier.register_agent(agent, trust_score=0.5)
        
        verifier.update_trust("Agent1", delta=0.3)
        assert verifier._identities["Agent1"].trust_score == 0.8
        
        # Test clamping at 1.0
        verifier.update_trust("Agent1", delta=0.5)
        assert verifier._identities["Agent1"].trust_score == 1.0
        
        # Test clamping at 0.0
        verifier.update_trust("Agent1", delta=-2.0)
        assert verifier._identities["Agent1"].trust_score == 0.0
    
    def test_handoff_logging(self):
        """Test audit logging."""
        policy = TrustPolicy(audit_logging=True)
        verifier = HandoffVerifier(policy)
        
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        verifier.register_agent(agent1)
        verifier.register_agent(agent2)
        
        verifier.verify_handoff("Agent1", "Agent2", {"ctx": "value"})
        
        log = verifier.get_handoff_log()
        assert len(log) == 1
        assert log[0].from_agent == "Agent1"
        assert log[0].to_agent == "Agent2"
        assert log[0].verified is True
        assert "ctx" in log[0].context_keys
        assert log[0].timestamp.tzinfo == timezone.utc
    
    def test_violation_callback(self):
        """Test violation callback is called."""
        violations = []
        
        def on_violation(from_agent, to_agent, reason):
            violations.append((from_agent, to_agent, reason))
        
        policy = TrustPolicy(on_violation=on_violation)
        verifier = HandoffVerifier(policy)
        
        agent1 = MockAgent("Agent1")
        verifier.register_agent(agent1)
        
        with pytest.raises(TrustViolationError):
            verifier.verify_handoff("Agent1", "Unknown")
        
        assert len(violations) == 1
        assert violations[0][0] == "Agent1"
        assert violations[0][1] == "Unknown"


class TestTrustedAgent:
    """Tests for TrustedAgent."""
    
    def test_wrap_agent(self):
        """Test agent wrapping."""
        policy = TrustPolicy()
        verifier = HandoffVerifier(policy)
        
        agent = MockAgent("TestAgent")
        trusted = TrustedAgent(agent, verifier, trust_score=0.8)
        
        assert trusted.name == "TestAgent"
        assert trusted.identity.trust_score == 0.8
    
    def test_passthrough_attributes(self):
        """Test attribute passthrough to wrapped agent."""
        policy = TrustPolicy()
        verifier = HandoffVerifier(policy)
        
        agent = MockAgent("TestAgent")
        agent.custom_attr = "custom_value"
        
        trusted = TrustedAgent(agent, verifier)
        
        assert trusted.custom_attr == "custom_value"


class TestTrustedSwarm:
    """Tests for TrustedSwarm."""
    
    def test_register_agent(self):
        """Test agent registration."""
        swarm = TrustedSwarm()
        
        agent = MockAgent("TestAgent")
        trusted = swarm.register_agent(agent, trust_score=0.8)
        
        assert trusted.name == "TestAgent"
        assert "TestAgent" in swarm._agents
    
    def test_trust_report(self):
        """Test trust report generation."""
        swarm = TrustedSwarm()
        
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        swarm.register_agent(agent1, trust_score=0.8)
        swarm.register_agent(agent2, trust_score=0.6)
        
        report = swarm.get_trust_report()
        
        assert "Agent1" in report["agents"]
        assert "Agent2" in report["agents"]
        assert report["agents"]["Agent1"]["trust_score"] == 0.8
        assert report["agents"]["Agent2"]["trust_score"] == 0.6
        assert report["handoff_count"] == 0
        assert report["violations"] == 0
    
    def test_allowed_targets_only(self):
        """Test only allowed targets can receive handoffs."""
        policy = TrustPolicy(allowed_targets={"Allowed"})
        swarm = TrustedSwarm(policy=policy)
        
        allowed = MockAgent("Allowed")
        blocked = MockAgent("NotAllowed")
        swarm.register_agent(allowed)
        swarm.register_agent(blocked)
        
        # Allowed works
        swarm.verifier.verify_handoff("Any", "Allowed")
        
        # Not in allowed list fails
        with pytest.raises(TrustViolationError, match="not in allowed"):
            swarm.verifier.verify_handoff("Any", "NotAllowed")


class TestTrustPolicy:
    """Tests for TrustPolicy."""
    
    def test_default_sensitive_keys(self):
        """Test default sensitive context keys."""
        policy = TrustPolicy()
        
        assert "password" in policy.sensitive_context_keys
        assert "api_key" in policy.sensitive_context_keys
        assert "token" in policy.sensitive_context_keys
    
    def test_custom_sensitive_keys(self):
        """Test custom sensitive context keys."""
        policy = TrustPolicy(
            sensitive_context_keys={"custom_secret", "private_data"}
        )
        
        assert "custom_secret" in policy.sensitive_context_keys
        assert "private_data" in policy.sensitive_context_keys
        assert "password" not in policy.sensitive_context_keys


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
