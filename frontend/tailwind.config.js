/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "#1e293b",
        background: "#090d16",
        foreground: "#f8fafc",
        card: "#0f172a",
        "card-foreground": "#f8fafc",
        primary: {
          DEFAULT: "#3b82f6",
          foreground: "#ffffff",
          dark: "#1d4ed8"
        },
        secondary: {
          DEFAULT: "#1e293b",
          foreground: "#94a3b8"
        },
        accent: {
          DEFAULT: "#06b6d4",
          foreground: "#ffffff"
        },
        success: {
          DEFAULT: "#10b981",
          foreground: "#ffffff"
        },
        warning: {
          DEFAULT: "#f59e0b",
          foreground: "#ffffff"
        },
        destructive: {
          DEFAULT: "#ef4444",
          foreground: "#ffffff"
        },
        muted: {
          DEFAULT: "#1e293b",
          foreground: "#64748b"
        }
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"]
      }
    },
  },
  plugins: [],
}
