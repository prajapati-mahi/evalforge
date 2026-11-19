"use client";

import React, { useEffect, useState } from "react";
import {
  KeyRound,
  CheckCircle2,
  AlertTriangle,
  Play,
  Save,
  Coins,
  ShieldAlert,
  Server,
  ExternalLink
} from "lucide-react";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

interface ProviderKey {
  id: number;
  provider_name: string;
  key_prefix?: string;
  is_active: boolean;
  is_default: boolean;
}

interface ModelPricing {
  id: number;
  provider: string;
  model_name: string;
  input_price_per_1m: number;
  output_price_per_1m: number;
  effective_date: string;
  is_custom: boolean;
}

export default function ProvidersPage() {
  const [keys, setKeys] = useState<ProviderKey[]>([]);
  const [pricing, setPricing] = useState<ModelPricing[]>([]);
  const [activeTab, setActiveTab] = useState<"keys" | "pricing">("keys");

  // Form
  const [providerName, setProviderName] = useState("openai");
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [testResult, setTestResult] = useState<Record<string, any>>({});
  const [testing, setTesting] = useState<string | null>(null);

  const loadData = () => {
    api.getProviders().then(setKeys).catch(console.error);
    api.getPricing().then(setPricing).catch(console.error);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleConfigure = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKeyInput.trim()) return;
    try {
      await api.configureProvider({
        provider_name: providerName,
        api_key: apiKeyInput.trim(),
      });
      setApiKeyInput("");
      loadData();
      alert("Provider credentials saved securely. Keys are never returned in cleartext.");
    } catch (err: any) {
      alert(err.message || "Failed to save provider key");
    }
  };

  const handleTestConnection = async (pName: string) => {
    setTesting(pName);
    try {
      const res = await api.testProvider(pName);
      setTestResult((prev) => ({ ...prev, [pName]: res }));
    } catch (err: any) {
      setTestResult((prev) => ({
        ...prev,
        [pName]: { status: "error", message: err.message || "Connection failed" },
      }));
    } finally {
      setTesting(null);
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <Header />

      <main className="flex-1 p-8 space-y-6 max-w-7xl mx-auto w-full">
        {/* Title */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              Model Providers & Pricing Management
            </h1>
            <p className="text-sm text-slate-400">
              Configure LLM API credentials, verify operational connectivity, and manage token pricing tables.
            </p>
          </div>

          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1 rounded-lg text-xs">
            <button
              onClick={() => setActiveTab("keys")}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === "keys" ? "bg-blue-600 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              API Credentials
            </button>
            <button
              onClick={() => setActiveTab("pricing")}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === "pricing" ? "bg-blue-600 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Pricing Tables (USD/1M)
            </button>
          </div>
        </div>

        {activeTab === "keys" ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Add Key Form */}
            <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-4">
              <h3 className="font-semibold text-sm text-white">Configure Provider Key</h3>
              <p className="text-xs text-slate-400">
                Credentials are encrypted at rest and never returned to the frontend.
              </p>

              <form onSubmit={handleConfigure} className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Provider</label>
                  <select
                    value={providerName}
                    onChange={(e) => setProviderName(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white"
                  >
                    <option value="openai">OpenAI (GPT-4o, GPT-4o-mini)</option>
                    <option value="anthropic">Anthropic (Claude 3.5 Sonnet/Haiku)</option>
                    <option value="gemini">Google Gemini (Gemini 1.5/2.0)</option>
                    <option value="mock">Mock Provider (Built-in Demo)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">API Key</label>
                  <input
                    type="password"
                    required
                    value={apiKeyInput}
                    onChange={(e) => setApiKeyInput(e.target.value)}
                    placeholder="sk-..."
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white font-mono"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-colors"
                >
                  <Save className="w-3.5 h-3.5" /> Save Encrypted Key
                </button>
              </form>
            </div>

            {/* Provider Connection Cards */}
            <div className="lg:col-span-2 space-y-3">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 px-1">
                Supported Provider Adapters
              </div>

              {[
                {
                  id: "mock",
                  name: "Mock Adapter (Deterministic Engine)",
                  desc: "Zero-dependency evaluation engine simulating token consumption, latency, and structured outputs.",
                  status: "operational",
                  requiresKey: false,
                },
                {
                  id: "openai",
                  name: "OpenAI REST & Chat API",
                  desc: "Integration with official GPT-4o, GPT-4o-mini, and text-embedding endpoints.",
                  status: "ready",
                  requiresKey: true,
                },
                {
                  id: "anthropic",
                  name: "Anthropic Messages API",
                  desc: "Integration with Claude 3.5 Sonnet, Claude 3.5 Haiku, and Claude 3 Opus.",
                  status: "ready",
                  requiresKey: true,
                },
                {
                  id: "gemini",
                  name: "Google Gemini REST API",
                  desc: "Integration with Gemini 1.5 Pro, Flash, and 2.0 Flash models.",
                  status: "ready",
                  requiresKey: true,
                },
              ].map((p) => {
                const configured = keys.find((k) => k.provider_name === p.id);
                const test = testResult[p.id];
                return (
                  <div
                    key={p.id}
                    className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-sm text-slate-100">{p.name}</h4>
                          {configured && (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                              Prefix: {configured.key_prefix}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-400">{p.desc}</p>
                      </div>

                      <button
                        onClick={() => handleTestConnection(p.id)}
                        disabled={testing === p.id}
                        className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors border border-slate-700"
                      >
                        <Play className="w-3 h-3 text-blue-400" />
                        {testing === p.id ? "Pinging..." : "Test Ping"}
                      </button>
                    </div>

                    {test && (
                      <div
                        className={`p-2.5 rounded-lg border text-xs font-mono flex items-center gap-2 ${
                          test.status === "connected"
                            ? "bg-emerald-950/20 border-emerald-500/30 text-emerald-300"
                            : "bg-rose-950/20 border-rose-500/30 text-rose-300"
                        }`}
                      >
                        {test.status === "connected" ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        ) : (
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                        )}
                        <span>{test.message || JSON.stringify(test)}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          /* Pricing Table */
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="font-semibold text-base text-white">Configured Model Pricing Tables</h3>
                <p className="text-xs text-slate-400">
                  Versioned USD cost per 1 Million tokens used to calculate execution economics.
                </p>
              </div>
              <span className="text-xs text-slate-400 font-mono">Rates in USD / 1M Tokens</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/50 text-[10px] uppercase font-semibold text-slate-400 border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-4">Provider</th>
                    <th className="py-2.5 px-4">Model Identifier</th>
                    <th className="py-2.5 px-4">Input Price / 1M</th>
                    <th className="py-2.5 px-4">Output Price / 1M</th>
                    <th className="py-2.5 px-4">Effective Date</th>
                    <th className="py-2.5 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {pricing.map((pr) => (
                    <tr key={pr.model_name} className="hover:bg-slate-800/30 font-mono">
                      <td className="py-2.5 px-4 uppercase text-blue-400">{pr.provider}</td>
                      <td className="py-2.5 px-4 font-bold text-white">{pr.model_name}</td>
                      <td className="py-2.5 px-4 text-emerald-400">${pr.input_price_per_1m.toFixed(3)}</td>
                      <td className="py-2.5 px-4 text-purple-400">${pr.output_price_per_1m.toFixed(3)}</td>
                      <td className="py-2.5 px-4 text-slate-400">{pr.effective_date}</td>
                      <td className="py-2.5 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Active
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
