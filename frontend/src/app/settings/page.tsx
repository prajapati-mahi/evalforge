"use client";

import React, { useEffect, useState } from "react";
import {
  Settings,
  FileDown,
  FileSpreadsheet,
  FileText,
  Activity,
  CheckCircle2,
  AlertTriangle,
  User,
  ShieldCheck,
  Server
} from "lucide-react";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { Experiment } from "@/types";

export default function SettingsPage() {
  const [projectId, setProjectId] = useState<number | undefined>();
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [selectedExpId, setSelectedExpId] = useState<number | undefined>();
  const [generating, setGenerating] = useState<string | null>(null);
  const [reportResult, setReportResult] = useState<any>(null);

  useEffect(() => {
    api.getExperiments(projectId).then((data) => {
      setExperiments(data);
      if (data.length > 0 && !selectedExpId) {
        setSelectedExpId(data[0].id);
      }
    }).catch(console.error);
  }, [projectId]);

  const handleGenerateReport = async (format: "pdf" | "csv") => {
    if (!selectedExpId) return;
    setGenerating(format);
    try {
      const res = await api.generateReport(selectedExpId, format);
      setReportResult(res);
      // Trigger browser download
      window.open(`http://127.0.0.1:8000${res.download_url}`, "_blank");
    } catch (err: any) {
      alert(err.message || "Failed to generate report.");
    } finally {
      setGenerating(null);
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <Header activeProjectId={projectId} onProjectChange={setProjectId} />

      <main className="flex-1 p-8 space-y-6 max-w-7xl mx-auto w-full">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            System Settings & Executive Reports
          </h1>
          <p className="text-sm text-slate-400">
            Export official PDF audit reports, download benchmark datasets in CSV, and monitor system infrastructure.
          </p>
        </div>

        {/* Report Generation Section */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="font-semibold text-base text-white flex items-center gap-2">
                <FileDown className="w-4 h-4 text-blue-400" />
                Downloadable Benchmark Reports
              </h3>
              <p className="text-xs text-slate-400">
                Generate formal compliance & accuracy summaries from stored experiment traces.
              </p>
            </div>
            <span className="text-xs font-mono text-slate-500">ReportLab & CSV Exporter</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1">Select Experiment to Export</label>
              <select
                value={selectedExpId || ""}
                onChange={(e) => setSelectedExpId(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white"
              >
                {experiments.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.name} (ID #{e.id} • {e.status.toUpperCase()})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-end gap-3">
              <button
                onClick={() => handleGenerateReport("pdf")}
                disabled={generating !== null || !selectedExpId}
                className="flex-1 py-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center justify-center gap-2 transition-colors shadow-sm"
              >
                <FileText className="w-4 h-4" />
                {generating === "pdf" ? "Rendering PDF..." : "Export Official PDF"}
              </button>

              <button
                onClick={() => handleGenerateReport("csv")}
                disabled={generating !== null || !selectedExpId}
                className="flex-1 py-2 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-semibold flex items-center justify-center gap-2 transition-colors border border-slate-700"
              >
                <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                {generating === "csv" ? "Exporting CSV..." : "Export Full CSV"}
              </button>
            </div>
          </div>

          {reportResult && (
            <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30 text-xs text-emerald-300 flex items-center justify-between">
              <span>Report generated successfully: <b>{reportResult.filename}</b></span>
              <a
                href={`http://127.0.0.1:8000${reportResult.download_url}`}
                target="_blank"
                download
                className="text-xs font-bold underline hover:text-emerald-200"
              >
                Click to Re-download
              </a>
            </div>
          )}
        </div>

        {/* Infrastructure & Services Status */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-4">
            <h3 className="font-semibold text-sm text-white flex items-center gap-2">
              <Server className="w-4 h-4 text-purple-400" /> Infrastructure Health
            </h3>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/40 border border-slate-700/50">
                <span className="text-slate-300 font-medium">FastAPI Engine</span>
                <span className="flex items-center gap-1.5 text-emerald-400 font-mono">
                  <CheckCircle2 className="w-3.5 h-3.5" /> v1.0.0 Online
                </span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/40 border border-slate-700/50">
                <span className="text-slate-300 font-medium">Database Layer</span>
                <span className="flex items-center gap-1.5 text-emerald-400 font-mono">
                  <CheckCircle2 className="w-3.5 h-3.5" /> PostgreSQL / SQLite Active
                </span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/40 border border-slate-700/50">
                <span className="text-slate-300 font-medium">Background Worker</span>
                <span className="flex items-center gap-1.5 text-emerald-400 font-mono">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Celery & Async Pipeline
                </span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/40 border border-slate-700/50">
                <span className="text-slate-300 font-medium">Demo Mode</span>
                <span className="flex items-center gap-1.5 text-blue-400 font-mono">
                  <ShieldCheck className="w-3.5 h-3.5" /> Enabled (Deterministic Mocks)
                </span>
              </div>
            </div>
          </div>

          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-4">
            <h3 className="font-semibold text-sm text-white flex items-center gap-2">
              <User className="w-4 h-4 text-blue-400" /> Active User Session
            </h3>

            <div className="space-y-2 text-xs">
              <div className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 space-y-1">
                <span className="text-slate-400 block text-[10px]">Authenticated Account</span>
                <span className="font-semibold text-white text-sm">Alex Rivera</span>
                <span className="text-slate-400 block font-mono text-[11px]">demo@evalforge.dev</span>
              </div>
              <div className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 space-y-1">
                <span className="text-slate-400 block text-[10px]">Assigned Role</span>
                <span className="font-semibold text-emerald-400 font-mono">Lead AI Engineer / Superuser</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
