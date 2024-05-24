from typing import Callable, Optional

from openai import OpenAI
from pydantic import Field

from instructor.function_calls import OpenAISchema
from instructor.client import Instructor


class Validator(OpenAISchema):
    """
    Validate if an attribute is correct and if not,
    return a new value with an error message
    """

    is_valid: bool = Field(
        default=True,
        description="Whether the attribute is valid based on the requirements",
    )
    reason: Optional[str] = Field(
        default=None,
        description="The error message if the attribute is not valid, otherwise None",
    )
    fixed_value: Optional[str] = Field(
        default=None,
        description="If the attribute is not valid, suggest a new value for the attribute",
    )


def llm_validator(
    statement: str,
    client: Instructor,
    allow_override: bool = False,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0,
) -> Callable[[str], str]:
    """
    Create a validator that uses the LLM to validate an attribute

    ## Usage

    ```python
    from instructor import llm_validator
    from pydantic import BaseModel, Field, field_validator

    class User(BaseModel):
        name: str = Annotated[str, llm_validator("The name must be a full name all lowercase")
        age: int = Field(description="The age of the person")

    try:
        user = User(name="Jason Liu", age=20)
    except ValidationError as e:
        print(e)
    ```

    ```
    1 validation error for User
    name
        The name is valid but not all lowercase (type=value_error.llm_validator)
    ```

    Note that there, the error message is written by the LLM, and the error type is `value_error.llm_validator`.

    Parameters:
        statement (str): The statement to validate
        model (str): The LLM to use for validation (default: "gpt-3.5-turbo-0613")
        temperature (float): The temperature to use for the LLM (default: 0)
        openai_client (OpenAI): The OpenAI client to use (default: None)
    """

    def llm(v: str) -> str:
        resp = client.chat.completions.create(
            response_model=Validator,
            messages=[
                {
                    "role": "system",
                    "content": "You are a world class validation model. Capable to determine if the following value is valid for the statement, if it is not, explain why and suggest a new value.",
                },
                {
                    "role": "user",
                    "content": f"Does `{v}` follow the rules: {statement}",
                },
            ],
            model=model,
            temperature=temperature,
        )

        # If the response is  not valid, return the reason, this could be used in
        # the future to generate a better response, via reasking mechanism.
        assert resp.is_valid, resp.reason

        if allow_override and not resp.is_valid and resp.fixed_value is not None:
            # If the value is not valid, but we allow override, return the fixed value
            return resp.fixed_value
        return v

    return llm


def openai_moderation(client: OpenAI) -> Callable[[str], str]:
    """
    Validates a message using OpenAI moderation model.

    Should only be used for monitoring inputs and outputs of OpenAI APIs
    Other use cases are disallowed as per:
    https://platform.openai.com/docs/guides/moderation/overview

    Example:
    ```python
    from instructor import OpenAIModeration

    class Response(BaseModel):
        message: Annotated[str, AfterValidator(OpenAIModeration(openai_client=client))]

    Response(message="I hate you")
    ```

    ```
     ValidationError: 1 validation error for Response
     message
    Value error, `I hate you.` was flagged for ['harassment'] [type=value_error, input_value='I hate you.', input_type=str]
    ```

    client (OpenAI): The OpenAI client to use, must be sync (default: None)
    """

    def validate_message_with_openai_mod(v: str) -> str:
        response = client.moderations.create(input=v)
        out = response.results[0]
        cats = out.categories.model_dump()
        if out.flagged:
            raise ValueError(
                f"`{v}` was flagged for {', '.join(cat for cat in cats if cats[cat])}"
            )

        return v

    return validate_message_with_openai_mod
