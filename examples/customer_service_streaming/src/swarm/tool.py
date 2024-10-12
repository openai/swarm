from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal


class Parameter(BaseModel):
    type: str
    description: Optional[str] = None
    enum: Optional[List[str]] = Field(None, alias='choices')


class FunctionParameters(BaseModel):
    type: Literal['object']  # Ensuring it's always 'object'
    properties: Dict[str, Parameter] = {}
    required: Optional[List[str]] = None


class FunctionTool(BaseModel):
    name: str
    description: Optional[str]
    parameters: FunctionParameters


class Tool(BaseModel):
    type: str
    function: Optional[FunctionTool]
    human_input: Optional[bool] = False
