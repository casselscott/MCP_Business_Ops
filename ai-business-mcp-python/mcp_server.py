import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(str, Enum):
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"

class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}

class MCPMessage(BaseModel):
    type: str
    request_id: str
    params: Optional[Dict[str, Any]] = None

class BusinessMCPServer:
    def __init__(self):
        self.app = FastAPI(title="Business Ops MCP Server")
        self.setup_routes()
        self.connected_clients = []
        
    def load_data(self, file_name: str) -> List[Dict]:
        """Load JSON data from file"""
        try:
            with open(f"data/{file_name}", "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_name}: {e}")
            return []
    
    def get_available_tools(self) -> List[Dict]:
        """Return list of available tools"""
        return [
            {
                "name": "get_revenue_summary",
                "description": "Get total revenue summary from closed sales",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_top_performers", 
                "description": "Get top performing employees",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "department": {
                            "type": "string",
                            "description": "Filter by department (optional)",
                            "enum": ["Engineering", "Sales", "Marketing", "Support"]
                        }
                    }
                }
            },
            {
                "name": "get_open_tickets",
                "description": "Get count and details of open support tickets", 
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "analyze_sales_performance",
                "description": "Analyze sales performance by region and status",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "region": {
                            "type": "string",
                            "description": "Filter by region (optional)",
                            "enum": ["North America", "Europe", "Asia"]
                        }
                    }
                }
            },
            {
                "name": "get_business_overview",
                "description": "Get comprehensive business overview across all departments",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    def get_revenue_summary(self) -> Dict[str, Any]:
        """Get sales revenue summary"""
        sales_data = self.load_data("sales.json")
        closed_won = [s for s in sales_data if s["status"] == "Closed Won"]
        in_progress = [s for s in sales_data if s["status"] == "In Progress"]
        lost = [s for s in sales_data if s["status"] == "Lost"]
        
        total_revenue = sum(s["amount"] for s in closed_won)
        potential_revenue = sum(s["amount"] for s in in_progress)
        win_rate = len(closed_won) / len(sales_data) if sales_data else 0
        
        return {
            "total_closed_revenue": total_revenue,
            "potential_revenue": potential_revenue,
            "closed_deals": len(closed_won),
            "deals_in_progress": len(in_progress),
            "lost_deals": len(lost),
            "win_rate": win_rate,
            "summary": f"✅ Total Closed Revenue: ${total_revenue:,} | 📊 {len(closed_won)} closed deals ({win_rate:.1%} win rate)"
        }
    
    def get_top_performers(self, department: Optional[str] = None) -> Dict[str, Any]:
        """Get top performing employees"""
        hr_data = self.load_data("hr.json")
        performers = [e for e in hr_data if e["performance"] == "Excellent"]
        
        if department:
            performers = [e for e in performers if e["department"] == department]
        
        performer_list = [
            {
                "name": p["name"],
                "department": p["department"], 
                "salary": p["salary"],
                "performance": p["performance"]
            }
            for p in performers
        ]
        
        # Fixed the f-string syntax
        if department:
            summary = f"🏆 Top performers in {department}: {', '.join(p['name'] for p in performers)}"
        else:
            performer_names = [f"{p['name']} ({p['department']})" for p in performers]
            summary = f"🏆 Top performers across company: {', '.join(performer_names)}"
        
        return {
            "top_performers": performer_list,
            "count": len(performers),
            "summary": summary
        }
    
    def get_open_tickets(self) -> Dict[str, Any]:
        """Get open support tickets"""
        tickets_data = self.load_data("support.json")
        open_tickets = [t for t in tickets_data if t["status"] != "Resolved"]
        
        by_status = {}
        by_priority = {}
        
        for ticket in open_tickets:
            by_status[ticket["status"]] = by_status.get(ticket["status"], 0) + 1
            by_priority[ticket["priority"]] = by_priority.get(ticket["priority"], 0) + 1
        
        status_summary = ", ".join(f"{status}: {count}" for status, count in by_status.items())
        return {
            "open_tickets_count": len(open_tickets),
            "tickets_by_status": by_status,
            "tickets_by_priority": by_priority,
            "open_tickets": open_tickets,
            "summary": f"📩 There are {len(open_tickets)} unresolved tickets ({status_summary})"
        }
    
    def analyze_sales_performance(self, region: Optional[str] = None) -> Dict[str, Any]:
        """Analyze sales performance"""
        sales_data = self.load_data("sales.json")
        filtered_sales = sales_data
        
        if region:
            filtered_sales = [s for s in sales_data if s["region"] == region]
        
        by_status = {}
        for sale in filtered_sales:
            by_status[sale["status"]] = by_status.get(sale["status"], 0) + 1
        
        total_amount = sum(s["amount"] for s in filtered_sales)
        closed_amount = sum(s["amount"] for s in filtered_sales if s["status"] == "Closed Won")
        
        avg_deal_size = total_amount / len(filtered_sales) if filtered_sales else 0
        
        if region:
            summary = f"📈 Sales in {region}: {len(filtered_sales)} deals totaling ${total_amount:,} (${closed_amount:,} closed)"
        else:
            summary = f"📈 Global Sales: {len(filtered_sales)} deals totaling ${total_amount:,} (${closed_amount:,} closed)"
        
        return {
            "region": region or "All Regions",
            "total_deals": len(filtered_sales),
            "total_amount": total_amount,
            "closed_amount": closed_amount,
            "deals_by_status": by_status,
            "average_deal_size": avg_deal_size,
            "summary": summary
        }
    
    def get_business_overview(self) -> Dict[str, Any]:
        """Get comprehensive business overview"""
        sales_data = self.load_data("sales.json")
        hr_data = self.load_data("hr.json")
        support_data = self.load_data("support.json")
        
        total_revenue = sum(s["amount"] for s in sales_data if s["status"] == "Closed Won")
        total_employees = len(hr_data)
        open_tickets = len([t for t in support_data if t["status"] != "Resolved"])
        top_performers = len([e for e in hr_data if e["performance"] == "Excellent"])
        
        departments = {
            "Engineering": len([e for e in hr_data if e["department"] == "Engineering"]),
            "Sales": len([e for e in hr_data if e["department"] == "Sales"]),
            "Marketing": len([e for e in hr_data if e["department"] == "Marketing"]),
            "Support": len([e for e in hr_data if e["department"] == "Support"])
        }
        
        return {
            "business_health": {
                "revenue": total_revenue,
                "employees": total_employees,
                "open_tickets": open_tickets,
                "top_performers": top_performers,
                "customer_satisfaction": "High"
            },
            "departments": departments,
            "summary": f"🏢 Business Overview: ${total_revenue:,} revenue, {total_employees} employees, {open_tickets} open tickets, {top_performers} top performers"
        }
    
    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution"""
        try:
            if tool_name == "get_revenue_summary":
                return self.get_revenue_summary()
            elif tool_name == "get_top_performers":
                return self.get_top_performers(arguments.get("department"))
            elif tool_name == "get_open_tickets":
                return self.get_open_tickets()
            elif tool_name == "analyze_sales_performance":
                return self.analyze_sales_performance(arguments.get("region"))
            elif tool_name == "get_business_overview":
                return self.get_business_overview()
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"error": str(e)}
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "Business Ops MCP Server", 
                "version": "1.0.0",
                "status": "running"
            }
        
        @self.app.get("/tools")
        async def list_tools():
            return {"tools": self.get_available_tools()}
        
        @self.app.post("/tools/{tool_name}")
        async def call_tool(tool_name: str, arguments: Dict[str, Any] = {}):
            result = self.handle_tool_call(tool_name, arguments)
            return {"result": result}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.connected_clients.append(websocket)
            logger.info("New WebSocket connection established")
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "tools/list":
                        response = {
                            "type": "tools/list",
                            "request_id": message.get("request_id"),
                            "result": {"tools": self.get_available_tools()}
                        }
                        await websocket.send_text(json.dumps(response))
                    
                    elif message.get("type") == "tools/call":
                        tool_name = message.get("params", {}).get("name")
                        arguments = message.get("params", {}).get("arguments", {})
                        
                        result = self.handle_tool_call(tool_name, arguments)
                        
                        response = {
                            "type": "tools/call",
                            "request_id": message.get("request_id"),
                            "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
                        }
                        await websocket.send_text(json.dumps(response))
                    
            except WebSocketDisconnect:
                self.connected_clients.remove(websocket)
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.connected_clients.remove(websocket)
    
    async def run_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the MCP server"""
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        logger.info(f"🚀 Business Ops MCP Server running on http://{host}:{port}")
        await server.serve()

# CLI interface for running the server
if __name__ == "__main__":
    import sys
    
    async def main():
        server = BusinessMCPServer()
        await server.run_server()
    
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        asyncio.run(main())
    else:
        print("Usage: python mcp_server.py server")
        print("Starting server on http://0.0.0.0:8000")
        asyncio.run(main())