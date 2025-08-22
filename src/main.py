import asyncio
import sys
from typing import Any, Sequence
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    Resource,
    Prompt,
    PromptMessage,
    INVALID_PARAMS,
    INTERNAL_ERROR
)
from loguru import logger

# Import our tool modules
from src.tools.external_api import external_api_tools
from src.tools.data_processor import data_processor_tools  
from src.tools.notification import notification_tools
from src.utils.logger import setup_logging
from src.config.settings import settings

class DifyMCPServer:
    """Main MCP Server for Dify integration"""
    
    def __init__(self):
        self.server = Server(settings.server_name)
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all MCP request handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools"""
            tools = []
            tools.extend(external_api_tools.get_tools())
            tools.extend(data_processor_tools.get_tools())
            tools.extend(notification_tools.get_tools())
            
            logger.info(f"Listed {len(tools)} available tools")
            return tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
            """Execute a tool"""
            try:
                logger.info(f"Calling tool: {name}", extra={"arguments": arguments})
                
                # Route to appropriate tool handler
                if name.startswith('api_'):
                    result = await external_api_tools.execute_tool(name, arguments)
                elif name in ['process_data', 'convert_format', 'analyze_data']:
                    result = await data_processor_tools.execute_tool(name, arguments)
                elif name.startswith('send_'):
                    result = await notification_tools.execute_tool(name, arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                logger.info(f"Tool {name} executed successfully")
                return result
                
            except ValueError as e:
                logger.error(f"Invalid parameters for tool {name}: {e}")
                raise INVALID_PARAMS(str(e))
            except Exception as e:
                logger.error(f"Internal error executing tool {name}: {e}")
                raise INTERNAL_ERROR(str(e))
        
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """List available resources"""
            return [
                Resource(
                    uri="config://server",
                    name="Server Configuration",
                    description="Current server configuration and status",
                    mimeType="application/json"
                ),
                Resource(
                    uri="logs://recent",
                    name="Recent Logs",
                    description="Recent server logs and activities",
                    mimeType="text/plain"
                ),
                Resource(
                    uri="api://schema",
                    name="API Schema",
                    description="External API schema and documentation",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a resource"""
            try:
                if uri == "config://server":
                    import json
                    config_data = {
                        "server_name": settings.server_name,
                        "server_version": settings.server_version,
                        "api_base_url": str(settings.external_api_base_url),
                        "uptime": "N/A",  # Could be calculated
                        "status": "running"
                    }
                    return json.dumps(config_data, indent=2)
                
                elif uri == "logs://recent":
                    # Read recent logs (simplified)
                    try:
                        with open("logs/app.log", "r") as f:
                            lines = f.readlines()
                            return "".join(lines[-100:])  # Last 100 lines
                    except FileNotFoundError:
                        return "No recent logs available"
                
                elif uri == "api://schema":
                    # Return API schema information
                    schema = {
                        "base_url": str(settings.external_api_base_url),
                        "authentication": "Bearer token",
                        "available_endpoints": [
                            "GET /users/{id}",
                            "POST /users",
                            "GET /search",
                            "PUT /users/{id}",
                            "DELETE /users/{id}"
                        ],
                        "rate_limit": settings.external_api_rate_limit
                    }
                    import json
                    return json.dumps(schema, indent=2)
                
                else:
                    raise ValueError(f"Unknown resource: {uri}")
                    
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                raise INTERNAL_ERROR(f"Failed to read resource: {e}")
        
        @self.server.list_prompts()
        async def list_prompts() -> list[Prompt]:
            """List available prompts"""
            return [
                Prompt(
                    name="api_data_analysis",
                    description="Analyze data retrieved from external API",
                    arguments=[
                        {
                            "name": "data",
                            "description": "Data to analyze",
                            "required": True
                        },
                        {
                            "name": "focus",
                            "description": "Analysis focus area",
                            "required": False
                        }
                    ]
                ),
                Prompt(
                    name="generate_report",
                    description="Generate a report based on processed data",
                    arguments=[
                        {
                            "name": "data",
                            "description": "Processed data",
                            "required": True
                        },
                        {
                            "name": "report_type",
                            "description": "Type of report",
                            "required": False
                        }
                    ]
                ),
                Prompt(
                    name="error_analysis",
                    description="Analyze and provide solutions for errors",
                    arguments=[
                        {
                            "name": "error_details",
                            "description": "Error information",
                            "required": True
                        }
                    ]
                )
            ]
        
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: dict[str, str]) -> dict[str, Any]:
            """Get a specific prompt"""
            try:
                if name == "api_data_analysis":
                    data = arguments.get("data", "")
                    focus = arguments.get("focus", "general insights")
                    
                    return {
                        "description": "Analyze API data and provide insights",
                        "messages": [
                            PromptMessage(
                                role="system",
                                content=TextContent(
                                    type="text",
                                    text="You are a data analyst. Analyze the provided API data and provide actionable insights with focus on the specified area."
                                )
                            ),
                            PromptMessage(
                                role="user",
                                content=TextContent(
                                    type="text",
                                    text=f"Please analyze this API data with focus on {focus}:\n\n{data}\n\nProvide key insights, patterns, and recommendations."
                                )
                            )
                        ]
                    }
                
                elif name == "generate_report":
                    data = arguments.get("data", "")
                    report_type = arguments.get("report_type", "summary")
                    
                    return {
                        "description": "Generate a comprehensive report",
                        "messages": [
                            PromptMessage(
                                role="system",
                                content=TextContent(
                                    type="text",
                                    text=f"You are a report generator. Create a detailed {report_type} report based on the provided data."
                                )
                            ),
                            PromptMessage(
                                role="user",
                                content=TextContent(
                                    type="text",
                                    text=f"Generate a {report_type} report based on this data:\n\n{data}\n\nInclude executive summary, key findings, and recommendations."
                                )
                            )
                        ]
                    }
                
                elif name == "error_analysis":
                    error_details = arguments.get("error_details", "")
                    
                    return {
                        "description": "Analyze errors and provide solutions",
                        "messages": [
                            PromptMessage(
                                role="system",
                                content=TextContent(
                                    type="text",
                                    text="You are a technical troubleshooter. Analyze the error details and provide practical solutions."
                                )
                            ),
                            PromptMessage(
                                role="user",
                                content=TextContent(
                                    type="text",
                                    text=f"Analyze this error and provide solutions:\n\n{error_details}\n\nInclude root cause analysis and step-by-step resolution."
                                )
                            )
                        ]
                    }
                
                else:
                    raise ValueError(f"Unknown prompt: {name}")
                    
            except Exception as e:
                logger.error(f"Error getting prompt {name}: {e}")
                raise INTERNAL_ERROR(f"Failed to get prompt: {e}")

    async def run(self):
        """Run the MCP server"""
        logger.info(f"Starting {settings.server_name} v{settings.server_version}")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    
    # Log startup information
    logger.info("Initializing Dify MCP Server")
    logger.info(f"External API: {settings.external_api_base_url}")
    logger.info(f"Log Level: {settings.log_level}")
    
    # Create and run server
    server = DifyMCPServer()
    await server.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)