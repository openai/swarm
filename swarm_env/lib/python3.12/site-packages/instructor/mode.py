import enum
import warnings


class Mode(enum.Enum):
    """The mode to use for patching the client"""

    FUNCTIONS = "function_call"
    PARALLEL_TOOLS = "parallel_tool_call"
    TOOLS = "tool_call"
    MISTRAL_TOOLS = "mistral_tools"
    JSON = "json_mode"
    MD_JSON = "markdown_json_mode"
    JSON_SCHEMA = "json_schema_mode"
    ANTHROPIC_TOOLS = "anthropic_tools"
    ANTHROPIC_JSON = "anthropic_json"
    COHERE_TOOLS = "cohere_tools"

    def __new__(cls, value: str) -> "Mode":
        member = object.__new__(cls)
        member._value_ = value

        # Deprecation warning for FUNCTIONS
        if value == "function_call":
            warnings.warn(
                "FUNCTIONS is deprecated and will be removed in future versions",
                DeprecationWarning,
                stacklevel=2,
            )

        return member
