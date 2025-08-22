# src/utils/http_client.py
import httpx
import asyncio
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
from src.config.settings import settings

class HTTPClient:
    def __init__(self):
        self.base_url = str(settings.external_api_base_url)
        self.api_key = settings.external_api_key
        self.timeout = settings.external_api_timeout
        
        # Rate limiting
        self._semaphore = asyncio.Semaphore(settings.external_api_rate_limit)
        
    async def _get_headers(self) -> Dict[str, str]:
        """Get default headers for API requests"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"{settings.server_name}/{settings.server_version}"
        }
        
        # Only add authorization if API key is not indicating guest access
        if self.api_key and self.api_key != "not_required_guest_access":
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return headers
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic and rate limiting"""
        
        async with self._semaphore:
            # Handle base URL ending with dot (for Frappe API endpoints)
            if self.base_url.endswith('.'):
                url = f"{self.base_url}{endpoint}"
            else:
                url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            # Log the actual URL and request details for debugging
            logger.info(f"HTTP {method} Request to: {url}")
            logger.info(f"Base URL: {self.base_url}, Endpoint: {endpoint}")
            logger.info(f"Params: {params}, JSON Data: {json_data}")
            
            request_headers = await self._get_headers()
            if headers:
                request_headers.update(headers)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    response = await client.request(
                        method=method,
                        url=url,
                        params=params,
                        json=json_data,
                        headers=request_headers
                    )
                    
                    response.raise_for_status()
                    
                    # Handle different content types
                    content_type = response.headers.get("content-type", "")
                    logger.info(f"Response received: Status {response.status_code}, Content-Type: {content_type}")
                    
                    if "application/json" in content_type:
                        json_response = response.json()
                        logger.info(f"JSON Response keys: {list(json_response.keys()) if isinstance(json_response, dict) else 'Not a dict'}")
                        return json_response
                    else:
                        text_response = response.text
                        logger.info(f"Text Response length: {len(text_response)}")
                        return {"content": text_response, "status_code": response.status_code}
                        
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error {e.response.status_code}: {e.response.text}", extra={
                        "url": url,
                        "status_code": e.response.status_code,
                        "response_text": e.response.text,
                        "request_params": params
                    })
                    raise
                except httpx.RequestError as e:
                    logger.error(f"Request error: {e}", extra={
                        "url": url,
                        "error_type": type(e).__name__,
                        "request_params": params
                    })
                    raise
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request"""
        return await self.request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST request"""
        return await self.request("POST", endpoint, json_data=json_data)
    
    async def put(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """PUT request"""
        return await self.request("PUT", endpoint, json_data=json_data)
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE request"""
        return await self.request("DELETE", endpoint)

# Global HTTP client instance
http_client = HTTPClient()