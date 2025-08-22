博主上一篇文章，是基于 Dify 的工作流编排能力和 RAGFlow 知识库，构建了一套端到端的水泵制造企业机加车间的数控机床的预测性维护(Predictive Maintenance)场景的AI智能体Agent。

**万物皆可MCP，本质上是万物皆可连接。**

本文将介绍如何从零开发Agent智能体所用到的MCP服务端。

博主上一篇文章中，Agent智能体工作流获取指定的CNC机床时序数据时，采用的是MCP方式。在Dify与MCP服务对接时，体现了Agent智能体通过MCP与定制化工业数据服务集成的灵活性，使得数据在送入LLM进行高级推理前，得到了最有效的预处理和整合。

MCP（Model Context Protocol）是一种协议，用于与需要复杂预处理或封装专有逻辑的外部服务进行交互。

本文所开发的MCP Server封装了从IIoT Platform时序数据库中查询和格式化CNC数据的逻辑。

## 🎯 引言：为什么需要 MCP Server？

在工业 4.0 时代，数控机床（CNC）的智能化监控和预测性维护已成为制造业数字化转型的关键一环。本项目通过构建一个专门的 Model Context Protocol (MCP) 服务器，巧妙地将 Dify 的 AI 工作流能力与工业物联网平台的实时数据无缝对接，实现了**"状态监测 → 异常判断 → 深度诊断 → 决策建议"**的智能化闭环。

想象一下：当 CNC 设备正在车间运转时，每一个主轴转速、每一次刀具切换、每一个轴向负载都被实时记录。而通过本 MCP Server，这些冰冷的数据瞬间变成了 AI 可以理解和分析的"语言"，让 Dify 能够像经验丰富的工程师一样，洞察设备的"健康状况"。

![AI智能体Agent工作流](https://mz-blog-res.oss-cn-beijing.aliyuncs.com/img/b010/dify_workflow.png)

博主的上一篇文章说明了如何将现场机床设备数据采集上来，并展示在工业物联网管理平台IIoT Platform和现场大屏上。

![大屏展示](https://mz-blog-res.oss-cn-beijing.aliyuncs.com/img/b010/rmms-3.png)

![系统架构](https://mz-blog-res.oss-cn-beijing.aliyuncs.com/img/b010/iot_architecture-2.png)

下面首先展示如何在Dify工作流中配置MCP客户端节点，然后介绍如何从零开发MCP服务端。

在Dify工具市场中搜索和添加MCP客户端。

![添加MCP客户端](https://mz-blog-res.oss-cn-beijing.aliyuncs.com/img/b010/mcp_tool.png)

在Dify工作流中配置MCP客户端节点。

> 注意：本文采用Streamable HTTP Transport方式，与MCP服务端进行通信。

![MCP客户端节点配置](https://mz-blog-res.oss-cn-beijing.aliyuncs.com/img/b010/mcp_tool_config.png)

**Dify节点类型**: MCP
**Dify节点名称**: `GET_CNC_DATA_SNAPSHOT`
**Dify节点功能**: 调用一个定制化的MCP服务接口 `get_iot_cnc_data_by_id`。此服务负责根据传入的`cnc_data_id`，从IIoT平台的时序数据库中查询该时刻点的CNC传感器数据快照。MCP服务在后台完成了数据清洗、格式化和单位统一，最终向Dify工作流返回一个干净、结构化的JSON对象，包含了该时刻的关键运行指标。

## 📚 项目概述

### 核心架构

![MCP Server架构](https://mz-blog-res.oss-cn-beijing.aliyuncs.com/img/b010/mcp_server.png)

```
Dify 工作流平台
    ↓ MCP Protocol (SSE/HTTP)
MCP 协议服务器 (端口 6019)
    ↓ 内部 API 调用
常规 HTTP 服务器 (端口 6018)
    ↓ HTTP REST API
Frappe/ERPNext API (iot.datawits.net:8000)
    ↓ 数据库查询
CNC 设备实时数据
```

这个架构设计的精妙之处在于：
- **双服务器模式**：既支持标准 HTTP API 调用，又实现了 MCP 协议
- **数据预处理**：在 MCP 层完成数据清洗和格式化，减轻 LLM 负担
- **灵活集成**：可以轻松扩展到其他工业数据源

## 🛠️ 开发指南

### 1. 环境准备

首先，让我们搭建开发环境：

```bash
# 克隆项目
git clone <repository-url>
cd dify-python-mcp-server

# 创建项目结构
mkdir -p src/{tools,utils,config}
mkdir -p tests logs config

# 安装依赖
pip install -r requirements.txt
```

### 2. 核心组件开发

#### 2.1 MCP 服务器主体

MCP 服务器是整个系统的心脏，负责处理来自 Dify 的请求：

```python
# src/main.py
class DifyMCPServer:
    """Main MCP Server for Dify integration"""
    
    def __init__(self):
        self.server = Server(settings.server_name)
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all MCP request handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """列出所有可用工具"""
            tools = []
            tools.extend(external_api_tools.get_tools())
            
            logger.info(f"Listed {len(tools)} available tools")
            return tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
            """执行工具调用"""
            try:
                logger.info(f"Calling tool: {name}", extra={"arguments": arguments})
                
                # 路由到相应的工具处理器
                if name.startswith('get_iot_'):
                    result = await external_api_tools.execute_tool(name, arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return result
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                raise
```

这段代码展示了 MCP 服务器的核心逻辑：注册工具列表，并根据工具名称路由到相应的处理函数。

#### 2.2 IoT CNC 数据工具实现

接下来是最关键的部分 - CNC 数据获取工具：

```python
# src/tools/external_api.py
class ExternalAPITools:
    """Tools for interacting with IoT CNC Data API"""
    
    def get_tools(self) -> List[Tool]:
        """返回可用的 IoT CNC API 工具列表"""
        return [
            Tool(
                name="get_iot_cnc_data",
                description="获取 CNC 数据记录，支持过滤和分页",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "equipment_id": {
                            "type": "string",
                            "description": "设备 ID 过滤（可选）"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 50,
                            "description": "返回记录数（默认50，最大1000）"
                        }
                    }
                }
            ),
            Tool(
                name="get_iot_cnc_data_by_id",
                description="根据 ID 获取特定 CNC 数据记录",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cnc_data_id": {
                            "type": "string",
                            "description": "CNC 数据记录 ID"
                        }
                    },
                    "required": ["cnc_data_id"]
                }
            )
        ]
    
    async def _get_iot_cnc_data_by_id(self, args: Dict[str, Any]) -> List[TextContent]:
        """获取特定 CNC 数据记录"""
        cnc_data_id = args["cnc_data_id"]
        
        try:
            response = await http_client.get("get_iot_cnc_data_by_id", 
                                           params={"cnc_data_id": cnc_data_id})
            
            # 从 Frappe 响应格式中提取数据
            message = response.get("message", {})
            if message.get("success"):
                data = message.get("data", {})
                
                return [TextContent(
                    type="text",
                    text=f"CNC 数据记录 (ID: {cnc_data_id}):\n```json\n{data}\n```"
                )]
                
        except Exception as e:
            raise Exception(f"获取 CNC 数据失败: {str(e)}")
```

注意这里的数据处理逻辑：
1. 从 Frappe API 获取原始数据
2. 提取并验证响应中的有效数据
3. 格式化为 MCP 协议要求的 TextContent 格式

#### 2.3 HTTP 客户端封装

为了确保与外部 API 的可靠通信，我们封装了一个智能的 HTTP 客户端：

```python
# src/utils/http_client.py
class HTTPClient:
    def __init__(self):
        self.base_url = str(settings.external_api_base_url)
        self.api_key = settings.external_api_key
        self.timeout = settings.external_api_timeout
        
        # 速率限制
        self._semaphore = asyncio.Semaphore(settings.external_api_rate_limit)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def request(self, method: str, endpoint: str, 
                     params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发起 HTTP 请求，带重试逻辑和速率限制"""
        
        async with self._semaphore:
            # 处理 Frappe API 特殊的 URL 格式（以点结尾）
            if self.base_url.endswith('.'):
                url = f"{self.base_url}{endpoint}"
            else:
                url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            logger.info(f"HTTP {method} Request to: {url}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=await self._get_headers()
                )
                
                response.raise_for_status()
                return response.json()
```

这个客户端的亮点：
- **自动重试**：使用指数退避策略处理网络波动
- **速率限制**：防止对上游 API 造成压力
- **灵活的 URL 处理**：兼容各种 API 端点格式

### 3. MCP 协议服务器实现

MCP 协议服务器是与 Dify 通信的关键组件：

```python
# src/mcp_http_server.py
class MCPHTTPServer:
    """MCP HTTP Server with SSE and Streamable HTTP transport support"""
    
    def setup_routes(self):
        # SSE 传输端点
        @self.app.get("/sse")
        async def mcp_sse_endpoint(request: Request):
            """MCP Server-Sent Events 传输端点"""
            
            async def generate():
                try:
                    while True:
                        if await request.is_disconnected():
                            break
                        
                        # 保持连接活跃
                        await asyncio.sleep(30)
                        yield "data: \n\n"
                        
                except Exception as e:
                    logger.error(f"SSE stream error: {e}")
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive"
                }
            )
        
        # MCP 协议请求处理
        @self.app.post("/sse")
        async def mcp_sse_request(request: Request):
            """处理通过 SSE 传输的 MCP 协议请求"""
            body = await request.json()
            logger.info(f"MCP SSE request: {body}")
            
            response = await self._handle_mcp_request(body)
            return JSONResponse(content=response)
    
    async def _handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 MCP 协议请求"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method == "tools/list":
            # 获取工具列表
            from src.tools.external_api import external_api_tools
            available_tools = external_api_tools.get_tools()
            
            tools = [{
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            } for tool in available_tools]
            
            result = {"tools": tools}
            
        elif method == "tools/call":
            # 执行工具
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # 处理参数 - 可能是字符串或字典
            if isinstance(arguments, str):
                arguments = json.loads(arguments) if arguments.strip() else {}
            
            # 执行工具并返回结果
            result_content = await external_api_tools.execute_tool(tool_name, arguments)
            result = {
                "content": [{
                    "type": "text",
                    "text": content.text
                } for content in result_content]
            }
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
```

### 4. 配置管理

使用 Pydantic 进行类型安全的配置管理：

```python
# src/config/settings.py
class Settings(BaseSettings):
    # 服务器配置
    server_name: str = Field(default="dify-external-api-server")
    server_version: str = Field(default="1.0.0")
    server_port: int = Field(default=6018)
    
    # 外部 API 配置
    external_api_base_url: Optional[HttpUrl] = Field(default=None)
    external_api_key: Optional[str] = Field(default=None)
    external_api_timeout: int = Field(default=30)
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

## 🚀 部署指南

### 1. Docker 容器化部署

#### 1.1 构建 Docker 镜像

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 使用国内镜像加速
RUN echo "deb https://mirrors.ustc.edu.cn/debian bookworm main contrib non-free non-free-firmware" \
    > /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install -i https://pypi.mirrors.ustc.edu.cn/simple/ \
    --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY config/ ./config/
COPY .env .

# 创建日志目录
RUN mkdir -p logs

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:6018/health || exit 1

CMD ["python", "-m", "src.http_server"]
```

#### 1.2 Docker Compose 编排

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 常规 HTTP API 服务器
  mcp-server:
    build: .
    network_mode: "host"
    environment:
      - SERVER_PORT=6018
      - LOG_LEVEL=INFO
      - EXTERNAL_API_BASE_URL=http://iot.datawits.net:8000/api/method/frappe.integrations.api_dify.
      - EXTERNAL_API_KEY=not_required_guest_access
    volumes:
      - ./src:/app/src      # 热重载开发
      - ./logs:/app/logs    # 日志持久化
    restart: unless-stopped
    command: ["python", "-m", "uvicorn", "src.http_server:app", 
              "--host", "0.0.0.0", "--port", "6018", "--reload"]
    
  # MCP 协议服务器（用于 Dify 集成）
  mcp-protocol-server:
    build: .
    network_mode: "host"
    environment:
      - SERVER_PORT=6019
      - LOG_LEVEL=INFO
      - EXTERNAL_API_BASE_URL=http://iot.datawits.net:8000/api/method/frappe.integrations.api_dify.
    volumes:
      - ./src:/app/src
      - ./logs:/app/logs
    restart: unless-stopped
    command: ["python", "-m", "uvicorn", "src.mcp_http_server:app", 
              "--host", "0.0.0.0", "--port", "6019", "--reload"]
```

### 2. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f mcp-protocol-server

# 健康检查
curl http://localhost:6019/health
```

### 3. Dify 集成配置

#### 3.1 在 Dify 中配置 MCP 服务器

在 Dify 的 MCP 配置中使用以下设置：

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

#### 3.2 创建 Dify 工作流

在 Dify 中创建一个使用 MCP 工具的工作流节点：

```yaml
节点名称: GET_CNC_DATA_SNAPSHOT
节点类型: MCP
工具名称: get_iot_cnc_data_by_id
输入参数:
  cnc_data_id: "{{cnc_record_id}}"
```

### 4. 测试验证

#### 4.1 测试 MCP 服务器健康状态

```bash
# 测试健康检查端点
curl http://localhost:6019/health

# 期望响应
{
  "status": "healthy",
  "timestamp": "2025-01-21T10:30:00",
  "transport": ["sse", "streamable_http"],
  "mcp_version": "2024-11-05"
}
```

#### 4.2 测试工具调用

```bash
# 直接测试工具调用
curl -X POST http://localhost:6019/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_iot_equipment_list",
    "arguments": {}
  }'

# 期望响应
{
  "content": [{
    "type": "text",
    "text": "Equipment List (2 unique equipment IDs):\n```json\n[\"dw-16\", \"dw-3\"]\n```"
  }]
}
```

#### 4.3 测试 CNC 数据获取

```bash
# 获取特定设备的 CNC 数据
curl -X POST http://localhost:6018/tools/get_iot_cnc_data \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "dw-16",
    "limit": 10
  }'
```

## 🎨 实际应用场景

### 场景一：设备异常预警

当 CNC 设备的主轴负载突然升高时，Dify 工作流可以：
1. 通过 MCP 获取实时数据
2. 分析负载趋势
3. 判断是否需要维护
4. 自动发送预警通知

### 场景二：生产效率分析

定期汇总分析：
1. 获取多台设备的运行数据
2. 计算设备利用率
3. 识别生产瓶颈
4. 生成优化建议报告

### 场景三：预测性维护

基于历史数据：
1. 分析设备运行模式
2. 预测潜在故障
3. 制定维护计划
4. 优化备件库存

## 🔧 故障排查

### 常见问题及解决方案

#### 1. 连接被拒绝
```bash
# 检查端口是否被占用
netstat -tuln | grep 6019

# 检查 Docker 容器状态
docker-compose ps
```

#### 2. SSE 连接断开
- 增加 `sse_read_timeout` 配置值
- 检查网络稳定性
- 查看服务器日志寻找断开原因

#### 3. 工具执行失败
```bash
# 查看详细日志
docker-compose logs -f mcp-protocol-server | grep ERROR

# 直接测试 Frappe API
curl http://iot.datawits.net:8000/api/method/frappe.integrations.api_dify.get_iot_cnc_data
```

## 🌟 最佳实践

### 1. 安全性
- 使用环境变量管理敏感信息
- 启用 HTTPS（生产环境）
- 实施 API 密钥轮换

### 2. 性能优化
- 使用连接池管理 HTTP 连接
- 实施缓存策略减少 API 调用
- 监控并调整速率限制

### 3. 可维护性
- 保持清晰的日志记录
- 使用类型提示和文档字符串
- 编写单元测试覆盖关键功能

## 📈 扩展能力

本项目的模块化设计使其易于扩展：

### 添加新的数据源
```python
# src/tools/new_datasource.py
class NewDataSourceTools:
    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="get_new_data",
                description="从新数据源获取数据",
                inputSchema={...}
            )
        ]
```

### 集成更多分析功能
- 添加机器学习模型进行异常检测
- 实现复杂的数据聚合和统计
- 集成可视化报表生成

## 🎯 总结

**万物皆可MCP**。

通过本 MCP Server，我们成功打通了 Dify AI 工作流与工业物联网数据的桥梁。这不仅仅是一个技术集成项目，更是推动智能制造的重要一步。无论您是想要监控单台设备，还是管理整个生产线，这个解决方案都能为您提供强大而灵活的支持。

**真正的智能，从来不是让机器变得更聪明，而是让机器更懂人的需要。**

我们总以为AI的价值在于超越人类，其实AI最大的价值在于成为人类的延伸。就像这个MCP服务器，它不是要替代工程师，而是要成为工程师的"第三只眼"，帮助人类看到原本看不见的设备状态。

**数据的价值在于洞察，洞察的价值在于行动**。

---



