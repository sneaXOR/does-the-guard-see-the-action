# Why this is a real security question

The exact reproduced integration behavior does not have a single canonical vulnerability name. It sits at the intersection of established security properties and newer work on tool-using agents.

## Established model

Access-control systems commonly separate a Policy Enforcement Point, which intercepts and transforms a request, from a Policy Decision Point, which evaluates it. If the enforcement point sends an incomplete request, a correct policy can return the wrong outcome for the real action.

- [A Formal Validation Approach for XACML 3.0 Access Control Policy](https://pmc.ncbi.nlm.nih.gov/articles/PMC9026700/)

The related complete-mediation principle says security-sensitive operations must be mediated by the reference monitor. This reproduction asks a practical follow-up: was the mediated action faithfully represented?

## Agent-specific evidence

Recent systems place enforcement directly at the agent tool-call boundary:

- [Runtime Policy Enforcement for MCP-Based LLM Agents](https://www.mdpi.com/2079-9292/15/13/2829)
- [ToolGuardian: Declarative Security for AI Agent-Tool Interactions](https://arxiv.org/abs/2607.21835)
- [Towards Verifiably Safe Tool Use for LLM Agents](https://arxiv.org/abs/2601.08012)

AgentDojo also evaluates security and utility through realistic tool execution rather than treating model text alone as the system outcome:

- [AgentDojo](https://arxiv.org/abs/2406.13352)

TOCTOU work on LLM agents is adjacent evidence that the continuity between a security check and later execution deserves explicit testing. It is not the same failure as the argument loss reproduced here:

- [Mind the Gap: Time-of-Check to Time-of-Use Vulnerabilities in LLM-Enabled Agents](https://arxiv.org/abs/2508.17155)

## Exact claim

This repository proves one thing: under the pinned public packages, the real runner carries `amount=10000`, the published governance hook evaluates an empty argument object, and the tool executes with `amount=10000`. A narrow context-aware control blocks the dangerous case and preserves a benign case.

It does not establish prevalence, exploitability in a deployed service, scientific novelty or a weakness in any private product.
