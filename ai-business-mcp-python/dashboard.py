import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
from pathlib import Path
import time

# Set page config
st.set_page_config(
    page_title="AI Business Operations Dashboard",
    page_icon="💼",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #4CAF50;
        margin: 10px 0;
    }
    .info-box {
        background-color: #e8f4fd;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #2196F3;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #ffc107;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

class BusinessDashboard:
    def __init__(self):
        self.base_path = Path(__file__).parent / "data"
        self.mcp_server_url = "http://localhost:8000"
        self.load_data()
    
    def load_data(self):
        """Load business data from JSON files"""
        try:
            with open(self.base_path / "sales.json") as f:
                self.sales_data = json.load(f)
            
            with open(self.base_path / "hr.json") as f:
                self.hr_data = json.load(f)
            
            with open(self.base_path / "support.json") as f:
                self.support_data = json.load(f)
                
            st.sidebar.success("✅ Local data loaded successfully!")
                
        except Exception as e:
            st.sidebar.error(f"❌ Error loading local data: {e}")
            self.sales_data = []
            self.hr_data = []
            self.support_data = []
    
    def test_mcp_connection(self):
        """Test connection to MCP server"""
        try:
            response = requests.get(f"{self.mcp_server_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def call_mcp_tool(self, tool_name: str, arguments: dict = None):
        """Call MCP server tool"""
        try:
            if arguments is None:
                arguments = {}
            
            response = requests.post(
                f"{self.mcp_server_url}/tools/{tool_name}",
                json=arguments
            )
            
            if response.status_code == 200:
                return response.json().get("result", {})
            else:
                return {"error": f"Server returned {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Connection failed: {str(e)}"}
    
    def calculate_metrics(self):
        """Calculate key business metrics"""
        # Sales metrics
        closed_sales = [s for s in self.sales_data if s.get("status") == "Closed Won"]
        self.total_revenue = sum(s.get("amount", 0) for s in closed_sales)
        self.avg_deal_size = self.total_revenue / len(closed_sales) if closed_sales else 0
        self.win_rate = len(closed_sales) / len(self.sales_data) if self.sales_data else 0
        self.total_deals = len(self.sales_data)
        
        # HR metrics
        self.total_employees = len(self.hr_data)
        self.top_performers = [e for e in self.hr_data if e.get("performance") == "Excellent"]
        self.avg_salary = sum(e.get("salary", 0) for e in self.hr_data) / len(self.hr_data) if self.hr_data else 0
        
        # Support metrics
        self.open_tickets = [t for t in self.support_data if t.get("status") != "Resolved"]
        self.resolution_rate = (len([t for t in self.support_data if t.get("status") == "Resolved"]) / 
                              len(self.support_data)) if self.support_data else 0
    
    def display_sidebar(self):
        """Display sidebar with info and MCP controls"""
        st.sidebar.title("🔧 Control Panel")
        
        # MCP Server Status
        mcp_connected = self.test_mcp_connection()
        if mcp_connected:
            st.sidebar.success("✅ MCP Server Connected")
        else:
            st.sidebar.error("❌ MCP Server Offline")
            st.sidebar.info("Start the server with: `python mcp_server.py server`")
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🤖 MCP Tools Demo")
        
        # Tool demonstrations
        if st.sidebar.button("Get Revenue Summary"):
            result = self.call_mcp_tool("get_revenue_summary")
            if "error" not in result:
                st.sidebar.success(result.get("summary", "Success"))
            else:
                st.sidebar.error(result["error"])
        
        if st.sidebar.button("Get Top Performers"):
            result = self.call_mcp_tool("get_top_performers")
            if "error" not in result:
                st.sidebar.success(result.get("summary", "Success"))
            else:
                st.sidebar.error(result["error"])
        
        if st.sidebar.button("Business Overview"):
            result = self.call_mcp_tool("get_business_overview")
            if "error" not in result:
                st.sidebar.success(result.get("summary", "Success"))
            else:
                st.sidebar.error(result["error"])
        
        st.sidebar.markdown("---")
        st.sidebar.info("""
        **MCP Features:**
        - Real-time business data access
        - AI-powered analytics
        - Secure data protocol
        - Cross-platform compatibility
        """)
    
    def display_overview(self):
        """Display overview metrics"""
        st.markdown('<div class="main-header">💼 AI Business Operations Dashboard</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Revenue", 
                f"${self.total_revenue:,.0f}",
                f"{self.total_deals} deals"
            )
        with col2:
            st.metric(
                "Employees", 
                self.total_employees,
                f"{len(self.top_performers)} top performers"
            )
        with col3:
            st.metric(
                "Support Tickets", 
                len(self.open_tickets),
                f"{self.resolution_rate:.1%} resolved"
            )
        with col4:
            st.metric(
                "Win Rate", 
                f"{self.win_rate:.1%}",
                f"${self.avg_deal_size:,.0f} avg deal"
            )
        
        # MCP Status
        mcp_connected = self.test_mcp_connection()
        if mcp_connected:
            st.markdown("""
            <div class="info-box">
            <strong>🤖 MCP Server Active:</strong> AI assistants can access real-time business data through the Model Context Protocol.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="warning-box">
            <strong>⚠️ MCP Server Offline:</strong> Start the server to enable AI assistant capabilities.
            <br><code>python mcp_server.py server</code>
            </div>
            """, unsafe_allow_html=True)
    
    def display_sales_tab(self):
        """Display sales analytics"""
        st.subheader("📊 Sales Performance")
        
        if not self.sales_data:
            st.warning("No sales data available")
            return
            
        sales_df = pd.DataFrame(self.sales_data)
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Deals", len(sales_df))
        with col2:
            closed_count = len(sales_df[sales_df['status'] == 'Closed Won'])
            st.metric("Closed Won", closed_count)
        with col3:
            pipeline_count = len(sales_df[sales_df['status'] == 'In Progress'])
            st.metric("In Pipeline", pipeline_count)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                sales_df, 
                names='status', 
                title='Deal Status Distribution',
                color='status'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            region_sales = sales_df.groupby('region')['amount'].sum().reset_index()
            fig = px.bar(
                region_sales, 
                x='region', 
                y='amount',
                title='Revenue by Region',
                color='region'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Regional performance
        st.subheader("Regional Performance")
        region_stats = sales_df.groupby('region').agg({
            'amount': ['sum', 'mean', 'count'],
            'status': lambda x: (x == 'Closed Won').mean()
        }).round(0)
        
        region_stats.columns = ['Total Revenue', 'Avg Deal Size', 'Deal Count', 'Win Rate']
        st.dataframe(region_stats, use_container_width=True)
    
    def display_hr_tab(self):
        """Display HR analytics"""
        st.subheader("👥 Human Resources Analytics")
        
        if not self.hr_data:
            st.warning("No HR data available")
            return
            
        hr_df = pd.DataFrame(self.hr_data)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Employees", len(hr_df))
        with col2:
            st.metric("Average Salary", f"${self.avg_salary:,.0f}")
        with col3:
            st.metric("Top Performers", len(self.top_performers))
        with col4:
            departments = hr_df['department'].nunique()
            st.metric("Departments", departments)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            dept_count = hr_df['department'].value_counts()
            fig = px.bar(
                dept_count,
                title='Employees by Department',
                labels={'value': 'Count', 'index': 'Department'},
                color=dept_count.index
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(
                hr_df,
                names='performance',
                title='Performance Distribution',
                color='performance'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Salary analysis
        st.subheader("Salary Analysis by Department")
        salary_by_dept = hr_df.groupby('department').agg({
            'salary': ['mean', 'min', 'max', 'count']
        }).round(0)
        
        salary_by_dept.columns = ['Average Salary', 'Min Salary', 'Max Salary', 'Employee Count']
        st.dataframe(salary_by_dept, use_container_width=True)
    
    def display_support_tab(self):
        """Display support analytics"""
        st.subheader("🎧 Customer Support Analytics")
        
        if not self.support_data:
            st.warning("No support data available")
            return
            
        support_df = pd.DataFrame(self.support_data)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tickets", len(support_df))
        with col2:
            st.metric("Open Tickets", len(self.open_tickets))
        with col3:
            st.metric("Resolution Rate", f"{self.resolution_rate:.1%}")
        with col4:
            critical_tickets = len(support_df[support_df['priority'] == 'Critical'])
            st.metric("Critical Tickets", critical_tickets)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            status_count = support_df['status'].value_counts()
            fig = px.pie(
                values=status_count.values,
                names=status_count.index,
                title='Tickets by Status'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            priority_count = support_df['priority'].value_counts()
            fig = px.bar(
                priority_count,
                title='Tickets by Priority',
                color=priority_count.index,
                labels={'value': 'Count', 'index': 'Priority'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Ticket details
        st.subheader("Ticket Details")
        
        # Open tickets
        open_tickets_df = support_df[support_df['status'] != 'Resolved']
        if not open_tickets_df.empty:
            st.write("**Open Tickets:**")
            st.dataframe(open_tickets_df[['ticket_id', 'client', 'issue', 'status', 'priority']], use_container_width=True)
        else:
            st.success("🎉 All tickets are resolved!")
        
        # Recent resolved tickets
        resolved_tickets = support_df[support_df['status'] == 'Resolved']
        if not resolved_tickets.empty:
            st.write("**Recently Resolved Tickets:**")
            st.dataframe(resolved_tickets[['ticket_id', 'client', 'issue', 'priority']], use_container_width=True)
    
    def display_ai_insights_tab(self):
        """Display AI insights and MCP integration"""
        st.subheader("🤖 AI-Powered Business Insights")
        
        insights = [
            {
                "title": "💰 Revenue Optimization",
                "content": f"Current win rate is {self.win_rate:.1%}. Focus on improving lead qualification and follow-up processes to increase this to 40%.",
                "icon": "💰",
                "action": "Review sales process and implement better qualification criteria"
            },
            {
                "title": "👥 Talent Management", 
                "content": f"You have {len(self.top_performers)} top performers across {len(set(e['department'] for e in self.hr_data))} departments.",
                "icon": "👥",
                "action": "Implement mentorship programs and retention strategies"
            },
            {
                "title": "🎧 Customer Support",
                "content": f"With {len(self.open_tickets)} open tickets ({len([t for t in self.open_tickets if t.get('priority') == 'Critical'])} critical), prioritize resolution times.",
                "icon": "🎧", 
                "action": "Set SLA targets for critical issues"
            },
            {
                "title": "📈 Growth Opportunities",
                "content": "North America shows strongest performance. Consider expanding sales teams in underperforming regions.",
                "icon": "📈",
                "action": "Develop regional expansion strategy"
            }
        ]
        
        for insight in insights:
            with st.container():
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{insight['icon']} {insight['title']}</h3>
                    <p><strong>Insight:</strong> {insight['content']}</p>
                    <p><strong>Recommended Action:</strong> {insight['action']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # MCP Integration Demo
        st.subheader("🔌 MCP Server Integration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **MCP Server Status:** 
            - REST API: `/tools`
            - WebSocket: `/ws` 
            - Real-time data access
            - AI assistant integration
            """)
        
        with col2:
            st.info("""
            **Available Tools:**
            - Revenue analysis
            - Employee performance  
            - Support metrics
            - Business overview
            - Sales analytics
            """)
        
        # Live MCP demo
        st.subheader("🎯 Live MCP Tool Demo")
        
        tool_col1, tool_col2 = st.columns(2)
        
        with tool_col1:
            tool_choice = st.selectbox(
                "Select MCP Tool:",
                ["get_revenue_summary", "get_top_performers", "get_open_tickets", "get_business_overview"]
            )
        
        with tool_col2:
            if st.button("Execute MCP Tool"):
                with st.spinner("Calling MCP server..."):
                    result = self.call_mcp_tool(tool_choice)
                    
                    if "error" not in result:
                        st.success("✅ Tool executed successfully!")
                        st.json(result)
                    else:
                        st.error(f"❌ {result['error']}")

    def run(self):
        """Run the dashboard"""
        self.display_sidebar()
        self.calculate_metrics()
        self.display_overview()
        
        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Sales", "👥 HR", "🎧 Support", "🤖 AI Insights"
        ])
        
        with tab1:
            self.display_sales_tab()
        
        with tab2:
            self.display_hr_tab()
        
        with tab3:
            self.display_support_tab()
        
        with tab4:
            self.display_ai_insights_tab()
        
        # Footer
        st.markdown("---")
        st.caption("""
        **🔍 AI Business Operations Demo** | 
        Built with Python & Streamlit | 
        MCP Server: FastAPI | 
        Data: Synthetic Business Data
        """)

# Run the dashboard
if __name__ == "__main__":
    dashboard = BusinessDashboard()
    dashboard.run()