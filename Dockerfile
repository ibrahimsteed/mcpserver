# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 替换 apt 源
RUN echo "deb https://mirrors.ustc.edu.cn/debian bookworm main contrib non-free non-free-firmware\n\
deb https://mirrors.ustc.edu.cn/debian bookworm-updates main contrib non-free non-free-firmware\n\
deb https://mirrors.ustc.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware" \
> /etc/apt/sources.list && \
    rm -f /etc/apt/sources.list.d/* && \
    apt-get clean && \
    apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*
    
# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install -i https://pypi.mirrors.ustc.edu.cn/simple/ --default-timeout=100 --retries=10 --no-cache-dir -r requirements.txt
# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY .env .

# Create logs directory
RUN mkdir -p logs

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Expose port
EXPOSE 6018

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:6018/health || exit 1

# Default command (can be overridden)
CMD ["python", "-m", "src.http_server"]