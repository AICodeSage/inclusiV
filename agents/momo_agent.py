#!/usr/bin/env python3
"""
MTN MoMo Transaction Agent for A2A Demo
Using the Agno framework for MTN MoMo transactions with A2A protocol compatibility.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional
import uvicorn
from dotenv import load_dotenv

# Load environment variables from root directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Agno Framework imports
from agno.agent.agent import Agent
from agno.models.openai import OpenAIChat

# A2A Protocol imports
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Message
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

# Import MoMo tools
from toolz import (
    buy_airtime, buy_data, transfer_money,
    check_balance, validate_number, check_tx_status,
    test_momo_connection, get_data_deals
)

# Load environment variables
load_dotenv()

# Configuration
PORT = os.getenv("PORT", "9999")
URL = os.getenv("URL", f"http://localhost:{PORT}")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Agent Skills - Define the MoMo Agent's capabilities
balance_skill = AgentSkill(
    id='balance_management',
    name='Balance Check & Account Management',
    description='Check MoMo wallet balance, account status, and transaction history.',
    tags=['balance', 'account', 'wallet', 'momo'],
    examples=[
        'Check my MoMo balance',
        'What is my current wallet balance?',
        'Show me my account status'
    ],
)

transfer_skill = AgentSkill(
    id='money_transfer',
    name='Money Transfer & Payments',
    description='Send money to other MoMo users and make payments.',
    tags=['transfer', 'send', 'payment', 'money'],
    examples=[
        'Send R100 to 0712345678',
        'Transfer money to my friend',
        'Pay R50 to merchant'
    ],
)

airtime_data_skill = AgentSkill(
    id='airtime_data_purchase',
    name='Airtime & Data Bundle Purchase',
    description='Buy airtime and data bundles for yourself or others.',
    tags=['airtime', 'data', 'bundles', 'purchase'],
    examples=[
        'Buy R50 airtime for my number',
        'Purchase 1GB data bundle',
        'Buy airtime for 0823456789'
    ],
)

transaction_skill = AgentSkill(
    id='transaction_management',
    name='Transaction Validation & Status',
    description='Validate phone numbers and check transaction status.',
    tags=['validation', 'transaction', 'status', 'verify'],
    examples=[
        'Check status of transaction TXN123456',
        'Validate phone number 0712345678',
        'Is my last transaction successful?'
    ],
)

# Agent Card - Describes the MoMo Agent's capabilities
public_agent_card = AgentCard(
    name='MTN MoMo Transaction Agent',
    description='MTN MoMo Transaction Agent for South African mobile money services. Handles balance checks, money transfers, airtime/data purchases, transaction validation, and bill payments through MTN MoMo API integration.',
    url=f'{URL}/',
    version='1.0.0',
    defaultInputModes=['text'],
    defaultOutputModes=['text'],
    capabilities=AgentCapabilities(streaming=True),
    skills=[balance_skill, transfer_skill, airtime_data_skill, transaction_skill],
    supportsAuthenticatedExtendedCard=True,
)

# Note: Removed custom_response_hook as it was causing compatibility issues with Agno framework

class MoMoTransactionAgent:
    """
    MTN MoMo Transaction Agent - Using Agno framework for MoMo transactions
    with A2A protocol compatibility.
    """
    
    def __init__(self):
        """Initialize the MoMo agent with Agno framework."""
        self.agno_agent = None
        self._initialize_agno_agent()
    
    def _initialize_agno_agent(self):
        """Initialize the Agno agent for MoMo transactions."""
        try:
            # Initialize Agno agent with MoMo tools
            self.agno_agent = Agent(
                model=OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None,
                tools=[
                    buy_airtime, buy_data, transfer_money,
                    check_balance, validate_number, check_tx_status,
                    test_momo_connection, get_data_deals,
                ],
                show_tool_calls=True,
                description="MoMo Agent that can buy airtime/data, transfer money, check balances, validate numbers, and check transactions.",
                # tool_hooks removed due to compatibility issues
                instructions=[
                    "You are a MoMo agent specifically for South Africa. You can buy airtime/data, transfer money, check balances, validate numbers, and check transactions.",
                    "",
                    "Important context:",
                    "- You operate in South Africa",
                    "- Default currency is ZAR (South African Rand)",
                    "- Phone numbers should be in South African format (+27)",
                    "- When users ask about airtime, data, or money transfers, assume they mean ZAR unless specified otherwise",
                    "- Always confirm South African phone numbers and amounts in ZAR",
                    "",
                    "When displaying balance information:",
                    "- Call check_balance tool ONCE to get balance data",
                    "- Display the balance clearly to the user",
                    "- Do NOT retry the balance check if it fails - show the error message instead",
                    "- Always provide helpful context about the balance and account status",
                    "",
                    "Only include the output in your response. No other text.",
                ],
            )
            
            print("📱 MoMo Agno agent initialized successfully")
                    
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize full MoMo Agno agent: {e}")
            print("   Falling back to mock responses.")
            self.agno_agent = None

    async def invoke(self, message: Message) -> str:
        """Process a MoMo transaction request using the Agno framework."""
        task = message.parts[0].root.text
        
        # If Agno agent is properly initialized, use it
        if self.agno_agent and OPENAI_API_KEY:
            try:
                print(f"📱 Processing MoMo request: {task}")
                # Use Agno's response generation with MoMo tools
                response = self.agno_agent.run(task)
                print(f"📱 Agno response type: {type(response)}")
                print(f"📱 Agno response: {response}")
                
                if response is None:
                    print("⚠️  Agno returned None - using fallback")
                    return self._generate_fallback_response(task, "Agno agent returned None")
                
                result = response.content if hasattr(response, 'content') else str(response)
                print(f"📱 Final result: {result}")
                return result
                
            except Exception as e:
                print(f"⚠️  MoMo Agno agent error: {e}")
                import traceback
                traceback.print_exc()
                return self._generate_fallback_response(task, str(e))
        
        # Fallback to mock response if Agno is not available
        print("⚠️  Using mock response - Agno not available")
        return self._generate_mock_response(task)
    
    def _generate_fallback_response(self, task: str, error: str) -> str:
        """Generate a fallback response when Agno encounters an error."""
        return f"""📱 **MTN MoMo Transaction Agent**

**Request:** {task}

⚠️  **Note:** MoMo service encountered an issue ({error}), providing manual assistance:

**Available MoMo Services:**

💰 **Balance & Account:**
- Check wallet balance and account status
- View transaction history
- Account management

💸 **Money Transfer:**
- Send money to MTN and other networks
- Receive money notifications
- Transfer confirmations

📱 **Airtime & Data:**
- Buy airtime for any network
- Purchase data bundles
- Gift airtime to others

🧾 **Transaction Support:**
- Check transaction status
- Validate phone numbers
- Transaction receipts

*This response was generated using MoMo's fallback system. For full functionality, ensure proper API keys are configured.*"""

    def _generate_mock_response(self, task: str) -> str:
        """Generate a mock response when Agno framework is not available."""
        task_lower = task.lower()
        
        if any(word in task_lower for word in ['balance', 'check balance', 'my balance']):
            return """💰 **MTN MoMo Balance Check**

**Available Balance:** R 1,250.50
**Currency:** ZAR (South African Rand)
**Account Status:** Active
**Last Transaction:** 2024-01-15 14:30

Your MoMo wallet is active and ready for transactions!

⚠️  **Configuration Notice:** MoMo agent requires API keys for live data.

**To Enable Full MoMo Features:**
1. Set `OPENAI_API_KEY` for transaction processing
2. Configure MoMo API credentials
3. Restart the agent for full functionality

*This is a demonstration response. Configure API keys for real MoMo transactions.*"""

        elif any(word in task_lower for word in ['send money', 'transfer', 'send r']):
            return """💸 **Money Transfer Service**

**Request:** {task}

⚠️  **Demo Mode:** MoMo transfer service requires API configuration.

**Transfer Process:**
1. Validate recipient number
2. Confirm transfer amount
3. Process transaction
4. Send confirmation SMS

**To Enable Live Transfers:**
- Configure OPENAI_API_KEY
- Set up MoMo API credentials
- Restart agent for full functionality

*This is a demonstration. Configure API keys for actual money transfers.*"""

        else:
            return f"""📱 **MTN MoMo Transaction Agent**

**Request:** {task}

⚠️  **Configuration Required:** MoMo agent needs API keys for full functionality.

**Available Services (Demo Mode):**
- 💰 Balance checks and account status
- 💸 Money transfers and payments  
- 📱 Airtime and data purchases
- 🧾 Transaction validation and status
- ✅ Phone number validation

**To Enable Full MoMo Services:**
1. Set `OPENAI_API_KEY` environment variable
2. Configure MoMo API credentials  
3. Restart the agent

*This is a demonstration of MoMo's service structure. Configure API keys for live transactions.*"""


class MoMoTransactionAgentExecutor(AgentExecutor):
    """MTN MoMo Transaction Agent Executor Implementation."""

    def __init__(self):
        self.agent = MoMoTransactionAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        result = await self.agent.invoke(context.message)
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')


def main():
    """Main function to start the MTN MoMo Transaction Agent server."""
    print(f"📱 Starting MTN MoMo Transaction Agent on port {PORT}...")
    
    if not OPENAI_API_KEY:
        print("⚠️  Warning: OPENAI_API_KEY not set. Agent will use mock responses.")
        print("   Set OPENAI_API_KEY environment variable for full MoMo capabilities.")
    
    request_handler = DefaultRequestHandler(
        agent_executor=MoMoTransactionAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=public_agent_card,
    )

    print(f"🚀 MTN MoMo Transaction Agent ready at {URL}")
    print("💰 Capabilities: Balance Check, Money Transfer, Airtime/Data Purchase, Transaction Management")
    
    uvicorn.run(server.build(), host='0.0.0.0', port=int(PORT))


if __name__ == '__main__':
    main()