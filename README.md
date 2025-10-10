# inclusiV — MoMo x MediRescue, safely in chat

inclusiV turns everyday MTN MoMo activity into safe, simple access to emergency health protection with MediRescue. It combines a modern chat UI, agent-to-agent (A2A) orchestration, real-time provider verification, and ZAR‑first transactional UX.

## Problem we’re solving
MoMo users lack affordable, instant emergency health support and face friction in digital transactions. Providers can’t verify member status in real time. inclusiV removes friction with confirmations, makes verification provider‑ready, and embeds micro‑insurance guidance directly in MoMo flows.

## Core features
- MTN MoMo: balance, send money, airtime/data, payments (ZAR display, reference IDs, mandatory confirmations)
- MediRescue: view Basic/Plus plans, enroll, show cover/waiting period, start emergency dispatch, issue medicine vouchers
- Provider verification: modal form (SA ID + optional phone) → Insurance Agent returns VERIFIED/NOT VERIFIED
- MediRescue Advisor: plan comparisons, budget‑fit guidance, waiting period and voucher rules, YellowBucks wallet explainer
- Research & Locator: web research and store/location lookup (MCP browser tools with LLM fallback)
- UI/UX: modern chat, confirmation/selection modals, branded intro that fades on first message

## Agents (ports)
- MTN MoMo Transaction Agent: `http://127.0.0.1:9999`
- MediRescue Advisor: `http://127.0.0.1:9998`
- Insurance Agent (MediRescue): `http://127.0.0.1:9996`
- Business Research & Locator Agent: `http://127.0.0.1:9997`

## Quick start

### 1) Frontend (Next.js)
```bash
pnpm install
# Create .env in repo root and set OPENAI_API_KEY
pnpm dev
# App at http://localhost:3000
```

### 2) Backend agents (Python)
```bash
cd agents
python -m venv .venv
source .venv/bin/activate
# Install your Python deps as needed, then:
./run_agents.sh
```

Environment variables (e.g., OpenAI, MoMo keys) are read from the root `.env`. See `SETUP_API_KEY.md` for details.

## Configuration notes
- Frontend orchestrator is in `src/app/api/copilotkit/route.ts` (A2A routing, confirmation rules, verification flow)
- Chat UI and modals live in `src/app/a2a-chat.tsx`
- Real MoMo tools in `agents/toolz.py` (handles sandbox EUR internally; users see ZAR)
- Insurance logic and verification tool in `agents/insurance_agent.py`
- MediRescue advisor guidance in `agents/medirescue_advisor.py`

## Use cases
- Buy data/airtime with confirmation and a reference number
- Compare MediRescue plans, enroll, and check cover/waiting days
- Provider verifies a patient (ID/phone) and gets immediate status
- Start an emergency transport; receive dispatch confirmation
- Receive a medicine voucher after a no‑claim cycle
- Apply YellowBucks bonus toward the MediRescue wallet (advisor guidance)

## License
MIT
# a2a-demo
