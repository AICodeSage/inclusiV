#!/usr/bin/env python3
"""
MoMo Micro-Health Insurance Agent (Emergency transport + medicine vouchers)
Using Agno + A2A for interop. Minimal in-memory state with simple JSON persistence.
"""
import os
import json
import uuid
import time
from typing import Any, Dict, Optional

import uvicorn
from dotenv import load_dotenv

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Agno
from agno.agent.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool

# A2A
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill, Message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("INSURANCE_PORT", "9996"))
URL = os.getenv("INSURANCE_URL", f"http://localhost:{PORT}")

STATE_FILE = os.path.join(os.path.dirname(__file__), "tmp_insurance_state.json")

def _load_state() -> Dict[str, Any]:
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {"members": {}, "claims": [], "vouchers": []}

def _save_state(state: Dict[str, Any]) -> None:
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception:
        pass


# ---------------------
# Tools (minimal logic)
# ---------------------
@tool(name="enroll_member", description="Enroll a member with tier 'basic' or 'plus'. Optionally capture South African ID number.")
def enroll_member(msisdn: str, tier: str = "basic", id_number: str = "") -> Dict[str, Any]:
    state = _load_state()
    member = state["members"].get(msisdn, {})
    now = int(time.time())
    member.update({
        "msisdn": msisdn,
        "tier": tier.lower(),
        "joined_at": now,
        "wait_until": now + 28*24*3600,  # 4-week waiting period
        "annual_cap_remaining": 2000 if tier.lower()=="basic" else 5000,
        "cycles_no_claim": 0,
    })
    if id_number:
        member["id_number"] = id_number.strip()
    state["members"][msisdn] = member
    _save_state(state)
    return {"status": "ok", "member": member}


@tool(name="show_cover", description="Show member cover summary.")
def show_cover(msisdn: str) -> Dict[str, Any]:
    state = _load_state()
    m = state["members"].get(msisdn)
    if not m:
        return {"status": "not_found", "message": "Member not enrolled"}
    now = int(time.time())
    waiting_days = max(0, int((m.get("wait_until", now) - now)/86400))
    tier = m.get("tier", "basic")
    cap = m.get("annual_cap_remaining", 0)
    return {
        "status": "ok",
        "msisdn": msisdn,
        "tier": tier,
        "waiting_days": waiting_days,
        "annual_cap_remaining": cap,
        "id_number": m.get("id_number", ""),
        "message": f"Tier {tier.capitalize()} • Waiting {waiting_days} days • Remaining cover R{cap}",
    }


@tool(name="start_emergency", description="Start emergency transport workflow and simulate partner dispatch.")
def start_emergency(msisdn: str, location: str = "") -> Dict[str, Any]:
    state = _load_state()
    m = state["members"].get(msisdn)
    if not m:
        return {"status": "not_found", "message": "Member not enrolled"}
    now = int(time.time())
    if now < m.get("wait_until", now):
        return {"status": "waiting_period", "message": "Waiting period active"}
    per_incident_cap = 1000 if m.get("tier") == "basic" else 2000
    claim_id = str(uuid.uuid4())
    # Simulate partner assigned and reserve amount
    paid = min(per_incident_cap, m.get("annual_cap_remaining", 0))
    m["annual_cap_remaining"] = max(0, m.get("annual_cap_remaining", 0) - paid)
    state["claims"].append({
        "id": claim_id, "msisdn": msisdn, "ts": now,
        "type": "transport", "paid_amount": paid, "location": location,
    })
    m["cycles_no_claim"] = 0
    state["members"][msisdn] = m
    _save_state(state)
    return {
        "status": "ok",
        "claim_id": claim_id,
        "paid_amount": paid,
        "message": f"🚑 Dispatch confirmed. Reserved up to R{paid} for transport. Claim {claim_id}.",
    }


@tool(name="issue_voucher", description="Issue medicine voucher for no-claim cycle (if eligible).")
def issue_voucher(msisdn: str, amount: str = "150") -> Dict[str, Any]:
    state = _load_state()
    m = state["members"].get(msisdn)
    if not m:
        return {"status": "not_found", "message": "Member not enrolled"}
    # Simplified eligibility: always allow demo issuance
    code = f"VCHR-{uuid.uuid4().hex[:8].upper()}"
    v = {"code": code, "msisdn": msisdn, "amount": amount, "expires_in_days": 90}
    state["vouchers"].append(v)
    _save_state(state)
    return {"status": "ok", "voucher": v, "message": f"🎟️ Issued voucher {code} for R{amount}"}


@tool(name="list_deals_by_budget", description="List once-off data deals within budget (mock).")
def list_deals_by_budget(budgetZAR: str) -> Dict[str, Any]:
    deals = [
        {"code": "50MB_DAILY", "name": "50MB Daily", "size": "50MB", "validity": "1 day", "priceZAR": "5"},
        {"code": "200MB_DAILY", "name": "200MB Daily", "size": "200MB", "validity": "1 day", "priceZAR": "12"},
        {"code": "1GB_WEEKLY", "name": "1GB Weekly", "size": "1GB", "validity": "7 days", "priceZAR": "35"},
        {"code": "3GB_WEEKLY", "name": "3GB Weekly", "size": "3GB", "validity": "7 days", "priceZAR": "79"},
        {"code": "5GB_ANYTIME", "name": "5GB Anytime", "size": "5GB", "validity": "30 days", "priceZAR": "149"},
    ]
    try:
        b = float(str(budgetZAR).replace("R", "").strip())
    except Exception:
        b = 0.0
    filtered = [d for d in deals if float(d["priceZAR"]) <= b]
    return {"status": "ok", "deals": filtered}


@tool(name="verify_member_by_id", description="Verify if a user with SA ID (and optional phone) is an active member for emergency transport. Optionally include provider_name to state it clearly in the message.")
def verify_member_by_id(id_number: str, msisdn: str = "", provider_name: str = "") -> Dict[str, Any]:
    state = _load_state()
    # Try by msisdn first if given
    m: Optional[Dict[str, Any]] = None
    if msisdn and msisdn in state.get("members", {}):
        m = state["members"][msisdn]
    # Else search by id
    if not m:
        for _msisdn, member in state.get("members", {}).items():
            if member.get("id_number") == id_number.strip():
                m = member
                msisdn = _msisdn
                break
    if not m:
        return {"status": "not_found", "verified": False, "provider": provider_name, "message": f"❌ NOT VERIFIED with {provider_name or 'provider'}: no active membership found for this ID."}
    now = int(time.time())
    waiting = now < m.get("wait_until", now)
    cap = m.get("annual_cap_remaining", 0)
    verified = (not waiting) and cap > 0
    status = "waiting" if waiting else ("active" if verified else "inactive")
    result = {
        "status": status,
        "verified": verified,
        "msisdn": msisdn,
        "id_number": m.get("id_number", ""),
        "tier": m.get("tier", "basic"),
        "annual_cap_remaining": cap,
        "provider": provider_name,
    }
    if verified:
        result["message"] = f"✅ VERIFIED with {provider_name or 'provider'}: member ACTIVE for emergency transport. Remaining cover R{cap}."
    elif waiting:
        result["message"] = f"⏳ NOT VERIFIED with {provider_name or 'provider'}: waiting period in effect."
    else:
        result["message"] = f"❌ NOT VERIFIED with {provider_name or 'provider'}: no available cover."
    return result


# --------------
# Agent metadata
# --------------
skills = [
    AgentSkill(
        id="membership",
        name="Membership & Cover",
        description="Enroll members, show cover, and manage waiting periods.",
        tags=["enroll", "cover", "member"],
    ),
    AgentSkill(
        id="emergency",
        name="Emergency Transport",
        description="Start emergency transport and simulate provider payout.",
        tags=["emergency", "transport"],
    ),
    AgentSkill(
        id="vouchers",
        name="Medicine Vouchers",
        description="Issue medicine vouchers for no-claim cycles.",
        tags=["voucher", "pharmacy"],
    ),
]

card = AgentCard(
    name="MoMo Micro-Health Insurance Agent",
    description="Emergency transport micro-insurance with medicine vouchers.",
    url=f"{URL}/",
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=skills,
)


class InsuranceAgent:
    def __init__(self) -> None:
        self.agent: Optional[Agent] = None
        self._init()

    def _init(self) -> None:
        tools = [
            enroll_member, show_cover, start_emergency,
            issue_voucher, list_deals_by_budget,
        ]
        self.agent = Agent(
            model=OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None,
            tools=tools,
            show_tool_calls=True,
            description="Insurance agent for emergency transport + vouchers.",
            instructions=[
                "You help MoMo users with simple emergency transport cover and medicine vouchers.",
                "Ask for the user's phone number and tier/budget only when needed.",
                "For data deal queries with a budget, call list_deals_by_budget and present options.",
                "Keep responses short and clear; output only the final content.",
            ],
        )

    async def invoke(self, message: Message) -> str:
        text = message.parts[0].root.text
        if not self.agent:
            return "Insurance agent not initialized."
        try:
            res = self.agent.run(text)
            return res.content if hasattr(res, "content") else str(res)
        except Exception as e:
            return f"Insurance service error: {e}"


class InsuranceExecutor(AgentExecutor):
    def __init__(self):
        self.agent = InsuranceAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        out = await self.agent.invoke(context.message)
        await event_queue.enqueue_event(new_agent_text_message(out))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")


def main():
    print(f"🛡️  Insurance Agent starting on {PORT}…")
    handler = DefaultRequestHandler(agent_executor=InsuranceExecutor(), task_store=InMemoryTaskStore())
    app = A2AStarletteApplication(agent_card=card, http_handler=handler, extended_agent_card=card)
    print(f"🚀 Insurance Agent ready at {URL}")
    uvicorn.run(app.build(), host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()


