"use client";

import React, { useState } from "react";
import {
  Gauge,
  Play,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Sparkles,
  ShieldCheck,
  Search,
  BookOpen,
  UserCheck
} from "lucide-react";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { formatPercentage } from "@/lib/utils";

const EVALUATOR_CARDS = [
  {
    id: "correctness",
    title: "Answer Correctness",
    category: "Factual Accuracy",
    desc: "Evaluates semantic & factual correspondence of the response against verified ground-truth reference.",
    formula: "F1 Overlap + Semantic Embedding & LLM Judge",
    threshold: ">= 0.70",
  },
  {
    id: "faithfulness",
    title: "Faithfulness (Grounding)",
    category: "Safety & Hallucination",
    desc: "Checks whether every assertion in the response can be directly inferred from the supplied context passages.",
    formula: "Supported Claims / Total Claims",
    threshold: ">= 0.80",
  },
  {
    id: "context_precision",
    title: "Context Precision",
    category: "RAG Retrieval",
    desc: "Measures whether retrieved context passages are focused and relevant to answering the query without noise.",
    formula: "Relevant Context Chunks / Retrieved Chunks",
    threshold: ">= 0.70",
  },
  {
    id: "context_recall",
    title: "Context Recall",
    category: "RAG Retrieval",
    desc: "Verifies whether the retrieved context contains all necessary facts required to answer the question completely.",
    formula: "Ground Truth Facts Captured / Total Required",
    threshold: ">= 0.75",
  },
  {
    id: "response_relevance",
    title: "Response Relevance",
    category: "User Experience",
    desc: "Penalizes evasiveness, excessive rambling, and off-topic diversions to ensure direct query resolution.",
    formula: "Semantic Query Alignment - Tangential Penalties",
    threshold: ">= 0.70",
  },
  {
    id: "hallucination",
    title: "Hallucination Freedom",
    category: "Safety",
    desc: "Audits for fabricated numbers, false entities, or ungrounded assertions diverging from truth sources.",
    formula: "1.0 - (Fabricated Assertions / Total Assertions)",
    threshold: ">= 0.85",
  },
];

export default function MetricsPage() {
  const [metricName, setMetricName] = useState("faithfulness");
  const [query, setQuery] = useState("What was Microsoft's Intelligent Cloud revenue in FY23?");
  const [response, setResponse] = useState("Intelligent Cloud revenue was $87.9 billion in FY23, an increase of 17%.");
  const [expectedOutput, setExpectedOutput] = useState("Intelligent Cloud revenue grew 17% to $87.9 billion.");
  const [context, setContext] = useState("Microsoft Annual Report FY23: Intelligent Cloud revenue was $87.9 billion and increased 17%, driven by Azure and other cloud services.");
  const [judgeModel, setJudgeModel] = useState("mock-gpt-4o");

  const [loading, setLoading] = useState(false);
  const [evalResult, setEvalResult] = useState<any>(null);

  // Human Review state
  const [humanScore, setHumanScore] = useState<number>(0.95);
  const [humanNotes, setHumanNotes] = useState("Verified against certified 10-K filing.");
  const [reviewed, setReviewed] = useState(false);

  const handleRunEvaluation = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setReviewed(false);
    try {
      const res = await api.runEvaluation({
        metric_name: metricName,
        query,
        response,
        expected_output: expectedOutput,
        context,
        judge_model: judgeModel,
      });
      setEvalResult(res);
      setHumanScore(res.score);
    } catch (err: any) {
      alert(err.message || "Failed to execute evaluator.");
    } finally {
      setLoading(false);
    }
  };

  const handleHumanReview = () => {
    if (!evalResult) return;
    setEvalResult({
      ...evalResult,
      score: humanScore,
      is_human_reviewed: true,
      human_notes: humanNotes,
    });
    setReviewed(true);
  };

  return (
    <div className="flex-1 flex flex-col">
      <Header />

      <main className="flex-1 p-8 space-y-8 max-w-7xl mx-auto w-full">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Evaluation Metrics & Testing Playground
          </h1>
          <p className="text-sm text-slate-400">
            Define, customize, and interactively test LLM-as-a-judge and heuristic metrics with human-in-the-loop review.
          </p>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {EVALUATOR_CARDS.map((m) => (
            <div
              key={m.id}
              onClick={() => setMetricName(m.id)}
              className={`p-4 rounded-xl border cursor-pointer transition-all space-y-2.5 ${
                metricName === m.id
                  ? "bg-blue-950/25 border-blue-500 shadow-md shadow-blue-500/10"
                  : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-semibold text-blue-400 px-2 py-0.5 rounded bg-blue-500/10">
                  {m.category}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">Pass: {m.threshold}</span>
              </div>
              <h3 className="font-bold text-sm text-white">{m.title}</h3>
              <p className="text-xs text-slate-400 leading-relaxed">{m.desc}</p>
              <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-500 font-mono">
                Method: {m.formula}
              </div>
            </div>
          ))}
        </div>

        {/* Interactive Evaluation Playground */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <h3 className="font-bold text-base text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-400" />
                Live Evaluator Playground
              </h3>
              <p className="text-xs text-slate-400">
                Test input queries and candidate responses against chosen evaluator metric in real time.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Judge Model:</span>
              <select
                value={judgeModel}
                onChange={(e) => setJudgeModel(e.target.value)}
                className="px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white"
              >
                <option value="mock-gpt-4o">Mock Judge (Deterministic)</option>
                <option value="gpt-4o-mini">OpenAI GPT-4o-mini</option>
                <option value="claude-3-5-haiku-20241022">Claude 3.5 Haiku</option>
              </select>
            </div>
          </div>

          <form onSubmit={handleRunEvaluation} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 block">User Query / Prompt</label>
                <textarea
                  rows={3}
                  required
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 block">Candidate Model Response</label>
                <textarea
                  rows={3}
                  required
                  value={response}
                  onChange={(e) => setResponse(e.target.value)}
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 block">Expected Ground Truth (Optional)</label>
                <textarea
                  rows={3}
                  value={expectedOutput}
                  onChange={(e) => setExpectedOutput(e.target.value)}
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 block">Retrieved Context / Documents (for Faithfulness/RAG)</label>
                <textarea
                  rows={3}
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <div className="text-xs text-slate-400">
                Selected metric: <b className="text-blue-400 uppercase">{metricName}</b>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-sm shadow-blue-500/20 transition-colors"
              >
                <Play className="w-3.5 h-3.5" /> {loading ? "Evaluating..." : "Execute Evaluator"}
              </button>
            </div>
          </form>

          {/* Evaluator Output Display */}
          {evalResult && (
            <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <span className={`text-xl font-bold ${evalResult.passed ? "text-emerald-400" : "text-rose-400"}`}>
                    {formatPercentage(evalResult.score)}
                  </span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase ${
                    evalResult.passed ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
                  }`}>
                    {evalResult.passed ? "PASSED BENCHMARK" : "FAILED BENCHMARK"}
                  </span>
                </div>
                <span className="text-xs text-slate-500 font-mono">
                  Latency: {evalResult.latency_ms} ms
                </span>
              </div>

              <div className="space-y-2">
                <span className="text-xs font-semibold uppercase text-slate-400 tracking-wider">
                  Judge Reasoning & Evidence
                </span>
                <p className="text-xs text-slate-200 bg-slate-900/80 p-3 rounded-lg border border-slate-800 leading-relaxed">
                  {evalResult.reasoning}
                </p>
              </div>

              {evalResult.supported_claims && evalResult.supported_claims.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block">
                    Supported Claims Verified:
                  </span>
                  <ul className="text-xs text-slate-300 space-y-1 list-disc pl-4">
                    {evalResult.supported_claims.map((c: string, idx: number) => (
                      <li key={idx}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}

              {evalResult.unsupported_claims && evalResult.unsupported_claims.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider block">
                    Unsupported / Hallucinated Claims:
                  </span>
                  <ul className="text-xs text-rose-300 space-y-1 list-disc pl-4">
                    {evalResult.unsupported_claims.map((c: string, idx: number) => (
                      <li key={idx}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Human Review Override Section */}
              <div className="mt-4 pt-4 border-t border-slate-800 space-y-3 bg-slate-900/40 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-amber-400 flex items-center gap-1.5">
                    <UserCheck className="w-4 h-4" /> Human-in-the-loop Calibration & Override
                  </span>
                  {reviewed && (
                    <span className="text-xs font-medium text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Human Verified
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="text-[11px] text-slate-400 block mb-1">Override Score (0.0 - 1.0)</label>
                    <input
                      type="number"
                      step="0.05"
                      min="0"
                      max="1"
                      value={humanScore}
                      onChange={(e) => setHumanScore(parseFloat(e.target.value))}
                      className="w-full px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white"
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="text-[11px] text-slate-400 block mb-1">Auditor Annotation / Notes</label>
                    <input
                      type="text"
                      value={humanNotes}
                      onChange={(e) => setHumanNotes(e.target.value)}
                      placeholder="Notes on why score was adjusted..."
                      className="w-full px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white"
                    />
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleHumanReview}
                  className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded text-xs font-semibold transition-colors"
                >
                  Save Human Calibration
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
