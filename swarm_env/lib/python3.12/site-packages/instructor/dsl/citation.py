from pydantic import BaseModel, Field, model_validator, ValidationInfo
from collections.abc import Generator


class CitationMixin(BaseModel):
    """
    Helpful mixing that can use `validation_context={"context": context}` in `from_response` to find the span of the substring_phrase in the context.

    ## Usage

    ```python
    from pydantic import BaseModel, Field
    from instructor import CitationMixin

    class User(BaseModel):
        name: str = Field(description="The name of the person")
        age: int = Field(description="The age of the person")
        role: str = Field(description="The role of the person")


    context = "Betty was a student. Jason was a student. Jason is 20 years old"

    user = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": "Extract jason from {context}",
            },
        response_model=User,
        validation_context={"context": context},
        ]
    )

    for quote in user.substring_quotes:
        assert quote in context

    print(user.model_dump())
    ```

    ## Result
    ```
    {
        "name": "Jason Liu",
        "age": 20,
        "role": "student",
        "substring_quotes": [
            "Jason was a student",
            "Jason is 20 years old",
        ]
    }
    ```

    """

    substring_quotes: list[str] = Field(
        description="List of unique and specific substrings of the quote that was used to answer the question.",
    )

    @model_validator(mode="after")  # type: ignore[misc]
    def validate_sources(self, info: ValidationInfo) -> "CitationMixin":
        """
        For each substring_phrase, find the span of the substring_phrase in the context.
        If the span is not found, remove the substring_phrase from the list.
        """
        if info.context is None:
            return self

        # Get the context from the info
        text_chunks = info.context.get("context", None)

        # Get the spans of the substring_phrase in the context
        spans = list(self.get_spans(text_chunks))
        # Replace the substring_phrase with the actual substring
        self.substring_quotes = [text_chunks[span[0] : span[1]] for span in spans]
        return self

    def _get_span(
        self, quote: str, context: str, errs: int = 5
    ) -> Generator[tuple[int, int], None, None]:
        import regex

        minor = quote
        major = context

        errs_ = 0
        s = regex.search(f"({minor}){{e<={errs_}}}", major)
        while s is None and errs_ <= errs:
            errs_ += 1
            s = regex.search(f"({minor}){{e<={errs_}}}", major)

        if s is not None:
            yield from s.spans()

    def get_spans(self, context: str) -> Generator[tuple[int, int], None, None]:
        for quote in self.substring_quotes:
            yield from self._get_span(quote, context)
