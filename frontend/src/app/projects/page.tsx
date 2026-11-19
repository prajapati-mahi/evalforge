"use client";

import React, { useEffect, useState } from "react";
import { FolderGit2, Plus, Trash2, Database, FlaskConical, Activity, Check, X } from "lucide-react";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { Project } from "@/types";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [projectType, setProjectType] = useState("rag");
  const [defaultModel, setDefaultModel] = useState("mock-gpt-4o");

  const loadProjects = () => {
    setLoading(true);
    api.getProjects()
      .then(setProjects)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await api.createProject({
        name,
        description,
        project_type: projectType,
        default_model: defaultModel,
      });
      setIsModalOpen(false);
      setName("");
      setDescription("");
      loadProjects();
    } catch (err: any) {
      alert(err.message || "Failed to create project");
    }
  };

  const handleDelete = async (id: number, pName: string) => {
    if (confirm(`Are you sure you want to delete project "${pName}"? All isolated datasets and experiments will be removed.`)) {
      try {
        await api.deleteProject(id);
        loadProjects();
      } catch (err: any) {
        alert(err.message || "Failed to delete project");
      }
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <Header />

      <main className="flex-1 p-8 space-y-6 max-w-7xl mx-auto w-full">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              Projects & Workspaces
            </h1>
            <p className="text-sm text-slate-400">
              Isolate datasets, evaluations, prompts, and traces across distinct AI applications.
            </p>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm shadow-blue-500/20"
          >
            <Plus className="w-4 h-4" /> New Project
          </button>
        </div>

        {/* Projects Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {projects.map((p) => (
            <div
              key={p.id}
              className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    {p.project_type}
                  </span>
                  <button
                    onClick={() => handleDelete(p.id, p.name)}
                    className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                    title="Delete Project"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <h3 className="font-semibold text-base text-slate-100">{p.name}</h3>
                <p className="text-xs text-slate-400 line-clamp-2">
                  {p.description || "No description provided."}
                </p>
              </div>

              <div className="pt-4 border-t border-slate-800/60 grid grid-cols-3 gap-2 text-center text-xs">
                <div className="p-2 rounded bg-slate-800/40">
                  <span className="block text-slate-400 text-[10px]">Datasets</span>
                  <span className="font-semibold text-slate-200">{p.num_datasets}</span>
                </div>
                <div className="p-2 rounded bg-slate-800/40">
                  <span className="block text-slate-400 text-[10px]">Experiments</span>
                  <span className="font-semibold text-slate-200">{p.num_experiments}</span>
                </div>
                <div className="p-2 rounded bg-slate-800/40">
                  <span className="block text-slate-400 text-[10px]">Traces</span>
                  <span className="font-semibold text-slate-200">{p.num_traces}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Create Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0f172a] border border-slate-800 rounded-xl w-full max-w-lg p-6 space-y-5 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-base font-semibold text-white">Create Evaluation Project</h3>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="text-slate-400 hover:text-slate-200 p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-300">Project Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Customer Support RAG Pipeline"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-300">Description</label>
                  <textarea
                    rows={3}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Describe the application architecture and evaluation goals..."
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-slate-300">Project Type</label>
                    <select
                      value={projectType}
                      onChange={(e) => setProjectType(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="rag">RAG Application</option>
                      <option value="qa">Question Answering</option>
                      <option value="summarization">Summarization</option>
                      <option value="classification">Classification</option>
                      <option value="agentic">Agentic Workflow</option>
                      <option value="general">General LLM</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-medium text-slate-300">Default Model</label>
                    <select
                      value={defaultModel}
                      onChange={(e) => setDefaultModel(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="mock-gpt-4o">mock-gpt-4o</option>
                      <option value="mock-claude-3-5-sonnet">mock-claude-3-5-sonnet</option>
                      <option value="mock-gemini-1.5-pro">mock-gemini-1.5-pro</option>
                      <option value="gpt-4o">OpenAI GPT-4o</option>
                      <option value="gpt-4o-mini">OpenAI GPT-4o-mini</option>
                      <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                      <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white shadow-sm"
                  >
                    Create Project
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
