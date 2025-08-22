# src/tools/notification.py
from typing import List, Dict, Any
from mcp.types import Tool, TextContent
from loguru import logger
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64
from src.config.settings import settings

class NotificationTools:
    """Tools for sending notifications"""
    
    def get_tools(self) -> List[Tool]:
        """Return list of notification tools"""
        return [
            Tool(
                name="send_email",
                description="Send an email notification",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient email address"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject"
                        },
                        "body": {
                            "type": "string",
                            "description": "Email body (supports HTML)"
                        },
                        "cc": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "CC recipients"
                        },
                        "bcc": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "BCC recipients"
                        },
                        "attachments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "filename": {"type": "string"},
                                    "content": {"type": "string", "description": "Base64 encoded content"},
                                    "content_type": {"type": "string", "default": "application/octet-stream"}
                                },
                                "required": ["filename", "content"]
                            },
                            "description": "Email attachments"
                        },
                        "is_html": {
                            "type": "boolean",
                            "default": False,
                            "description": "Whether the body contains HTML"
                        }
                    },
                    "required": ["to", "subject", "body"]
                }
            ),
            Tool(
                name="send_template_email",
                description="Send an email using a predefined template",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient email address"
                        },
                        "template": {
                            "type": "string",
                            "enum": ["welcome", "notification", "alert", "report"],
                            "description": "Email template to use"
                        },
                        "variables": {
                            "type": "object",
                            "description": "Template variables"
                        }
                    },
                    "required": ["to", "template"]
                }
            ),
            Tool(
                name="send_webhook",
                description="Send a webhook notification",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "Webhook URL"
                        },
                        "method": {
                            "type": "string",
                            "enum": ["POST", "PUT", "PATCH"],
                            "default": "POST",
                            "description": "HTTP method"
                        },
                        "payload": {
                            "type": "object",
                            "description": "Webhook payload"
                        },
                        "headers": {
                            "type": "object",
                            "description": "Additional headers"
                        }
                    },
                    "required": ["url", "payload"]
                }
            )
        ]
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute the specified notification tool"""
        try:
            logger.info(f"Executing notification tool: {name}", extra={"arguments": arguments})
            
            if name == "send_email":
                return await self._send_email(arguments)
            elif name == "send_template_email":
                return await self._send_template_email(arguments)
            elif name == "send_webhook":
                return await self._send_webhook(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.error(f"Notification tool execution failed: {name}", extra={"error": str(e)})
            return [TextContent(
                type="text",
                text=f"Error executing {name}: {str(e)}"
            )]
    
    async def _send_email(self, args: Dict[str, Any]) -> List[TextContent]:
        """Send email notification"""
        if not settings.smtp_host:
            raise Exception("SMTP configuration not available")
        
        to = args["to"]
        subject = args["subject"]
        body = args["body"]
        cc = args.get("cc", [])
        bcc = args.get("bcc", [])
        attachments = args.get("attachments", [])
        is_html = args.get("is_html", False)
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = settings.smtp_user
            msg['To'] = to
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            for attachment in attachments:
                part = MIMEBase('application', 'octet-stream')
                content = base64.b64decode(attachment['content'])
                part.set_payload(content)
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["filename"]}'
                )
                msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            
            recipients = [to] + cc + bcc
            server.sendmail(settings.smtp_user, recipients, msg.as_string())
            server.quit()
            
            return [TextContent(
                type="text",
                text=f"Email sent successfully to {to}"
            )]
            
        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")
    
    async def _send_template_email(self, args: Dict[str, Any]) -> List[TextContent]:
        """Send email using template"""
        to = args["to"]
        template = args["template"]
        variables = args.get("variables", {})
        
        try:
            # Load template
            template_config = self._get_email_template(template)
            
            # Replace variables in template
            subject = template_config["subject"]
            body = template_config["body"]
            
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                subject = subject.replace(placeholder, str(value))
                body = body.replace(placeholder, str(value))
            
            # Send email using the template
            email_args = {
                "to": to,
                "subject": subject,
                "body": body,
                "is_html": template_config.get("is_html", False)
            }
            
            return await self._send_email(email_args)
            
        except Exception as e:
            raise Exception(f"Failed to send template email: {str(e)}")
    
    async def _send_webhook(self, args: Dict[str, Any]) -> List[TextContent]:
        """Send webhook notification"""
        from src.utils.http_client import http_client
        
        url = args["url"]
        method = args.get("method", "POST")
        payload = args["payload"]
        headers = args.get("headers", {})
        
        try:
            # Add timestamp to payload
            payload["timestamp"] = datetime.now().isoformat()
            
            # Send webhook
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
            
            return [TextContent(
                type="text",
                text=f"Webhook sent successfully to {url} (Status: {response.status_code})"
            )]
            
        except Exception as e:
            raise Exception(f"Failed to send webhook: {str(e)}")
    
    def _get_email_template(self, template_name: str) -> Dict[str, Any]:
        """Get email template configuration"""
        templates = {
            "welcome": {
                "subject": "Welcome {name}!",
                "body": """
                <h1>Welcome to our service!</h1>
                <p>Hello {name},</p>
                <p>Thank you for joining us. We're excited to have you on board!</p>
                <p>Best regards,<br>The Team</p>
                """,
                "is_html": True
            },
            "notification": {
                "subject": "Notification: {title}",
                "body": """
                <h2>{title}</h2>
                <p>{message}</p>
                <p>Details: {details}</p>
                """,
                "is_html": True
            },
            "alert": {
                "subject": "ALERT: {alert_type}",
                "body": """
                <h2 style="color: red;">ALERT: {alert_type}</h2>
                <p><strong>Message:</strong> {message}</p>
                <p><strong>Severity:</strong> {severity}</p>
                <p><strong>Time:</strong> {timestamp}</p>
                """,
                "is_html": True
            },
            "report": {
                "subject": "Report: {report_name}",
                "body": """
                <h2>Report: {report_name}</h2>
                <p>Generated on: {date}</p>
                <div>{content}</div>
                """,
                "is_html": True
            }
        }
        
        if template_name not in templates:
            raise ValueError(f"Unknown email template: {template_name}")
        
        return templates[template_name]

# Global instance
notification_tools = NotificationTools()