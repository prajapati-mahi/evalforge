import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(val: number): string {
  if (val >= 1_000_000) {
    return (val / 1_000_000).toFixed(1) + "M";
  }
  if (val >= 1_000) {
    return (val / 1_000).toFixed(1) + "k";
  }
  return val.toLocaleString();
}

export function formatCurrency(amount: number): string {
  if (amount === 0) return "$0.00";
  if (amount < 0.01) {
    return `$${amount.toFixed(4)}`;
  }
  return `$${amount.toFixed(2)}`;
}

export function formatPercentage(val: number): string {
  return `${(val * 100).toFixed(1)}%`;
}

export function formatLatency(ms: number): string {
  if (ms < 1000) {
    return `${Math.round(ms)} ms`;
  }
  return `${(ms / 1000).toFixed(2)} s`;
}
