# src/utils/validation.py
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
import re

class APIRequestModel(BaseModel):
    """Base model for API requests"""
    endpoint: str = Field(..., min_length=1, description="API endpoint")
    method: str = Field(default="GET", description="HTTP method")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Request body data")
    
    @validator('method')
    def validate_method(cls, v):
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        if v.upper() not in allowed_methods:
            raise ValueError(f'Method must be one of {allowed_methods}')
        return v.upper()
    
    @validator('endpoint')
    def validate_endpoint(cls, v):
        # Basic endpoint validation
        if not re.match(r'^[a-zA-Z0-9/_-]+$', v):
            raise ValueError('Endpoint contains invalid characters')
        return v

class EmailModel(BaseModel):
    """Model for email sending"""
    to: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    attachments: Optional[List[Dict[str, str]]] = Field(default=None)

class DataProcessingModel(BaseModel):
    """Model for data processing operations"""
    operation: str = Field(..., description="Processing operation")
    data: Dict[str, Any] = Field(..., description="Data to process")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Processing options")
    
    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['filter', 'transform', 'aggregate', 'validate', 'format']
        if v not in allowed_operations:
            raise ValueError(f'Operation must be one of {allowed_operations}')
        return v

def validate_tool_input(tool_name: str, arguments: Dict[str, Any]) -> None:
    """Validate tool input arguments"""
    validators = {
        'send_email': EmailModel,
        'process_data': DataProcessingModel,
    }
    
    # IoT CNC tools use their own schema validation, so we skip custom validation for them
    iot_cnc_tools = {
        'get_iot_cnc_data', 
        'get_iot_cnc_data_by_id', 
        'get_iot_equipment_list', 
        'search_cnc_data', 
        'get_equipment_summary'
    }
    
    if tool_name in iot_cnc_tools:
        # IoT CNC tools are validated by MCP framework using their inputSchema
        return
    
    if tool_name in validators:
        try:
            validators[tool_name](**arguments)
        except Exception as e:
            raise ValueError(f"Validation failed for {tool_name}: {str(e)}")