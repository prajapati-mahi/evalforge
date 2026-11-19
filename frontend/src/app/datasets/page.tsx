"use client";

import React, { useEffect, useState } from "react";
import {
  Database,
  Plus,
  Upload,
  Download,
  Trash2,
  FileCheck2,
  AlertCircle,
  Sparkles,
  ChevronRight,
  Eye,
  FileText
} from "lucide-react";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { Dataset, DatasetCase } from "@/types";

export default function DatasetsPage() {
  const [projectId, setProjectId] = useState<number | undefined>();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [cases, setCases] = useState<DatasetCase[]>([]);
  const [loadingCases, setLoadingCases] = useState(false);

  // Upload & Validation state
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadName, setUploadName] = useState("");
  const [uploadDesc, setUploadDesc] = useState("");
  const [validationResult, setValidationResult] = useState<any>(null);
  const [validating, setValidating] = useState(false);

  // New Case Modal
  const [isCaseModalOpen, setIsCaseModalOpen] = useState(false);
  const [caseInput, setCaseInput] = useState("");
  const [caseExpected, setCaseExpected] = useState("");
  const [caseContext, setCaseContext] = useState("");

  const loadDatasets = () => {
    api.getDatasets(projectId).then((data) => {
      setDatasets(data);
      if (data.length > 0 && !selectedDataset) {
        setSelectedDataset(data[0]);
      }
    }).catch(console.error);
  };

  useEffect(() => {
    loadDatasets();
  }, [projectId]);

  useEffect(() => {
    if (selectedDataset) {
      setLoadingCases(true);
      api.getDatasetCases(selectedDataset.id)
        .then(setCases)
        .catch(console.error)
        .finally(() => setLoadingCases(false));
    } else {
      setCases([]);
    }
  }, [selectedDataset]);

  const handleSeedSample = async () => {
    if (!projectId) return alert("Select an active project first.");
    try {
      const res = await api.seedSampleDataset(projectId);
      loadDatasets();
      setSelectedDataset(res);
    } catch (err: any) {
      alert(err.message || "Failed to seed sample dataset.");
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadFile(file);
    if (!uploadName) {
      setUploadName(file.name.replace(/\.[^/.]+$/, ""));
    }

    // Live validation
    setValidating(true);
    try {
      const val = await api.validateDatasetUpload(file);
      setValidationResult(val);
    } catch (err: any) {
      console.error(err);
    } finally {
      setValidating(false);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !projectId) return;
    try {
      const res = await api.uploadDataset(projectId, uploadName, uploadDesc, uploadFile);
      setIsUploadModalOpen(false);
      setUploadFile(null);
      setValidationResult(null);
      setUploadName("");
      setUploadDesc("");
      loadDatasets();
      setSelectedDataset(res);
    } catch (err: any) {
      alert(err.message || "Failed to upload dataset");
    }
  };

  const handleAddCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDataset || !caseInput.trim()) return;
    try {
      await api.addDatasetCase(selectedDataset.id, {
        input_text: caseInput,
        expected_output: caseExpected,
        context: caseContext,
      });
      setIsCaseModalOpen(false);
      setCaseInput("");
      setCaseExpected("");
      setCaseContext("");
      // reload cases
      const updatedCases = await api.getDatasetCases(selectedDataset.id);
      setCases(updatedCases);
      loadDatasets();
    } catch (err: any) {
      alert(err.message || "Failed to add case");
    }
  };

  const handleDeleteCase = async (caseId: number) => {
    if (confirm("Delete this test case?")) {
      try {
        await api.deleteDatasetCase(caseId);
        if (selectedDataset) {
          const updated = await api.getDatasetCases(selectedDataset.id);
          setCases(updated);
        }
      } catch (err: any) {
        alert(err.message || "Failed to delete case");
      }
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <Header activeProjectId={projectId} onProjectChange={setProjectId} />

      <main className="flex-1 p-8 space-y-6 max-w-7xl mx-auto w-full">
        {/* Title & Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              Dataset Management & Schemas
            </h1>
            <p className="text-sm text-slate-400">
              Curate, validate, and manage ground-truth test sets with context passages for RAG evaluation.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSeedSample}
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center gap-2 border border-slate-700/60 transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              Load Sample Benchmark
            </button>
            <button
              onClick={() => setIsUploadModalOpen(true)}
              className="px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm shadow-blue-500/20"
            >
              <Upload className="w-3.5 h-3.5" />
              Upload CSV / JSONL
            </button>
          </div>
        </div>

        {/* Dataset Workspace Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Datasets List */}
          <div className="space-y-3">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
              Available Datasets ({datasets.length})
            </div>
            <div className="space-y-2">
              {datasets.map((d) => (
                <div
                  key={d.id}
                  onClick={() => setSelectedDataset(d)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    selectedDataset?.id === d.id
                      ? "bg-blue-950/20 border-blue-500/50 shadow-md shadow-blue-500/5"
                      : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                        {d.file_format.toUpperCase()} • v{d.version}
                      </span>
                      <h4 className="font-semibold text-sm text-slate-100">{d.name}</h4>
                      <p className="text-xs text-slate-400 line-clamp-2">{d.description}</p>
                    </div>
                    <ChevronRight className={`w-4 h-4 shrink-0 transition-transform ${selectedDataset?.id === d.id ? "rotate-90 text-blue-400" : "text-slate-600"}`} />
                  </div>
                  <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
                    <span>{d.num_cases} test cases</span>
                    <span>{new Date(d.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Test Cases Viewer & Editor */}
          <div className="lg:col-span-2 space-y-4">
            {selectedDataset ? (
              <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-800">
                  <div>
                    <h3 className="font-semibold text-base text-white">{selectedDataset.name}</h3>
                    <p className="text-xs text-slate-400">Inspection of individual query, expected output, and context.</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <a
                      href={`http://127.0.0.1:8000/api/v1/datasets/${selectedDataset.id}/download`}
                      download
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" /> Export JSONL
                    </a>
                    <button
                      onClick={() => setIsCaseModalOpen(true)}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors"
                    >
                      <Plus className="w-3.5 h-3.5" /> Add Case
                    </button>
                  </div>
                </div>

                {/* Cases Table */}
                <div className="space-y-3 overflow-y-auto max-h-[620px] pr-1">
                  {cases.map((c, idx) => (
                    <div key={c.id} className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-blue-400">Case #{idx + 1}</span>
                        <button
                          onClick={() => handleDeleteCase(c.id)}
                          className="text-slate-500 hover:text-rose-400 p-1 transition-colors"
                          title="Delete Case"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <div className="space-y-1.5">
                        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Input Query</span>
                        <p className="text-xs text-slate-100 bg-slate-900/60 p-2.5 rounded border border-slate-800/80 font-mono">
                          {c.input_text}
                        </p>
                      </div>

                      {c.expected_output && (
                        <div className="space-y-1.5">
                          <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider block">Expected Output</span>
                          <p className="text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded border border-slate-800/80">
                            {c.expected_output}
                          </p>
                        </div>
                      )}

                      {c.context && (
                        <div className="space-y-1.5">
                          <span className="text-[10px] font-semibold text-cyan-400 uppercase tracking-wider block">Retrieved Context / Passage</span>
                          <p className="text-xs text-slate-400 bg-slate-900/60 p-2.5 rounded border border-slate-800/80 line-clamp-3">
                            {c.context}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                  {cases.length === 0 && (
                    <div className="text-center py-12 text-slate-500 text-xs">
                      No test cases in this dataset yet. Click &quot;Add Case&quot; or upload files.
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
                Select a dataset from the list to view and manage cases.
              </div>
            )}
          </div>
        </div>

        {/* Upload Modal with Live Schema Validation */}
        {isUploadModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0f172a] border border-slate-800 rounded-xl w-full max-w-xl p-6 space-y-5 shadow-2xl max-h-[90vh] overflow-y-auto">
              <h3 className="text-base font-semibold text-white">Upload Dataset & Schema Validator</h3>

              <form onSubmit={handleUploadSubmit} className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Dataset Name</label>
                  <input
                    type="text"
                    required
                    value={uploadName}
                    onChange={(e) => setUploadName(e.target.value)}
                    placeholder="e.g. Production RAG Benchmark"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Description</label>
                  <textarea
                    rows={2}
                    value={uploadDesc}
                    onChange={(e) => setUploadDesc(e.target.value)}
                    placeholder="Optional description..."
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Upload CSV or JSONL File</label>
                  <input
                    type="file"
                    accept=".jsonl,.csv,.json"
                    required
                    onChange={handleFileChange}
                    className="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer"
                  />
                  <p className="text-[11px] text-slate-500 mt-1">
                    Accepts records with <code>input</code>, <code>expected_output</code>, and optional <code>context</code> fields.
                  </p>
                </div>

                {/* Validation Feedback */}
                {validationResult && (
                  <div className={`p-4 rounded-lg border space-y-2 text-xs ${
                    validationResult.is_valid
                      ? "bg-emerald-950/20 border-emerald-500/30 text-emerald-300"
                      : "bg-rose-950/20 border-rose-500/30 text-rose-300"
                  }`}>
                    <div className="flex items-center gap-2 font-semibold">
                      {validationResult.is_valid ? (
                        <>
                          <FileCheck2 className="w-4 h-4 text-emerald-400" />
                          Schema Validation Passed: {validationResult.valid_rows} valid rows
                        </>
                      ) : (
                        <>
                          <AlertCircle className="w-4 h-4 text-rose-400" />
                          Validation Failed: {validationResult.invalid_rows} errors detected
                        </>
                      )}
                    </div>

                    {validationResult.errors.length > 0 && (
                      <div className="space-y-1 max-h-32 overflow-y-auto pt-1 font-mono text-[11px]">
                        {validationResult.errors.map((err: any, idx: number) => (
                          <div key={idx} className="text-rose-400">
                            • Row {err.row_index} [{err.field}]: {err.error}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Preview Table */}
                    {validationResult.preview.length > 0 && (
                      <div className="pt-2 border-t border-slate-800">
                        <span className="text-[10px] uppercase font-semibold text-slate-400 block mb-1">Parsed Sample Rows</span>
                        <div className="space-y-1">
                          {validationResult.preview.slice(0, 2).map((p: any, i: number) => (
                            <div key={i} className="bg-slate-900/60 p-2 rounded text-slate-300 font-mono text-[11px]">
                              Q: {p.input}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsUploadModalOpen(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 text-xs text-slate-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!validationResult?.is_valid}
                    className="px-4 py-2 rounded-lg bg-blue-600 disabled:opacity-50 text-xs font-semibold text-white shadow-sm"
                  >
                    Confirm & Save Dataset
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Add Case Modal */}
        {isCaseModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0f172a] border border-slate-800 rounded-xl w-full max-w-lg p-6 space-y-4 shadow-2xl">
              <h3 className="text-base font-semibold text-white">Add Benchmark Test Case</h3>

              <form onSubmit={handleAddCase} className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Input Question / Prompt</label>
                  <textarea
                    rows={3}
                    required
                    value={caseInput}
                    onChange={(e) => setCaseInput(e.target.value)}
                    placeholder="Enter the query to test..."
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Expected Ground Truth Answer</label>
                  <textarea
                    rows={2}
                    value={caseExpected}
                    onChange={(e) => setCaseExpected(e.target.value)}
                    placeholder="Expected factual answer..."
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Retrieved Context (for RAG)</label>
                  <textarea
                    rows={3}
                    value={caseContext}
                    onChange={(e) => setCaseContext(e.target.value)}
                    placeholder="Context passages retrieved from vector DB or documentation..."
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsCaseModalOpen(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 text-xs text-slate-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-blue-600 text-xs font-semibold text-white shadow-sm"
                  >
                    Save Case
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
