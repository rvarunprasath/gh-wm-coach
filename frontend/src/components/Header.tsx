"use client";

import React from "react";
import { Sparkles, UploadCloud, Link as LinkIcon, RotateCcw, TrendingUp, ShieldCheck } from "lucide-react";
import { PortfolioSnapshot } from "@/lib/types";

interface HeaderProps {
  portfolio: PortfolioSnapshot | null;
  onOpenUpload: () => void;
  onOpenConnect: () => void;
  onReset: () => void;
  isResetting: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  portfolio,
  onOpenUpload,
  onOpenConnect,
  onReset,
  isResetting,
}) => {
  const formatCurrency = (val: number = 0) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-30 px-6 py-3.5 transition-all">
      <div className="max-w-[1700px] mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Logo and Tagline */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Sparkles className="w-5 h-5 text-slate-950 font-bold" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                GH Wealth Coach
                <span className="text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                  GraphRAG v1.0
                </span>
              </h1>
            </div>
            <p className="text-xs text-slate-400 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              Continuous Personal Knowledge Graph & Financial Ledger
            </p>
          </div>
        </div>

        {/* Live Metrics Pills */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="bg-slate-800/80 border border-slate-700/60 px-3.5 py-1.5 rounded-xl flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <div>
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">Net Worth</div>
              <div className="text-sm font-bold text-emerald-400">
                {portfolio ? formatCurrency(portfolio.net_worth) : "₹0"}
              </div>
            </div>
          </div>

          <div className="bg-slate-800/80 border border-slate-700/60 px-3.5 py-1.5 rounded-xl flex items-center gap-2.5">
            <TrendingUp className="w-4 h-4 text-indigo-400" />
            <div>
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">Monthly Savings</div>
              <div className="text-sm font-bold text-slate-100">
                {portfolio ? formatCurrency(portfolio.monthly_savings) : "₹0"}{" "}
                <span className="text-[10px] font-normal text-slate-400">/mo</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={onOpenUpload}
            className="flex items-center gap-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-3.5 py-2 rounded-lg transition-colors shadow-sm"
          >
            <UploadCloud className="w-3.5 h-3.5 text-emerald-400" />
            Upload Statement
          </button>

          <button
            onClick={onOpenConnect}
            className="flex items-center gap-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-3.5 py-2 rounded-lg transition-colors shadow-sm"
          >
            <LinkIcon className="w-3.5 h-3.5 text-indigo-400" />
            Connect API
          </button>

          <button
            onClick={onReset}
            disabled={isResetting}
            title="Reset portfolio to initial seed state"
            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg border border-transparent hover:border-slate-700 transition-colors"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isResetting ? "animate-spin text-emerald-400" : ""}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
