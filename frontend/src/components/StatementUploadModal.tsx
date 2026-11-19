"use client";

import React, { useState } from "react";
import { X, UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { uploadStatement } from "@/lib/api";

interface StatementUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
}

export const StatementUploadModal: React.FC<StatementUploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResultMessage(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a bank or mutual fund statement file.");
      return;
    }

    setIsUploading(true);
    setError(null);
    try {
      const res = await uploadStatement(file);
      setResultMessage(res.extracted_summary);
      onUploadSuccess();
      setTimeout(() => {
        setIsUploading(false);
      }, 1500);
    } catch (err: any) {
      setError(err.message || "Failed to parse statement.");
      setIsUploading(false);
    }
  };

  // Preset demo test statements for easy user testing
  const uploadDemoStatement = async (type: "bank" | "mf") => {
    setIsUploading(true);
    setError(null);
    try {
      let content = "";
      let filename = "";
      if (type === "bank") {
        filename = "HDFC_Bank_Statement.csv";
        content = `Date,Description,Amount,Type\n2026-11-01,Salary Credit Tech Corp,150000,CREDIT\n2026-11-05,Mutual Fund SIP Debit,35000,DEBIT\n2026-11-10,Closing Balance: 580000,0,CREDIT\n`;
      } else {
        filename = "Zerodha_Holdings_Consolidated.csv";
        content = `Instrument,Qty,Current Value\nTata Motors Ltd,50,480000\nReliance Industries,100,285000\nICICI Bank Ltd,150,195000\n`;
      }

      const blob = new Blob([content], { type: "text/csv" });
      const demoFile = new File([blob], filename, { type: "text/csv" });
      const res = await uploadStatement(demoFile);
      setResultMessage(res.extracted_summary);
      onUploadSuccess();
      setIsUploading(false);
    } catch (err: any) {
      setError(err.message || "Failed to process demo statement.");
      setIsUploading(false);
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
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <UploadCloud className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Upload Financial Statement</h3>
            <p className="text-xs text-slate-400">PDF or CSV (Bank statement, Mutual Fund CAS, Demat)</p>
          </div>
        </div>

        {/* Upload Drop Area */}
        <label className="border-2 border-dashed border-slate-700 hover:border-emerald-500/50 rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-colors bg-slate-950/40">
          <FileText className="w-8 h-8 text-slate-400 mb-2" />
          <span className="text-sm font-medium text-slate-200">
            {file ? file.name : "Click to select or drag and drop file"}
          </span>
          <span className="text-xs text-slate-500 mt-1">Supports PDF, CSV, Excel (max 20MB)</span>
          <input
            type="file"
            accept=".pdf,.csv,.xlsx"
            onChange={handleFileChange}
            className="hidden"
          />
        </label>

        {/* Quick Demo Pre-fills */}
        <div className="mt-4 pt-3 border-t border-slate-800">
          <span className="text-xs text-slate-400 font-medium block mb-2">Or test with demo statements:</span>
          <div className="flex gap-2">
            <button
              onClick={() => uploadDemoStatement("bank")}
              disabled={isUploading}
              className="flex-1 text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 py-1.5 px-2 rounded-lg transition-colors"
            >
              📄 HDFC Bank CSV
            </button>
            <button
              onClick={() => uploadDemoStatement("mf")}
              disabled={isUploading}
              className="flex-1 text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 py-1.5 px-2 rounded-lg transition-colors"
            >
              📈 Zerodha Holdings CSV
            </button>
          </div>
        </div>

        {/* Feedback Messages */}
        {resultMessage && (
          <div className="mt-4 p-3 rounded-xl bg-emerald-950/30 border border-emerald-800/40 text-xs text-emerald-300 flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400 mt-0.5" />
            <span>{resultMessage}</span>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-950/30 border border-rose-800/40 text-xs text-rose-300 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Action Button */}
        <div className="mt-5 flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 text-xs font-semibold transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={!file || isUploading}
            className="flex-1 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 text-slate-950 text-xs font-bold transition-colors flex items-center justify-center gap-1.5 shadow-md shadow-emerald-500/20"
          >
            {isUploading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            {isUploading ? "Extracting Facts..." : "Upload & Sync Graph"}
          </button>
        </div>
      </div>
    </div>
  );
};
