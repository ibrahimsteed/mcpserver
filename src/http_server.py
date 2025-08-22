# src/http_server.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import json
from typing import Dict, Any
from datetime import datetime
import uvicorn
from src.main import DifyMCPServer
from src.config.settings import settings
from src.utils.logger import setup_logging
from loguru import logger

app = FastAPI(
    title=settings.server_name,
    description="MCP Server for Dify Integration with External APIs",
    version=settings.server_version
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global MCP server instance
mcp_server = None

@app.on_event("startup")
async def startup_event():
    """Initialize the server on startup"""
    global mcp_server
    setup_logging()
    mcp_server = DifyMCPServer()
    logger.info("HTTP MCP Server initialized")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server": settings.server_name,
        "version": settings.server_version
    }

@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "name": settings.server_name,
        "version": settings.server_version,
        "description": "MCP Server for Dify Integration",
        "endpoints": {
            "health": "/health",
            "tools": "/tools",
            "mcp": "/mcp",
            "docs": "/docs"
        }
    }

@app.get("/tools")
async def list_available_tools():
    """List all available tools"""
    if not mcp_server:
        raise HTTPException(status_code=500, detail="Server not initialized")
    
    try:
        # Get tools from all modules
        from src.tools.external_api import external_api_tools
        from src.tools.data_processor import data_processor_tools
        from src.tools.notification import notification_tools
        
        tools = []
        tools.extend(external_api_tools.get_tools())
        tools.extend(data_processor_tools.get_tools())
        tools.extend(notification_tools.get_tools())
        
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                }
                for tool in tools
            ],
            "total": len(tools)
        }
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/{tool_name}")
async def execute_tool_direct(tool_name: str, arguments: Dict[str, Any]):
    """Execute a tool directly via HTTP POST"""
    if not mcp_server:
        raise HTTPException(status_code=500, detail="Server not initialized")
    
    try:
        logger.info(f"Direct tool execution: {tool_name}", extra={"arguments": arguments})
        
        # Route to appropriate tool handler
        from src.tools.external_api import external_api_tools
        from src.tools.data_processor import data_processor_tools
        from src.tools.notification import notification_tools
        
        # IoT CNC Data API tools
        iot_cnc_tools = {
            'get_iot_cnc_data', 
            'get_iot_cnc_data_by_id', 
            'get_iot_equipment_list', 
            'search_cnc_data', 
            'get_equipment_summary'
        }
        
        if tool_name in iot_cnc_tools:
            result = await external_api_tools.execute_tool(tool_name, arguments)
        elif tool_name in ['process_data', 'convert_format', 'analyze_data']:
            result = await data_processor_tools.execute_tool(tool_name, arguments)
        elif tool_name.startswith('send_'):
            result = await notification_tools.execute_tool(tool_name, arguments)
        else:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
        
        return {
            "tool": tool_name,
            "result": [content.text for content in result],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp")
async def mcp_sse_endpoint():
    """MCP Server-Sent Events endpoint for real-time communication"""
    
    async def event_stream():
        """Generate SSE events for MCP communication"""
        try:
            # Initialize SSE connection
            yield f"data: {json.dumps({'type': 'connection', 'status': 'connected'})}\n\n"
            
            # Keep connection alive and handle MCP protocol
            while True:
                # This is a simplified SSE implementation
                # In a real implementation, you'd handle the full MCP protocol
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

@app.post("/mcp/tools")
async def mcp_tool_call(request: Dict[str, Any]):
    """Handle MCP tool calls via HTTP POST"""
    try:
        tool_name = request.get("name")
        arguments = request.get("arguments", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="Missing tool name")
        
        # Execute tool using the same logic as direct execution
        result = await execute_tool_direct(tool_name, arguments)
        
        # Return in MCP format
        return {
            "content": [
                {
                    "type": "text",
                    "text": result["result"][0] if result["result"] else "No output"
                }
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP tool call error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Development server runner
def run_development_server():
    """Run the development server"""
    uvicorn.run(
        "src.http_server:app",
        host="0.0.0.0",
        port=settings.server_port,
        reload=True,
        log_level=settings.log_level.lower()
    )

if __name__ == "__main__":
    run_development_server()