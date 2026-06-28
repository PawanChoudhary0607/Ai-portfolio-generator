/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "rgb(var(--color-ink-900) / <alpha-value>)",
          700: "rgb(var(--color-ink-700) / <alpha-value>)",
          500: "rgb(var(--color-ink-500) / <alpha-value>)",
          300: "rgb(var(--color-ink-300) / <alpha-value>)",
          200: "rgb(var(--color-ink-200) / <alpha-value>)",
          100: "rgb(var(--color-ink-100) / <alpha-value>)",
        },
        surface: {
          DEFAULT: "rgb(var(--color-surface) / <alpha-value>)",
          subtle: "rgb(var(--color-surface-subtle) / <alpha-value>)",
        },
        accent: {
          50: "rgb(var(--color-accent-50) / <alpha-value>)",
          100: "rgb(var(--color-accent-100) / <alpha-value>)",
          400: "rgb(var(--color-accent-400) / <alpha-value>)",
          500: "rgb(var(--color-accent-500) / <alpha-value>)",
          600: "rgb(var(--color-accent-600) / <alpha-value>)",
          700: "rgb(var(--color-accent-700) / <alpha-value>)",
        },
        success: "rgb(var(--color-success) / <alpha-value>)",
        warning: "rgb(var(--color-warning) / <alpha-value>)",
        danger: "rgb(var(--color-danger) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(0 0 0 / 0.04), 0 1px 1px 0 rgb(0 0 0 / 0.03)",
        popover: "0 4px 16px -2px rgb(0 0 0 / 0.10), 0 2px 6px -1px rgb(0 0 0 / 0.06)",
        lift: "0 12px 32px -8px rgb(24 24 27 / 0.12), 0 2px 8px -2px rgb(24 24 27 / 0.06)",
      },
      borderRadius: {
        md: "8px",
        lg: "10px",
        xl: "16px",
        "2xl": "20px",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.45" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s ease-out both",
        "pulse-soft": "pulse-soft 1.6s ease-in-out infinite",
        shimmer: "shimmer 1.4s linear infinite",
      },
    },
  },
  plugins: [],
};
