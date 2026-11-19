"use client";

import React, { useEffect, useState } from "react";
import {
  Scale,
  Trophy,
  Zap,
  Coins,
  Clock,
  Sparkles,
  ChevronDown,
  CheckCircle2,
  XCircle,
  HelpCircle
} from "lucide-react";
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid
} from "recharts";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { Experiment, ModelComparisonData } from "@/types";
import { formatCurrency, formatLatency, formatPercentage } from "@/lib/utils";

const MODEL_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#a855f7", "#ec4899"];

export default function ModelComparisonPage() {
  const [projectId, setProjectId] = useState<number | undefined>();
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [selectedExpId, setSelectedExpId] = useState<number | undefined>();
  const [comparison, setComparison] = useState<ModelComparisonData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getExperiments(projectId).then((data) => {
      setExperiments(data);
      if (data.length > 0 && !selectedExpId) {
        setSelectedExpId(data[0].id);
      }
    }).catch(console.error);
  }, [projectId]);

  useEffect(() => {
    if (selectedExpId) {
      setLoading(true);
      api.getModelComparison(selectedExpId)
        .then(setComparison)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [selectedExpId]);

  return (
    <div className="flex-1 flex flex-col">
      <Header activeProjectId={projectId} onProjectChange={setProjectId} />

      <main className="flex-1 p-8 space-y-6 max-w-7xl mx-auto w-full">
        {/* Title & Experiment Selector */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              Model Comparison & Pareto Trade-offs
            </h1>
            <p className="text-sm text-slate-400">
              Benchmark multiple LLM candidates on identical test sets across quality, speed, and cost.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Experiment:</span>
            <select
              value={selectedExpId || ""}
              onChange={(e) => setSelectedExpId(Number(e.target.value))}
              className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs font-medium text-white focus:outline-none focus:border-blue-500"
            >
              {experiments.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name} (ID #{e.id})
                </option>
              ))}
            </select>
          </div>
        </div>

        {comparison ? (
          <>
            {/* Top Summaries & Win Rates */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {comparison.model_summaries.map((s, idx) => {
                const color = MODEL_COLORS[idx % MODEL_COLORS.length];
                return (
                  <div
                    key={s.model_name}
                    className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-4 relative overflow-hidden"
                  >
                    <div
                      className="absolute top-0 left-0 w-full h-1"
                      style={{ backgroundColor: color }}
                    />
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-[10px] font-mono uppercase text-slate-400">
                          {s.provider_name}
                        </span>
                        <h3 className="font-bold text-base text-white">{s.model_name}</h3>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Win Rate</span>
                        <span className="text-sm font-bold text-amber-400 flex items-center gap-1">
                          <Trophy className="w-3.5 h-3.5" /> {s.win_rate}%
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="p-2 rounded bg-slate-800/40">
                        <span className="text-slate-400 text-[10px] block">Correctness</span>
                        <span className="font-semibold text-slate-200">
                          {formatPercentage(s.avg_correctness)}
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-800/40">
                        <span className="text-slate-400 text-[10px] block">Faithfulness</span>
                        <span className="font-semibold text-slate-200">
                          {formatPercentage(s.avg_faithfulness)}
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-800/40">
                        <span className="text-slate-400 text-[10px] block">Avg Latency</span>
                        <span className="font-semibold text-amber-300">
                          {formatLatency(s.avg_latency_ms)}
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-800/40">
                        <span className="text-slate-400 text-[10px] block">Total Cost</span>
                        <span className="font-semibold text-purple-300">
                          {formatCurrency(s.total_cost)}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Radar Chart & Latency/Cost Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Radar Chart */}
              <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Multi-Dimensional Capability Radar</h3>
                  <p className="text-xs text-slate-500">Normalised 0-100 scores across evaluators</p>
                </div>
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="75%" data={comparison.radar_data}>
                      <PolarGrid stroke="#1e293b" />
                      <PolarAngleAxis dataKey="metric" stroke="#94a3b8" fontSize={11} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#475569" fontSize={9} />
                      <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }} />
                      <Legend />
                      {comparison.models.map((modelName, i) => (
                        <Radar
                          key={modelName}
                          name={modelName}
                          dataKey={modelName}
                          stroke={MODEL_COLORS[i % MODEL_COLORS.length]}
                          fill={MODEL_COLORS[i % MODEL_COLORS.length]}
                          fillOpacity={0.25}
                        />
                      ))}
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Latency vs Cost Bar Chart */}
              <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Latency & Cost Comparison</h3>
                  <p className="text-xs text-slate-500">Speed (ms) vs Economic footprint</p>
                </div>
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={comparison.model_summaries}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="model_name" stroke="#64748b" fontSize={10} />
                      <YAxis stroke="#64748b" fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }} />
                      <Legend />
                      <Bar dataKey="avg_latency_ms" fill="#f59e0b" name="Avg Latency (ms)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Side-by-Side Test Case Inspection */}
            <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-4">
              <div>
                <h3 className="text-base font-semibold text-white">Side-by-Side Case Evaluation</h3>
                <p className="text-xs text-slate-400">
                  Inspect exact model responses and factual correctness scores on the same input prompt.
                </p>
              </div>

              <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1">
                {comparison.side_by_side_cases.map((sc, idx) => (
                  <div key={sc.case_id} className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/50 space-y-3">
                    <div className="flex items-center justify-between text-xs pb-2 border-b border-slate-800">
                      <span className="font-semibold text-blue-400">Test Case #{idx + 1}</span>
                      <span className="text-slate-400">ID: {sc.case_id}</span>
                    </div>

                    <div className="space-y-1">
                      <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Prompt Input</span>
                      <p className="text-xs font-mono bg-slate-900/60 p-2.5 rounded text-slate-200 border border-slate-800">
                        {sc.input}
                      </p>
                    </div>

                    {sc.expected && (
                      <div className="space-y-1">
                        <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider block">Expected Output</span>
                        <p className="text-xs bg-slate-900/60 p-2 rounded text-slate-300 border border-slate-800">
                          {sc.expected}
                        </p>
                      </div>
                    )}

                    {/* Side-by-side models output columns */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
                      {comparison.models.map((modelName, mIdx) => {
                        const mData = sc.models[modelName];
                        if (!mData) return null;
                        const color = MODEL_COLORS[mIdx % MODEL_COLORS.length];
                        return (
                          <div
                            key={modelName}
                            className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2 flex flex-col justify-between"
                          >
                            <div className="space-y-1.5">
                              <div className="flex items-center justify-between">
                                <span className="font-semibold text-xs text-white" style={{ color }}>
                                  {modelName}
                                </span>
                                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                  mData.correctness >= 0.7
                                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                    : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                                }`}>
                                  Score: {formatPercentage(mData.correctness)}
                                </span>
                              </div>
                              <p className="text-xs text-slate-300 line-clamp-4 leading-relaxed">
                                {mData.output || "No output generated"}
                              </p>
                            </div>

                            <div className="flex items-center justify-between text-[10px] text-slate-400 pt-2 border-t border-slate-800/60">
                              <span>{formatLatency(mData.latency_ms)}</span>
                              <span>{mData.tokens} toks</span>
                              <span>{formatCurrency(mData.cost)}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="h-64 flex items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
            {loading ? "Calculating comparative statistical metrics..." : "Select an experiment to view comparison analysis."}
          </div>
        )}
      </main>
    </div>
  );
}
