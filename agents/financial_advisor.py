import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables from root directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from a2a.types import (
    Message
)
import openai

PORT = os.getenv("PORT", "9998")
URL = os.getenv("URL", f"http://localhost:{PORT}")

class MediRescueAdvisorAgent:
    """MediRescue Advisor Agent: advises on MediRescue micro‑health insurance plans, cover, and usage."""

    async def invoke(self, message: Message) -> str:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "developer", "content": """You are the MediRescue Advisor Agent. Your role is to clearly explain, compare, and recommend MediRescue micro‑health insurance options and usage.

WHAT YOU COVER:
- Plan guidance: differences between Basic and Plus (pricing, benefits, annual caps, per‑incident limits)
- Waiting period: standard 4‑week waiting period before emergency transport benefits activate
- Eligibility & enrollment: what’s needed to enroll (MSISDN, optional SA ID), how to proceed
- Emergency workflow: how dispatch works, what’s covered, typical amounts, claim references
- Vouchers: when medicine vouchers are issued (e.g., no‑claim cycles), validity and usage
- Budget fit: help users pick a plan that suits their budget and needs

PLANS (default demo values):
- Basic: R29/mo • Up to R1,000 per incident • R2,000 annual cover
- Plus:  R59/mo • Up to R2,000 per incident • R5,000 annual cover

GUIDANCE STYLE:
- Be concise, friendly, and practical. Use South African context and Rand amounts.
- If the user asks to see plans, suggest opening the plans picker.
- If the user chooses a plan, suggest enrollment next (which will be handled by the Insurance Agent).
- If asked to verify membership status, indicate that verification is handled by the Insurance Agent.

IMPORTANT:
- You do not execute enrollments or verifications yourself; you advise. Enrollment and verification are performed by the Insurance Agent.
"""},
                {"role": "user", "content": message.parts[0].root.text}
            ]
        )
        return response.choices[0].message.content

skill = AgentSkill(
    id='medirescue_advisor_agent',
    name='MediRescue Advisor',
    description='Advises on MediRescue micro‑health insurance plans, cover limits, waiting periods, emergency transport flow, and vouchers.',
    tags=['insurance', 'medirescue', 'health', 'advice', 'plans', 'vouchers'],
    examples=[
        'Explain the difference between Basic and Plus plans',
        'Which plan fits a tight budget and occasional emergencies?',
        'How does the waiting period work for new members?',
        'What happens during an emergency transport dispatch?',
        'When do I get a medicine voucher if I don’t claim?',
    ],
)

public_agent_card = AgentCard(
    name='MediRescue Advisor',
    description='Advisor for MediRescue micro‑health insurance: plan guidance (Basic/Plus), cover limits, waiting periods, emergency flow, and vouchers.',
    url=f'{URL}/',
    version='1.0.0',
    defaultInputModes=['text'],
    defaultOutputModes=['text'],
    capabilities=AgentCapabilities(streaming=True),
    skills=[skill],  # Only the basic skill for the public card
    supportsAuthenticatedExtendedCard=True,
)


class MediRescueAdvisorAgentExecutor(AgentExecutor):
    """MediRescue Advisor Agent Implementation."""

    def __init__(self):
        self.agent = MediRescueAdvisorAgent()

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
    request_handler = DefaultRequestHandler(
        agent_executor=MediRescueAdvisorAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=public_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=int(PORT))

if __name__ == '__main__':
    main()
