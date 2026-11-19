"use client";

import React, { useEffect, useState } from "react";
import { FolderGit2, CheckCircle2, User as UserIcon, Plus } from "lucide-react";
import { api } from "@/lib/api";
import { Project } from "@/types";

export function Header({
  activeProjectId,
  onProjectChange,
}: {
  activeProjectId?: number;
  onProjectChange?: (id: number) => void;
}) {
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    api.getProjects().then((data) => {
      setProjects(data);
      if (data.length > 0 && !activeProjectId && onProjectChange) {
        onProjectChange(data[0].id);
      }
    }).catch(() => {});
  }, []);

  return (
    <header className="h-16 border-b border-slate-800/80 bg-[#090d16]/90 backdrop-blur px-8 flex items-center justify-between z-10 sticky top-0">
      {/* Project Selector */}
      <div className="flex items-center gap-3">
        <span className="text-xs font-medium text-slate-400">Active Scope:</span>
        <div className="relative flex items-center">
          <FolderGit2 className="w-4 h-4 text-blue-400 absolute left-3 pointer-events-none" />
          <select
            value={activeProjectId || ""}
            onChange={(e) => onProjectChange?.(Number(e.target.value))}
            className="pl-9 pr-8 py-1.5 bg-slate-900 border border-slate-700/80 rounded-md text-xs font-medium text-slate-200 focus:outline-none focus:border-blue-500 appearance-none cursor-pointer hover:bg-slate-800/70 transition-colors"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.project_type.toUpperCase()})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1 bg-slate-900/80 border border-slate-800 rounded-full text-xs text-slate-300">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>Celery & Evaluators Ready</span>
        </div>

        <div className="flex items-center gap-2.5 pl-3 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 font-semibold text-xs">
            AR
          </div>
          <div className="text-left hidden sm:block">
            <span className="text-xs font-medium text-slate-200 block leading-tight">Alex Rivera</span>
            <span className="text-[10px] text-slate-500">Lead AI Engineer</span>
          </div>
        </div>
      </div>
    </header>
  );
}
