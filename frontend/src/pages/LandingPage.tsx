import { Link } from "react-router-dom";
import { PublicNav } from "@/components/PublicNav";
import { PublicFooter } from "@/components/PublicFooter";
import { Button } from "@/components/Button";
import { ThemePreview } from "@/components/ThemePreview";
import { PipelineStrip, type PipelineStage } from "@/components/PipelineStrip";
import { EmptyState } from "@/components/EmptyState";

const STAGES: PipelineStage[] = [
  { label: "Uploading resume", detail: "Your PDF is received and queued for processing." },
  { label: "Extracting text", detail: "PyMuPDF pulls structured text from every page of the PDF." },
  { label: "AI analysis", detail: "A local Qwen3 model reads your experience and identifies your strengths." },
  { label: "Generating portfolio", detail: "Hero, about, skills, and project sections are written and structured." },
  { label: "Building website", detail: "Content is rendered into your chosen theme as a static site." },
  { label: "Done", detail: "Your portfolio is ready to preview, switch themes on, and export." },
];

const THEMES = [
  { value: "minimal-white-orange", label: "Minimal", description: "Clean white layout with orange accents and generous whitespace." },
  { value: "executive-black-gold", label: "Executive", description: "Black-and-gold layout for senior, leadership-oriented profiles." },
  { value: "developer-dark", label: "Developer", description: "Dark, monospace-forward layout suited to engineering portfolios." },
  { value: "creative-portfolio", label: "Creative", description: "Expressive layout with bolder type and imagery for creative work." },
  { value: "modern-saas", label: "Modern SaaS", description: "Product-style layout modeled on modern SaaS marketing sites." },
];

const FEATURES = [
  {
    title: "Runs on a local AI engine",
    body: "Your resume is analyzed by a local LLM, not a third-party API — your data stays on the server you control.",
  },
  {
    title: "Five distinct themes",
    body: "Each theme is a genuinely different layout, not a palette swap — pick the one that fits how you want to be seen.",
  },
  {
    title: "Built-in accessibility",
    body: "Generated sites ship with sensible contrast, keyboard navigation, and mobile-friendly layouts by default.",
  },
  {
    title: "Always free to generate",
    body: "Uploading, analyzing, and generating your portfolio costs nothing. Supporting development is optional.",
  },
];

const FAQS = [
  {
    q: "Is my resume data private?",
    a: "Your resume is processed by a local AI engine rather than a third-party AI API, so its contents aren't sent off to an external service to generate your portfolio.",
  },
  {
    q: "Is this really free?",
    a: "Yes. Uploading a resume and generating a portfolio is free, full stop. There's an optional Support page if you'd like to help fund development — it's never required.",
  },
  {
    q: "What file formats are supported?",
    a: "PDF resumes only, for now. Scanned or image-only PDFs aren't supported yet since there's no text to extract.",
  },
  {
    q: "Can I change the theme after generating?",
    a: "Theme switching is on its way — today, the AI analysis and content generation steps are ready, and theme selection ships next.",
  },
];

export function LandingPage() {
  return (
    <div className="bg-white">
      <PublicNav />

      {/* Hero */}
      <section className="relative overflow-hidden border-b border-ink-200 bg-white">
        <div className="mx-auto grid max-w-6xl items-center gap-16 px-6 py-20 md:grid-cols-[1.1fr_1fr] md:py-28">
          <div className="animate-fade-up">
            <span className="eyebrow inline-flex items-center gap-2 rounded-full border border-ink-200 px-3 py-1 text-ink-500">
              <span className="h-1.5 w-1.5 rounded-full bg-accent-600" />
              Resume → Portfolio, automatically
            </span>
            <h1 className="mt-5 text-4xl font-semibold leading-[1.08] tracking-tight text-ink-900 md:text-[3.25rem]">
              Your resume already has the story. We give it a website.
            </h1>
            <p className="mt-5 max-w-md text-base leading-relaxed text-ink-500">
              Upload your PDF. A local AI reads your experience, writes your sections, and builds a
              site — no design work, no copywriting, no template wrangling.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link to="/signup">
                <Button size="md" className="h-11 px-5 text-base">
                  Upload your resume
                </Button>
              </Link>
              <a href="#how-it-works">
                <Button variant="secondary" size="md" className="h-11 px-5 text-base">
                  See how it works
                </Button>
              </a>
            </div>
            <p className="mt-4 text-xs text-ink-500">No credit card. No paywall. Ever.</p>
          </div>

          {/* Signature visual: a real generated site, not a mockup */}
          <div className="relative animate-fade-up [animation-delay:120ms]">
            <div className="overflow-hidden rounded-xl border border-ink-200 shadow-lift">
              <div className="flex items-center gap-1.5 border-b border-ink-200 bg-surface px-3 py-2">
                <span className="h-2 w-2 rounded-full bg-ink-200" />
                <span className="h-2 w-2 rounded-full bg-ink-200" />
                <span className="h-2 w-2 rounded-full bg-ink-200" />
                <span className="eyebrow ml-2 text-ink-500">yourname.dev</span>
              </div>
              <ThemePreview theme="minimal-white-orange" label="Minimal" className="h-72 rounded-none border-0 md:h-80" />
            </div>
            <p className="eyebrow mt-3 text-ink-500">
              Real output — Minimal theme, generated from a sample resume
            </p>
          </div>
        </div>
      </section>

      {/* Animated workflow — the one signature motion moment on this page */}
      <section id="how-it-works" className="border-b border-ink-200 py-20">
        <div className="mx-auto max-w-6xl px-6">
          <p className="eyebrow text-accent-600">How it works</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink-900 md:text-3xl">
            One pipeline. Six steps. Nothing left for you to design.
          </h2>
          <p className="mt-3 max-w-xl text-sm leading-relaxed text-ink-500">
            This is the same sequence that runs for every resume you upload — watch it move below.
          </p>

          <div className="mt-12">
            <PipelineStrip stages={STAGES} />
          </div>

          {/* Full sequence for screen readers and anyone who'd rather not wait for the animation */}
          <ul className="sr-only">
            {STAGES.map((stage) => (
              <li key={stage.label}>
                {stage.label}: {stage.detail}
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Themes — real generated examples, not mockups */}
      <section id="themes" className="border-b border-ink-200 bg-surface py-20">
        <div className="mx-auto max-w-6xl px-6">
          <p className="eyebrow text-accent-600">Themes</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink-900 md:text-3xl">
            Five layouts, not five color swaps.
          </h2>
          <p className="mt-3 max-w-xl text-sm leading-relaxed text-ink-500">
            Every theme restructures the page, not just the palette. These are real pages generated
            by the engine from a sample resume — not illustrations.
          </p>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
            {THEMES.map((theme) => (
              <a
                key={theme.value}
                href={`/theme-previews/${theme.value}.png`}
                target="_blank"
                rel="noopener noreferrer"
                className="group rounded-xl border border-ink-200 bg-white p-3 transition-colors hover:border-ink-300"
              >
                <ThemePreview theme={theme.value} label={theme.label} className="h-32 transition-opacity group-hover:opacity-90" />
                <p className="mt-3 text-sm font-semibold text-ink-900">{theme.label}</p>
                <p className="mt-1 text-xs leading-relaxed text-ink-500">{theme.description}</p>
                <span className="eyebrow mt-2 inline-block text-accent-600 group-hover:text-accent-700">
                  View full example ↗
                </span>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-b border-ink-200 py-20">
        <div className="mx-auto max-w-6xl px-6">
          <p className="eyebrow text-accent-600">Features</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink-900 md:text-3xl">
            Built like production software, not a demo.
          </h2>
          <div className="mt-10 divide-y divide-ink-200 border-t border-ink-200">
            {FEATURES.map((f) => (
              <div key={f.title} className="grid gap-2 py-6 sm:grid-cols-[1fr_2fr] sm:gap-8">
                <h3 className="text-base font-semibold text-ink-900">{f.title}</h3>
                <p className="text-sm leading-relaxed text-ink-500">{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials are intentionally omitted until real customer quotes exist. */}
      <section className="border-b border-ink-200 bg-surface py-20">
        <div className="mx-auto max-w-6xl px-6">
          <p className="eyebrow text-accent-600">From the people who use it</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink-900 md:text-3xl">
            Your story could be the first one here.
          </h2>
          <div className="mt-8 rounded-xl border border-dashed border-ink-300 bg-white">
            <EmptyState
              title="No stories yet — be among the first to try Portfolio AI"
              description="Generate your portfolio, then tell us how it went. We'll feature real feedback here as it comes in."
              action={
                <Link to="/signup">
                  <Button variant="secondary" size="sm">
                    Try it now
                  </Button>
                </Link>
              }
            />
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="border-b border-ink-200 py-20">
        <div className="mx-auto max-w-3xl px-6">
          <p className="eyebrow text-accent-600">FAQ</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink-900 md:text-3xl">
            Questions you might have
          </h2>
          <div className="mt-8 divide-y divide-ink-200">
            {FAQS.map((item) => (
              <details key={item.q} className="group py-5">
                <summary className="flex cursor-pointer list-none items-center justify-between text-sm font-medium text-ink-900">
                  {item.q}
                  <span className="ml-4 flex-shrink-0 font-mono text-ink-500 transition-transform group-open:rotate-45">
                    +
                  </span>
                </summary>
                <p className="mt-3 text-sm leading-relaxed text-ink-500">{item.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Support development — teaser; full options live on /support */}
      <section className="border-b border-ink-200 py-16">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 px-6 sm:flex-row sm:items-center">
          <div>
            <p className="eyebrow text-accent-600">Support development</p>
            <h2 className="mt-2 text-xl font-semibold tracking-tight text-ink-900">
              Generation is free, forever. Supporting it is optional.
            </h2>
            <p className="mt-2 max-w-md text-sm leading-relaxed text-ink-500">
              Nothing is gated behind a payment. If Portfolio AI saved you time, there are a few
              optional ways to help fund development.
            </p>
          </div>
          <Link to="/support" className="flex-shrink-0">
            <Button variant="secondary" size="md" className="h-10 px-5">
              View support options
            </Button>
          </Link>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-ink-900 py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-2xl font-semibold tracking-tight text-white md:text-3xl">
            Upload your resume. See your portfolio take shape.
          </h2>
          <p className="mt-3 text-sm text-ink-300">Free, no signup tricks, no surprise paywall later.</p>
          <div className="mt-7">
            <Link to="/signup">
              <Button size="md" className="h-11 px-6 text-base">
                Generate your portfolio
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}

