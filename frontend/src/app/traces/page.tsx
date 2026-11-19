"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Layers,
  ChevronRight,
  ChevronDown,
  Database,
  Cpu,
  Gauge,
  Wrench
} from "lucide-react";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { Trace, TraceSpan } from "@/types";
import { formatCurrency, formatLatency } from "@/lib/utils";

export default function TracesPage() {
  const [projectId, setProjectId] = useState<number | undefined>();
  const [traces, setTraces] = useState<Trace[]>([]);
  const [selectedTrace, setSelectedTrace] = useState<Trace | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(false);

  const loadTraces = () => {
    setLoading(true);
    api.getTraces(projectId, statusFilter || undefined, undefined, search || undefined)
      .then((data) => {
        setTraces(data);
        if (data.length > 0 && !selectedTrace) {
          setSelectedTrace(data[0]);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTraces();
  }, [projectId, statusFilter, search]);

  const getSpanIcon = (type: string) => {
    switch (type) {
      case "retrieval":
        return <Database className="w-3.5 h-3.5 text-cyan-400" />;
      case "model_generation":
        return <Cpu className="w-3.5 h-3.5 text-blue-400" />;
      case "evaluation":
        return <Gauge className="w-3.5 h-3.5 text-emerald-400" />;
      default:
        return <Wrench className="w-3.5 h-3.5 text-amber-400" />;
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <Header activeProjectId={projectId} onProjectChange={setProjectId} />

      <main className="flex-1 p-8 space-y-6 max-w-7xl mx-auto w-full">
        {/* Title & Filter Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              Execution Traces & Hierarchical Spans
            </h1>
            <p className="text-sm text-slate-400">
              Inspect granular retrieval passages, model invocations, tool calls, and latency waterfalls.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search traces..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8 pr-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 w-44"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="success">Success</option>
              <option value="error">Error</option>
            </select>
          </div>
        </div>

        {/* Traces Explorer Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Traces List */}
          <div className="space-y-3">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
              Traces Stream ({traces.length})
            </div>
            <div className="space-y-2 max-h-[680px] overflow-y-auto pr-1">
              {traces.map((t) => {
                const isSelected = selectedTrace?.id === t.id;
                return (
                  <div
                    key={t.id}
                    onClick={() => setSelectedTrace(t)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all space-y-2 ${
                      isSelected
                        ? "bg-blue-950/20 border-blue-500/50 shadow-md shadow-blue-500/5"
                        : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="space-y-0.5">
                        <span className="text-[10px] font-mono text-slate-500">#{t.id}</span>
                        <h4 className="font-semibold text-xs text-slate-200 line-clamp-1">{t.trace_name}</h4>
                      </div>
                      <span
                        className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded ${
                          t.status === "success"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                        }`}
                      >
                        {t.status}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                      <span className="flex items-center gap-1 font-mono">
                        <Clock className="w-3 h-3 text-amber-400" /> {formatLatency(t.latency_ms)}
                      </span>
                      <span>{t.total_tokens} toks</span>
                      <span>{formatCurrency(t.total_cost)}</span>
                    </div>
                  </div>
                );
              })}
              {traces.length === 0 && (
                <div className="text-center py-12 text-slate-500 text-xs">
                  No traces match current filters.
                </div>
              )}
            </div>
          </div>

          {/* Trace Detail & Chronological Waterfall */}
          <div className="lg:col-span-2 space-y-4">
            {selectedTrace ? (
              <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
                  <div>
                    <span className="text-xs text-blue-400 font-mono font-semibold">TRACE IDENTIFIER #{selectedTrace.id}</span>
                    <h3 className="font-bold text-base text-white">{selectedTrace.trace_name}</h3>
                    <p className="text-xs text-slate-400">
                      Started: {new Date(selectedTrace.start_time).toLocaleString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-3 text-xs bg-slate-800/50 p-2 rounded-lg border border-slate-700/60">
                    <div>
                      <span className="text-slate-400 block text-[10px]">Latency</span>
                      <span className="font-semibold text-amber-300">{formatLatency(selectedTrace.latency_ms)}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Tokens</span>
                      <span className="font-semibold text-slate-200">{selectedTrace.total_tokens}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Cost</span>
                      <span className="font-semibold text-purple-300">{formatCurrency(selectedTrace.total_cost)}</span>
                    </div>
                  </div>
                </div>

                {/* Waterfall Spans Timeline */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Execution Timeline & Nested Spans ({selectedTrace.spans.length})
                    </h4>
                    <span className="text-[10px] text-slate-500 font-mono">End-to-End Waterfall</span>
                  </div>

                  <div className="space-y-3 relative before:absolute before:inset-0 before:left-3.5 before:w-0.5 before:bg-slate-800">
                    {selectedTrace.spans.map((span, idx) => (
                      <div key={span.id} className="relative pl-8 space-y-2 group">
                        {/* Dot indicator */}
                        <div className="absolute left-1.5 top-2.5 w-4 h-4 rounded-full bg-slate-900 border-2 border-blue-500 flex items-center justify-center -translate-x-1/2">
                          <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                        </div>

                        <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 space-y-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              {getSpanIcon(span.span_type)}
                              <span className="font-semibold text-xs text-white">{span.span_name}</span>
                              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-900 text-slate-400">
                                {span.span_type}
                              </span>
                            </div>
                            <span className="text-xs font-mono text-amber-400 font-semibold">
                              {formatLatency(span.latency_ms)}
                            </span>
                          </div>

                          {span.input_data && (
                            <div className="space-y-1">
                              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Input Payload</span>
                              <div className="text-xs font-mono bg-slate-900/80 p-2.5 rounded border border-slate-800 text-slate-300 line-clamp-3">
                                {span.input_data}
                              </div>
                            </div>
                          )}

                          {span.output_data && (
                            <div className="space-y-1">
                              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Output / Extracted Claims</span>
                              <div className="text-xs font-mono bg-slate-900/80 p-2.5 rounded border border-slate-800 text-slate-300 line-clamp-3">
                                {span.output_data}
                              </div>
                            </div>
                          )}

                          {span.attributes_json && Object.keys(span.attributes_json).length > 0 && (
                            <div className="flex flex-wrap gap-2 pt-1 border-t border-slate-800/60 text-[10px] font-mono text-slate-400">
                              {Object.entries(span.attributes_json).map(([k, v]) => (
                                <span key={k} className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                                  {k}: <b className="text-slate-300">{typeof v === "object" ? JSON.stringify(v) : String(v)}</b>
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
                Select a trace from the left stream to inspect granular spans.
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
