class IncompleteOutputException(Exception):
    """Exception raised when the output from LLM is incomplete due to max tokens limit reached."""

    def __init__(
        self,
        message: str = "The output is incomplete due to a max_tokens length limit.",
    ) -> None:
        self.message = message
        super().__init__(self.message)
