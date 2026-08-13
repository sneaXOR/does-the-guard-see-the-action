# Does the guard see the action that actually runs?

This is a small, runnable investigation of one question: when an agent uses a tool, does the security check see the same arguments as the tool that actually runs?

```text
agent asks:       transfer_funds(amount=10000)
guard checks:     transfer_funds({})
runtime executes: transfer_funds(amount=10000)
```

In this reproduction, the security rule is reasonable for the input it receives. The problem is that it receives the wrong input.

This uses a public integration between Microsoft Agent Governance Toolkit 5.0.0 and OpenAI Agents SDK 0.19.4.

Pinned source context: Microsoft Agent Governance Toolkit commit `81955d48025c6b11deb3fc9dabf89f74f4145775`. The install itself uses the published `5.0.0` packages.

## What you get in one minute

Run the reproduction after setup and you will see:

```text
PUBLISHED INTEGRATION
agent/framework:  amount=10000
guard inspected:  {}
guard decision:   ALLOW
runtime effect:   ledger=[10000]
result:           MISMATCH

REPAIR CHECK
dangerous 10000:  BLOCKED
benign 50:        ALLOWED
```

That is the whole claim. The guard allowed a transfer because it inspected `{}`, while the runtime executed `amount=10000`. The narrow repaired path gives the guard the arguments already available in the SDK hook, blocks the dangerous case, and preserves a benign transfer.

## Run it

Windows PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
.\.venv\Scripts\python.exe .\reproduce.py
.\.venv\Scripts\python.exe -m unittest -v
```

No API key or external service is used. The model is scripted locally. The only side effect is an in-memory list.

## What is running

```text
scripted local model
  -> real OpenAI Agents Runner
  -> Microsoft governance hook
  -> real policy decision
  -> inert transfer tool
```

The reproducer records the arguments at the framework hook, the arguments inspected by the governance integration, the decision, and the final ledger.

## Why this matters

Agent security increasingly relies on controlling tool calls at runtime. A control is only useful if it evaluates the action that will actually execute. This is related to established security ideas such as complete mediation and policy enforcement points.

The exact integration issue does not have a standard name. I call the property being tested "action fidelity at the policy boundary."

See [RESEARCH.md](RESEARCH.md) for the supporting work and the limits of the claim.

## Limits

- This is one public compatibility reproduction, not a universal scanner.
- It does not show that Fabraix or other agent systems have the same issue.
- It does not estimate how common this failure mode is.
- The repair is a discriminating control, not a proposed upstream patch.
- No production action, account, network target or real money is involved.
