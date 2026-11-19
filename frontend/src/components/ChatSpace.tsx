"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Mic, MicOff, Bot, User, Sparkles, Database, Network, CheckCircle2, ChevronDown, ChevronUp } from "lucide-react";
import { ChatMessage } from "@/lib/types";

interface ChatSpaceProps {
  messages: ChatMessage[];
  onSendMessage: (msg: string, isAudio?: boolean) => Promise<void>;
  isSending: boolean;
}

export const ChatSpace: React.FC<ChatSpaceProps> = ({ messages, onSendMessage, isSending }) => {
  const [input, setInput] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [expandedTraceId, setExpandedTraceId] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  // Web Speech API initialization
  useEffect(() => {
    if (typeof window !== "undefined" && ("SpeechRecognition" in window || "webkitSpeechRecognition" in window)) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-IN";

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          setInput(transcript);
          onSendMessage(transcript, true);
        }
        setIsListening(false);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, [onSendMessage]);

  const toggleVoice = () => {
    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setIsListening(true);
      recognitionRef.current.start();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;
    const msg = input.trim();
    setInput("");
    await onSendMessage(msg, false);
  };

  const sendPreset = (presetText: string) => {
    onSendMessage(presetText, false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] bg-slate-900/40 border border-slate-800/80 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-sm">
      {/* Interaction Header */}
      <div className="px-5 py-3.5 border-b border-slate-800 bg-slate-900/70 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Active Interaction Space
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            </h2>
            <p className="text-[11px] text-slate-400">Continuous AI Coach with Knowledge Graph Memory</p>
          </div>
        </div>

        {/* Quick info tag */}
        <span className="text-[11px] bg-slate-800 text-slate-400 px-2.5 py-1 rounded-md border border-slate-700">
          Speech + Text Ingestion Enabled
        </span>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.map((m) => (
          <div key={m.id} className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}>
            <div className={`flex gap-3 max-w-[88%] ${m.sender === "user" ? "flex-row-reverse" : "flex-row"}`}>
              {/* Avatar */}
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold ${
                  m.sender === "user"
                    ? "bg-indigo-600 text-white"
                    : "bg-emerald-500 text-slate-950"
                }`}
              >
                {m.sender === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Content */}
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  m.sender === "user"
                    ? "bg-indigo-600/90 text-white shadow-md shadow-indigo-600/10"
                    : "bg-slate-800/90 border border-slate-700/60 text-slate-200 shadow-sm"
                }`}
              >
                {m.isAudio && (
                  <div className="flex items-center gap-1.5 text-[10px] text-indigo-200 mb-1 font-medium">
                    <Mic className="w-3 h-3" /> Voice Utterance Transcribed
                  </div>
                )}
                <div className="whitespace-pre-wrap space-y-2">{m.text}</div>
              </div>
            </div>

            {/* Reasoning Trace Drawer (For Coach Messages) */}
            {m.sender === "coach" && m.reasoning_trace && (
              <div className="ml-10 mt-2 max-w-[85%] w-full">
                <button
                  onClick={() => setExpandedTraceId(expandedTraceId === m.id ? null : m.id)}
                  className="flex items-center gap-1.5 text-[11px] text-slate-400 hover:text-emerald-400 bg-slate-900/60 border border-slate-800 px-2.5 py-1 rounded-lg transition-colors"
                >
                  <Sparkles className="w-3 h-3 text-emerald-400" />
                  <span>Grounding Trace & Memory Sync</span>
                  {expandedTraceId === m.id ? (
                    <ChevronUp className="w-3 h-3 ml-1" />
                  ) : (
                    <ChevronDown className="w-3 h-3 ml-1" />
                  )}
                </button>

                {expandedTraceId === m.id && (
                  <div className="mt-1.5 p-3 rounded-xl bg-slate-950/70 border border-slate-800/90 text-xs space-y-2.5 animate-fadeIn">
                    {/* Facts Extracted */}
                    {m.reasoning_trace.facts_extracted?.length > 0 && (
                      <div>
                        <div className="text-[10px] font-bold text-emerald-400 flex items-center gap-1.5 uppercase tracking-wide">
                          <CheckCircle2 className="w-3 h-3" /> Facts Extracted & Saved
                        </div>
                        <ul className="mt-1 space-y-1 text-slate-300">
                          {m.reasoning_trace.facts_extracted.map((fact, idx) => (
                            <li key={idx} className="flex items-start gap-1.5 bg-emerald-950/20 px-2 py-1 rounded border border-emerald-900/30">
                              <span>•</span>
                              <span>{fact}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Knowledge Graph Grounding */}
                    {m.reasoning_trace.graph_context_used?.length > 0 && (
                      <div>
                        <div className="text-[10px] font-bold text-indigo-400 flex items-center gap-1.5 uppercase tracking-wide">
                          <Network className="w-3 h-3" /> Knowledge Graph Grounding
                        </div>
                        <ul className="mt-1 space-y-1 text-slate-400">
                          {m.reasoning_trace.graph_context_used.map((ctx, idx) => (
                            <li key={idx} className="flex items-start gap-1.5">
                              <span>→</span>
                              <span>{ctx}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Ledger Accounts Consulted */}
                    {m.reasoning_trace.accounts_consulted?.length > 0 && (
                      <div>
                        <div className="text-[10px] font-bold text-teal-400 flex items-center gap-1.5 uppercase tracking-wide">
                          <Database className="w-3 h-3" /> Ledger Accounts Consulted
                        </div>
                        <div className="mt-1 flex flex-wrap gap-1.5">
                          {m.reasoning_trace.accounts_consulted.map((acc, idx) => (
                            <span key={idx} className="bg-slate-800 px-2 py-0.5 rounded text-[11px] text-slate-300 border border-slate-700">
                              {acc}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {isSending && (
          <div className="flex gap-3 items-center text-slate-400 text-xs py-2">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <span>Coach is analyzing Knowledge Graph and Ledger balances...</span>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Suggested Prompt Pills */}
      <div className="px-4 py-2 border-t border-slate-800/80 bg-slate-900/40 flex items-center gap-2 overflow-x-auto no-scrollbar">
        <span className="text-[11px] text-slate-500 shrink-0 font-medium">Try speaking/asking:</span>
        <button
          onClick={() => sendPreset("I hold total equity in stocks worth 20 lakhs")}
          className="text-xs bg-slate-800/80 hover:bg-slate-700 text-emerald-300 border border-emerald-500/30 px-3 py-1 rounded-full shrink-0 transition-colors"
        >
          "I hold total equity in stocks worth 20 lakhs"
        </button>
        <button
          onClick={() => sendPreset("Can I afford to purchase a 50 lakh apartment in 2 years?")}
          className="text-xs bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1 rounded-full shrink-0 transition-colors"
        >
          "Can I buy a 50 lakh apartment in 2 years?"
        </button>
        <button
          onClick={() => sendPreset("My daughter Ananya is starting college in 2028")}
          className="text-xs bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1 rounded-full shrink-0 transition-colors"
        >
          "My daughter Ananya is starting college in 2028"
        </button>
      </div>

      {/* Input Box and Voice Controller */}
      <form onSubmit={handleSubmit} className="p-3.5 border-t border-slate-800 bg-slate-900/80 flex items-center gap-2">
        <button
          type="button"
          onClick={toggleVoice}
          title={isListening ? "Listening... click to stop" : "Click to speak your financial update"}
          className={`p-2.5 rounded-xl transition-all ${
            isListening
              ? "bg-rose-500 text-white voice-recording-pulse shadow-lg shadow-rose-500/30"
              : "bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
          }`}
        >
          {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4 text-emerald-400" />}
        </button>

        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isListening ? "Listening... speak now" : "Ask a question or state your finances (e.g. 'I hold 20 lakhs in stocks')..."}
          disabled={isSending}
          className="flex-1 bg-slate-950 border border-slate-800 focus:border-emerald-500/60 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-colors"
        />

        <button
          type="submit"
          disabled={!input.trim() || isSending}
          className="p-2.5 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 disabled:hover:bg-emerald-500 text-slate-950 font-semibold rounded-xl transition-colors shadow-md shadow-emerald-500/20"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
