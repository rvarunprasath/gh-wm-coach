"use client";

import React from "react";
import { PieChart, Wallet, ArrowUpRight, Shield, Layers, Building2 } from "lucide-react";
import { PortfolioSnapshot as IPortfolioSnapshot } from "@/lib/types";

interface PortfolioSnapshotProps {
  portfolio: IPortfolioSnapshot | null;
}

export const PortfolioSnapshot: React.FC<PortfolioSnapshotProps> = ({ portfolio }) => {
  if (!portfolio) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500 text-sm">
        Loading financial snapshot...
      </div>
    );
  }

  const formatCurrency = (val: number = 0) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  const getColorForClass = (assetClass: string) => {
    switch (assetClass.toUpperCase()) {
      case "EQUITY":
        return { bg: "bg-emerald-500", text: "text-emerald-400", border: "border-emerald-500/30", fill: "#10b981" };
      case "MUTUAL_FUND":
        return { bg: "bg-indigo-500", text: "text-indigo-400", border: "border-indigo-500/30", fill: "#6366f1" };
      case "DEBT":
        return { bg: "bg-amber-500", text: "text-amber-400", border: "border-amber-500/30", fill: "#f59e0b" };
      case "GOLD":
        return { bg: "bg-yellow-400", text: "text-yellow-400", border: "border-yellow-400/30", fill: "#facc15" };
      case "REAL_ESTATE":
        return { bg: "bg-rose-500", text: "text-rose-400", border: "border-rose-500/30", fill: "#f43f5e" };
      case "LIQUID":
      default:
        return { bg: "bg-cyan-500", text: "text-cyan-400", border: "border-cyan-500/30", fill: "#06b6d4" };
    }
  };

  return (
    <div className="space-y-5">
      {/* Asset Allocation Progress Bar */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <PieChart className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Asset Allocation Breakdown
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-medium">
            Total: {formatCurrency(portfolio.net_worth)}
          </span>
        </div>

        {/* Stacked Allocation Bar */}
        <div className="w-full h-3 rounded-full overflow-hidden flex bg-slate-800 p-0.5 gap-0.5">
          {portfolio.allocations.map((item, idx) => {
            const color = getColorForClass(item.asset_class);
            return (
              <div
                key={idx}
                style={{ width: `${Math.max(item.percentage, 2)}%` }}
                className={`h-full ${color.bg} transition-all duration-500 rounded-sm`}
                title={`${item.asset_class}: ${item.percentage}% (${formatCurrency(item.value)})`}
              />
            );
          })}
        </div>

        {/* Allocation Badges */}
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-2.5">
          {portfolio.allocations.map((item, idx) => {
            const color = getColorForClass(item.asset_class);
            return (
              <div
                key={idx}
                className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex flex-col justify-between"
              >
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span className="flex items-center gap-1.5 font-medium">
                    <span className={`w-2 h-2 rounded-full ${color.bg}`} />
                    {item.asset_class.replace("_", " ")}
                  </span>
                  <span className={`font-semibold ${color.text}`}>{item.percentage}%</span>
                </div>
                <div className="text-sm font-bold text-slate-100 mt-1">
                  {formatCurrency(item.value)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Individual Holdings Table */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Portfolio Holdings & Assets ({portfolio.holdings.length})
            </h3>
          </div>
          <span className="text-[11px] text-emerald-400 font-medium">Live Ledger</span>
        </div>

        <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
          {portfolio.holdings.map((h) => {
            const color = getColorForClass(h.asset_type);
            return (
              <div
                key={h.id}
                className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/60 flex items-center justify-between hover:border-slate-700 transition-colors"
              >
                <div>
                  <div className="text-xs font-semibold text-slate-200 flex items-center gap-2">
                    {h.asset_name}
                    {h.symbol && (
                      <span className="text-[10px] text-slate-400 bg-slate-800 px-1.5 py-0.2 rounded">
                        {h.symbol}
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5 flex items-center gap-1.5">
                    <span className={`${color.text} font-medium`}>{h.asset_type}</span>
                    {h.units && <span>• {h.units} units</span>}
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-xs font-bold text-slate-100">
                    {formatCurrency(h.current_value)}
                  </div>
                  <div className="text-[10px] text-emerald-400 flex items-center justify-end">
                    <ArrowUpRight className="w-2.5 h-2.5" /> Tracked
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Connected Accounts & Bank Balances */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Connected Accounts & Banks
            </h3>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {portfolio.accounts.map((acc) => (
            <div
              key={acc.id}
              className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/60 flex items-center justify-between"
            >
              <div>
                <div className="text-xs font-semibold text-slate-200">
                  {acc.institution_name}
                </div>
                <div className="text-[10px] text-slate-500">
                  {acc.account_type} {acc.account_number_masked && `(${acc.account_number_masked})`}
                </div>
              </div>
              <div className="text-xs font-bold text-cyan-400">
                {formatCurrency(acc.balance)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
