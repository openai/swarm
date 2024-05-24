# Future imports to ensure compatibility with Python 3.9
from __future__ import annotations

import mistralai.client
import mistralai.async_client as mistralaiasynccli
import instructor
from typing import overload, Any


@overload
def from_mistral(
    client: mistralai.client.MistralClient,
    mode: instructor.Mode = instructor.Mode.MISTRAL_TOOLS,
    **kwargs: Any,
) -> instructor.Instructor: ...


@overload
def from_mistral(
    client: mistralaiasynccli.MistralAsyncClient,
    mode: instructor.Mode = instructor.Mode.MISTRAL_TOOLS,
    **kwargs: Any,
) -> instructor.AsyncInstructor: ...


def from_mistral(
    client: mistralai.client.MistralClient | mistralaiasynccli.MistralAsyncClient,
    mode: instructor.Mode = instructor.Mode.MISTRAL_TOOLS,
    **kwargs: Any,
) -> instructor.Instructor | instructor.AsyncInstructor:
    assert mode in {
        instructor.Mode.MISTRAL_TOOLS,
    }, "Mode be one of {instructor.Mode.MISTRAL_TOOLS}"

    assert isinstance(
        client, (mistralai.client.MistralClient, mistralaiasynccli.MistralAsyncClient)
    ), "Client must be an instance of mistralai.client.MistralClient or mistralai.async_cli.MistralAsyncClient"

    if isinstance(client, mistralai.client.MistralClient):
        return instructor.Instructor(
            client=client,
            create=instructor.patch(create=client.chat, mode=mode),
            provider=instructor.Provider.MISTRAL,
            mode=mode,
            **kwargs,
        )

    else:
        return instructor.AsyncInstructor(
            client=client,
            create=instructor.patch(create=client.chat, mode=mode),
            provider=instructor.Provider.MISTRAL,
            mode=mode,
            **kwargs,
        )
