# OSOP Workflow Examples for Swarm

[OSOP](https://github.com/osopcloud/osop-spec) (Open Standard for Orchestration Protocols) is a portable YAML format for describing multi-agent workflows — think OpenAPI, but for agent orchestration.

## What's Here

| File | Description |
|------|-------------|
| `swarm-customer-service.osop.yaml` | Customer service with triage agent routing to billing, technical, and sales specialists — with human escalation fallback |

## Why OSOP?

Swarm's lightweight agent handoff pattern is elegant and powerful. OSOP provides a **framework-agnostic way to describe** those handoff patterns so they can be:

- **Documented** — readable YAML that non-developers can understand
- **Validated** — check workflow structure before running it
- **Ported** — same workflow definition works across Swarm, AutoGen, CrewAI, etc.
- **Visualized** — render the workflow as a graph in the [OSOP Editor](https://github.com/osopcloud/osop-editor)

## Quick Start

```bash
# Validate the workflow
pip install osop
osop validate swarm-customer-service.osop.yaml

# Or just read the YAML — it's self-documenting
cat swarm-customer-service.osop.yaml
```

## How It Maps to Swarm

| OSOP Concept | Swarm Equivalent |
|---|---|
| `node` with `type: agent, subtype: coordinator` | Triage `Agent` with handoff functions |
| `node` with `type: agent, subtype: worker` | Specialist `Agent` |
| `edge` with `mode: conditional` | Handoff function return |
| `edge` with `mode: fallback` | Escalation handoff |
| `runtime.config.tools` | Agent `functions` list |

## Learn More

- [OSOP Spec](https://github.com/osopcloud/osop-spec) — full specification
- [OSOP Examples](https://github.com/osopcloud/osop-examples) — 30+ workflow templates
- [OSOP Editor](https://github.com/osopcloud/osop-editor) — visual workflow editor
