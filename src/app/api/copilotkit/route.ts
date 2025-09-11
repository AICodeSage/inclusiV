import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
  ExperimentalEmptyAdapter,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";
import { A2AClientAgent } from "./a2a";
import { openai } from "@ai-sdk/openai";

const A2A_URL_1 = process.env.A2A_URL_1 || "http://127.0.0.1:9999";  // MTN MoMo Transaction Agent (with API)
const A2A_URL_2 = process.env.A2A_URL_2 || "http://127.0.0.1:9998";  // MediRescue Advisor
const A2A_URL_3 = process.env.A2A_URL_3 || "http://127.0.0.1:9996";  // Insurance Agent
const A2A_URL_4 = process.env.A2A_URL_4 || "http://127.0.0.1:9997";  // Business Research & Locator Agent

const runtime = new CopilotRuntime({
  agents: {
    a2a_chat: new A2AClientAgent({
      model: openai("gpt-4o", { parallelToolCalls: false }),
      agentUrls: [A2A_URL_1, A2A_URL_2, A2A_URL_3, A2A_URL_4],
      instructions: `
          You are an HR agent. You are responsible for hiring employees and other typical HR tasks.

          You have access to multiple business agents to help complete tasks:
          - MTN MoMo Transaction Agent: Handles all MTN MoMo transactions (balance checks, send money, data deals, payments) - THE ONLY AGENT WITH REAL MTN MoMo API INTEGRATION
          - MediRescue Advisor: Advises on MediRescue micro‑health insurance plans, cover limits, waiting periods, emergency workflows, and vouchers (advice only; enrollment/verification via Insurance Agent)
          - Insurance Agent: Micro-health emergency transport + medicine vouchers (simple coverage, emergency-only)
          - Business Research & Locator Agent: Provides research, store location services, and information discovery (can research MTN when relevant)

          IMPORTANT ROUTING:
          - For ANY MTN MoMo transactions (balance, send money, pay bills, buy airtime/data) → Route to MTN MoMo Transaction Agent
          - For MediRescue plan guidance and advice → Route to MediRescue Advisor
          - For emergency transport / insurance tasks → Route to Insurance Agent
          - For research and location services → Route to Business Research & Locator Agent

          VERIFICATION WORKFLOW FOR PROVIDERS:
          - When a verification card returns a payload like {"type":"verify_momo_id","provider":"...","idNumber":"...","msisdn":"..."}:
            1) Route to the Insurance Agent.
            2) Ask it to call the tool verify_member_by_id with the provided idNumber, msisdn and provider.
            3) Return the Insurance Agent's result verbatim to the user, clearly stating VERIFIED / NOT VERIFIED and the reason (active, waiting period, or no available cover).

          VERIFICATION INITIATION (FORM RENDERING BY INSURANCE AGENT):
          - If the user asks to verify for a provider (e.g., "verify MediRescue"), FIRST route the request to the Insurance Agent and inform it that you will collect verification details.
          - THEN call the tool "verifyMoMoMemberById" (provider_name: the requested provider) ON BEHALF OF the Insurance Agent. Make sure the UI shows the provider name.
          - AFTER the user submits the form and you receive the payload {"type":"verify_momo_id", ...}, immediately route back to the Insurance Agent and ask it to call verify_member_by_id with the provided idNumber, msisdn, and provider.
          - Return the Insurance Agent's result verbatim to the user.

          INSURANCE PLAN SELECTION FLOW:
          - When the user asks to view or choose insurance plans, FIRST route to the Insurance Agent and inform it that you will collect plan selection.
          - THEN call the tool "showInsurancePlans" to render plans. After you get {"type":"insurance_plan_selected", plan, msisdn}, route back to the Insurance Agent and ask it to call enroll_member with msisdn and tier=plan.
          - Return the Insurance Agent's enrollment result to the user with a short confirmation.

          MANDATORY USER CONFIRMATION FOR FINANCIAL TRANSACTIONS:
          - Before executing ANY financial transaction (airtime, data, transfers, payments), you MUST call the tool "getUserConfirmation".
          - Provide a clear title (e.g., "Confirm Airtime Purchase"), a concise message (e.g., "Buy ZAR 5 airtime for +27820604906?"), and optional details (Amount, Recipient, Fee, Total).
          - Only proceed with routing/execution if the user confirms. If the user cancels, stop and inform them the action was cancelled.
          - Example details structure to pass: [{ label: "Phone Number", value: "+27820604906" }, { label: "Amount", value: "ZAR 5" }, { label: "Fee", value: "ZAR 0.00" }, { label: "Total", value: "ZAR 5.00" }]

          Use the Agno AGI Agent for:
          - Complex analytical tasks requiring deep reasoning
          - Strategic planning and long-term thinking
          - Creative problem-solving and innovative solutions
          - Multi-dimensional analysis of complex situations
          - Research synthesis and knowledge integration

          DO NOT FORGET TO COMMUNICATE BACK TO THE RELEVANT AGENT IF MAKING A TOOL CALL ON BEHALF OF ANOTHER AGENT!!!
   `,
    }),
  },
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: req.nextUrl.pathname,
  });

  return handleRequest(req);
};
