import { PortfolioSnapshot, GraphData, ChatMessage, ReasoningTrace } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export async function fetchPortfolio(userId: string = "default_user"): Promise<PortfolioSnapshot> {
  const res = await fetch(`${API_BASE}/portfolio?user_id=${userId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load portfolio snapshot");
  return res.json();
}

export async function fetchGraph(userId: string = "default_user"): Promise<GraphData> {
  const res = await fetch(`${API_BASE}/graph?user_id=${userId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load knowledge graph");
  return res.json();
}

export async function sendChatMessage(
  message: string,
  userId: string = "default_user",
  isAudio: boolean = false
): Promise<{ reply: string; reasoning_trace: ReasoningTrace; updated_portfolio: boolean; updated_graph: boolean }> {
  const endpoint = isAudio ? `${API_BASE}/voice` : `${API_BASE}/chat`;
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, user_id: userId, audio_transcript: isAudio }),
  });
  if (!res.ok) throw new Error("Failed to send message to coach");
  return res.json();
}

export async function uploadStatement(
  file: File,
  userId: string = "default_user"
): Promise<{ filename: string; status: string; extracted_summary: string; items_detected: number }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("user_id", userId);

  const res = await fetch(`${API_BASE}/ingest/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Statement upload failed");
  return res.json();
}

export async function connectApi(
  provider: string,
  userId: string = "default_user"
): Promise<{ status: string; provider: string; message: string }> {
  const res = await fetch(`${API_BASE}/ingest/connect-api?provider=${encodeURIComponent(provider)}&user_id=${userId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("API integration failed");
  return res.json();
}

export async function resetPortfolio(userId: string = "default_user"): Promise<any> {
  const res = await fetch(`${API_BASE}/portfolio/reset?user_id=${userId}`, { method: "POST" });
  if (!res.ok) throw new Error("Reset failed");
  return res.json();
}
