from __future__ import annotations

from typing import overload, Any

import groq
import instructor


@overload
def from_groq(
    client: groq.Groq,
    mode: instructor.Mode = instructor.Mode.TOOLS,
    **kwargs: Any,
) -> instructor.Instructor: ...


@overload
def from_groq(
    client: groq.AsyncGroq,
    mode: instructor.Mode = instructor.Mode.TOOLS,
    **kwargs: Any,
) -> instructor.Instructor: ...


def from_groq(
    client: groq.Groq | groq.AsyncGroq,
    mode: instructor.Mode = instructor.Mode.TOOLS,
    **kwargs: Any,
) -> instructor.Instructor:
    assert mode in {
        instructor.Mode.JSON,
        instructor.Mode.TOOLS,
    }, "Mode be one of {instructor.Mode.JSON, instructor.Mode.TOOLS}"

    assert isinstance(
        client, (groq.Groq, groq.AsyncGroq)
    ), "Client must be an instance of groq.GROQ"

    if isinstance(client, groq.Groq):
        return instructor.Instructor(
            client=client,
            create=instructor.patch(create=client.chat.completions.create, mode=mode),
            provider=instructor.Provider.GROQ,
            mode=mode,
            **kwargs,
        )

    else:
        return instructor.Instructor(
            client=client,
            create=instructor.patch(create=client.chat.completions.create, mode=mode),
            provider=instructor.Provider.GROQ,
            mode=mode,
            **kwargs,
        )
