# src/tools/external_api.py
from typing import List, Dict, Any
from mcp.types import Tool, TextContent
from loguru import logger
from src.utils.http_client import http_client
from src.utils.validation import validate_tool_input

class ExternalAPITools:
    """Tools for interacting with IoT CNC Data API"""
    
    def get_tools(self) -> List[Tool]:
        """Return list of available IoT CNC API tools"""
        return [
            Tool(
                name="get_iot_cnc_data",
                description="Get CNC data records with optional filtering and pagination",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "equipment_id": {
                            "type": "string",
                            "description": "Filter results by specific equipment ID (optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 50,
                            "minimum": 1,
                            "maximum": 1000,
                            "description": "Number of records to return (default: 50, max: 1000)"
                        },
                        "offset": {
                            "type": "integer",
                            "default": 0,
                            "minimum": 0,
                            "description": "Number of records to skip for pagination (default: 0)"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_iot_cnc_data_by_id",
                description="Get a specific CNC data record by its ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cnc_data_id": {
                            "type": "string",
                            "description": "The ID of the CNC data record to retrieve"
                        }
                    },
                    "required": ["cnc_data_id"]
                }
            ),
            Tool(
                name="get_iot_equipment_list",
                description="Get a list of unique equipment IDs from all CNC data records",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="search_cnc_data",
                description="Advanced search for CNC data with multiple filters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "equipment_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of equipment IDs to filter by"
                        },
                        "operation_mode": {
                            "type": "string",
                            "enum": ["AUTO", "MANUAL"],
                            "description": "Filter by operation mode"
                        },
                        "has_alarm": {
                            "type": "boolean",
                            "description": "Filter records with or without alarms"
                        },
                        "min_workpiece_count": {
                            "type": "integer",
                            "description": "Minimum workpiece count filter"
                        },
                        "date_from": {
                            "type": "string",
                            "description": "Filter records from this date (YYYY-MM-DD format)"
                        },
                        "date_to": {
                            "type": "string",
                            "description": "Filter records to this date (YYYY-MM-DD format)"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 50,
                            "minimum": 1,
                            "maximum": 1000,
                            "description": "Number of records to return"
                        },
                        "offset": {
                            "type": "integer",
                            "default": 0,
                            "minimum": 0,
                            "description": "Number of records to skip for pagination"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_equipment_summary",
                description="Get summary statistics for specific equipment",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "equipment_id": {
                            "type": "string",
                            "description": "Equipment ID to get summary for"
                        },
                        "date_from": {
                            "type": "string",
                            "description": "Start date for summary (YYYY-MM-DD format)"
                        },
                        "date_to": {
                            "type": "string", 
                            "description": "End date for summary (YYYY-MM-DD format)"
                        }
                    },
                    "required": ["equipment_id"]
                }
            )
        ]
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute the specified tool"""
        try:
            logger.info(f"Executing IoT CNC tool: {name}", extra={"arguments": arguments, "arguments_type": type(arguments)})
            
            # Ensure arguments is a dict
            if not isinstance(arguments, dict):
                logger.warning(f"Arguments is not a dict, converting: {arguments}")
                arguments = {}
            
            # Validate input
            validate_tool_input(name, arguments)
            
            if name == "get_iot_cnc_data":
                return await self._get_iot_cnc_data(arguments)
            elif name == "get_iot_cnc_data_by_id":
                return await self._get_iot_cnc_data_by_id(arguments)
            elif name == "get_iot_equipment_list":
                return await self._get_iot_equipment_list(arguments)
            elif name == "search_cnc_data":
                return await self._search_cnc_data(arguments)
            elif name == "get_equipment_summary":
                return await self._get_equipment_summary(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.error(f"Tool execution failed: {name}", extra={"error": str(e)})
            return [TextContent(
                type="text",
                text=f"Error executing {name}: {str(e)}"
            )]
    
    async def _get_iot_cnc_data(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get CNC data with optional filtering and pagination"""
        params = {}
        
        if args.get("equipment_id"):
            params["equipment_id"] = args["equipment_id"]
        if args.get("limit"):
            params["limit"] = args["limit"]
        if args.get("offset"):
            params["offset"] = args["offset"]
        
        try:
            # Log the request details for debugging
            logger.info(f"Making HTTP request to endpoint: get_iot_cnc_data", extra={"params": params})
            response = await http_client.get("get_iot_cnc_data", params=params)
            logger.info(f"HTTP response received", extra={"status": "success", "response_keys": list(response.keys())})
            
            # Extract data from Frappe response format
            message = response.get("message", {})
            if message.get("success"):
                data = message.get("data", [])
                total_count = message.get("total_count", len(data))
                returned_count = message.get("returned_count", len(data))
                
                return [TextContent(
                    type="text",
                    text=f"CNC Data Retrieved ({returned_count} of {total_count} records):\n```json\n{data}\n```"
                )]
            else:
                error_msg = message.get("message", "Unknown error")
                raise Exception(f"API returned error: {error_msg}")
            
        except Exception as e:
            raise Exception(f"Failed to get CNC data: {str(e)}")
    
    async def _get_iot_cnc_data_by_id(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get specific CNC data record by ID"""
        cnc_data_id = args["cnc_data_id"]
        
        params = {"cnc_data_id": cnc_data_id}
        
        try:
            # Log the request details for debugging
            logger.info(f"Making HTTP request to endpoint: get_iot_cnc_data_by_id", extra={"params": params})
            response = await http_client.get("get_iot_cnc_data_by_id", params=params)
            
            # Extract data from Frappe response format
            message = response.get("message", {})
            if message.get("success"):
                data = message.get("data", {})
                
                return [TextContent(
                    type="text",
                    text=f"CNC Data Record (ID: {cnc_data_id}):\n```json\n{data}\n```"
                )]
            else:
                error_msg = message.get("message", "Unknown error")
                raise Exception(f"API returned error: {error_msg}")
            
        except Exception as e:
            raise Exception(f"Failed to get CNC data by ID {cnc_data_id}: {str(e)}")
    
    async def _get_iot_equipment_list(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get list of unique equipment IDs"""
        try:
            # Log the request details for debugging
            logger.info(f"Making HTTP request to endpoint: get_iot_equipment_list", extra={"params": {}})
            response = await http_client.get("get_iot_equipment_list")
            
            # Extract data from Frappe response format
            message = response.get("message", {})
            if message.get("success"):
                equipment_list = message.get("data", [])
                count = message.get("count", len(equipment_list))
                
                return [TextContent(
                    type="text",
                    text=f"Equipment List ({count} unique equipment IDs):\n```json\n{equipment_list}\n```"
                )]
            else:
                error_msg = message.get("message", "Unknown error")
                raise Exception(f"API returned error: {error_msg}")
            
        except Exception as e:
            raise Exception(f"Failed to get equipment list: {str(e)}")
    
    async def _search_cnc_data(self, args: Dict[str, Any]) -> List[TextContent]:
        """Advanced search for CNC data with multiple filters"""
        # Build search parameters
        params = {}
        
        # Add filters from arguments
        if args.get("equipment_ids"):
            # For multiple equipment IDs, we'll need to make multiple calls or use the base method
            equipment_ids = args["equipment_ids"]
            if len(equipment_ids) == 1:
                params["equipment_id"] = equipment_ids[0]
            else:
                # Multiple IDs - we'll use the first one and note the limitation
                params["equipment_id"] = equipment_ids[0]
                logger.warning(f"Multiple equipment IDs provided, using first one: {equipment_ids[0]}")
        
        if args.get("limit"):
            params["limit"] = args["limit"]
        if args.get("offset"):
            params["offset"] = args["offset"]
        
        try:
            response = await http_client.get("get_iot_cnc_data", params=params)
            
            # Extract and filter data from Frappe response
            message = response.get("message", {})
            if message.get("success"):
                data = message.get("data", [])
                
                # Apply additional client-side filters
                filtered_data = self._apply_search_filters(data, args)
                
                return [TextContent(
                    type="text",
                    text=f"Filtered CNC Data ({len(filtered_data)} records found):\n```json\n{filtered_data}\n```"
                )]
            else:
                error_msg = message.get("message", "Unknown error")
                raise Exception(f"API returned error: {error_msg}")
            
        except Exception as e:
            raise Exception(f"Failed to search CNC data: {str(e)}")
    
    async def _get_equipment_summary(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get summary statistics for specific equipment"""
        equipment_id = args["equipment_id"]
        
        # Get all data for the equipment first
        params = {"equipment_id": equipment_id, "limit": 1000}
        
        try:
            response = await http_client.get("get_iot_cnc_data", params=params)
            
            # Extract data from Frappe response format
            message = response.get("message", {})
            if message.get("success"):
                data = message.get("data", [])
                
                # Calculate summary statistics
                summary = self._calculate_equipment_summary(data, args)
                
                return [TextContent(
                    type="text",
                    text=f"Equipment Summary for {equipment_id}:\n```json\n{summary}\n```"
                )]
            else:
                error_msg = message.get("message", "Unknown error")
                raise Exception(f"API returned error: {error_msg}")
            
        except Exception as e:
            raise Exception(f"Failed to get equipment summary for {equipment_id}: {str(e)}")
    
    def _apply_search_filters(self, data: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """Apply client-side filters to CNC data"""
        filtered_data = data
        
        # Filter by operation mode
        if filters.get("operation_mode"):
            filtered_data = [d for d in filtered_data if d.get("operation_mode") == filters["operation_mode"]]
        
        # Filter by alarm presence
        if filters.get("has_alarm") is not None:
            if filters["has_alarm"]:
                filtered_data = [d for d in filtered_data if d.get("alarm_code") is not None]
            else:
                filtered_data = [d for d in filtered_data if d.get("alarm_code") is None]
        
        # Filter by minimum workpiece count
        if filters.get("min_workpiece_count"):
            min_count = filters["min_workpiece_count"]
            filtered_data = [d for d in filtered_data if d.get("workpiece_count", 0) >= min_count]
        
        return filtered_data
    
    def _calculate_equipment_summary(self, data: List[Dict], filters: Dict[str, Any]) -> Dict:
        """Calculate summary statistics for equipment data"""
        if not data:
            return {"error": "No data available for this equipment"}
        
        # Filter by date range if provided
        filtered_data = data
        if filters.get("date_from") or filters.get("date_to"):
            # Note: Date filtering would need to be implemented based on actual date format
            pass
        
        # Calculate statistics
        total_records = len(filtered_data)
        total_workpieces = sum(d.get("workpiece_count", 0) for d in filtered_data)
        
        # Calculate average loads
        loads = {
            "spindle": [float(d.get("spindle_load", "0").replace("%", "")) for d in filtered_data if d.get("spindle_load")],
            "x_axis": [float(d.get("x_axis_load", "0").replace("%", "")) for d in filtered_data if d.get("x_axis_load")],
            "y_axis": [float(d.get("y_axis_load", "0").replace("%", "")) for d in filtered_data if d.get("y_axis_load")],
            "z_axis": [float(d.get("z_axis_load", "0").replace("%", "")) for d in filtered_data if d.get("z_axis_load")]
        }
        
        avg_loads = {}
        for axis, values in loads.items():
            avg_loads[f"avg_{axis}_load"] = f"{sum(values) / len(values):.1f}%" if values else "N/A"
        
        # Count operation modes
        operation_modes = {}
        for record in filtered_data:
            mode = record.get("operation_mode", "Unknown")
            operation_modes[mode] = operation_modes.get(mode, 0) + 1
        
        # Count alarms
        alarm_count = sum(1 for d in filtered_data if d.get("alarm_code"))
        
        return {
            "equipment_id": filtered_data[0].get("equipment_id") if filtered_data else "Unknown",
            "total_records": total_records,
            "total_workpieces": total_workpieces,
            "average_workpieces_per_record": total_workpieces / total_records if total_records > 0 else 0,
            "operation_mode_distribution": operation_modes,
            "alarm_percentage": f"{(alarm_count / total_records * 100):.1f}%" if total_records > 0 else "N/A",
            **avg_loads,
            "date_range": {
                "from": filters.get("date_from", "Not specified"),
                "to": filters.get("date_to", "Not specified")
            }
        }

# Global instance
external_api_tools = ExternalAPITools()