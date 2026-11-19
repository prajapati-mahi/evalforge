"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Coins,
  Cpu,
  TrendingUp,
  FileText,
  Play,
  ArrowRight,
  Database,
  RefreshCw
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from "recharts";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { DashboardMetrics } from "@/types";
import { formatNumber, formatCurrency, formatLatency, formatPercentage } from "@/lib/utils";

export default function OverviewPage() {
  const [projectId, setProjectId] = useState<number | undefined>();
  const [timeRange, setTimeRange] = useState("30d");
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = () => {
    setLoading(true);
    api.getDashboardMetrics(projectId, timeRange)
      .then(setMetrics)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchMetrics();
  }, [projectId, timeRange]);

  return (
    <div className="flex-1 flex flex-col">
      <Header activeProjectId={projectId} onProjectChange={setProjectId} />

      <main className="flex-1 p-8 space-y-8 max-w-7xl mx-auto w-full">
        {/* Welcome & Filter Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              Evaluation & Observability Dashboard
            </h1>
            <p className="text-sm text-slate-400">
              Live quantitative benchmarks across correctness, context grounding, cost, and latency.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-1 flex items-center gap-1 text-xs">
              {(["24h", "7d", "30d", "all"] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => setTimeRange(r)}
                  className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                    timeRange === r
                      ? "bg-blue-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {r.toUpperCase()}
                </button>
              ))}
            </div>

            <button
              onClick={fetchMetrics}
              className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
              title="Refresh Metrics"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* Empty State / Getting Started */}
        {metrics?.is_empty && (
          <div className="border border-blue-500/30 bg-blue-950/20 rounded-xl p-8 text-center space-y-4">
            <div className="w-12 h-12 rounded-xl bg-blue-600/20 border border-blue-500/40 mx-auto flex items-center justify-center text-blue-400">
              <Sparkles className="w-6 h-6" />
            </div>
            <div className="max-w-md mx-auto space-y-1">
              <h3 className="text-lg font-semibold text-white">No Evaluation Records Found</h3>
              <p className="text-xs text-slate-400">
                Get started by creating a dataset and running your first multi-model evaluation experiment.
              </p>
            </div>
            <div className="flex items-center justify-center gap-3 pt-2">
              <Link
                href="/datasets"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium flex items-center gap-2"
              >
                <Database className="w-4 h-4" /> Load Benchmark Dataset
              </Link>
              <Link
                href="/experiments"
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium flex items-center gap-2"
              >
                <Play className="w-4 h-4" /> New Experiment
              </Link>
            </div>
          </div>
        )}

        {/* KPI Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Avg Correctness</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">
              {metrics ? formatPercentage(metrics.avg_correctness) : "--"}
            </div>
            <p className="text-[11px] text-slate-500">Target benchmark &gt; 85%</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Avg Faithfulness</span>
              <TrendingUp className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">
              {metrics ? formatPercentage(metrics.avg_faithfulness) : "--"}
            </div>
            <p className="text-[11px] text-slate-500">Context grounding adherence</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Average Latency</span>
              <Clock className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">
              {metrics ? formatLatency(metrics.avg_latency_ms) : "--"}
            </div>
            <p className="text-[11px] text-slate-500">End-to-end response time</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Total Estimated Cost</span>
              <Coins className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">
              {metrics ? formatCurrency(metrics.total_cost) : "--"}
            </div>
            <p className="text-[11px] text-slate-500">
              {metrics ? formatNumber(metrics.total_tokens) : 0} tokens evaluated
            </p>
          </div>
        </div>

        {/* Secondary KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-1">
            <span className="text-xs text-slate-400">Total Evaluations</span>
            <div className="text-xl font-semibold text-slate-200">
              {metrics ? formatNumber(metrics.total_evaluations) : 0} runs
            </div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-1">
            <span className="text-xs text-slate-400">Test Cases Executed</span>
            <div className="text-xl font-semibold text-slate-200">
              {metrics ? formatNumber(metrics.total_test_cases) : 0} cases
            </div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-1">
            <span className="text-xs text-slate-400">Execution Success Rate</span>
            <div className="text-xl font-semibold text-emerald-400">
              {metrics ? `${metrics.success_rate}%` : "100%"}
            </div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-1">
            <span className="text-xs text-slate-400">Failed Executions</span>
            <div className="text-xl font-semibold text-rose-400">
              {metrics ? metrics.failed_executions : 0} errors
            </div>
          </div>
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Score Over Time */}
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-200">Evaluation Scores Over Time</h3>
                <p className="text-xs text-slate-500">Tracking accuracy & context grounding progression</p>
              </div>
            </div>
            <div className="h-64 w-full">
              {metrics?.score_over_time && metrics.score_over_time.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={metrics.score_over_time}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="date_label" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px" }}
                      formatter={(val: any) => [`${val}%`, ""]}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="correctness" stroke="#3b82f6" strokeWidth={2} name="Correctness %" />
                    <Line type="monotone" dataKey="faithfulness" stroke="#06b6d4" strokeWidth={2} name="Faithfulness %" />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">
                  No chronological data recorded yet.
                </div>
              )}
            </div>
          </div>

          {/* Model Performance Comparison */}
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-200">Model Performance Breakdown</h3>
              <p className="text-xs text-slate-500">Correctness & Faithfulness across models</p>
            </div>
            <div className="h-64 w-full">
              {metrics?.model_performance && metrics.model_performance.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={metrics.model_performance}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="model_name" stroke="#64748b" fontSize={10} />
                    <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px" }}
                      formatter={(val: any) => [`${val}%`, ""]}
                    />
                    <Legend />
                    <Bar dataKey="correctness" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Correctness %" />
                    <Bar dataKey="faithfulness" fill="#10b981" radius={[4, 4, 0, 0]} name="Faithfulness %" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">
                  No model comparisons recorded yet.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Latency Distribution */}
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-200">Latency Distribution</h3>
              <p className="text-xs text-slate-500">Count of executions by duration bucket</p>
            </div>
            <div className="h-60 w-full">
              {metrics?.latency_distribution && metrics.latency_distribution.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={metrics.latency_distribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="range_label" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px" }}
                    />
                    <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Executions" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">
                  No latency records available.
                </div>
              )}
            </div>
          </div>

          {/* Quick Action Navigation */}
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-col justify-between">
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-200">Platform Quick Actions</h3>
              <p className="text-xs text-slate-500">Execute key engineering workflows with one click</p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <Link
                  href="/experiments"
                  className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60 hover:bg-slate-800 hover:border-blue-500/50 transition-all flex items-center justify-between group"
                >
                  <div className="space-y-0.5">
                    <span className="text-xs font-semibold text-slate-200 group-hover:text-blue-400">Launch Experiment</span>
                    <p className="text-[11px] text-slate-400">Run multi-model benchmarks</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-blue-400 transition-colors" />
                </Link>

                <Link
                  href="/comparison"
                  className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60 hover:bg-slate-800 hover:border-cyan-500/50 transition-all flex items-center justify-between group"
                >
                  <div className="space-y-0.5">
                    <span className="text-xs font-semibold text-slate-200 group-hover:text-cyan-400">Model Comparison</span>
                    <p className="text-[11px] text-slate-400">Radar & win-rate trade-offs</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 transition-colors" />
                </Link>

                <Link
                  href="/traces"
                  className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60 hover:bg-slate-800 hover:border-emerald-500/50 transition-all flex items-center justify-between group"
                >
                  <div className="space-y-0.5">
                    <span className="text-xs font-semibold text-slate-200 group-hover:text-emerald-400">Inspect Traces</span>
                    <p className="text-[11px] text-slate-400">Hierarchical span timelines</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 transition-colors" />
                </Link>

                <Link
                  href="/metrics"
                  className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60 hover:bg-slate-800 hover:border-purple-500/50 transition-all flex items-center justify-between group"
                >
                  <div className="space-y-0.5">
                    <span className="text-xs font-semibold text-slate-200 group-hover:text-purple-400">Evaluator Playground</span>
                    <p className="text-[11px] text-slate-400">Test judges & human review</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-purple-400 transition-colors" />
                </Link>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
              <span>All metrics computed directly from persistent database records.</span>
              <span className="font-mono text-[11px] text-slate-500">EvalEngine v1.0</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
