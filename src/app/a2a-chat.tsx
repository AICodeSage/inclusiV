"use client";
import React, { useEffect, useState, useCallback } from "react";
import "@copilotkit/react-ui/styles.css";

import {
  CopilotKit,
  useCoAgent,
  useCoAgentStateRender,
  useCopilotAction,
  useCopilotChat,
} from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";

interface A2AChatProps {
  onNotification?: () => void;
}

const A2AChat: React.FC<A2AChatProps> = ({ onNotification }) => {
  return (
    <CopilotKit
      runtimeUrl={`/api/copilotkit`}
      showDevConsole={false}
      // agent lock to the relevant agent
      agent="a2a_chat"
    >
      <Chat onNotification={onNotification} />
    </CopilotKit>
  );
};

interface A2AChatState {
  a2aMessages: { name: string; to: string; message: string }[];
}

interface Seat {
  seatNumber: number;
  status: "available" | "occupied";
  name?: string;
}

interface Table {
  name: string;
  seats: Seat[];
}

const Chat = ({ onNotification }: { onNotification?: () => void }) => {
  const { state } = useCoAgent({ name: "a2a_chat" });

  const { isLoading, visibleMessages } = useCopilotChat();
  const [brandAnimateIn, setBrandAnimateIn] = useState(false);

  useEffect(() => {
    if ((visibleMessages?.length || 0) === 0) {
      const id = setTimeout(() => setBrandAnimateIn(true), 60);
      return () => clearTimeout(id);
    }
    setBrandAnimateIn(false);
  }, [visibleMessages?.length]);

  const handleNotification = useCallback(() => {
    onNotification?.();
  }, [onNotification]);

  useEffect(() => {
    if (
      visibleMessages.length > 0 &&
      (!isLoading ||
        (
          visibleMessages[visibleMessages.length - 1] as unknown as {
            name?: string;
          }
        ).name === "pickTable")
    ) {
      handleNotification();
    }
  }, [isLoading, visibleMessages, handleNotification]);

  React.useEffect(() => {
    // This effect runs when a2aMessages changes - no specific action needed
  }, [state?.a2aMessages]);

  useCoAgentStateRender<A2AChatState>({
    name: "a2a_chat",
    render: ({ state }) => {
      if (!state.a2aMessages || state.a2aMessages.length === 0) {
        return null;
      }
      return (
        <div className="w-full max-w-[800px] mx-auto mb-4 text-left px-4">
          <div className="space-y-2">
            {state.a2aMessages.map((message, idx) => {
              return (
                <div
                  key={idx}
                  className="bg-white border border-gray-200 rounded-lg px-3 py-2"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 min-w-[160px]">
                      <span
                        className={`px-2 py-1 rounded-full text-[10px] font-medium ${
                          message.name === "Agent"
                            ? "bg-green-100 text-green-700"
                            : "bg-blue-100 text-blue-700"
                        }`}
                      >
                        {message.name}
                      </span>
                      <span className="text-muted-foreground text-[11px]">
                        →
                      </span>
                      <span className="px-2 py-1 rounded-full text-[10px] font-medium bg-white border border-gray-300 text-muted-foreground">
                        {message.to}
                      </span>
                    </div>
                    <span className="break-words text-[11px] flex-1">
                      {message.message}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      );
    },
  });

  // Insurance plans picker (modal): lets user view and choose a plan
  useCopilotAction({
    name: "showInsurancePlans",
    description:
      "Render available micro-health insurance plans as cards (Basic, Plus). Returns selected plan and prompts enrollment.",
    parameters: [
      { name: "msisdn", type: "string", description: "Optional MSISDN to enroll", required: false },
    ],
    renderAndWaitForResponse: function ShowInsurancePlans({ args, respond }) {
      const plans = [
        {
          id: "basic",
          name: "Basic",
          price: "R29/mo",
          cap: "R2,000 annual cover",
          perIncident: "Up to R1,000 per incident",
          features: ["Emergency transport", "Simple, affordable", "4‑week waiting period"],
        },
        {
          id: "plus",
          name: "Plus",
          price: "R59/mo",
          cap: "R5,000 annual cover",
          perIncident: "Up to R2,000 per incident",
          features: ["Priority dispatch", "Higher cover limits", "4‑week waiting period"],
        },
      ];

      const [selected, setSelected] = useState<string | null>(null);
      const [busy, setBusy] = useState(false);
      const [closed, setClosed] = useState(false);

      const submit = () => {
        if (!selected || busy) return;
        setBusy(true);
        respond?.(
          JSON.stringify({
            type: "insurance_plan_selected",
            plan: selected,
            msisdn: (args.msisdn || "").trim(),
          })
        );
        Promise.resolve().then(() => setClosed(true));
      };

      if (closed) {
        return <div />;
      }

      return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center px-4">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
          <div className="relative z-[61] my-8 mx-auto max-w-2xl w-full overflow-hidden rounded-2xl border border-white/20 bg-white/50 backdrop-blur-sm supports-[backdrop-filter]:bg-white/40 shadow-xl">
            <div className="flex items-start gap-3 px-6 py-4 border-b border-white/20">
              <div className="inline-flex h-10 w-10 flex-none items-center justify-center rounded-full bg-slate-900/80 text-white shadow-sm ring-4 ring-white/20">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div className="min-w-0">
                <h2 className="truncate text-lg font-semibold text-slate-900">Choose your Micro‑Health plan</h2>
                <p className="mt-1 text-sm text-slate-600">Emergency transport + simple cover. Cancel anytime.</p>
              </div>
            </div>

            <div className="px-6 py-6 grid grid-cols-1 md:grid-cols-2 gap-5">
              {plans.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setSelected(p.id)}
                  className={`text-left rounded-2xl border overflow-hidden transform transition-all duration-200 ${
                    selected === p.id
                      ? "border-slate-900/20 bg-white shadow-2xl ring-2 ring-slate-900/10"
                      : "border-slate-200 bg-white/80 hover:bg-white hover:shadow-2xl hover:-translate-y-0.5"
                  }`}
                >
                  <div className="p-5">
                    <div className="flex items-center justify-between">
                      <div className="text-lg font-semibold text-slate-900">{p.name}</div>
                      <div className="text-slate-900 font-extrabold text-xl">{p.price}</div>
                    </div>
                    <div className="mt-3 text-sm text-slate-700">{p.cap}</div>
                    <div className="mt-1 text-sm text-slate-700">{p.perIncident}</div>
                    <ul className="mt-3 text-sm text-slate-600 list-disc pl-5 space-y-1">
                      {p.features.map((f, i) => (
                        <li key={i}>{f}</li>
                      ))}
                    </ul>
                  </div>
                </button>
              ))}
            </div>

            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/20">
              <button
                onClick={submit}
                disabled={!selected || busy}
                className={`inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
                  !selected
                    ? "bg-slate-400"
                    : busy
                    ? "bg-slate-900/80"
                    : "bg-slate-900 hover:bg-slate-800"
                }`}
              >
                {busy ? (
                  <>
                    <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                    </svg>
                    Submitting…
                  </>
                ) : (
                  selected ? `Continue with ${selected.toUpperCase()}` : "Choose a plan"
                )}
              </button>
            </div>
          </div>
        </div>
      );
    },
  });

  // Verification card: styled like the confirmation card (collect SA ID and optional phone)
  useCopilotAction({
    name: "verifyMoMoMemberById",
    description:
      "Render a verification card for private health providers to input South African ID number (and optional phone). Returns a payload to verify the MoMo user.",
    parameters: [
      { name: "provider_name", type: "string", description: "Provider name (e.g., MediRescue)", required: false },
    ],
    renderAndWaitForResponse: function VerifyByIdCard({ args, respond }) {
      const [idNumber, setIdNumber] = useState<string>("");
      const [msisdn, setMsisdn] = useState<string>("");
      const [consent, setConsent] = useState<boolean>(false);
      const [error, setError] = useState<string>("");
      const [busy, setBusy] = useState<boolean>(false);
      const [submitted, setSubmitted] = useState<boolean>(false);
      const [closed, setClosed] = useState<boolean>(false);

      const isValidId = (v: string) => /^[0-9]{13}$/.test(v.trim());

      const submit = () => {
        setError("");
        if (!isValidId(idNumber)) {
          setError("Please enter a valid 13‑digit South African ID number.");
          return;
        }
        if (!consent) {
          setError("Please confirm consent/emergency legal basis to proceed.");
          return;
        }
        setBusy(true);
        respond?.(
          JSON.stringify({
            type: "verify_momo_id",
            provider: args.provider_name || "",
            idNumber: idNumber.trim(),
            msisdn: (msisdn || "").trim(),
          })
        );
        // Flip button state to Submitted after sending
        Promise.resolve().then(() => {
          setSubmitted(true);
          setClosed(true); // Immediately close modal and return to chat
        });
      };

      if (closed) {
        return <div />;
      }

      return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center px-4">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

          {/* Modal Card */}
          <div className="relative z-[61] my-8 mx-auto max-w-md w-full overflow-hidden rounded-2xl border border-white/20 bg-white/50 backdrop-blur-sm supports-[backdrop-filter]:bg-white/40 shadow-xl">
            {/* Header (matches confirmation card style) */}
            <div className="flex items-start gap-3 px-6 py-4 border-b border-white/20">
              <div className="inline-flex h-10 w-10 flex-none items-center justify-center rounded-full bg-slate-900/80 text-white shadow-sm ring-4 ring-white/20">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="min-w-0">
                <h2 className="truncate text-lg font-semibold text-slate-900">Emergency MoMo Verification</h2>
                {args.provider_name ? (
                  <p className="mt-1 text-sm text-slate-600">Provider: {args.provider_name}</p>
                ) : null}
              </div>
            </div>

            {/* Body */}
            <div className="px-6 py-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">South African ID Number</label>
                <input
                  value={idNumber}
                  onChange={(e) => setIdNumber(e.target.value.replace(/[^0-9]/g, "").slice(0, 13))}
                  placeholder="13 digits"
                  className="w-full rounded-lg border border-slate-300 bg-white/90 px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Phone Number (optional)</label>
                <input
                  value={msisdn}
                  onChange={(e) => setMsisdn(e.target.value)}
                  placeholder="+2782… or 082…"
                  className="w-full rounded-lg border border-slate-300 bg-white/90 px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-500"
                />
              </div>
              <label className="flex items-start gap-2 text-xs text-slate-700">
                <input
                  type="checkbox"
                  className="mt-0.5"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                />
                I confirm consent/emergency legal basis to verify this MoMo user for medical response.
              </label>
              {error ? <div className="text-xs text-red-600">{error}</div> : null}
            </div>

            {/* Footer (matches confirmation card style) */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/20">
              <button
                disabled={busy || submitted}
                onClick={submit}
                className={`inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-50 ${
                  submitted
                    ? "bg-green-600"
                    : busy
                    ? "bg-slate-900/80"
                    : "bg-slate-900 hover:bg-slate-800 focus:ring-slate-500/50"
                }`}
              >
                {submitted ? (
                  <>
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    Submitted
                  </>
                ) : busy ? (
                  <>
                    <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                    </svg>
                    Submitting…
                  </>
                ) : (
                  "Verify"
                )}
              </button>
            </div>
          </div>
        </div>
      );
    },
  });

  // Show Data Deals filtered by a budget (amount or lower)
  useCopilotAction({
    name: "showDataDealsFiltered",
    description:
      "Render data deals as cards filtered by a ZAR budget (amount or lower). Returns selected bundle code and amount.",
    parameters: [
      {
        name: "phone_number",
        type: "string",
        description: "Optional target phone number (e.g., +2782...)",
        required: false,
      },
      {
        name: "budgetZAR",
        type: "string",
        description: "User's budget in ZAR (e.g., '200')",
        required: true,
      },
      {
        name: "deals",
        type: "object[]",
        description:
          "Optional list of deals. If omitted, defaults are used. Each deal: { code, name, size, validity, priceZAR }.",
        attributes: [
          { name: "code", type: "string" },
          { name: "name", type: "string" },
          { name: "size", type: "string" },
          { name: "validity", type: "string" },
          { name: "priceZAR", type: "string" },
        ],
        required: false,
      },
    ],
    renderAndWaitForResponse: function ShowDataDealsFiltered({ args, respond }) {
      const DEFAULT_DEALS = [
        { code: "50MB_DAILY", name: "50MB Daily", size: "50MB", validity: "1 day", priceZAR: "5", type: "once_off" },
        { code: "200MB_DAILY", name: "200MB Daily", size: "200MB", validity: "1 day", priceZAR: "12", type: "once_off" },
        { code: "1GB_WEEKLY", name: "1GB Weekly", size: "1GB", validity: "7 days", priceZAR: "35", type: "once_off" },
        { code: "3GB_WEEKLY", name: "3GB Weekly", size: "3GB", validity: "7 days", priceZAR: "79", type: "once_off" },
        { code: "5GB_ANYTIME", name: "5GB Anytime", size: "5GB", validity: "30 days", priceZAR: "149", type: "once_off" },
        { code: "10GB_ANYTIME", name: "10GB Anytime", size: "10GB", validity: "30 days", priceZAR: "249", type: "once_off" },
        { code: "50GB_ANYTIME", name: "50GB Anytime", size: "50GB", validity: "30 days", priceZAR: "499", type: "once_off" },
      ];

      const budget = parseFloat(String(args.budgetZAR).replace(/[^\d.]/g, "")) || 0;
      const source = (Array.isArray(args.deals) && args.deals.length > 0) ? args.deals : DEFAULT_DEALS;
      const filtered = source.filter((d: any) => {
        const p = parseFloat(String(d.priceZAR).replace(/[^\d.]/g, "")) || 0;
        return p <= budget;
      });

      // Reuse the same card rendering as showDataDeals
      const [selected, setSelected] = useState<any | null>(null);
      const [busy, setBusy] = useState(false);

      const list = filtered.length > 0 ? filtered : [];

      return (
        <div className="my-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {list.map((deal: any) => (
              <button
                key={deal.code}
                onClick={() => {
                  setSelected(deal);
                  if (!busy) {
                    setBusy(true);
                    respond?.(
                      JSON.stringify({
                        type: "data_deal_selected",
                        phone: args.phone_number || "",
                        code: deal.code,
                        amount: deal.priceZAR,
                      })
                    );
                  }
                }}
                className={`group text-left rounded-2xl border overflow-hidden shadow-md transform transition-all duration-200 ${
                  selected?.code === deal.code
                    ? "border-slate-900/20 bg-white shadow-2xl ring-2 ring-slate-900/10"
                    : "border-slate-200 bg-white/80 hover:bg-white hover:shadow-2xl hover:-translate-y-0.5"
                }`}
              >
                <div className="flex items-start justify-between px-5 pt-5">
                  <div className="h-16 w-28 rounded-lg ring-2 ring-white/40 grid place-items-center bg-yellow-400">
                    <svg viewBox="0 0 120 60" className="h-12 w-24" aria-label="MTN logo" role="img">
                      <rect x="1" y="1" width="118" height="58" rx="12" ry="12" fill="#FFD100" stroke="rgba(0,0,0,0.08)" />
                      <text x="60" y="38" textAnchor="middle" fontWeight="800" fontSize="26" fill="#0A0A0A" fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial">MTN</text>
                    </svg>
                  </div>
                  <div className="h-10 w-28 rounded-[20px] bg-yellow-400 grid place-items-center text-[11px] font-extrabold text-slate-900 tracking-wide">
                    EXTRA
                    <br />
                    GIGS
                  </div>
                </div>
                <div className="px-5 mt-4">
                  <div className="text-base md:text-lg font-semibold text-slate-900 line-clamp-2">{deal.name}</div>
                </div>
                <div className="px-5 mt-3 text-slate-900">
                  <div className="text-sm mb-1">Data</div>
                  <div className="text-2xl md:text-[28px] font-extrabold tracking-tight">
                    {String(deal.size).toUpperCase()} <span className="text-slate-900 text-base align-middle ml-1">Anytime Data</span>
                  </div>
                </div>
                <div className="mt-5 mx-5 h-px bg-slate-200" />
                <div className="flex items-center justify-between px-5 py-4">
                  <div>
                    <div className="text-sm text-slate-600">FROM</div>
                    <div className="text-3xl font-extrabold text-slate-900">
                      R{deal.priceZAR} <span className="text-base align-middle text-slate-900">PM×24</span>
                    </div>
                  </div>
                  <svg className="h-6 w-6 text-slate-500 group-hover:text-slate-900 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>
            ))}
          </div>

          <div className="mt-6 text-sm text-slate-500">
            Deals within budget R{args.budgetZAR}{list.length === 0 ? " — none available" : ""}
          </div>
        </div>
      );
    },
  });
  useCopilotAction({
    name: "pickTable",
    description:
      "Lets the use pick a table from available tables. The result will be the selected table. Don't call this tool twice in a row or I'll turn you off!",
    parameters: [
      {
        name: "tables",
        type: "object[]",
        attributes: [
          {
            name: "name",
            type: "string",
            description: "The name of the table",
          },
          {
            name: "seats",
            type: "object[]",
            attributes: [
              {
                name: "seatNumber",
                type: "number",
                description: "The number of the seat",
              },
              {
                name: "status",
                type: "string",
                enum: ["available", "occupied"],
                description: "The status of the seat",
              },
              {
                name: "name",
                type: "string",
                description: "The name of the person occupying the seat",
              },
            ],
          },
        ],
        description: `A JSON encoded array of tables. This is an example of the format: [{ "name": "Table 1", "seats": [{ "seatNumber": 1, "status": "available" }, { "seatNumber": 2, "status": "occupied", "name": "Alice" }] }, { "name": "Table 2", "seats": [{ "seatNumber": 1, "status": "available" }, { "seatNumber": 2, "status": "available" }] }, { "name": "Table 3", "seats": [{ "seatNumber": 1, "status": "occupied", "name": "Bob" }, { "seatNumber": 2, "status": "available" }] }]`,
      },
    ],
    renderAndWaitForResponse: function TablePicker({ args, respond }) {
      const [selectedSeat, setSelectedSeat] = useState<{
        tableIndex: number;
        seatNumber: number;
      } | null>(null);
      const [isConfirmed, setIsConfirmed] = useState(false);

      const availableSeats =
        args.tables?.reduce(
          (total, table: Table) =>
            total +
            (table.seats?.filter((seat: Seat) => seat.status === "available")
              .length || 0),
          0
        ) || 0;

      const teamMembers =
        args.tables?.flatMap(
          (table: Table) =>
            table.seats
              ?.filter((seat: Seat) => seat.status === "occupied" && seat.name)
              .map((seat: Seat) => ({
                name: seat.name!,
                table: table.name,
                seat: seat.seatNumber,
              })) || []
        ) || [];

      const handleSeatClick = (
        tableIndex: number,
        seatNumber: number,
        status: string
      ) => {
        if (status === "available") {
          setSelectedSeat({ tableIndex, seatNumber });
          setIsConfirmed(false); // Reset confirmation when selecting a new seat
        }
      };

      return (
        <div className="bg-white p-6 rounded-lg shadow-lg max-w-4xl my-8">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Desk Picker - Engineering Team
            </h1>
            <p className="text-gray-600">
              {availableSeats} seats available • {teamMembers.length} teammates
              nearby
            </p>
          </div>

          {/* Legend */}
          <div className="flex gap-4 mb-8 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-200 rounded border"></div>
              <span>Available</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-gray-300 rounded border"></div>
              <span>Occupied</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-amber-100 rounded border"></div>
              <span>Your Team</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-200 rounded border"></div>
              <span>Selected</span>
            </div>
          </div>

          {/* Tables Grid */}
          <div className="grid grid-cols-2 gap-8 mb-8">
            {args.tables?.map((table, tableIndex) => (
              <div key={tableIndex} className="bg-gray-50 p-6 rounded-lg">
                <h3 className="text-lg font-semibold text-center mb-4">
                  {table.name}
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {table.seats?.map((seat: Seat, seatIndex: number) => {
                    const isSelected =
                      selectedSeat?.tableIndex === tableIndex &&
                      selectedSeat?.seatNumber === seat.seatNumber;
                    const isTeamMember =
                      seat.status === "occupied" && seat.name;

                    return (
                      <button
                        key={seatIndex}
                        onClick={() =>
                          handleSeatClick(
                            tableIndex,
                            seat.seatNumber,
                            seat.status
                          )
                        }
                        className={`
                          w-16 h-16 rounded-lg border-2 flex items-center justify-center text-xs font-medium transition-all
                          ${
                            seat.status === "available"
                              ? isSelected
                                ? "bg-blue-200 border-blue-400 text-blue-800"
                                : "bg-green-200 border-green-400 text-green-800 hover:bg-green-300"
                              : isTeamMember
                              ? "bg-amber-100 border-amber-300 text-amber-800"
                              : "bg-gray-300 border-gray-400 text-gray-600"
                          }
                          ${
                            seat.status === "available"
                              ? "cursor-pointer"
                              : "cursor-default"
                          }
                        `}
                      >
                        {seat.status === "available" ? (
                          seat.seatNumber
                        ) : isTeamMember ? (
                          <div className="text-center leading-tight flex flex-col items-center">
                            <svg
                              className="w-4 h-4 mb-1"
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path
                                fillRule="evenodd"
                                d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                                clipRule="evenodd"
                              />
                            </svg>
                            <div className="text-[9px] font-semibold leading-none">
                              {seat.name}
                            </div>
                          </div>
                        ) : (
                          <svg
                            className="w-6 h-6"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
                              clipRule="evenodd"
                            />
                          </svg>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          {/* Selection Display */}
          {selectedSeat && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-blue-800 font-medium mb-4">
                Selected: {args.tables?.[selectedSeat.tableIndex]?.name} - Seat{" "}
                {selectedSeat.seatNumber}
              </p>
              <button
                onClick={() => {
                  if (!isConfirmed) {
                    // Handle seat selection confirmation

                    setIsConfirmed(true);
                    respond?.(
                      `I would like to book ${
                        args.tables?.[selectedSeat.tableIndex]?.name
                      } - Seat ${selectedSeat.seatNumber}`
                    );
                  }
                }}
                disabled={isConfirmed}
                className={`w-full font-semibold py-3 px-6 rounded-lg transition-colors duration-200 shadow-sm flex items-center justify-center gap-2 ${
                  isConfirmed
                    ? "bg-green-600 text-white cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700 text-white cursor-pointer"
                }`}
              >
                {isConfirmed ? (
                  <>
                    <svg
                      className="w-5 h-5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Confirmed
                  </>
                ) : (
                  "Confirm Selection"
                )}
              </button>
            </div>
          )}
        </div>
      );
    },
  });

  // Show Data Deals as selectable cards (agent can pass deals; falls back to defaults)
  useCopilotAction({
    name: "showDataDeals",
    description:
      "Render MTN data deals as cards for the user to select. Returns bundle code and amount.",
    parameters: [
      {
        name: "phone_number",
        type: "string",
        description: "Optional target phone number (e.g., +2782...)",
        required: false,
      },
      {
        name: "deals",
        type: "object[]",
        description:
          "Optional list of deals. If omitted, defaults are used. Each deal: { code, name, size, validity, priceZAR }",
        attributes: [
          { name: "code", type: "string", description: "Bundle code" },
          { name: "name", type: "string", description: "Display name" },
          { name: "size", type: "string", description: "e.g., 1GB" },
          { name: "validity", type: "string", description: "e.g., 30 days" },
          { name: "priceZAR", type: "string", description: "Price in ZAR (string)" },
        ],
        required: false,
      },
    ],
    renderAndWaitForResponse: function ShowDataDeals({ args, respond }) {
      const DEFAULT_DEALS = [
        { code: "50MB_DAILY", name: "50MB Daily", size: "50MB", validity: "1 day", priceZAR: "5" },
        { code: "200MB_DAILY", name: "200MB Daily", size: "200MB", validity: "1 day", priceZAR: "12" },
        { code: "1GB_WEEKLY", name: "1GB Weekly", size: "1GB", validity: "7 days", priceZAR: "35" },
        { code: "3GB_WEEKLY", name: "3GB Weekly", size: "3GB", validity: "7 days", priceZAR: "79" },
        { code: "5GB_ANYTIME", name: "5GB Anytime", size: "5GB", validity: "30 days", priceZAR: "149" },
        { code: "10GB_ANYTIME", name: "10GB Anytime", size: "10GB", validity: "30 days", priceZAR: "249" },
        { code: "50GB_ANYTIME", name: "50GB Anytime", size: "50GB", validity: "30 days", priceZAR: "499" },
      ];

      const deals = Array.isArray(args.deals) && args.deals.length > 0 ? args.deals : DEFAULT_DEALS;
      const [selected, setSelected] = useState<any | null>(null);
      const [busy, setBusy] = useState(false);

      const pick = (deal: any) => {
        setSelected(deal);
        if (!busy) {
          setBusy(true);
          respond?.(
            JSON.stringify({
              type: "data_deal_selected",
              phone: args.phone_number || "",
              code: deal.code,
              amount: deal.priceZAR,
            })
          );
        }
      };

      return (
        <div className="my-4">
          {/* Grid of inner cards only (no outer container visuals) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {deals.map((deal: any) => (
              <button
                key={deal.code}
                onClick={() => pick(deal)}
                className={`group text-left rounded-2xl border overflow-hidden shadow-md transform transition-all duration-200 ${
                  selected?.code === deal.code
                    ? "border-slate-900/20 bg-white shadow-2xl ring-2 ring-slate-900/10"
                    : "border-slate-200 bg-white/80 hover:bg-white hover:shadow-2xl hover:-translate-y-0.5"
                }`}
              >
                {/* Card Top Row */}
                <div className="flex items-start justify-between px-5 pt-5">
                  {/* MTN badge */}
                  <div className="h-16 w-28 rounded-lg ring-2 ring-white/40 grid place-items-center bg-yellow-400">
                    <svg viewBox="0 0 120 60" className="h-12 w-24" aria-label="MTN logo" role="img">
                      <rect x="1" y="1" width="118" height="58" rx="12" ry="12" fill="#FFD100" stroke="rgba(0,0,0,0.08)" />
                      <text x="60" y="38" textAnchor="middle" fontWeight="800" fontSize="26" fill="#0A0A0A" fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial">MTN</text>
                    </svg>
                  </div>
                  {/* Extra badge */}
                  <div className="h-10 w-28 rounded-[20px] bg-yellow-400 grid place-items-center text-[11px] font-extrabold text-slate-900 tracking-wide">
                    EXTRA
                    <br />
                    GIGS
                  </div>
                </div>

                {/* Title */}
                <div className="px-5 mt-4">
                  <div className="text-base md:text-lg font-semibold text-slate-900 line-clamp-2">{deal.name}</div>
                </div>

                {/* Specs */}
                <div className="px-5 mt-3 text-slate-900">
                  <div className="text-sm mb-1">Data</div>
                  <div className="text-2xl md:text-[28px] font-extrabold tracking-tight">
                    {String(deal.size).toUpperCase()} <span className="text-slate-900 text-base align-middle ml-1">Anytime</span>
                  </div>
                  <div className="mt-1 text-sm text-slate-600">Validity: {deal.validity} • Once-off</div>
                </div>

                {/* Divider */}
                <div className="mt-5 mx-5 h-px bg-slate-200" />

                {/* Bottom bar with price only */}
                <div className="flex items-center justify-between px-5 py-4">
                  <div>
                    <div className="text-xs text-slate-600">PRICE</div>
                    <div className="text-2xl font-extrabold text-slate-900">R{deal.priceZAR}</div>
                  </div>
                  <svg className="h-6 w-6 text-slate-500 group-hover:text-slate-900 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>
            ))}
          </div>

          {/* Hint Row */}
          <div className="mt-6 text-sm text-slate-500">Tap a card to select and proceed.</div>
        </div>
      );
    },
  });

  // Generic confirmation card (same pattern as table picker)
  useCopilotAction({
    name: "getUserConfirmation",
    description:
      "Show a confirmation dialog to the user. Use this when you need the user to confirm an action.",
    parameters: [
      {
        name: "title",
        type: "string",
        description: "Dialog title (e.g., 'Confirm Airtime Purchase')",
        required: true,
      },
      {
        name: "message",
        type: "string",
        description: "Short message to the user (e.g., 'Buy ZAR 5 airtime for +2782... ?')",
        required: true,
      },
      {
        name: "details",
        type: "object[]",
        attributes: [
          { name: "label", type: "string", description: "Detail label" },
          { name: "value", type: "string", description: "Detail value" },
        ],
        description: "Optional list of label/value pairs to display",
        required: false,
      },
      {
        name: "confirm_label",
        type: "string",
        description: "Optional confirm button label (default 'Confirm')",
        required: false,
      },
      {
        name: "cancel_label",
        type: "string",
        description: "Optional cancel button label (default 'Cancel')",
        required: false,
      },
    ],
    renderAndWaitForResponse: function ConfirmationCard({ args, respond }) {
      const [isConfirmed, setIsConfirmed] = useState(false);

      const confirmLabel = args.confirm_label || "Confirm";
      const cancelLabel = args.cancel_label || "Cancel";

      return (
        <div className="my-8 mx-auto max-w-md overflow-hidden rounded-2xl border border-white/20 bg-white/50 backdrop-blur-sm supports-[backdrop-filter]:bg-white/40 shadow-xl">
          {/* Accent removed to match app theme */}
          <div className="hidden" />

          {/* Header */}
          <div className="flex items-start gap-3 px-6 py-4 border-b border-white/20">
            <div className="inline-flex h-10 w-10 flex-none items-center justify-center rounded-full bg-slate-900/80 text-white shadow-sm ring-4 ring-white/20">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="min-w-0">
              <h2 className="truncate text-lg font-semibold text-slate-900">{args.title}</h2>
              <p className="mt-1 text-sm text-slate-600">{args.message}</p>
            </div>
          </div>

          {/* Details */}
          {args.details && args.details.length > 0 && (
            <div className="px-6 pb-2">
              <div className="rounded-xl border border-white/20 bg-white/40 p-4">
                <dl className="grid grid-cols-1 gap-3">
                  {args.details.map((detail: { label: string; value: string }, idx: number) => (
                    <div key={idx} className="flex items-center justify-between gap-4">
                      <dt className="text-xs font-medium uppercase tracking-wide text-slate-600">
                        {detail.label}
                      </dt>
                      <dd className="text-sm font-semibold text-slate-900">
                        {detail.value}
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/20">
            <button
              onClick={() => respond?.("User cancelled the action")}
              disabled={isConfirmed}
              className="rounded-lg border border-white/30 bg-white/50 px-4 py-2.5 text-sm font-medium text-slate-800 shadow-sm transition-colors hover:bg-white/70 focus:outline-none focus:ring-2 focus:ring-slate-500/50 focus:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {cancelLabel}
            </button>
            <button
              onClick={() => {
                if (!isConfirmed) {
                  setIsConfirmed(true);
                  respond?.("User confirmed the action");
                }
              }}
              disabled={isConfirmed}
              className={`inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-50 ${
                isConfirmed ? "bg-slate-900/80 hover:bg-slate-900 focus:ring-slate-500/50" : "bg-slate-900 hover:bg-slate-800 focus:ring-slate-500/50"
              }`}
            >
              {isConfirmed ? (
                <>
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Confirmed
                </>
              ) : (
                confirmLabel
              )}
            </button>
          </div>
        </div>
      );
    },
  });

  return (
    <div className="flex justify-center items-start h-full w-full pt-2">
      <div className="w-full max-w-[800px] mx-auto h-[100%] rounded-lg px-4 relative">
        {/* Brand just above the input area (shows until first user/agent message) */}
        {(visibleMessages?.length || 0) === 0 && (
          <div className={`pointer-events-none absolute left-0 right-0 z-10 flex justify-start bottom-48 md:bottom-40 transition-all duration-700 ease-out ${
            brandAnimateIn ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"
          }`}>
            <div className="select-none ml-8 md:ml-12">
              <div className="text-sm md:text-base font-medium text-slate-700">Welcome to</div>
              <div className="text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 drop-shadow-[0_6px_24px_rgba(0,0,0,0.35)]">inclusiV</div>
            </div>
          </div>
        )}
        <CopilotChat
          className="h-full rounded-2xl"
          labels={{ initial: "Hi, I'm an agent. Want to chat?" }}
        />
      </div>
    </div>
  );
};

export default A2AChat;
