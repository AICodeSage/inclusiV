#!/usr/bin/env python3
"""
Business Research & Locator Agent - Web research and location services agent using MCP framework
for comprehensive business research, store location, and information discovery.

This agent provides:
- Web research and information gathering
- Store and business location services
- Market research and competitive analysis
- Contact information discovery
- General information lookup and browsing
"""

import os
import asyncio
import uvicorn
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# MCP imports
try:
    from mcp_use import MCPAgent, MCPClient
    MCP_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: mcp_use not available. Install with: pip install mcp-use")
    MCP_AVAILABLE = False

# A2A imports
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    Message, AgentCard, AgentSkill, AgentCapabilities
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

# Load environment variables from parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

# Configuration
PORT = os.getenv("PORT", "9997")
URL = os.getenv("URL", f"http://localhost:{PORT}")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Agent Skills - Define the Research Agent's capabilities
research_skill = AgentSkill(
    id='web_research',
    name='Web Research & Information Gathering',
    description='Comprehensive web research, information discovery, and data collection from online sources.',
    tags=['research', 'web', 'information', 'data'],
    examples=[
        'Research the latest trends in fintech',
        'Find information about MTN MoMo services',
        'Gather market data on mobile payments in South Africa'
    ],
)

location_skill = AgentSkill(
    id='store_locator',
    name='Store & Business Location Services',
    description='Find store locations, business addresses, and contact information.',
    tags=['location', 'stores', 'addresses', 'contact'],
    examples=[
        'Find MTN stores in Johannesburg',
        'Locate the nearest bank branch',
        'Get contact details for University of Limpopo'
    ],
)

analysis_skill = AgentSkill(
    id='market_analysis',
    name='Market Research & Competitive Analysis',
    description='Analyze market trends, competitor information, and business intelligence.',
    tags=['analysis', 'market', 'competition', 'business'],
    examples=[
        'Analyze mobile money market in South Africa',
        'Compare MTN services with competitors',
        'Research business opportunities in fintech'
    ],
)

browsing_skill = AgentSkill(
    id='web_browsing',
    name='Web Browsing & Navigation',
    description='Navigate websites, extract information, and interact with web content.',
    tags=['browsing', 'navigation', 'websites', 'extraction'],
    examples=[
        'Navigate to a specific website and extract information',
        'Browse through multiple pages to gather data',
        'Extract contact details from company websites'
    ],
)

# Public Agent Card
public_agent_card = AgentCard(
    name='Business Research & Locator Agent',
    description='Business Research & Locator Agent for comprehensive web research, store location services, market analysis, and information discovery. Specializes in finding business information, contact details, and conducting market research.',
    url=f'{URL}/',
    version='1.0.0',
    defaultInputModes=['text'],
    defaultOutputModes=['text'],
    capabilities=AgentCapabilities(streaming=True),
    skills=[research_skill, location_skill, analysis_skill, browsing_skill],
    supportsAuthenticatedExtendedCard=True,
)

class BusinessResearchAgent:
    """
    Business Research & Locator Agent - Using MCP framework for web research
    with A2A protocol compatibility.
    """
    
    def __init__(self):
        """Initialize the Research agent with MCP framework."""
        self.mcp_agent = None
        self._initialize_mcp_agent()
    
    def _initialize_mcp_agent(self):
        """Initialize the MCP agent for web research."""
        try:
            if not MCP_AVAILABLE:
                print("⚠️  MCP not available - using fallback mode")
                self.mcp_agent = None
                self.llm = None
                return
                
            if not OPENAI_API_KEY:
                print("⚠️  Warning: OPENAI_API_KEY not found")
                self.mcp_agent = None
                self.llm = None
                return
            
            # Check if browser_mcp.json config exists
            config_path = os.path.join(os.path.dirname(__file__), "browser_mcp.json")
            if not os.path.exists(config_path):
                print(f"⚠️  Warning: MCP config file not found at {config_path}")
                # Fallback to LLM-only mode
                self.llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)
                self.mcp_agent = None
                print("✅ Business Research Agent initialized with LLM fallback")
                return
            
            try:
                # Create MCPClient from config file
                print("🔍 Initializing MCP client with browser tools...")
                client = MCPClient.from_config_file(config_path)
                
                # Create LLM
                llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)
                
                # Create MCP agent with browser capabilities
                self.mcp_agent = MCPAgent(llm=llm, client=client, max_steps=30)
                self.llm = llm
                
                print("✅ Business Research Agent initialized with full MCP browser capabilities")
                
            except Exception as mcp_error:
                print(f"⚠️  MCP browser tools failed to initialize: {mcp_error}")
                print("   Falling back to LLM-only mode")
                # Fallback to LLM-only mode
                self.llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)
                self.mcp_agent = None
                print("✅ Business Research Agent initialized with LLM fallback")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize Research agent: {e}")
            print("   Using mock responses.")
            self.mcp_agent = None
            self.llm = None

    async def invoke(self, message: Message) -> str:
        """Process a research request using the research framework."""
        task = message.parts[0].root.text
        
        # If MCP agent is available, use it for full web research
        if self.mcp_agent and OPENAI_API_KEY:
            try:
                print(f"🔍 Processing research request with MCP browser tools: {task}")
                # Use MCP agent for web research with browser capabilities
                result = await self.mcp_agent.run(task, max_steps=30)
                print(f"🔍 MCP research completed")
                return f"🔍 **Business Research & Locator Agent**\n\n{str(result)}"
                
            except Exception as e:
                print(f"⚠️  MCP Research agent error: {e}")
                import traceback
                traceback.print_exc()
                # Fall back to LLM-only mode
                if hasattr(self, 'llm') and self.llm:
                    print("🔄 Falling back to LLM-only research...")
                    return await self._llm_research(task)
                else:
                    return self._generate_fallback_response(task, str(e))
        
        # If LLM is available, use it for research guidance
        elif hasattr(self, 'llm') and self.llm and OPENAI_API_KEY:
            return await self._llm_research(task)
        
        # Fallback to mock response if nothing is available
        print("⚠️  Using mock response - no research capabilities available")
        return self._generate_mock_response(task)
    
    async def _llm_research(self, task: str) -> str:
        """Perform research using LLM only (without web browsing)."""
        try:
            print(f"🔍 Processing research request with LLM: {task}")
            
            # Use LLM to provide research guidance and information
            research_prompt = f"""You are a Business Research & Locator Agent specializing in South African business information, particularly MTN and mobile money services.

Research Request: {task}

Please provide comprehensive research guidance and information on this topic. Include:
1. Key information and facts you know
2. Relevant contacts or locations if applicable (based on your knowledge)
3. Market insights for South African context
4. Specific details about MTN services when relevant
5. Actionable recommendations

Focus on South African business context and provide practical, useful information. If you need to browse the web for current information, mention that web browsing capabilities would provide more up-to-date results."""

            response = self.llm.invoke(research_prompt)
            result = response.content if hasattr(response, 'content') else str(response)
            
            print(f"🔍 LLM research result generated")
            return f"🔍 **Business Research & Locator Agent**\n\n{result}"
            
        except Exception as e:
            print(f"⚠️  LLM Research error: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_fallback_response(task, str(e))
    
    def _generate_fallback_response(self, task: str, error: str) -> str:
        """Generate a fallback response when MCP encounters an error."""
        return f"""🔍 **Business Research & Locator Agent**

I encountered an issue while processing your research request: "{task}"

**Error Details:** {error}

**Alternative Suggestions:**
- Try rephrasing your request with more specific keywords
- Check if the website or service is currently accessible
- For store locations, try searching for "[business name] + [location]"
- For contact information, try "[company name] + contact details"

I can help with:
- Web research and information gathering
- Store and business location services  
- Market research and analysis
- Contact information discovery
- General information lookup

Please try your request again or let me know how else I can assist you!"""

    def _generate_mock_response(self, task: str) -> str:
        """Generate a mock response when MCP is not available."""
        return f"""🔍 **Business Research & Locator Agent**

**Research Request:** {task}

**Mock Response for Testing:**
I would normally use web browsing capabilities to research this topic, but I'm currently in mock mode.

**What I can help with:**
- 🌐 Web research and information gathering
- 📍 Store and business location services
- 📊 Market research and competitive analysis
- 📞 Contact information discovery
- 🔍 General information lookup and browsing

**To enable full functionality:**
1. Install MCP dependencies: `pip install mcp-use`
2. Configure browser_mcp.json for web browsing
3. Ensure OpenAI API key is properly set

**Sample Research Capabilities:**
- Navigate to university websites and extract contact details
- Find MTN store locations in specific cities
- Research market trends in mobile payments
- Gather competitive analysis data
- Extract business information from websites

Please configure the MCP framework for full web research capabilities!"""

class BusinessResearchAgentExecutor(AgentExecutor):
    """Business Research Agent Executor Implementation."""
    
    def __init__(self):
        self.agent = BusinessResearchAgent()
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute the research agent."""
        try:
            # Get the message from context
            message = context.message
            
            # Process the research request
            response = await self.agent.invoke(message)
            
            # Send the response
            await event_queue.enqueue_event(new_agent_text_message(response))
            
        except Exception as e:
            error_message = f"Research agent error: {str(e)}"
            print(f"❌ {error_message}")
            await event_queue.enqueue_event(new_agent_text_message(error_message))
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception('cancel not supported')

def main():
    """Main function to run the Business Research Agent."""
    print(f"🔍 Starting Business Research & Locator Agent on port {PORT}")
    
    # Create the request handler with our agent executor
    request_handler = DefaultRequestHandler(
        agent_executor=BusinessResearchAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    
    # Create the Starlette application
    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=public_agent_card,
    )
    
    print(f"🔍 Business Research & Locator Agent ready at {URL}")
    print("🌐 Capabilities: Web Research, Store Location, Market Analysis, Information Discovery")
    
    # Run the server
    uvicorn.run(server.build(), host="0.0.0.0", port=int(PORT))

if __name__ == '__main__':
    main()
