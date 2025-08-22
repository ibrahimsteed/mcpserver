# src/mcp_http_server.py
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from loguru import logger

from src.main import DifyMCPServer
from src.config.settings import settings
from src.utils.logger import setup_logging

class MCPHTTPServer:
    """MCP HTTP Server with SSE and Streamable HTTP transport support"""
    
    def __init__(self):
        self.app = FastAPI(
            title=f"{settings.server_name} - MCP Protocol",
            description="MCP Server supporting SSE and Streamable HTTP transports",
            version=settings.server_version
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.mcp_server = None
        self.setup_routes()
    
    def setup_routes(self):
        """Setup MCP protocol routes"""
        
        @self.app.on_event("startup")
        async def startup_event():
            setup_logging()
            self.mcp_server = DifyMCPServer()
            logger.info("MCP HTTP Server initialized")
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "transport": ["sse", "streamable_http"],
                "mcp_version": "2024-11-05"
            }
        
        # SSE Transport Endpoint
        @self.app.get("/sse")
        async def mcp_sse_endpoint(request: Request):
            """MCP Server-Sent Events transport endpoint"""
            
            async def generate():
                # Send empty stream first - no automatic messages
                # Dify will send actual MCP requests via separate HTTP calls
                try:
                    while True:
                        # Check if client disconnected
                        if await request.is_disconnected():
                            break
                        
                        # Keep connection alive with minimal overhead
                        await asyncio.sleep(30)
                        # Send empty data to keep connection alive
                        yield "data: \n\n"
                        
                except Exception as e:
                    logger.error(f"SSE stream error: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*"
                }
            )
        
        # CORS preflight for SSE
        @self.app.options("/sse")
        async def mcp_sse_options():
            """Handle CORS preflight for SSE"""
            return Response(
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Max-Age": "86400"
                }
            )
        
        # MCP SSE Request Handler
        @self.app.post("/sse")
        async def mcp_sse_request(request: Request):
            """Handle MCP protocol requests over SSE"""
            try:
                # Log raw request for debugging
                raw_body = await request.body()
                logger.info(f"Raw request body: {raw_body.decode('utf-8')}")
                
                # Parse JSON from raw body
                import json
                body = json.loads(raw_body.decode('utf-8'))
                logger.info(f"MCP SSE request received: {body}")
                
                # Handle the MCP request
                response = await self._handle_mcp_request(body)
                
                # If response is None (for notifications), return empty 200 response
                if response is None:
                    logger.info("MCP notification handled, no response needed")
                    return JSONResponse(
                        content={},
                        headers={
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Headers": "*"
                        }
                    )
                
                logger.info(f"MCP SSE response: {response}")
                return JSONResponse(
                    content=response,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "*"
                    }
                )
                
            except Exception as e:
                logger.error(f"MCP SSE request error: {e}")
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": body.get("id") if 'body' in locals() else None,
                        "error": {"code": -32603, "message": str(e)}
                    },
                    status_code=500,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "*"
                    }
                )
        
        # Streamable HTTP Transport Endpoint
        @self.app.post("/mcp")
        async def mcp_streamable_endpoint(request: Request):
            """MCP Streamable HTTP transport endpoint"""
            try:
                # Log raw request for debugging
                raw_body = await request.body()
                logger.info(f"MCP Raw request body: {raw_body.decode('utf-8')}")
                
                # Parse JSON from raw body
                import json
                body = json.loads(raw_body.decode('utf-8'))
                logger.info(f"MCP Parsed request: {body}")
                
                response = await self._handle_mcp_request(body)
                
                if response is None:
                    logger.info("MCP notification handled, returning empty response")
                    return JSONResponse(content={})
                
                logger.info(f"MCP Response: {response}")
                return JSONResponse(content=response)
            except Exception as e:
                logger.error(f"MCP Streamable HTTP error: {e}", exc_info=True)
                return JSONResponse(
                    content={"error": {"code": -32603, "message": str(e)}},
                    status_code=500
                )
        
        # Initialize endpoint
        @self.app.post("/initialize")
        async def mcp_initialize(request: Dict[str, Any]):
            """MCP Initialize handshake"""
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    }
                },
                "serverInfo": {
                    "name": settings.server_name,
                    "version": settings.server_version
                }
            }
        
        # List tools endpoint
        @self.app.post("/tools/list")
        async def mcp_list_tools():
            """List available MCP tools"""
            if not self.mcp_server:
                raise HTTPException(status_code=500, detail="Server not initialized")
            
            # Get tools from MCP server
            tools = []
            
            # Add IoT CNC tools
            tools.extend([
                {
                    "name": "get_iot_cnc_data",
                    "description": "Get CNC data records with optional filtering and pagination",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "equipment_id": {"type": "string", "description": "Filter by equipment ID"},
                            "limit": {"type": "integer", "default": 50, "description": "Number of records"},
                            "offset": {"type": "integer", "default": 0, "description": "Records to skip"}
                        }
                    }
                },
                {
                    "name": "get_iot_cnc_data_by_id",
                    "description": "Get specific CNC data record by ID",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "cnc_data_id": {"type": "string", "description": "CNC data record ID"}
                        },
                        "required": ["cnc_data_id"]
                    }
                },
                {
                    "name": "get_iot_equipment_list",
                    "description": "Get list of unique equipment IDs",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ])
            
            return {"tools": tools}
        
        # Call tool endpoint
        @self.app.post("/tools/call")
        async def mcp_call_tool(request: Dict[str, Any]):
            """Execute MCP tool call"""
            try:
                tool_name = request.get("name")
                arguments = request.get("arguments", {})
                
                if not tool_name:
                    raise HTTPException(status_code=400, detail="Missing tool name")
                
                logger.info(f"MCP tool call: {tool_name}", extra={"arguments": arguments})
                
                # Route to appropriate tool handler
                from src.tools.external_api import external_api_tools
                
                # Execute tool
                result = await external_api_tools.execute_tool(tool_name, arguments)
                
                # Return in MCP format
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": content.text
                        } for content in result
                    ]
                }
                
            except Exception as e:
                logger.error(f"MCP tool execution error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _sse_stream(self, request: Request):
        """Generate SSE stream for MCP communication"""
        try:
            # Send MCP initialization notification
            init_message = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True}
                    },
                    "serverInfo": {
                        "name": settings.server_name,
                        "version": settings.server_version
                    }
                }
            }
            yield f"data: {json.dumps(init_message)}\n\n"
            
            # Keep connection alive with minimal heartbeats
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                # Send heartbeat every 60 seconds
                await asyncio.sleep(60)
                heartbeat = {
                    "jsonrpc": "2.0",
                    "method": "notifications/ping",
                    "params": {
                        "timestamp": datetime.now().isoformat()
                    }
                }
                yield f"data: {json.dumps(heartbeat)}\n\n"
                
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            error_message = {
                "jsonrpc": "2.0",
                "method": "notifications/error", 
                "params": {"message": str(e)}
            }
            yield f"data: {json.dumps(error_message)}\n\n"
    
    async def _handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any] | None:
        """Handle MCP protocol request"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True}
                    },
                    "serverInfo": {
                        "name": settings.server_name,
                        "version": settings.server_version
                    }
                }
            elif method == "notifications/initialized":
                # Handle initialization notification - this is a notification, no response expected
                logger.info("MCP client initialized")
                return None  # Notifications don't return responses
            elif method == "notifications/ping":
                # Handle ping notification
                logger.debug("MCP ping received")
                return None  # Notifications don't return responses
            elif method == "tools/list":
                # Get tools list from external_api_tools
                from src.tools.external_api import external_api_tools
                
                # Get all available tools from the tools class
                available_tools = external_api_tools.get_tools()
                
                # Convert Tool objects to MCP format
                tools = []
                for tool in available_tools:
                    tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    })
                
                result = {"tools": tools}
            elif method == "tools/call":
                # Execute tool
                tool_name = params.get("name")
                raw_arguments = params.get("arguments", {})
                
                if not tool_name:
                    raise Exception("Missing tool name")
                
                logger.info(f"MCP tool call: {tool_name}", extra={"raw_arguments": raw_arguments, "type": type(raw_arguments)})
                
                # Handle arguments - they might come as a string or dict
                arguments = {}
                if isinstance(raw_arguments, str):
                    try:
                        if raw_arguments.strip():  # Only parse if not empty
                            arguments = json.loads(raw_arguments)
                        else:
                            arguments = {}
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse arguments JSON: {raw_arguments}")
                        raise Exception(f"Invalid JSON arguments: {e}")
                elif isinstance(raw_arguments, dict):
                    arguments = raw_arguments
                else:
                    logger.warning(f"Unexpected arguments type: {type(raw_arguments)}")
                    arguments = {}
                
                logger.info(f"Parsed arguments: {arguments}")
                
                # Route to appropriate tool handler
                from src.tools.external_api import external_api_tools
                
                # Execute tool
                result_content = await external_api_tools.execute_tool(tool_name, arguments)
                
                # Return in MCP format
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": content.text
                        } for content in result_content
                    ]
                }
            else:
                raise Exception(f"Unknown method: {method}")
            
            # Handle notifications (no response expected)
            if method and method.startswith("notifications/"):
                return None
            
            # Return response for requests
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            # Don't return error responses for notifications
            if method and method.startswith("notifications/"):
                logger.warning(f"Notification error ignored: {e}")
                return None
                
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }

# Create global app instance
mcp_http_server = MCPHTTPServer()
app = mcp_http_server.app 