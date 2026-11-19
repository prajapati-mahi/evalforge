"use client";

import React, { useEffect, useState } from "react";
import {
  FlaskConical,
  Plus,
  Play,
  RotateCcw,
  StopCircle,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  ChevronRight,
  Eye,
  FileCheck2,
  X
} from "lucide-react";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { Experiment, Dataset, Prompt } from "@/types";
import { formatLatency, formatCurrency, formatPercentage } from "@/lib/utils";

export default function ExperimentsPage() {
  const [projectId, setProjectId] = useState<number | undefined>();
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [selectedExp, setSelectedExp] = useState<Experiment | null>(null);
  const [expResults, setExpResults] = useState<any>(null);
  const [loadingResults, setLoadingResults] = useState(false);

  // New Experiment Wizard Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [expName, setExpName] = useState("");
  const [expDesc, setExpDesc] = useState("");
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | undefined>();
  const [selectedPromptId, setSelectedPromptId] = useState<number | undefined>();
  const [selectedModels, setSelectedModels] = useState<string[]>(["mock-gpt-4o", "mock-claude-3-5-sonnet"]);
  const [selectedEvaluators, setSelectedEvaluators] = useState<string[]>([
    "correctness",
    "faithfulness",
    "response_relevance",
    "hallucination",
  ]);

  const loadData = () => {
    api.getExperiments(projectId).then((data) => {
      setExperiments(data);
      if (data.length > 0 && !selectedExp) {
        setSelectedExp(data[0]);
      }
    }).catch(console.error);

    api.getDatasets(projectId).then(setDatasets).catch(console.error);
    if (projectId) {
      api.getPrompts(projectId).then(setPrompts).catch(console.error);
    }
  };

  useEffect(() => {
    loadData();
  }, [projectId]);

  // Poll running experiments
  useEffect(() => {
    const hasRunning = experiments.some((e) => e.status === "running" || e.status === "queued");
    if (!hasRunning) return;

    const timer = setInterval(() => {
      api.getExperiments(projectId).then(setExperiments).catch(console.error);
      if (selectedExp) {
        api.getExperimentResults(selectedExp.id).then(setExpResults).catch(console.error);
      }
    }, 2500);

    return () => clearInterval(timer);
  }, [experiments, projectId, selectedExp]);

  useEffect(() => {
    if (selectedExp) {
      setLoadingResults(true);
      api.getExperimentResults(selectedExp.id)
        .then(setExpResults)
        .catch(console.error)
        .finally(() => setLoadingResults(false));
    }
  }, [selectedExp]);

  const handleCreateExperiment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId || !selectedDatasetId || !expName.trim()) return;
    try {
      const created = await api.createExperiment({
        project_id: projectId,
        name: expName,
        description: expDesc,
        dataset_id: selectedDatasetId,
        prompt_version_id: selectedPromptId,
        config: {
          models: selectedModels,
          evaluators: selectedEvaluators,
          temperature: 0.2,
          max_tokens: 512,
        },
      });
      setIsModalOpen(false);
      setExpName("");
      setExpDesc("");
      loadData();
      setSelectedExp(created);
    } catch (err: any) {
      alert(err.message || "Failed to create experiment");
    }
  };

  const handleRun = async (id: number) => {
    try {
      await api.runExperiment(id);
      loadData();
    } catch (err: any) {
      alert(err.message || "Failed to run experiment");
    }
  };

  const handleCancel = async (id: number) => {
    try {
      await api.cancelExperiment(id);
      loadData();
    } catch (err: any) {
      alert(err.message || "Failed to cancel experiment");
    }
  };

  const toggleModel = (m: string) => {
    setSelectedModels((prev) =>
      prev.includes(m) ? (prev.length > 1 ? prev.filter((x) => x !== m) : prev) : [...prev, m]
    );
  };

  const toggleEvaluator = (ev: string) => {
    setSelectedEvaluators((prev) =>
      prev.includes(ev) ? (prev.length > 1 ? prev.filter((x) => x !== ev) : prev) : [...prev, ev]
    );
  };

  return (
    <div className="flex-1 flex flex-col">
      <Header activeProjectId={projectId} onProjectChange={setProjectId} />

      <main className="flex-1 p-8 space-y-6 max-w-7xl mx-auto w-full">
        {/* Title */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              Experiment Engine & Benchmarks
            </h1>
            <p className="text-sm text-slate-400">
              Run repeatable, reproducible evaluation pipelines across single or multiple LLM providers.
            </p>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm shadow-blue-500/20"
          >
            <Plus className="w-4 h-4" /> New Experiment
          </button>
        </div>

        {/* Experiment Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Experiment List */}
          <div className="space-y-3">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
              Recorded Experiments ({experiments.length})
            </div>
            <div className="space-y-2">
              {experiments.map((exp) => {
                const isSelected = selectedExp?.id === exp.id;
                const isRunning = exp.status === "running" || exp.status === "queued";
                return (
                  <div
                    key={exp.id}
                    onClick={() => setSelectedExp(exp)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all space-y-3 ${
                      isSelected
                        ? "bg-blue-950/20 border-blue-500/50 shadow-md shadow-blue-500/5"
                        : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${
                              exp.status === "completed"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : isRunning
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse"
                                : exp.status === "cancelled"
                                ? "bg-slate-800 text-slate-400"
                                : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            }`}
                          >
                            {exp.status}
                          </span>
                          <span className="text-[10px] text-slate-500">ID #{exp.id}</span>
                        </div>
                        <h4 className="font-semibold text-sm text-slate-100">{exp.name}</h4>
                        <p className="text-xs text-slate-400 line-clamp-1">{exp.description}</p>
                      </div>
                      <ChevronRight
                        className={`w-4 h-4 shrink-0 transition-transform ${
                          isSelected ? "rotate-90 text-blue-400" : "text-slate-600"
                        }`}
                      />
                    </div>

                    {/* Progress Bar */}
                    {exp.total_cases > 0 && (
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-[10px] text-slate-400">
                          <span>Progress</span>
                          <span>
                            {exp.processed_cases} / {exp.total_cases} cases
                          </span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500 transition-all duration-300"
                            style={{
                              width: `${Math.min(
                                100,
                                Math.round((exp.processed_cases / exp.total_cases) * 100)
                              )}%`,
                            }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Experiment Detail / Runs & Test Cases */}
          <div className="lg:col-span-2 space-y-4">
            {selectedExp ? (
              <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-6">
                {/* Header with Run / Cancel buttons */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-lg text-white">{selectedExp.name}</h3>
                      <span className="text-xs text-slate-500 font-mono">
                        {selectedExp.status.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">{selectedExp.description}</p>
                  </div>

                  <div className="flex items-center gap-2">
                    {selectedExp.status === "running" || selectedExp.status === "queued" ? (
                      <button
                        onClick={() => handleCancel(selectedExp.id)}
                        className="px-3.5 py-1.5 rounded-lg bg-rose-600/20 text-rose-300 hover:bg-rose-600/30 border border-rose-500/30 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                      >
                        <StopCircle className="w-3.5 h-3.5" /> Cancel Execution
                      </button>
                    ) : (
                      <button
                        onClick={() => handleRun(selectedExp.id)}
                        className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm shadow-blue-500/20"
                      >
                        <Play className="w-3.5 h-3.5" /> Execute Benchmark
                      </button>
                    )}
                  </div>
                </div>

                {/* Model Runs Summary Cards */}
                {expResults?.runs && expResults.runs.length > 0 && (
                  <div className="space-y-4">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Evaluated Models ({expResults.runs.length})
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {expResults.runs.map((r: any) => {
                        const sm = r.summary_metrics || {};
                        return (
                          <div
                            key={r.id}
                            className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-3"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-sm text-slate-100">{r.model_name}</span>
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-300">
                                {r.provider_name}
                              </span>
                            </div>

                            <div className="grid grid-cols-3 gap-2 text-center text-xs">
                              <div className="p-2 rounded bg-slate-900/60">
                                <span className="block text-[10px] text-slate-400">Correctness</span>
                                <span className="font-bold text-blue-400">
                                  {formatPercentage(sm.avg_correctness || 0)}
                                </span>
                              </div>
                              <div className="p-2 rounded bg-slate-900/60">
                                <span className="block text-[10px] text-slate-400">Faithfulness</span>
                                <span className="font-bold text-cyan-400">
                                  {formatPercentage(sm.avg_faithfulness || 0)}
                                </span>
                              </div>
                              <div className="p-2 rounded bg-slate-900/60">
                                <span className="block text-[10px] text-slate-400">Avg Latency</span>
                                <span className="font-bold text-amber-400">
                                  {formatLatency(sm.avg_latency_ms || 0)}
                                </span>
                              </div>
                            </div>

                            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                              <span>Tokens: {sm.total_tokens?.toLocaleString() || 0}</span>
                              <span>Cost: {formatCurrency(sm.total_cost || 0)}</span>
                              <span className="text-emerald-400">
                                {sm.success_count || 0} passed
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Detailed Test Case Output Viewer */}
                    <div className="space-y-3 pt-4 border-t border-slate-800">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                        Individual Test Case Executions & Grounding Verification
                      </h4>
                      <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                        {expResults.runs[0]?.test_case_runs?.map((cr: any, idx: number) => (
                          <div
                            key={cr.id}
                            className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50 space-y-3 text-xs"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-slate-300">Case #{idx + 1}</span>
                              <div className="flex items-center gap-2">
                                <span className="text-slate-400">{formatLatency(cr.latency_ms)}</span>
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                    cr.status === "success"
                                      ? "bg-emerald-500/10 text-emerald-400"
                                      : "bg-rose-500/10 text-rose-400"
                                  }`}
                                >
                                  {cr.status.toUpperCase()}
                                </span>
                              </div>
                            </div>

                            <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800 font-mono text-[11px] text-slate-300">
                              <span className="text-slate-500 block mb-1">PROMPT INQUIRY:</span>
                              {cr.input_text}
                            </div>

                            <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800 text-[11px] text-slate-200">
                              <span className="text-blue-400 font-semibold block mb-1">
                                GENERATED RESPONSE ({expResults.runs[0].model_name}):
                              </span>
                              {cr.generated_output}
                            </div>

                            {/* Evaluator Scores Pill Strip */}
                            {cr.evaluations && cr.evaluations.length > 0 && (
                              <div className="flex flex-wrap gap-2 pt-1">
                                {cr.evaluations.map((ev: any) => (
                                  <div
                                    key={ev.id}
                                    className={`px-2.5 py-1 rounded-md border text-[11px] flex items-center gap-1.5 ${
                                      ev.passed
                                        ? "bg-emerald-950/20 border-emerald-500/30 text-emerald-300"
                                        : "bg-rose-950/20 border-rose-500/30 text-rose-300"
                                    }`}
                                  >
                                    <span className="font-medium capitalize">{ev.metric_name}:</span>
                                    <span className="font-bold">{formatPercentage(ev.score)}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
                Select an experiment from the left pane to view details and execute.
              </div>
            )}
          </div>
        </div>

        {/* New Experiment Wizard Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0f172a] border border-slate-800 rounded-xl w-full max-w-xl p-6 space-y-5 shadow-2xl max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-base font-semibold text-white">Create Evaluation Experiment</h3>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="text-slate-400 hover:text-slate-200 p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleCreateExperiment} className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Experiment Name</label>
                  <input
                    type="text"
                    required
                    value={expName}
                    onChange={(e) => setExpName(e.target.value)}
                    placeholder="e.g. GPT-4o vs Claude 3.5 Sonnet RAG Factuality"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Description</label>
                  <textarea
                    rows={2}
                    value={expDesc}
                    onChange={(e) => setExpDesc(e.target.value)}
                    placeholder="Objective of this benchmark run..."
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Target Dataset</label>
                    <select
                      required
                      value={selectedDatasetId || ""}
                      onChange={(e) => setSelectedDatasetId(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="">Select a dataset...</option>
                      {datasets.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name} ({d.num_cases} cases)
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Prompt Template (Optional)</label>
                    <select
                      value={selectedPromptId || ""}
                      onChange={(e) => setSelectedPromptId(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="">Direct Query (Default)</option>
                      {prompts.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} (v{p.current_version})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Model Selection Multi-Check */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-300 block">
                    Models to Benchmark (Multi-select)
                  </label>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {[
                      { id: "mock-gpt-4o", label: "Mock GPT-4o (Fast Demo)" },
                      { id: "mock-claude-3-5-sonnet", label: "Mock Claude 3.5 Sonnet" },
                      { id: "mock-gemini-1.5-pro", label: "Mock Gemini 1.5 Pro" },
                      { id: "gpt-4o-mini", label: "OpenAI GPT-4o-mini" },
                    ].map((m) => (
                      <div
                        key={m.id}
                        onClick={() => toggleModel(m.id)}
                        className={`p-2.5 rounded-lg border cursor-pointer flex items-center justify-between ${
                          selectedModels.includes(m.id)
                            ? "bg-blue-600/15 border-blue-500 text-white"
                            : "bg-slate-900 border-slate-800 text-slate-400"
                        }`}
                      >
                        <span>{m.label}</span>
                        {selectedModels.includes(m.id) && (
                          <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Evaluator Suite */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-300 block">
                    Active Evaluator Metrics
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                    {[
                      { id: "correctness", label: "Answer Correctness" },
                      { id: "faithfulness", label: "Faithfulness" },
                      { id: "context_precision", label: "Context Precision" },
                      { id: "context_recall", label: "Context Recall" },
                      { id: "response_relevance", label: "Response Relevance" },
                      { id: "hallucination", label: "Hallucination Freedom" },
                    ].map((ev) => (
                      <div
                        key={ev.id}
                        onClick={() => toggleEvaluator(ev.id)}
                        className={`p-2 rounded-lg border cursor-pointer flex items-center justify-between ${
                          selectedEvaluators.includes(ev.id)
                            ? "bg-cyan-600/15 border-cyan-500 text-cyan-200"
                            : "bg-slate-900 border-slate-800 text-slate-400"
                        }`}
                      >
                        <span className="text-[11px] font-medium">{ev.label}</span>
                        {selectedEvaluators.includes(ev.id) && (
                          <CheckCircle2 className="w-3 h-3 text-cyan-400" />
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 text-xs text-slate-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-blue-600 text-xs font-semibold text-white shadow-sm"
                  >
                    Create & Configure
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
