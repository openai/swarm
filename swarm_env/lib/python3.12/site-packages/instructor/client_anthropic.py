from __future__ import annotations

import anthropic
import instructor

from typing import overload, Any


@overload
def from_anthropic(
    client: (
        anthropic.Anthropic | anthropic.AnthropicBedrock | anthropic.AnthropicVertex
    ),
    mode: instructor.Mode = instructor.Mode.ANTHROPIC_JSON,
    **kwargs: Any,
) -> instructor.Instructor: ...


@overload
def from_anthropic(
    client: (
        anthropic.AsyncAnthropic
        | anthropic.AsyncAnthropicBedrock
        | anthropic.AsyncAnthropicVertex
    ),
    mode: instructor.Mode = instructor.Mode.ANTHROPIC_JSON,
    **kwargs: Any,
) -> instructor.AsyncInstructor: ...


def from_anthropic(
    client: (
        anthropic.Anthropic
        | anthropic.AsyncAnthropic
        | anthropic.AnthropicBedrock
        | anthropic.AsyncAnthropicBedrock
        | anthropic.AsyncAnthropicVertex
        | anthropic.AnthropicVertex
    ),
    mode: instructor.Mode = instructor.Mode.ANTHROPIC_JSON,
    **kwargs: Any,
) -> instructor.Instructor | instructor.AsyncInstructor:
    assert (
        mode
        in {
            instructor.Mode.ANTHROPIC_JSON,
            instructor.Mode.ANTHROPIC_TOOLS,
        }
    ), "Mode be one of {instructor.Mode.ANTHROPIC_JSON, instructor.Mode.ANTHROPIC_TOOLS}"

    assert isinstance(
        client,
        (
            anthropic.Anthropic,
            anthropic.AsyncAnthropic,
            anthropic.AnthropicBedrock,
            anthropic.AnthropicVertex,
            anthropic.AsyncAnthropicBedrock,
            anthropic.AsyncAnthropicVertex,
        ),
    ), "Client must be an instance of {anthropic.Anthropic, anthropic.AsyncAnthropic, anthropic.AnthropicBedrock, anthropic.AsyncAnthropicBedrock,  anthropic.AnthropicVertex, anthropic.AsyncAnthropicVertex}"

    if mode == instructor.Mode.ANTHROPIC_TOOLS:
        create = client.beta.tools.messages.create  # type: ignore - unknown in stubs
    else:
        create = client.messages.create

    if isinstance(
        client,
        (anthropic.Anthropic, anthropic.AnthropicBedrock, anthropic.AnthropicVertex),
    ):
        return instructor.Instructor(
            client=client,
            create=instructor.patch(create=create, mode=mode),
            provider=instructor.Provider.ANTHROPIC,
            mode=mode,
            **kwargs,
        )

    else:
        return instructor.AsyncInstructor(
            client=client,
            create=instructor.patch(create=create, mode=mode),
            provider=instructor.Provider.ANTHROPIC,
            mode=mode,
            **kwargs,
        )
