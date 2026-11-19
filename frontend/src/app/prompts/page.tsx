"use client";

import React, { useEffect, useState } from "react";
import {
  FileCode2,
  Plus,
  Play,
  History,
  CheckCircle2,
  Sparkles,
  GitCommit,
  Clock,
  Coins,
  ChevronRight,
  X
} from "lucide-react";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { Prompt, PromptVersion } from "@/types";
import { formatCurrency, formatLatency } from "@/lib/utils";

export default function PromptsPage() {
  const [projectId, setProjectId] = useState<number | undefined>();
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null);
  const [versions, setVersions] = useState<PromptVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<PromptVersion | null>(null);

  // New Prompt Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [template, setTemplate] = useState("Context:\n{{context}}\n\nQuestion:\n{{input}}\n\nAnswer:");
  const [systemInstruction, setSystemInstruction] = useState("You are an accurate AI assistant.");

  // New Version Modal
  const [isVersionModalOpen, setIsVersionModalOpen] = useState(false);
  const [vTemplate, setVTemplate] = useState("");
  const [vSystem, setVSystem] = useState("");
  const [changeSummary, setChangeSummary] = useState("");

  // Test Playground
  const [testVariables, setTestVariables] = useState<Record<string, string>>({
    context: "Retrieval-Augmented Generation (RAG) grounds LLM outputs in verified facts.",
    input: "What is RAG?"
  });
  const [testModel, setTestModel] = useState("mock-gpt-4o");
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const loadPrompts = () => {
    if (!projectId) return;
    api.getPrompts(projectId).then((data) => {
      setPrompts(data);
      if (data.length > 0 && !selectedPrompt) {
        setSelectedPrompt(data[0]);
      }
    }).catch(console.error);
  };

  useEffect(() => {
    loadPrompts();
  }, [projectId]);

  useEffect(() => {
    if (selectedPrompt) {
      api.getPromptVersions(selectedPrompt.id).then((vData) => {
        setVersions(vData);
        if (vData.length > 0) {
          setSelectedVersion(vData[0]);
          setVTemplate(vData[0].template_text);
          setVSystem(vData[0].system_instruction || "");
        }
      }).catch(console.error);
    }
  }, [selectedPrompt]);

  const handleCreatePrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId || !name.trim()) return;
    try {
      const p = await api.createPrompt({
        project_id: projectId,
        name,
        description,
        initial_template: template,
        system_instruction: systemInstruction
      });
      setIsModalOpen(false);
      setName("");
      setDescription("");
      loadPrompts();
      setSelectedPrompt(p);
    } catch (err: any) {
      alert(err.message || "Failed to create prompt");
    }
  };

  const handleCreateVersion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPrompt || !vTemplate.trim()) return;
    try {
      const nv = await api.createPromptVersion(selectedPrompt.id, {
        template_text: vTemplate,
        system_instruction: vSystem,
        change_summary: changeSummary
      });
      setIsVersionModalOpen(false);
      setChangeSummary("");
      // reload versions
      const vData = await api.getPromptVersions(selectedPrompt.id);
      setVersions(vData);
      setSelectedVersion(nv);
      loadPrompts();
    } catch (err: any) {
      alert(err.message || "Failed to save version");
    }
  };

  const handleTestPrompt = async () => {
    if (!selectedVersion) return;
    setTesting(true);
    try {
      const res = await api.testPrompt({
        template_text: selectedVersion.template_text,
        system_instruction: selectedVersion.system_instruction,
        variables: testVariables,
        model_name: testModel
      });
      setTestResult(res);
    } catch (err: any) {
      alert(err.message || "Prompt test failed");
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <Header activeProjectId={projectId} onProjectChange={setProjectId} />

      <main className="flex-1 p-8 space-y-6 max-w-7xl mx-auto w-full">
        {/* Title */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              Prompt Library & Version Governance
            </h1>
            <p className="text-sm text-slate-400">
              Manage prompt templates with immutable version history, variables detection, and live testing.
            </p>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-sm shadow-blue-500/20"
          >
            <Plus className="w-4 h-4" /> New Prompt
          </button>
        </div>

        {/* Prompts Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Prompts List */}
          <div className="space-y-3">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
              Prompt Templates ({prompts.length})
            </div>
            <div className="space-y-2">
              {prompts.map((p) => {
                const isSelected = selectedPrompt?.id === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => setSelectedPrompt(p)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all space-y-2 ${
                      isSelected
                        ? "bg-blue-950/20 border-blue-500/50 shadow-md shadow-blue-500/5"
                        : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="space-y-0.5">
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-blue-400">
                          v{p.current_version}
                        </span>
                        <h4 className="font-semibold text-sm text-slate-100">{p.name}</h4>
                        <p className="text-xs text-slate-400 line-clamp-1">{p.description}</p>
                      </div>
                      <ChevronRight
                        className={`w-4 h-4 shrink-0 transition-transform ${
                          isSelected ? "rotate-90 text-blue-400" : "text-slate-600"
                        }`}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Prompt Version Detail & Test Playground */}
          <div className="lg:col-span-2 space-y-4">
            {selectedPrompt && selectedVersion ? (
              <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-lg text-white">{selectedPrompt.name}</h3>
                      <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 text-xs font-mono font-semibold">
                        ACTIVE v{selectedVersion.version_number}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">{selectedPrompt.description}</p>
                  </div>

                  <button
                    onClick={() => {
                      setVTemplate(selectedVersion.template_text);
                      setVSystem(selectedVersion.system_instruction || "");
                      setIsVersionModalOpen(true);
                    }}
                    className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors"
                  >
                    <GitCommit className="w-3.5 h-3.5 text-blue-400" /> Commit New Version
                  </button>
                </div>

                {/* Versions History Strip */}
                <div className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Version History
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {versions.map((v) => (
                      <button
                        key={v.id}
                        onClick={() => setSelectedVersion(v)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors flex items-center gap-2 ${
                          selectedVersion.id === v.id
                            ? "bg-blue-600 text-white font-semibold"
                            : "bg-slate-800 text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        v{v.version_number}: {v.change_summary || "Revision"}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Template Inspector */}
                <div className="space-y-3">
                  <div className="space-y-1">
                    <span className="text-[10px] font-semibold uppercase text-slate-400 tracking-wider">
                      System Instructions
                    </span>
                    <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg text-xs text-slate-300 font-mono">
                      {selectedVersion.system_instruction || "No system instruction specified."}
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-semibold uppercase text-slate-400 tracking-wider">
                        Template Text
                      </span>
                      <div className="flex items-center gap-1 text-[11px] text-slate-500">
                        Variables detected:{" "}
                        {selectedVersion.variables.map((vr) => (
                          <span key={vr} className="px-1.5 py-0.2 bg-slate-800 text-blue-400 rounded font-mono">
                            {`{{${vr}}}`}
                          </span>
                        ))}
                      </div>
                    </div>
                    <pre className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg text-xs text-slate-200 font-mono whitespace-pre-wrap leading-relaxed">
                      {selectedVersion.template_text}
                    </pre>
                  </div>
                </div>

                {/* Live Prompt Test Playground */}
                <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-xs text-white uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-blue-400" /> Test Prompt with Variables
                    </h4>
                    <select
                      value={testModel}
                      onChange={(e) => setTestModel(e.target.value)}
                      className="px-2.5 py-1 bg-slate-800 border border-slate-700 rounded text-xs text-white font-mono"
                    >
                      <option value="mock-gpt-4o">mock-gpt-4o</option>
                      <option value="mock-claude-3-5-sonnet">mock-claude-3-5-sonnet</option>
                      <option value="gpt-4o-mini">gpt-4o-mini</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {selectedVersion.variables.map((vr) => (
                      <div key={vr} className="space-y-1">
                        <label className="text-[10px] font-mono text-blue-400 block">{`{{${vr}}}`}</label>
                        <input
                          type="text"
                          value={testVariables[vr] || ""}
                          onChange={(e) =>
                            setTestVariables({ ...testVariables, [vr]: e.target.value })
                          }
                          placeholder={`Value for ${vr}...`}
                          className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white"
                        />
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <button
                      onClick={handleTestPrompt}
                      disabled={testing}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
                    >
                      <Play className="w-3.5 h-3.5" /> {testing ? "Running Test..." : "Execute Test"}
                    </button>

                    {testResult && (
                      <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
                        <span>Latency: {formatLatency(testResult.latency_ms)}</span>
                        <span>Tokens: {testResult.total_tokens || (testResult.input_tokens + testResult.output_tokens)}</span>
                        <span>Cost: {formatCurrency(testResult.cost_estimate)}</span>
                      </div>
                    )}
                  </div>

                  {testResult && (
                    <div className="space-y-2 pt-2 border-t border-slate-800">
                      <span className="text-[10px] font-semibold uppercase text-slate-400 tracking-wider block">
                        Model Output Response:
                      </span>
                      <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-xs text-slate-200 font-mono whitespace-pre-wrap">
                        {testResult.response_text}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
                Select a prompt from the left pane to view versions and execute tests.
              </div>
            )}
          </div>
        </div>

        {/* Create Prompt Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0f172a] border border-slate-800 rounded-xl w-full max-w-lg p-6 space-y-4 shadow-2xl">
              <h3 className="text-base font-semibold text-white">Create Prompt Template</h3>

              <form onSubmit={handleCreatePrompt} className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Prompt Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. RAG Extraction Synthesizer"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Description</label>
                  <input
                    type="text"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Purpose of this prompt..."
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">System Instruction</label>
                  <input
                    type="text"
                    value={systemInstruction}
                    onChange={(e) => setSystemInstruction(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white font-mono"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    Template Text (Use <code>{`{{var}}`}</code> for variables)
                  </label>
                  <textarea
                    rows={4}
                    required
                    value={template}
                    onChange={(e) => setTemplate(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white font-mono"
                  />
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
                    Create Prompt
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Commit New Version Modal */}
        {isVersionModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0f172a] border border-slate-800 rounded-xl w-full max-w-lg p-6 space-y-4 shadow-2xl">
              <h3 className="text-base font-semibold text-white">Commit New Prompt Version</h3>

              <form onSubmit={handleCreateVersion} className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Change Summary</label>
                  <input
                    type="text"
                    required
                    value={changeSummary}
                    onChange={(e) => setChangeSummary(e.target.value)}
                    placeholder="e.g. Added strict negative constraints against hallucination"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">System Instruction</label>
                  <input
                    type="text"
                    value={vSystem}
                    onChange={(e) => setVSystem(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white font-mono"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Template Text</label>
                  <textarea
                    rows={4}
                    required
                    value={vTemplate}
                    onChange={(e) => setVTemplate(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white font-mono"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsVersionModalOpen(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 text-xs text-slate-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-blue-600 text-xs font-semibold text-white shadow-sm"
                  >
                    Commit Version
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
