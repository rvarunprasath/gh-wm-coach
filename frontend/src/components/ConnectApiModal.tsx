"use client";

import React, { useState } from "react";
import { X, Link as LinkIcon, CheckCircle2, ShieldCheck, Loader2 } from "lucide-react";
import { connectApi } from "@/lib/api";

interface ConnectApiModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnectSuccess: () => void;
}

export const ConnectApiModal: React.FC<ConnectApiModalProps> = ({
  isOpen,
  onClose,
  onConnectSuccess,
}) => {
  const [connectingProvider, setConnectingProvider] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const providers = [
    {
      id: "zerodha",
      name: "Zerodha Kite",
      desc: "Sync stock holdings, mutual fund folios, and live market valuations.",
      badge: "Broker API",
      color: "text-amber-400",
    },
    {
      id: "groww",
      name: "Groww",
      desc: "Import direct mutual funds, equity holdings, and SIP schedules.",
      badge: "Broker API",
      color: "text-emerald-400",
    },
    {
      id: "aggregator",
      name: "RBI Account Aggregator (Setu / Finvu)",
      desc: "Consent-based live read of all savings accounts, FDs, and bank balances.",
      badge: "Account Aggregator",
      color: "text-cyan-400",
    },
  ];

  const handleConnect = async (providerId: string) => {
    setConnectingProvider(providerId);
    setStatusMessage(null);
    try {
      const res = await connectApi(providerId);
      setStatusMessage(res.message);
      onConnectSuccess();
      setTimeout(() => {
        setConnectingProvider(null);
      }, 1000);
    } catch (e: any) {
      setStatusMessage(e.message || "Failed to connect.");
      setConnectingProvider(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-100 p-1 rounded-lg"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <LinkIcon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Connect Existing Systems via API</h3>
            <p className="text-xs text-slate-400">Secure Read-Only Access via RBI Account Aggregator & Broker APIs</p>
          </div>
        </div>

        <div className="space-y-3">
          {providers.map((p) => (
            <div
              key={p.id}
              className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors flex items-center justify-between"
            >
              <div className="pr-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-100">{p.name}</span>
                  <span className="text-[10px] bg-slate-800 text-slate-400 border border-slate-700 px-1.5 py-0.2 rounded">
                    {p.badge}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1 leading-snug">{p.desc}</p>
              </div>

              <button
                onClick={() => handleConnect(p.id)}
                disabled={connectingProvider !== null}
                className="shrink-0 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
              >
                {connectingProvider === p.id ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <LinkIcon className="w-3.5 h-3.5" />
                )}
                <span>Sync</span>
              </button>
            </div>
          ))}
        </div>

        {statusMessage && (
          <div className="mt-4 p-3 rounded-xl bg-emerald-950/30 border border-emerald-800/40 text-xs text-emerald-300 flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400 mt-0.5" />
            <span>{statusMessage}</span>
          </div>
        )}

        <div className="mt-5 p-3 rounded-xl bg-slate-950 border border-slate-800/80 flex items-center gap-2 text-[11px] text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>256-bit encryption. Zero credentials stored; tokenized consents only.</span>
        </div>
      </div>
    </div>
  );
};
