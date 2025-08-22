# Dify MCP Server Setup Guide

This guide explains how to configure your MCP server to work with Dify's Plugin MCP HTTP with SSE (Server-Sent Events) or Streamable HTTP transport.

## 🏗️ Architecture

```
Dify Platform
    ↓ MCP Protocol (SSE/Streamable HTTP)
MCP Protocol Server (localhost:6019)
    ↓ Internal API calls
Regular HTTP Server (localhost:6018)
    ↓ HTTP REST API
Frappe/ERPNext API (iot.datawits.net:8000)
    ↓ Database Query
CNC Equipment Data (Real-time IoT)
```

## 🚀 Starting the Servers

### Option 1: Both Servers (Recommended)
```bash
# Start both regular HTTP API and MCP protocol servers
docker-compose up

# This will start:
# - Regular HTTP API Server on port 6018
# - MCP Protocol Server on port 6019
```

### Option 2: MCP Protocol Server Only
```bash
# Start only the MCP protocol server
docker-compose up mcp-protocol-server
```

### Option 3: Development Mode
```bash
# Start with hot-reload enabled
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## 🔌 Dify MCP Configuration

### MCP Server Endpoints

Your MCP server provides these endpoints:

| Transport | Endpoint | Description |
|-----------|----------|-------------|
| **SSE** | `http://localhost:6019/sse` | Server-Sent Events transport |
| **Streamable HTTP** | `http://localhost:6019/mcp` | JSON-RPC over HTTP |
| **Health Check** | `http://localhost:6019/health` | Server health status |

### Dify Plugin MCP HTTP Configuration

Use this configuration in your Dify MCP settings:

#### Option 1: SSE Transport (Recommended)
```json
{
  "iot_cnc_data": {
    "transport": "sse",
    "url": "http://127.0.0.1:6019/sse",
    "headers": {
      "Content-Type": "application/json",
      "Accept": "text/event-stream"
    },
    "timeout": 60,
    "sse_read_timeout": 60
  }
}
```

#### Option 2: Streamable HTTP Transport
```json
{
  "iot_cnc_data": {
    "transport": "streamable_http",
    "url": "http://127.0.0.1:6019/mcp",
    "headers": {
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    "timeout": 60
  }
}
```

#### Option 3: Multiple Configurations
```json
{
  "iot_cnc_sse": {
    "transport": "sse",
    "url": "http://127.0.0.1:6019/sse",
    "timeout": 60,
    "sse_read_timeout": 60
  },
  "iot_cnc_http": {
    "transport": "streamable_http",
    "url": "http://127.0.0.1:6019/mcp",
    "timeout": 60
  }
}
```

## 🛠️ Available Tools

The MCP server provides these tools for Dify:

### 1. `get_iot_cnc_data`
Retrieve CNC data records with filtering and pagination.

**Parameters:**
- `equipment_id` (optional): Filter by specific equipment ID
- `limit` (optional): Number of records to return (default: 50, max: 1000)
- `offset` (optional): Number of records to skip (default: 0)

**Example Usage in Dify:**
```
Get the latest 10 CNC data records for equipment dw-16
```

### 2. `get_iot_cnc_data_by_id`
Get a specific CNC data record by its ID.

**Parameters:**
- `cnc_data_id` (required): The ID of the CNC data record

**Example Usage in Dify:**
```
Get CNC data for record ID cnc-dw-16-0020
```

### 3. `get_iot_equipment_list`
Get a list of all unique equipment IDs.

**Parameters:** None

**Example Usage in Dify:**
```
List all available CNC equipment
```

## 🧪 Testing the Setup

### 1. Test Server Health
```bash
curl http://localhost:6019/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-18T23:55:00.000000",
  "transport": ["sse", "streamable_http"],
  "mcp_version": "2024-11-05"
}
```

### 2. Test SSE Endpoint
```bash
curl -N -H "Accept: text/event-stream" http://localhost:6019/sse
```

Expected response:
```
data: {"type": "initialized", "timestamp": "2025-07-18T23:55:00.000000"}

data: {"type": "heartbeat", "timestamp": "2025-07-18T23:55:30.000000"}
```

### 3. Test MCP Tool Call
```bash
curl -X POST http://localhost:6019/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_iot_equipment_list", "arguments": {}}'
```

Expected response:
```json
{
  "content": [
    {
      "type": "text",
      "text": "Equipment List (2 unique equipment IDs):\n```json\n[\"dw-16\", \"dw-3\"]\n```"
    }
  ]
}
```

## 🔧 Configuration Files

### Environment Variables
The server uses these environment variables (set in `.env` or docker-compose):

```env
SERVER_PORT=6019                    # MCP server port
LOG_LEVEL=INFO                      # Logging level
EXTERNAL_API_BASE_URL=http://iot.datawits.net:8000/api/method/frappe.integrations.api_dify.
EXTERNAL_API_KEY=not_required_guest_access
```

### Custom Configuration
You can modify the MCP server behavior by editing:
- `src/mcp_http_server.py` - Main MCP protocol implementation
- `src/tools/external_api.py` - Tool definitions and logic
- `dify-mcp-config.json` - Sample Dify configuration

## 🚨 Troubleshooting

### Common Issues:

1. **Connection Refused**
   - Ensure the MCP server is running on port 6019
   - Check if the port is accessible from Dify

2. **SSE Connection Drops**
   - Increase `sse_read_timeout` in configuration
   - Check network stability between Dify and MCP server

3. **Tool Execution Failures**
   - Verify Frappe API is accessible
   - Check logs: `docker-compose logs mcp-protocol-server`

4. **Authentication Issues**
   - Ensure Frappe API allows guest access
   - Verify `EXTERNAL_API_KEY` configuration

### Debugging Commands:

```bash
# View MCP server logs
docker-compose logs -f mcp-protocol-server

# Test Frappe API directly
curl -X POST http://iot.datawits.net:8000/api/method/frappe.integrations.api_dify.get_iot_cnc_data \
  -H "Content-Type: application/json" -d '{}'

# Check server health
curl http://localhost:6019/health
```

## 🔗 Integration with Dify

1. **Add MCP Server**: In Dify's MCP configuration, add your server using the configuration above
2. **Test Connection**: Verify the connection is established
3. **Use Tools**: Create workflows that use the available CNC data tools
4. **Monitor**: Check both Dify and MCP server logs for any issues

## 📈 Performance Tips

- Use **SSE transport** for real-time applications
- Use **Streamable HTTP** for simple request-response patterns
- Adjust timeout values based on your network latency
- Monitor server logs for performance insights
- Consider caching for frequently accessed data

The MCP server is now ready for production use with Dify! 🎉 