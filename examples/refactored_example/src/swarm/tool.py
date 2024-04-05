from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal

class Parameter(BaseModel):
    type: str
    description: Optional[str] = None
    enum: Optional[List[str]] = Field(None, alias='choices')

class Tool(BaseModel):
    name: str
    description: str
    parameters: Optional[Dict[str, Parameter]] = {}
    required: Optional[List[str]] = []
    human_input: Optional[bool] = False
