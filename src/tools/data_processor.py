# src/tools/data_processor.py
from typing import List, Dict, Any, Union
from mcp.types import Tool, TextContent
from loguru import logger
import json
import pandas as pd
from datetime import datetime, date

class DataProcessorTools:
    """Tools for processing and transforming data"""
    
    def get_tools(self) -> List[Tool]:
        """Return list of data processing tools"""
        return [
            Tool(
                name="process_data",
                description="Process and transform data using various operations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["filter", "transform", "aggregate", "validate", "format"],
                            "description": "Type of processing operation"
                        },
                        "data": {
                            "type": "object",
                            "description": "Data to process"
                        },
                        "options": {
                            "type": "object",
                            "description": "Processing options and parameters"
                        }
                    },
                    "required": ["operation", "data"]
                }
            ),
            Tool(
                name="convert_format",
                description="Convert data between different formats (CSV, JSON, XML)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": "Data to convert"
                        },
                        "from_format": {
                            "type": "string",
                            "enum": ["csv", "json", "xml", "yaml"],
                            "description": "Source format"
                        },
                        "to_format": {
                            "type": "string",
                            "enum": ["csv", "json", "xml", "yaml"],
                            "description": "Target format"
                        },
                        "options": {
                            "type": "object",
                            "description": "Conversion options"
                        }
                    },
                    "required": ["data", "from_format", "to_format"]
                }
            ),
            Tool(
                name="analyze_data",
                description="Analyze data and generate insights",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "object",
                            "description": "Data to analyze"
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["summary", "statistics", "trends", "anomalies"],
                            "default": "summary",
                            "description": "Type of analysis to perform"
                        }
                    },
                    "required": ["data"]
                }
            )
        ]
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute the specified data processing tool"""
        try:
            logger.info(f"Executing data processing tool: {name}", extra={"arguments": arguments})
            
            if name == "process_data":
                return await self._process_data(arguments)
            elif name == "convert_format":
                return await self._convert_format(arguments)
            elif name == "analyze_data":
                return await self._analyze_data(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.error(f"Data processing tool execution failed: {name}", extra={"error": str(e)})
            return [TextContent(
                type="text",
                text=f"Error executing {name}: {str(e)}"
            )]
    
    async def _process_data(self, args: Dict[str, Any]) -> List[TextContent]:
        """Process data based on operation type"""
        operation = args["operation"]
        data = args["data"]
        options = args.get("options", {})
        
        try:
            if operation == "filter":
                result = self._filter_data(data, options)
            elif operation == "transform":
                result = self._transform_data(data, options)
            elif operation == "aggregate":
                result = self._aggregate_data(data, options)
            elif operation == "validate":
                result = self._validate_data(data, options)
            elif operation == "format":
                result = self._format_data(data, options)
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            return [TextContent(
                type="text",
                text=f"Data Processing Result ({operation}):\n```json\n{json.dumps(result, indent=2, default=str)}\n```"
            )]
            
        except Exception as e:
            raise Exception(f"Data processing failed: {str(e)}")
    
    def _filter_data(self, data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Filter data based on criteria"""
        criteria = options.get("criteria", {})
        
        if isinstance(data, list):
            filtered = []
            for item in data:
                if self._matches_criteria(item, criteria):
                    filtered.append(item)
            return {"filtered_data": filtered, "count": len(filtered)}
        else:
            matches = self._matches_criteria(data, criteria)
            return {"matches_criteria": matches, "data": data if matches else None}
    
    def _transform_data(self, data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data structure"""
        transformations = options.get("transformations", {})
        
        if isinstance(data, list):
            transformed = []
            for item in data:
                transformed_item = self._apply_transformations(item, transformations)
                transformed.append(transformed_item)
            return {"transformed_data": transformed}
        else:
            transformed = self._apply_transformations(data, transformations)
            return {"transformed_data": transformed}
    
    def _aggregate_data(self, data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate data"""
        if not isinstance(data, list):
            data = [data]
        
        group_by = options.get("group_by")
        aggregations = options.get("aggregations", ["count"])
        
        if group_by:
            # Group by field
            groups = {}
            for item in data:
                key = item.get(group_by, "unknown")
                if key not in groups:
                    groups[key] = []
                groups[key].append(item)
            
            result = {}
            for group_key, group_data in groups.items():
                result[group_key] = self._calculate_aggregations(group_data, aggregations)
            
            return {"aggregated_data": result}
        else:
            # Aggregate all data
            return {"aggregated_data": self._calculate_aggregations(data, aggregations)}
    
    def _validate_data(self, data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against rules"""
        rules = options.get("rules", {})
        required_fields = options.get("required_fields", [])
        
        errors = []
        warnings = []
        
        # Check required fields
        if isinstance(data, dict):
            for field in required_fields:
                if field not in data or data[field] is None:
                    errors.append(f"Missing required field: {field}")
        
        # Apply validation rules
        for field, rule in rules.items():
            if field in data:
                value = data[field]
                if not self._validate_field(value, rule):
                    errors.append(f"Validation failed for {field}: {rule}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "data": data
        }
    
    def _format_data(self, data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Format data for display or export"""
        format_type = options.get("format", "table")
        
        if format_type == "table" and isinstance(data, list):
            # Convert to table format
            if data:
                headers = list(data[0].keys()) if data else []
                rows = [[str(item.get(header, "")) for header in headers] for item in data]
                return {"headers": headers, "rows": rows, "format": "table"}
        elif format_type == "summary":
            # Create summary format
            if isinstance(data, list):
                return {
                    "total_records": len(data),
                    "sample_record": data[0] if data else None,
                    "format": "summary"
                }
            else:
                return {"record": data, "format": "summary"}
        
        return {"formatted_data": data, "format": format_type}
    
    def _matches_criteria(self, item: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if item matches filter criteria"""
        for field, condition in criteria.items():
            if field not in item:
                return False
            
            value = item[field]
            if isinstance(condition, dict):
                # Complex condition
                operator = condition.get("op", "eq")
                expected = condition.get("value")
                
                if operator == "eq" and value != expected:
                    return False
                elif operator == "ne" and value == expected:
                    return False
                elif operator == "gt" and value <= expected:
                    return False
                elif operator == "lt" and value >= expected:
                    return False
                elif operator == "contains" and expected not in str(value):
                    return False
            else:
                # Simple equality check
                if value != condition:
                    return False
        
        return True
    
    def _apply_transformations(self, item: Dict[str, Any], transformations: Dict[str, Any]) -> Dict[str, Any]:
        """Apply transformations to a single item"""
        result = item.copy()
        
        for field, transformation in transformations.items():
            if isinstance(transformation, dict):
                operation = transformation.get("operation")
                params = transformation.get("params", {})
                
                if operation == "rename" and field in result:
                    new_name = params.get("to")
                    if new_name:
                        result[new_name] = result.pop(field)
                elif operation == "format" and field in result:
                    format_type = params.get("type")
                    if format_type == "date" and result[field]:
                        # Format date
                        try:
                            date_obj = datetime.fromisoformat(str(result[field]))
                            result[field] = date_obj.strftime(params.get("format", "%Y-%m-%d"))
                        except:
                            pass
                elif operation == "calculate" and field in result:
                    # Perform calculation
                    expression = params.get("expression", "")
                    # Simple calculations only for security
                    if "+" in expression:
                        parts = expression.split("+")
                        if len(parts) == 2 and parts[1].strip().isdigit():
                            result[field] = float(result[field]) + float(parts[1].strip())
        
        return result
    
    def _calculate_aggregations(self, data: List[Dict[str, Any]], aggregations: List[str]) -> Dict[str, Any]:
        """Calculate aggregations for a group of data"""
        result = {}
        
        if "count" in aggregations:
            result["count"] = len(data)
        
        # Find numeric fields for other aggregations
        numeric_fields = set()
        for item in data:
            for key, value in item.items():
                if isinstance(value, (int, float)):
                    numeric_fields.add(key)
        
        for field in numeric_fields:
            values = [item.get(field, 0) for item in data if isinstance(item.get(field), (int, float))]
            
            if "sum" in aggregations and values:
                result[f"{field}_sum"] = sum(values)
            if "avg" in aggregations and values:
                result[f"{field}_avg"] = sum(values) / len(values)
            if "min" in aggregations and values:
                result[f"{field}_min"] = min(values)
            if "max" in aggregations and values:
                result[f"{field}_max"] = max(values)
        
        return result
    
    def _validate_field(self, value: Any, rule: Dict[str, Any]) -> bool:
        """Validate a single field against a rule"""
        if "type" in rule:
            expected_type = rule["type"]
            if expected_type == "string" and not isinstance(value, str):
                return False
            elif expected_type == "number" and not isinstance(value, (int, float)):
                return False
            elif expected_type == "boolean" and not isinstance(value, bool):
                return False
        
        if "min_length" in rule and isinstance(value, str):
            if len(value) < rule["min_length"]:
                return False
        
        if "max_length" in rule and isinstance(value, str):
            if len(value) > rule["max_length"]:
                return False
        
        if "pattern" in rule and isinstance(value, str):
            import re
            if not re.match(rule["pattern"], value):
                return False
        
        return True
    
    async def _convert_format(self, args: Dict[str, Any]) -> List[TextContent]:
        """Convert data between formats"""
        data = args["data"]
        from_format = args["from_format"]
        to_format = args["to_format"]
        options = args.get("options", {})
        
        try:
            # Parse source format
            if from_format == "json":
                parsed_data = json.loads(data)
            elif from_format == "csv":
                import io
                df = pd.read_csv(io.StringIO(data))
                parsed_data = df.to_dict("records")
            elif from_format == "yaml":
                import yaml
                parsed_data = yaml.safe_load(data)
            else:
                raise ValueError(f"Unsupported source format: {from_format}")
            
            # Convert to target format
            if to_format == "json":
                result = json.dumps(parsed_data, indent=2, default=str)
            elif to_format == "csv":
                if isinstance(parsed_data, list):
                    df = pd.DataFrame(parsed_data)
                    result = df.to_csv(index=False)
                else:
                    raise ValueError("CSV format requires array data")
            elif to_format == "yaml":
                import yaml
                result = yaml.dump(parsed_data, default_flow_style=False)
            else:
                raise ValueError(f"Unsupported target format: {to_format}")
            
            return [TextContent(
                type="text",
                text=f"Format Conversion ({from_format} → {to_format}):\n```{to_format}\n{result}\n```"
            )]
            
        except Exception as e:
            raise Exception(f"Format conversion failed: {str(e)}")
    
    async def _analyze_data(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze data and generate insights"""
        data = args["data"]
        analysis_type = args.get("analysis_type", "summary")
        
        try:
            if analysis_type == "summary":
                result = self._generate_summary(data)
            elif analysis_type == "statistics":
                result = self._generate_statistics(data)
            elif analysis_type == "trends":
                result = self._analyze_trends(data)
            elif analysis_type == "anomalies":
                result = self._detect_anomalies(data)
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            return [TextContent(
                type="text",
                text=f"Data Analysis ({analysis_type}):\n```json\n{json.dumps(result, indent=2, default=str)}\n```"
            )]
            
        except Exception as e:
            raise Exception(f"Data analysis failed: {str(e)}")
    
    def _generate_summary(self, data: Union[Dict, List]) -> Dict[str, Any]:
        """Generate data summary"""
        if isinstance(data, list):
            return {
                "total_records": len(data),
                "fields": list(data[0].keys()) if data else [],
                "sample_records": data[:3] if len(data) > 3 else data,
                "data_types": self._analyze_data_types(data)
            }
        else:
            return {
                "record_type": "single",
                "fields": list(data.keys()),
                "field_count": len(data),
                "data_types": {k: type(v).__name__ for k, v in data.items()}
            }
    
    def _generate_statistics(self, data: Union[Dict, List]) -> Dict[str, Any]:
        """Generate statistical analysis"""
        if not isinstance(data, list):
            data = [data]
        
        stats = {}
        
        # Analyze numeric fields
        for item in data:
            for key, value in item.items():
                if isinstance(value, (int, float)):
                    if key not in stats:
                        stats[key] = {"values": [], "type": "numeric"}
                    stats[key]["values"].append(value)
        
        # Calculate statistics
        for field, info in stats.items():
            if info["type"] == "numeric" and info["values"]:
                values = info["values"]
                info.update({
                    "count": len(values),
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "sum": sum(values)
                })
                # Calculate standard deviation
                mean = info["mean"]
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                info["std_dev"] = variance ** 0.5
                
                del info["values"]  # Remove raw values from output
        
        return stats
    
    def _analyze_trends(self, data: Union[Dict, List]) -> Dict[str, Any]:
        """Analyze data trends"""
        if not isinstance(data, list) or len(data) < 2:
            return {"message": "Trend analysis requires at least 2 data points"}
        
        trends = {}
        
        # Look for time-based or sequential patterns
        for key in data[0].keys():
            values = [item.get(key) for item in data if isinstance(item.get(key), (int, float))]
            
            if len(values) >= 2:
                # Simple trend calculation
                trend_direction = "stable"
                if values[-1] > values[0]:
                    trend_direction = "increasing"
                elif values[-1] < values[0]:
                    trend_direction = "decreasing"
                
                # Calculate change rate
                change_rate = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
                
                trends[key] = {
                    "direction": trend_direction,
                    "change_rate_percent": round(change_rate, 2),
                    "start_value": values[0],
                    "end_value": values[-1]
                }
        
        return trends
    
    def _detect_anomalies(self, data: Union[Dict, List]) -> Dict[str, Any]:
        """Detect anomalies in data"""
        if not isinstance(data, list):
            return {"message": "Anomaly detection requires multiple data points"}
        
        anomalies = {}
        
        for key in data[0].keys():
            values = [item.get(key) for item in data if isinstance(item.get(key), (int, float))]
            
            if len(values) >= 3:
                mean = sum(values) / len(values)
                std_dev = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5
                
                # Simple outlier detection (values beyond 2 standard deviations)
                outliers = []
                for i, value in enumerate(values):
                    if abs(value - mean) > 2 * std_dev:
                        outliers.append({"index": i, "value": value, "deviation": abs(value - mean) / std_dev})
                
                if outliers:
                    anomalies[key] = {
                        "outliers": outliers,
                        "mean": mean,
                        "std_dev": std_dev,
                        "threshold": 2 * std_dev
                    }
        
        return anomalies
    
    def _analyze_data_types(self, data: List[Dict]) -> Dict[str, str]:
        """Analyze data types across all records"""
        type_analysis = {}
        
        if not data:
            return type_analysis
        
        for item in data:
            for key, value in item.items():
                value_type = type(value).__name__
                if key not in type_analysis:
                    type_analysis[key] = value_type
                elif type_analysis[key] != value_type:
                    type_analysis[key] = "mixed"
        
        return type_analysis

# Global instance
data_processor_tools = DataProcessorTools()