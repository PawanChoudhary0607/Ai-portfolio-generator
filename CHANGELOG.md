# CHANGELOG

## Final productization pass

- Completed the portfolio export flow with authenticated `Open Website`, `Download HTML`, and `Download ZIP` actions.
- Added real theme rerendering from the saved portfolio JSON; switching themes does not rerun extraction, AI analysis, or portfolio generation.
- Added bundled demo website previews for the theme gallery when a user has no generated portfolio in context.
- Reworked the Results page so the generated website is the primary preview, with theme selection, export controls, metadata, and collapsible generated content.
- Replaced the support page with a focused donation page for Buy Me A Coffee, PayPal, and UPI, including QR, UPI ID copy, and mobile deep link support.
- Removed dead sidebar/settings UI and visible future-facing milestone copy.
- Sanitized generated `portfolio_data.json` exports so internal model metadata is not shipped to users.
- Confirmed frontend production build and lint; Python package tests could not run in this shell because no Python environment with `pytest`/FastAPI is available.
# CHANGELOG — Premium UI Redesign Pass

This pass is frontend-first, as scoped. No changes were made to the resume
extraction, AI analysis, portfolio generation, or website generation logic
in `website-generator/`. The 779-test engine suite passes unchanged.

## Implementation summary

**Bug fix (Priority 1, carried over from the previous session):**
The backend's `OLLAMA_MODEL` default didn't match the model actually
installed (`qwen3:14b`); no `backend/.env` existed, so it silently fell
back to the stale `qwen3:8b` default. Fixed at the config layer — model
selection was already environment-driven everywhere it's used, so this
was a one-line default change plus generating a real `.env` from the
example, not an architecture change.

**Security hardening (uncovered during the read-through, fixed at the
backend/engine isolation boundary — `generator_service.py` and
`schemas/portfolio.py` — never inside the frozen engine):**
- Pipeline failure messages previously forwarded the raw engine exception
  text straight to the API response. Several engine exceptions
  (`PDFNotFoundError`, `InvalidPDFError`, `EmptyPDFError`,
  `OllamaUnavailableError`, `ModelNotFoundError`) embed the full server
  filesystem path or the Ollama host/model name in their message. A
  translation table now maps each known exception type to plain,
  client-safe copy; the original exception (with full technical detail)
  is logged server-side only, via the new `GeneratorServiceError`
  constructor, and never reaches the client.
- `PortfolioDetailOut` (the `GET /portfolios/{id}` response) was
  serializing the engine's `llm_model` field straight from
  `portfolio_schema_json`, exposing which AI model generated the content.
  A model validator now strips it before the response is ever built.
- Upload validation trusted the client-supplied `Content-Type` header
  alone. It now also checks the actual file signature (`%PDF-` magic
  bytes) before accepting a file, since the header is trivially spoofed.

**UI redesign (Priority 2):**
- New shared design tokens (`tailwind.config.js`, `index.css`): warm
  neutral `surface` tint, `lift`/`popover` shadows, `fade-up` /
  `pulse-soft` / `shimmer` keyframes, global visible focus states, and a
  `prefers-reduced-motion` override so animation never becomes a barrier.
- New shared components: `EmptyState`, `ErrorState` (Problem / Possible
  reason / Suggested fix / Retry — used everywhere an error can surface,
  and never shown raw backend text), `Skeleton` / `SkeletonRow` /
  `SkeletonCard` (replacing blank-while-loading screens), `ThemeSwatch`
  (an honest abstract layout preview built from CSS, not a fabricated
  "generated portfolio" screenshot), `PublicNav` / `PublicFooter`.
- **Landing page** (`/`, new): hero with an original animated
  resume→portfolio visual (pure CSS, no cloned assets), How it Works,
  Themes (real catalog), Features, an honest "testimonials" placeholder
  (no fabricated quotes or names), FAQ, CTA, footer.
- **Dashboard**: quick-link cards (New portfolio / Templates / Support),
  named greeting, skeleton loading states, empty states with calls to
  action, and portfolio rows now link through to the new Results page.
- **Upload flow**: friendly `ErrorState` for upload/processing failures
  instead of raw red text, animated in-progress step icon, a "View
  portfolio" action on success.
- **Results page** (`/portfolios/:id`, new): renders the actual generated
  content (hero, about, skills, projects) from `portfolio_schema_json`,
  a theme picker backed by the real catalog, and export/preview actions
  that call the real (currently `501`) backend routes and degrade to a
  clear "ships in a later milestone" notice rather than a dead button or
  a console error.
- **Theme Gallery** (`/themes`, new): all five real catalog themes with
  abstract previews and descriptions.
- **Support page** (`/support`, new): GitHub Sponsors / Buy Me a Coffee /
  Ko-fi / Razorpay / UPI placeholders. Generation stays free; these are
  explicitly optional and gate nothing. Replace the placeholder `href`s
  with real links before shipping.
- **Settings page** (`/settings`, new): default theme and export-folder
  preferences (stored locally), dark mode and language as visibly
  disabled "coming soon", and a non-editable "AI engine: managed
  locally" notice — the actual model name is intentionally never exposed
  here, per the backend security rules.
- Auth pages (`AuthLayout`) got a lighter touch: same component, swapped
  to the new `surface` tone, with the logo now linking back to `/`.

## Files modified

**Backend**
- `backend/app/core/config.py` — default model fix
- `backend/.env.example`, `backend/.env` (new) — default model fix
- `backend/app/services/generator_service.py` — friendly-message
  translation layer, server-side-only logging of original exceptions
- `backend/app/services/storage_service.py` — magic-byte upload check
- `backend/app/schemas/portfolio.py` — strip `llm_model` before
  serialization
- `README.md` — setup instructions updated to match

**Frontend**
- `frontend/tailwind.config.js`, `frontend/src/index.css` — design tokens
- `frontend/src/components/EmptyState.tsx` (new)
- `frontend/src/components/ErrorState.tsx` (new)
- `frontend/src/components/Skeleton.tsx` (new)
- `frontend/src/components/ThemeSwatch.tsx` (new)
- `frontend/src/components/PublicNav.tsx` (new)
- `frontend/src/components/PublicFooter.tsx` (new)
- `frontend/src/components/AppShell.tsx` — added Theme Gallery / Support
  / Settings links
- `frontend/src/components/AuthLayout.tsx` — surface tone, home link
- `frontend/src/components/ProcessingSteps.tsx` — animated in-progress icon
- `frontend/src/pages/LandingPage.tsx` (new)
- `frontend/src/pages/ResultsPage.tsx` (new)
- `frontend/src/pages/ThemeGalleryPage.tsx` (new)
- `frontend/src/pages/SupportPage.tsx` (new)
- `frontend/src/pages/SettingsPage.tsx` (new)
- `frontend/src/pages/DashboardPage.tsx` — quick links, skeletons, empty
  states, clickable portfolio rows
- `frontend/src/pages/UploadPage.tsx` — `ErrorState`, view-portfolio link
- `frontend/src/api/client.ts` — typed `portfolioApi.get` as
  `PortfolioDetail`, added `previewTheme` / `exportZip` calls against the
  real (currently `501`) routes
- `frontend/src/App.tsx` — new routes, `/` now serves the landing page
- `shared/types.ts` — added `PortfolioDetail`

## Verification performed

- `website-generator` test suite: **779 passed**, unchanged
- Backend: full manual smoke test against a live server — signup, login,
  dashboard overview, theme catalog, a spoofed-content-type upload
  (rejected by the new magic-byte check), and a malformed-PDF upload
  (failed pipeline produces the sanitized client message while the
  server log retains the full path/traceback)
- Frontend: `tsc -b --noEmit` clean, `vite build` clean (no new
  dependencies added)

## Known limitations

- **Theme preview, "Open website," ZIP/HTML export, and publishing are
  still not implemented on the backend** — those routes intentionally
  still return `501`, since implementing them is explicitly out of scope
  for this pass (per "Do NOT create backend endpoints unless absolutely
  required" and the deferred-milestone list: theme selection, editing,
  deployment, billing, analytics, collaboration). The frontend calls the
  real routes and shows a clear, honest "ships in a later milestone"
  message rather than faking success.
- **No backend test suite exists yet** for `backend/` (only the frozen
  engine has one). The verification above was a manual end-to-end smoke
  test against a running server, not an automated regression suite —
  worth adding as its own milestone.
- **Support page links are placeholders** (`href="#"`) — replace with
  your real GitHub Sponsors / Buy Me a Coffee / Ko-fi / Razorpay / UPI
  details before shipping; shipping fabricated-looking but non-functional
  payment links to real users would be misleading.
- **Settings page preferences are local-only** (`localStorage`) — there's
  no backend user-preferences table yet, so they don't sync across
  devices. Wiring that up would mean adding a small, real endpoint, which
  felt outside "frontend-first" scope for this pass.
- **"Testimonials" section is an honest placeholder**, not fabricated
  quotes — no specific feature was skipped here; this is a deliberate
  choice to avoid shipping fake social proof to real users.

---

## Premium redesign — Stage 1: Design system + Landing page

Scope for this stage, per the new redesign brief (`ai-portfolio-saas-redesign.zip`):
design system polish and a full landing page rewrite. Dashboard, upload flow,
processing experience, support/settings, and the full accessibility/testing
pass are intentionally **not** part of this stage — staged the same way prior
sessions on this project have been, with a check-in between major components
rather than one unreviewed pass over the whole app.

### Added
- **Real theme preview screenshots.** `website-generator/scripts/generate_theme_previews.py`
  runs the actual (frozen, untouched) generation engine against the existing
  test fixture (`tests/website/fixtures/valid_portfolio.json`) for all five
  themes, then screenshots each rendered page with Playwright at 1440×960 @2x.
  Output lands in `frontend/public/theme-previews/*.png`. These are real
  generated pages, not illustrations or mockups.
- **`ThemePreview` component** (`frontend/src/components/ThemePreview.tsx`) —
  renders the real screenshot for a theme, with a graceful fallback to the
  existing abstract `ThemeSwatch` if an image is ever missing (e.g. before
  the script has been run in a fresh environment). `ThemeSwatch` itself is
  unchanged and still used where a screenshot would be illegible at small
  size (the compact theme picker on the Results page, `h-12`).
- **`PipelineStrip` component** (`frontend/src/components/PipelineStrip.tsx`) —
  the landing page's one signature motion element: a live filmstrip of the
  real six-stage generation pipeline (Uploading → Extracting → AI Analysis →
  Generating → Building → Done), cycling continuously. Respects
  `prefers-reduced-motion` (freezes on the final stage instead of animating).
  A `sr-only` list of all six stages with full descriptions sits alongside it
  so screen-reader users and anyone who doesn't want to wait for the
  animation get the same information immediately.

### Changed
- **Landing page rewritten** (`frontend/src/pages/LandingPage.tsx`) — moved
  away from the generic feature-grid/icon-bullet template toward an editorial,
  hairline-divided layout in line with the brief's Linear/Raycast/Framer/
  Stripe/Arc reference points. Sections, in order: hero (headline + a real
  generated-site screenshot, not a fake browser mockup), animated workflow,
  theme showcase (real screenshots, link to view the full-size example),
  features (editorial list, not icon cards), honest testimonials empty state,
  FAQ, a support-development teaser linking to `/support`, and a closing CTA.
- **`ThemeGalleryPage`** now shows real screenshots via `ThemePreview` instead
  of the abstract `ThemeSwatch`, plus a "View full example" link that opens
  the actual generated screenshot.

### Judgment calls flagged for review
- The brief lists "Theme showcase" and "Real generated portfolio examples"
  as two separate landing-page sections. I merged them into one section
  (theme grid using real screenshots, each linking out to the full-size
  image) rather than building two sections that would have shown
  substantially the same content twice. Flagging this since it's a scope
  interpretation, not something explicitly requested.
- Hero visual changed from the previous "fake browser mockup made of color
  blocks" to an actual screenshot of the Minimal theme. This is a more
  literal reading of "avoid placeholder-looking layouts" / "real generated
  portfolio examples," but means the hero is theme-specific rather than
  theme-neutral — worth a look before this ships broadly.

### Verified
- `npx tsc --noEmit` — clean.
- `npm run build` — clean production build.
- `website-generator` test suite — **779 passed** (untouched, frozen engine
  unaffected by this stage's changes).
- Visual check via Playwright screenshots at desktop (1440px) and mobile
  (390px) viewports — see stage notes; no backend test suite exists yet for
  `backend/`, so no backend tests were run (pre-existing gap, not introduced
  by this stage).

### Deferred to later stages (not done yet)
- Dashboard redesign, upload flow polish, animated processing experience,
  Results page rework, Support page payment methods (PayPal, UPI QR),
  Settings UX, full accessibility audit (ARIA/keyboard/contrast pass beyond
  what already existed), and final end-to-end testing + ZIP delivery.

---

## Premium redesign — Stage 2: Dashboard, Upload flow, Processing, Results

Scope: Dashboard redesign, Upload flow redesign, Processing experience, and
Results page redesign. Landing page untouched except where a shared
component it depends on had a real bug (see below). No backend code was
changed in this stage — everything here is a frontend rework against the
existing, unmodified API contract.

### New design principle applied throughout
Every redesigned page was rebuilt around one question: *what's the one
primary action here?* Concretely:
- **Dashboard** → upload a resume (if you haven't) / see your portfolios.
- **Upload** → one primary button per state, not three competing ones.
- **Results** → review what was generated; everything not-yet-real is one
  quiet sentence, not several buttons that attempt-then-fail.

### Added
- **`LiveProcessingStrip`** (`frontend/src/components/LiveProcessingStrip.tsx`)
  — the real, data-driven counterpart to the landing page's `PipelineStrip`.
  Same visual language (numbered circles, filling connector lines), but
  driven entirely by real state: real upload progress for "Uploading,"
  the real four `ResumeProcessingStep` statuses (using the backend's own
  label/detail text verbatim) for the middle stages, and the real
  `overall_status` for "Done." A failed stage halts the strip in place
  (red marker, connector stops filling) instead of continuing to animate.
- **Resumable processing view.** `UploadPage` now accepts `?resume=<id>`
  and will fetch that resume's real current status and either resume
  polling (if still in progress) or show its final state — using only the
  existing `GET /resumes/{id}` and `GET /resumes/{id}/status` endpoints, no
  new backend code. The Dashboard links to this for any non-terminal resume
  ("View progress"), so refreshing the page or coming back later doesn't
  lose your place.

### Changed
- **Dashboard** — replaced five always-present panels (recent resumes,
  generated portfolios, published sites, drafts, version history) with two:
  "Your portfolios" (the real product output, primary) and a smaller,
  quieter "Recent uploads" list (secondary). Drafts is a strict subset of
  generated portfolios today since nothing moves a portfolio out of draft
  yet, so a separate Drafts panel was pure duplication. Published sites and
  version history are collapsed into one closing sentence instead of two
  permanently-empty cards. Removed the quick-links card row, which mostly
  duplicated the sidebar nav. Single primary CTA ("Upload a resume") in the
  header throughout.
- **Upload flow** — processing now renders as the `LiveProcessingStrip`
  instead of the old vertical checklist, for visual continuity with the
  landing page's pipeline. Reduced the complete/failed states from three
  competing buttons to one primary action + one quiet text link.
- **Results page** — the large theme-layout preview is now the visual
  centerpiece, with pill tabs to switch between all five real theme
  screenshots (the same ones generated in Stage 1) instantly, client-side.
  Removed the previous "Preview this theme / Open website / Download ZIP /
  Download HTML" buttons that called real-but-501 endpoints and only
  revealed they weren't ready after a failed request — replaced with one
  upfront sentence stating plainly what's not available yet (per this
  stage's brief: label clearly instead of pretending it works). Added
  light polling so a portfolio still mid-generation updates automatically
  without a manual refresh.

### Fixed (bug discovered during this stage, not part of the original ask)
- **`AppShell` sidebar didn't collapse on mobile at all.** At narrow
  viewports the fixed 240px sidebar squeezed all page content into the
  remainder, wrapping button text and breaking every authenticated page —
  including the ones being redesigned in this stage. Replaced with a
  responsive layout: a slim top bar with a menu toggle below the `lg`
  breakpoint, opening a slide-in drawer with a backdrop; unchanged static
  sidebar at `lg` and above.
- **`PipelineStrip` (landing page) and `LiveProcessingStrip` (upload flow)
  clipped the last 1–2 stages on narrow screens** — six stages in a single
  flex row don't fit a 390px viewport, so "Building website" and "Done"
  were partially or fully cut off. Both now sit in a horizontally
  scrollable container with a fixed minimum width, so every stage stays
  legible and reachable instead of being squeezed or hidden. This is the
  only change made to anything the landing page renders in this stage,
  and it was made because the brief explicitly allows fixing a discovered
  bug — the section's content and motion are otherwise untouched.

### Verified
- `npx tsc --noEmit` — clean.
- `npm run build` — clean production build.
- `website-generator` test suite — **779 passed**, unaffected (no backend
  or engine code touched this stage).
- **Real end-to-end verification**, not just visual inspection: ran the
  actual backend (FastAPI + SQLite) and frontend dev server together,
  signed up a real user through the real `/auth/signup` endpoint, and
  uploaded a real generated PDF resume through the real `/resumes` upload
  endpoint. Extraction genuinely succeeded; AI analysis genuinely failed
  (no local Ollama model is available in this environment) — which
  verified the real failure path end-to-end (`LiveProcessingStrip`'s
  failed-state rendering, the dashboard's "failed" badge, the resumable
  `?resume=` view) using the product's actual behavior, not a simulated
  one. To verify the success path (which requires a completed AI run that
  this sandbox can't produce), one Resume + Portfolio row was inserted
  directly into the database using the same `valid_portfolio.json` fixture
  already used for the Stage 1 theme screenshots, purely to exercise the
  Dashboard and Results UI against real schema-shaped data — this is a
  test-seeding step for verification only, not a claim that the AI run
  itself was tested. The seeded rows and dev database were deleted after
  verification; nothing from this process ships.
- Checked desktop (1280px) and mobile (390px) for Dashboard (empty state
  and populated state), Upload (idle, real failure, mobile drawer), and
  Results (theme switching, mobile) — including via real screenshots
  rather than only reading the code.

### Deferred to later stages (not done yet)
- Support page payment methods (PayPal, UPI QR), Settings UX, full
  accessibility audit (this stage relied on the focus/reduced-motion
  foundations already in place from Stage 1; no dedicated ARIA/contrast
  pass was done), and final end-to-end testing + ZIP delivery.

---

## Premium redesign — Stage 3: Support page, accessibility audit

Scope: Support page payment methods (PayPal, UPI), and an accessibility
pass across everything touched in Stages 1–2. Settings page was reviewed
and left as-is — it already only exposes user-facing preferences and
already labels the AI engine as "Managed locally" with no internal config
exposed, which is what the brief asked for.

### Added
- **`SupportSection`** (`frontend/src/components/SupportSection.tsx`) — the
  support-methods grid + UPI block factored out into a standalone,
  configurable component (`methods`/`upi`/`footerNote` props), per the
  brief's explicit ask to make this reusable across future projects.
  `SupportPage` is now a thin config wrapper around it.
- **PayPal** added as a support method, alongside the existing GitHub
  Sponsors, Buy Me a Coffee, Ko-fi, and Razorpay.
- **Real UPI deep link.** Alongside the QR code (still a placeholder image
  slot — there's no real merchant VPA to generate one from), added an
  "Open in UPI app" link using a real `upi://pay?pa=...&pn=...` deep link,
  so the UPI option also "simply opens a link" on a phone, not just a QR
  to scan. Both still point at placeholder values (`your-username`,
  `your-vpa@upi`) since there's no real payment account configured —
  clearly commented in the file as the one thing to fill in before launch.

### Fixed (accessibility audit)
- **Upload dropzone was completely unreachable by keyboard.** It was a
  plain `<div onClick>` with a visually-hidden native file input — the
  only way to trigger file selection was a mouse click. Now a real
  `role="button"` with `tabIndex`, a visible focus ring, an accessible
  label, and Enter/Space activation.
- **Mobile nav drawer (introduced in Stage 2) had no keyboard escape
  route.** Added Escape-to-close, focus moves into the drawer on open and
  back to the menu button on close, and proper `role="dialog"` /
  `aria-modal` semantics.
- **Five components were silently rendering full-strength dark text where
  a muted caption color was clearly intended.** They used `text-ink-400`,
  a shade that was never defined in `tailwind.config.js` — Tailwind just
  emits no rule for an unknown shade, so the class was a no-op everywhere
  it was used (confirmed via computed style: captions were rendering as
  `rgb(24,24,27)`, i.e. full ink-900, not muted at all). Rather than adding
  a new pale shade to the palette — `ink-400` at a typical "muted caption"
  lightness fails WCAG AA contrast at the small text sizes these captions
  use — redirected all five usages to the existing `ink-500`, which is
  already used elsewhere in the app and passes AA (~4.8:1 on white).
- **`Input`** now links its hint/error text to the field via
  `aria-describedby` and sets `aria-invalid`, instead of showing
  validation text with no programmatic association to the field.
- **`Button`**'s loading spinner is now `aria-hidden`, and the button sets
  `aria-busy` while loading, instead of a decorative spinner being exposed
  to assistive tech with no state conveyed.
- Removed `ProcessingSteps.tsx`, a component made obsolete by Stage 2's
  `LiveProcessingStrip` and left orphaned (zero imports) — dead code, not
  a behavior change.

### Verified
- `npx tsc --noEmit` — clean.
- `npm run build` — clean production build.
- `website-generator` test suite — **779 passed**, unaffected.
- Re-verified the Stage 1 contrast bug fix by reading the actual computed
  `color` of the previously-broken caption in a real browser
  (`rgb(113,113,122)` — ink-500 — confirmed, not just read from source).
- Verified real keyboard-only operation: tabbed through the Upload page
  with no mouse and confirmed focus reaches the dropzone with a visible
  ring and the correct accessible name, via Playwright driving a real
  signed-up account against the real backend.
- Screenshotted the Support page with all five methods + UPI rendering
  correctly against the real running app.

### Deferred to later stages (not done yet)
- Final full end-to-end manual click-through of the entire flow listed in
  the original brief, and the final delivery ZIP — both intentionally
  left for the explicit final stage, next.

---

## Premium redesign — Stage 4: Final end-to-end verification

Final pass requested by the original brief: a full manual click-through of
Landing → Login/Signup → Dashboard → Upload → Processing → Results → Theme
gallery → Support → Settings, run against the real app rather than read
from the code, plus the delivery package.

### Verified
- Ran the real backend (FastAPI + SQLite, fresh empty database) and the
  real frontend dev server together for this pass.
- **Landing → Signup → Dashboard**: signed up a brand-new account through
  the real `/auth/signup` form, landed on the empty-state Dashboard.
- **Dashboard → Theme gallery → Support → Settings**: clicked through the
  sidebar to each page; all render correctly with no console errors other
  than a `fonts.googleapis.com` 403, which is this sandbox's network
  egress policy blocking the Google Fonts CDN request — not an app bug,
  and not something that would happen in a normal deployment with internet
  access.
- **Dashboard → Upload → Processing → real failure → back to Dashboard**:
  used Playwright's real file-chooser API to upload the actual generated
  PDF resume through the real dropzone (not a simulated event) — confirmed
  it correctly halts on a genuine AI-analysis failure (no local Ollama in
  this sandbox), then logged out and back in with the same account and
  confirmed the dashboard correctly shows the failed upload from a fresh
  session, not just in-memory state.
- Spot-checked computed CSS once more on the hero CTA button to rule out a
  styling regression that a compressed screenshot made it look like there
  might be — confirmed `background-color: rgb(234,88,12)` (accent-600),
  exactly as intended; this was a false alarm caused by image compression,
  not a real issue.
- `npx tsc --noEmit`, `npm run build`, and the `website-generator` test
  suite (**779 passed**) all re-confirmed clean at the end of this stage.
- All test accounts and the dev SQLite database created during this and
  prior stages were deleted; nothing from the verification process ships.

### Known pre-existing limitations (not introduced by this redesign, not
fixed by it either — flagged for visibility)
- There is still no automated backend test suite (only the frozen
  `website-generator` engine has one). Verification in this redesign was
  manual and Playwright-driven against the real running app rather than
  via backend unit/integration tests, because none exist yet to run.
- Theme selection, publishing, and export are still 501 stubs by design
  (per the existing project's "no scope creep" principle) — the Results
  and Theme Gallery pages now state this clearly upfront instead of
  discovering it through failed requests, but the underlying capability
  itself is intentionally unbuilt, same as before this redesign.

