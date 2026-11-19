"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/Header";
import { ChatSpace } from "@/components/ChatSpace";
import { PortfolioSnapshot } from "@/components/PortfolioSnapshot";
import { LifeTimeline } from "@/components/LifeTimeline";
import { KnowledgeGraphView } from "@/components/KnowledgeGraphView";
import { StatementUploadModal } from "@/components/StatementUploadModal";
import { ConnectApiModal } from "@/components/ConnectApiModal";
import { fetchPortfolio, fetchGraph, sendChatMessage, resetPortfolio } from "@/lib/api";
import { PortfolioSnapshot as IPortfolioSnapshot, GraphData, ChatMessage } from "@/lib/types";
import { PieChart, Milestone, Network, ShieldCheck } from "lucide-react";

export default function Home() {
  const [portfolio, setPortfolio] = useState<IPortfolioSnapshot | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [activeRightTab, setActiveRightTab] = useState<"portfolio" | "timeline" | "graph">("portfolio");
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isConnectOpen, setIsConnectOpen] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isGraphLoading, setIsGraphLoading] = useState(false);

  // Initial Seeded Conversation
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg-welcome",
      sender: "coach",
      text: "👋 Welcome to your AI Financial Coach!\n\nI continuously organize your personal finances into a **Dual-Store Knowledge Graph & Relational Ledger**.\n\nYou can speak or type updates (e.g. *\"I hold total equity in stocks worth 20 lakhs\"*), upload bank or mutual fund statements, or ask trade-off questions like *\"Can I buy a 50L home in 2 years?\"*.\n\nNotice the right pane: it maintains your live portfolio snapshot, life events roadmap, and knowledge graph without you ever having to re-explain your background.",
      timestamp: new Date().toLocaleTimeString(),
      reasoning_trace: {
        graph_context_used: ["User: Rahul Sharma (Moderate Risk)", "Dependents: Ananya (Daughter 14 yrs)", "Milestone: Ananya College (2028)"],
        accounts_consulted: ["HDFC Bank Savings: ₹4,50,000", "Zerodha Demat: ₹1,50,000"],
        facts_extracted: ["Loaded initial family tree, holdings, and life goals into Knowledge Graph."],
      },
    },
  ]);

  // Load Data
  const loadData = useCallback(async () => {
    try {
      const [pData, gData] = await Promise.all([fetchPortfolio(), fetchGraph()]);
      setPortfolio(pData);
      setGraphData(gData);
    } catch (err) {
      console.error("Error loading financial data:", err);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle Chat / Voice send
  const handleSendMessage = async (msgText: string, isAudio: boolean = false) => {
    const userMsgId = `user-${Date.now()}`;
    const userMessage: ChatMessage = {
      id: userMsgId,
      sender: "user",
      text: msgText,
      timestamp: new Date().toLocaleTimeString(),
      isAudio,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsSending(true);

    try {
      const resp = await sendChatMessage(msgText, "default_user", isAudio);
      const coachMessage: ChatMessage = {
        id: `coach-${Date.now()}`,
        sender: "coach",
        text: resp.reply,
        timestamp: new Date().toLocaleTimeString(),
        reasoning_trace: resp.reasoning_trace,
      };

      setMessages((prev) => [...prev, coachMessage]);

      // If facts were extracted, automatically refresh the portfolio and knowledge graph
      if (resp.updated_portfolio || resp.updated_graph) {
        await loadData();
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: "coach",
          text: `⚠️ Error contacting the coach: ${err.message || "Failed to reach backend."}`,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  // Reset to initial state
  const handleReset = async () => {
    if (!confirm("Reset all financial tables and knowledge graph to initial state?")) return;
    setIsResetting(true);
    try {
      await resetPortfolio();
      await loadData();
      setMessages([
        {
          id: `msg-reset-${Date.now()}`,
          sender: "coach",
          text: "🔄 Reset complete! All balances, family members, and knowledge graph links have been restored to default.",
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } catch (e) {
      console.error(e);
    } finally {
      setIsResetting(false);
    }
  };

  const handleRefreshGraph = async () => {
    setIsGraphLoading(true);
    try {
      const gData = await fetchGraph();
      setGraphData(gData);
    } finally {
      setIsGraphLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#080d1a] text-slate-100">
      {/* Top Navigation */}
      <Header
        portfolio={portfolio}
        onOpenUpload={() => setIsUploadOpen(true)}
        onOpenConnect={() => setIsConnectOpen(true)}
        onReset={handleReset}
        isResetting={isResetting}
      />

      {/* Main Two-Pane Workspace */}
      <main className="flex-1 max-w-[1700px] w-full mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Pane: Active Interaction Space (Chat + Voice) */}
        <section className="lg:col-span-7 flex flex-col">
          <ChatSpace
            messages={messages}
            onSendMessage={handleSendMessage}
            isSending={isSending}
          />
        </section>

        {/* Right Pane: Portfolio Snapshot, Life Events Timeline & Knowledge Graph */}
        <section className="lg:col-span-5 flex flex-col space-y-4">
          {/* Segmented Tab Controls */}
          <div className="bg-slate-900/80 p-1.5 rounded-xl border border-slate-800 flex items-center justify-between gap-1 shadow-sm">
            <button
              onClick={() => setActiveRightTab("portfolio")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
                activeRightTab === "portfolio"
                  ? "bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              }`}
            >
              <PieChart className="w-3.5 h-3.5" />
              <span>Snapshot</span>
            </button>

            <button
              onClick={() => setActiveRightTab("timeline")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
                activeRightTab === "timeline"
                  ? "bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              }`}
            >
              <Milestone className="w-3.5 h-3.5" />
              <span>Life Goals</span>
            </button>

            <button
              onClick={() => setActiveRightTab("graph")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
                activeRightTab === "graph"
                  ? "bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              }`}
            >
              <Network className="w-3.5 h-3.5" />
              <span>Knowledge Graph</span>
            </button>
          </div>

          {/* Right Tab Content */}
          <div className="flex-1 overflow-y-auto max-h-[calc(100vh-165px)] pr-1">
            {activeRightTab === "portfolio" && (
              <PortfolioSnapshot portfolio={portfolio} />
            )}

            {activeRightTab === "timeline" && (
              <LifeTimeline goals={portfolio?.goals || []} />
            )}

            {activeRightTab === "graph" && (
              <KnowledgeGraphView
                graphData={graphData}
                onRefresh={handleRefreshGraph}
                isLoading={isGraphLoading}
              />
            )}
          </div>
        </section>
      </main>

      {/* Modals */}
      <StatementUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={() => {
          loadData();
          setIsUploadOpen(false);
        }}
      />

      <ConnectApiModal
        isOpen={isConnectOpen}
        onClose={() => setIsConnectOpen(false)}
        onConnectSuccess={() => {
          loadData();
          setIsConnectOpen(false);
        }}
      />
    </div>
  );
}
