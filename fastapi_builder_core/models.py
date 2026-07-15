from pydantic import BaseModel
from typing import List

class FieldModel(BaseModel):
    name: str
    type: str
    required: bool = True

class EndpointModel(BaseModel):
    module: str
    path: str
    method: str
    summary: str
    request_fields: List[FieldModel]
    response_fields: List[FieldModel]
    require_auth: bool = False
    generate_tests: bool = False
    db_type: str = "sqlite"  
