"use client";

import React, { useState } from "react";
import { Network, RefreshCw, User, Users, Calendar, Coins, Building, Info } from "lucide-react";
import { GraphData, GraphNode } from "@/lib/types";

interface KnowledgeGraphViewProps {
  graphData: GraphData | null;
  onRefresh: () => void;
  isLoading: boolean;
}

export const KnowledgeGraphView: React.FC<KnowledgeGraphViewProps> = ({ graphData, onRefresh, isLoading }) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-xs">
        <Network className="w-8 h-8 mb-2 opacity-40 text-emerald-400" />
        No knowledge graph entities registered yet.
      </div>
    );
  }

  // Node styling helper
  const getNodeVisuals = (label: string) => {
    switch (label) {
      case "User":
        return { color: "#10b981", border: "#34d399", icon: User, badge: "User" };
      case "FamilyMember":
        return { color: "#ec4899", border: "#f472b6", icon: Users, badge: "Family" };
      case "LifeEvent":
        return { color: "#8b5cf6", border: "#a78bfa", icon: Calendar, badge: "Event" };
      case "Asset":
        return { color: "#06b6d4", border: "#22d3ee", icon: Coins, badge: "Asset" };
      case "Account":
      case "Institution":
        return { color: "#f59e0b", border: "#fbbf24", icon: Building, badge: "Account" };
      default:
        return { color: "#64748b", border: "#94a3b8", icon: Info, badge: "Entity" };
    }
  };

  return (
    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-emerald-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Personal Knowledge Graph ({graphData.nodes.length} Nodes, {graphData.edges.length} Edges)
          </h3>
        </div>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          title="Reload graph"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-emerald-400" : ""}`} />
        </button>
      </div>

      <p className="text-xs text-slate-400">
        Every question, uploaded statement, and verbal update links together here to ground all future advice.
      </p>

      {/* Interactive Entity Matrix & Node Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-h-64 overflow-y-auto pr-1">
        {graphData.nodes.map((node) => {
          const visuals = getNodeVisuals(node.label);
          const Icon = visuals.icon;
          const isSelected = selectedNode?.id === node.id;

          return (
            <div
              key={node.id}
              onClick={() => setSelectedNode(node)}
              className={`p-3 rounded-lg border transition-all cursor-pointer flex items-center justify-between ${
                isSelected
                  ? "bg-slate-800 border-emerald-400 shadow-sm"
                  : "bg-slate-950/60 border-slate-800/80 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
                  style={{ backgroundColor: `${visuals.color}20`, color: visuals.color }}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-200">
                    {node.properties?.name || node.name || node.properties?.title || node.id}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {node.properties?.relation
                      ? `${node.properties.relation} ${node.properties?.age ? `(${node.properties.age}y)` : ""}`
                      : node.properties?.target_year
                      ? `Target ${node.properties.target_year}`
                      : node.properties?.valuation
                      ? `₹${Number(node.properties.valuation).toLocaleString("en-IN")}`
                      : visuals.badge}
                  </div>
                </div>
              </div>

              <span
                className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded border"
                style={{
                  color: visuals.color,
                  borderColor: `${visuals.color}40`,
                  backgroundColor: `${visuals.color}10`,
                }}
              >
                {node.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Selected Node Inspector Drawer */}
      {selectedNode && (
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs animate-fadeIn">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2 mb-2">
            <span className="font-bold text-slate-200 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Node: {selectedNode.properties?.name || selectedNode.properties?.title || selectedNode.name}
            </span>
            <span className="text-[10px] text-slate-500 font-mono">{selectedNode.id}</span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-slate-400 text-[11px]">
            <div>
              <span className="text-slate-500">Label: </span>
              <span className="text-slate-300 font-medium">{selectedNode.label}</span>
            </div>
            {Object.entries(selectedNode.properties || {}).map(([k, v]) => {
              if (typeof v === "object" || k === "label") return null;
              return (
                <div key={k} className="truncate">
                  <span className="text-slate-500">{k}: </span>
                  <span className="text-slate-200 font-medium">{String(v)}</span>
                </div>
              );
            })}
          </div>

          {/* Connected Edges */}
          <div className="mt-2.5 pt-2 border-t border-slate-800/80">
            <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Connected Graph Relations</div>
            <div className="flex flex-wrap gap-1.5">
              {graphData.edges
                .filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
                .map((e) => (
                  <span
                    key={e.id}
                    className="text-[10px] bg-slate-900 border border-slate-800 text-slate-300 px-2 py-0.5 rounded flex items-center gap-1"
                  >
                    <span>{e.source === selectedNode.id ? "→ OUT" : "← IN"}:</span>
                    <strong className="text-indigo-400">{e.relation}</strong>
                  </span>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* Graph Relationships Summary Bar */}
      <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
        <span>Continuous Graph Sync: Active</span>
        <span className="text-emerald-400 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Grounded in SQLite + NetworkX
        </span>
      </div>
    </div>
  );
};
