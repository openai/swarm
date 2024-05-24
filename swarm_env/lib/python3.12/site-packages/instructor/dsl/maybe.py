from pydantic import BaseModel, Field, create_model  # type: ignore - remove once Pydantic is updated
from typing import Generic, Optional, TypeVar

T = TypeVar("T", bound=BaseModel)


class MaybeBase(BaseModel, Generic[T]):
    """
    Extract a result from a model, if any, otherwise set the error and message fields.
    """

    result: Optional[T]
    error: bool = Field(default=False)
    message: Optional[str]

    def __bool__(self) -> bool:
        return self.result is not None


def Maybe(model: type[T]) -> type[MaybeBase[T]]:
    """
    Create a Maybe model for a given Pydantic model. This allows you to return a model that includes fields for `result`, `error`, and `message` for sitatations where the data may not be present in the context.

    ## Usage

    ```python
    from pydantic import BaseModel, Field
    from instructor import Maybe

    class User(BaseModel):
        name: str = Field(description="The name of the person")
        age: int = Field(description="The age of the person")
        role: str = Field(description="The role of the person")

    MaybeUser = Maybe(User)
    ```

    ## Result

    ```python
    class MaybeUser(BaseModel):
        result: Optional[User]
        error: bool = Field(default=False)
        message: Optional[str]

        def __bool__(self):
            return self.result is not None
    ```

    Parameters:
        model (Type[BaseModel]): The Pydantic model to wrap with Maybe.

    Returns:
        MaybeModel (Type[BaseModel]): A new Pydantic model that includes fields for `result`, `error`, and `message`.
    """
    return create_model(
        f"Maybe{model.__name__}",
        __base__=MaybeBase,
        reuslts=(
            Optional[model],
            Field(
                default=None,
                description="Correctly extracted result from the model, if any, otherwise None",
            ),
        ),
        error=(bool, Field(default=False)),
        message=(
            Optional[str],
            Field(
                default=None,
                description="Error message if no result was found, should be short and concise",
            ),
        ),
    )
