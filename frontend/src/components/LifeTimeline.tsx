"use client";

import React from "react";
import { Milestone, Calendar, CheckCircle2, Clock, Target, Users } from "lucide-react";
import { GoalItem } from "@/lib/types";

interface LifeTimelineProps {
  goals: GoalItem[];
}

export const LifeTimeline: React.FC<LifeTimelineProps> = ({ goals }) => {
  const formatCurrency = (val: number = 0) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="space-y-4">
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Milestone className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Life Events & Financial Milestones
            </h3>
          </div>
          <span className="text-[11px] text-slate-400">Knowledge Graph Mapped</span>
        </div>
        <p className="text-xs text-slate-400 mb-4">
          Every conversation continuously updates this timeline. The AI balances your cash flow against these future milestones.
        </p>

        {/* Timeline Items */}
        <div className="relative pl-6 space-y-6 before:content-[''] before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
          {goals.map((g, idx) => {
            const isCompleted = (g.accumulated_amount || 0) >= g.target_amount;
            const progress = g.target_amount > 0 ? Math.min(100, Math.round(((g.accumulated_amount || 0) / g.target_amount) * 100)) : 0;

            return (
              <div key={g.id || idx} className="relative">
                {/* Milestone Node Dot */}
                <div
                  className={`absolute -left-6 top-1 w-3.5 h-3.5 rounded-full border-2 border-slate-900 ${
                    isCompleted ? "bg-emerald-400" : "bg-indigo-500"
                  }`}
                />

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                      {g.title}
                      {g.title.toLowerCase().includes("ananya") && (
                        <span className="text-[10px] bg-indigo-950/60 text-indigo-300 border border-indigo-800/50 px-1.5 py-0.2 rounded-full flex items-center gap-1">
                          <Users className="w-2.5 h-2.5" /> Daughter
                        </span>
                      )}
                    </span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-emerald-400" /> {g.target_year}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-400 my-1">
                    <span>Target: {formatCurrency(g.target_amount)}</span>
                    <span className="font-semibold text-slate-200">
                      Accumulated: {formatCurrency(g.accumulated_amount || 0)} ({progress}%)
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden mt-2">
                    <div
                      style={{ width: `${progress}%` }}
                      className={`h-full ${isCompleted ? "bg-emerald-400" : "bg-indigo-500"} transition-all duration-500`}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
