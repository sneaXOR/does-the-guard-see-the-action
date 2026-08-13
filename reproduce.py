from __future__ import annotations

import asyncio
import json
import warnings
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module=r"agent_os(\.|$)")

from agent_os.integrations.openai_agents_sdk import GovernanceRunHooks, OpenAIAgentsKernel
from agents import Agent, Runner, function_tool, set_tracing_disabled
from agents.agent_output import AgentOutputSchemaBase
from agents.handoffs import Handoff
from agents.items import ModelResponse, TResponseInputItem, TResponseOutputItem, TResponseStreamEvent
from agents.model_settings import ModelSettings
from agents.models.interface import Model, ModelTracing
from agents.tool import Tool
from agents.tool_context import ToolContext
from agents.usage import Usage
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage, ResponseOutputText


set_tracing_disabled(True)


@dataclass(frozen=True)
class Result:
    amount: int
    framework_args: dict[str, Any]
    guard_args: dict[str, Any] | None
    blocked: bool
    ledger: list[int]


def function_call(amount: int) -> ResponseFunctionToolCall:
    return ResponseFunctionToolCall(
        id="item-1",
        call_id="call-1",
        type="function_call",
        name="transfer_funds",
        arguments=json.dumps({"amount": amount}),
    )


def final_message() -> ResponseOutputMessage:
    return ResponseOutputMessage(
        id="item-2",
        type="message",
        role="assistant",
        content=[ResponseOutputText(text="done", type="output_text", annotations=[], logprobs=[])],
        status="completed",
    )


class ScriptedModel(Model):
    """Local deterministic model: emit one tool call, then stop."""

    def __init__(self, amount: int) -> None:
        self.outputs: list[list[TResponseOutputItem]] = [[function_call(amount)], [final_message()]]

    async def get_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        conversation_id: str | None,
        prompt: Any | None,
    ) -> ModelResponse:
        del system_instructions, input, model_settings, tools, output_schema
        del handoffs, tracing, previous_response_id, conversation_id, prompt
        return ModelResponse(output=self.outputs.pop(0), usage=Usage(), response_id="local-script")

    async def stream_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None = None,
        conversation_id: str | None = None,
        prompt: Any | None = None,
    ) -> AsyncIterator[TResponseStreamEvent]:
        del system_instructions, input, model_settings, tools, output_schema
        del handoffs, tracing, previous_response_id, conversation_id, prompt
        if False:
            yield
        raise NotImplementedError


class InspectingHooks(GovernanceRunHooks):
    def __init__(self, kernel: OpenAIAgentsKernel, *, repaired: bool) -> None:
        super().__init__(kernel)
        self.repaired = repaired
        self.framework_args: dict[str, Any] | None = None
        self.guard_args: dict[str, Any] | None = None

    async def on_tool_start(self, context: Any, agent: Any, tool: Any) -> None:
        if isinstance(context, ToolContext):
            self.framework_args = json.loads(context.tool_arguments)
        self.guard_args = getattr(tool, "args", None)
        if self.repaired and self.framework_args is not None:
            tool.args = self.framework_args
        await super().on_tool_start(context, agent, tool)


async def run_case(amount: int, *, repaired: bool) -> Result:
    ledger: list[int] = []

    @function_tool
    def transfer_funds(amount: int) -> str:
        """Record an inert synthetic transfer."""
        ledger.append(amount)
        return "recorded"

    hooks = InspectingHooks(OpenAIAgentsKernel(blocked_patterns=["10000"]), repaired=repaired)
    agent = Agent(
        name="local-test-agent",
        instructions="Execute the scripted local action.",
        model=ScriptedModel(amount),
        tools=[transfer_funds],
    )

    blocked = False
    try:
        await Runner.run(agent, "Run the scripted action.", hooks=hooks)
    except Exception:
        blocked = True

    return Result(
        amount=amount,
        framework_args=hooks.framework_args or {},
        guard_args=hooks.guard_args,
        blocked=blocked,
        ledger=ledger,
    )


async def collect() -> tuple[Result, Result, Result]:
    published = await run_case(10000, repaired=False)
    repaired = await run_case(10000, repaired=True)
    benign = await run_case(50, repaired=True)
    return published, repaired, benign


def verify(published: Result, repaired: Result, benign: Result) -> None:
    assert published.framework_args == {"amount": 10000}
    assert published.guard_args is None
    assert published.blocked is False
    assert published.ledger == [10000]
    assert repaired.blocked is True
    assert repaired.ledger == []
    assert benign.blocked is False
    assert benign.ledger == [50]


async def main() -> None:
    published, repaired, benign = await collect()
    verify(published, repaired, benign)

    print("PUBLISHED INTEGRATION")
    print("agent/framework:  amount=10000")
    print(f"guard inspected:  {json.dumps(published.guard_args or {})}")
    print("guard decision:   ALLOW")
    print(f"runtime effect:   ledger={published.ledger}")
    print("result:           MISMATCH\n")
    print("REPAIR CHECK")
    print(f"dangerous 10000:  {'BLOCKED' if repaired.blocked else 'ALLOWED'}")
    print(f"benign 50:        {'BLOCKED' if benign.blocked else 'ALLOWED'}")
    print("\nNo API call. No external target. In-memory effect only.")


if __name__ == "__main__":
    asyncio.run(main())
