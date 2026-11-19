"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FolderGit2,
  Database,
  FlaskConical,
  Scale,
  Gauge,
  Activity,
  FileCode2,
  KeyRound,
  Settings,
  Sparkles,
  ShieldCheck
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { label: "Overview", href: "/", icon: LayoutDashboard },
  { label: "Projects", href: "/projects", icon: FolderGit2 },
  { label: "Datasets", href: "/datasets", icon: Database },
  { label: "Experiments", href: "/experiments", icon: FlaskConical },
  { label: "Model Comparison", href: "/comparison", icon: Scale },
  { label: "Evaluation Metrics", href: "/metrics", icon: Gauge },
  { label: "Traces & Spans", href: "/traces", icon: Activity },
  { label: "Prompt Library", href: "/prompts", icon: FileCode2 },
  { label: "Providers & Keys", href: "/providers", icon: KeyRound },
  { label: "Settings & Reports", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-[#0b101b] flex flex-col h-screen select-none shrink-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800/80 gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 via-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
            EvalForge
            <span className="text-[10px] uppercase font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 px-1.5 py-0.5 rounded">
              v1.0
            </span>
          </span>
          <p className="text-[11px] text-slate-400">LLM Benchmarking & Eval</p>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
          Platform Workspace
        </div>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-600/15 text-blue-400 border border-blue-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              )}
            >
              <Icon className={cn("w-4 h-4", isActive ? "text-blue-400" : "text-slate-400")} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Demo Mode & Operational Badge */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/30 space-y-3">
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-2.5 text-xs text-emerald-400">
          <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-400" />
          <div className="leading-tight">
            <span className="font-semibold block">Demo Mode Active</span>
            <span className="text-[11px] text-emerald-400/80">Deterministic mock evaluation</span>
          </div>
        </div>

        <div className="text-[11px] text-slate-400 flex items-center justify-between px-1">
          <span>FastAPI Engine</span>
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Online
          </span>
        </div>
      </div>
    </aside>
  );
}
