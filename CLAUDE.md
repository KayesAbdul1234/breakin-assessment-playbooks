# CLAUDE.md — Frontend Website Rules

## Always Do First
- **Invoke the `frontend-design` skill** before writing any frontend code, every session, no exceptions.

## Reference Images
- If a reference image is provided: match layout, spacing, typography, and color exactly. Swap in placeholder content (images via `https://placehold.co/`, generic copy). Do not improve or add to the design.
- If no reference image: design from scratch with high craft (see guardrails below).
- Screenshot your output, compare against reference, fix mismatches, re-screenshot. Do at least 2 comparison rounds. Stop only when no visible differences remain or user says so.

## Local Server
- **Always serve on localhost** — never screenshot a `file:///` URL.
- Start the dev server: `python3 serve.py` (serves the project root at `http://localhost:3000`; the landing page is `http://localhost:3000/site/`)
- `serve.py` lives in the project root and needs only the Python standard library. Start it in the background before taking any screenshots.
- Pages written in Artifact format (no `<!doctype>`) are wrapped in the same skeleton the Artifact host adds, so local renders match the published page.
- If the server is already running, do not start a second instance. Check with `curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/site/` (200 = running).

## Screenshot Workflow
- No Node or Puppeteer on this Mac. `screenshot.py` drives the installed Google Chrome (`/Applications/Google Chrome.app`) headless via the DevTools protocol, standard library only.
- **Always screenshot from localhost:** `python3 screenshot.py http://localhost:3000/site/`
- Screenshots are saved automatically to `./temporary screenshots/screenshot-N.png` (auto-incremented, never overwritten). Captures are full-page by default.
- Optional label suffix: `python3 screenshot.py http://localhost:3000/site/ label` → saves as `screenshot-N-label.png`
- Options (combine freely):
  - `--mobile` — true 390px phone width with mobile emulation (don't rely on window size; headless Chrome won't go below ~500px)
  - `--dark` — `prefers-color-scheme: dark` (default is light, regardless of the Mac's system theme)
  - `--width N` — custom viewport width
  - `--top N` — capture only the first N CSS px (e.g. `--top 900` for the hero)
  - `--from Y` — start the capture at Y CSS px; use with `--top` to slice long pages (e.g. `--mobile --from 1400 --top 2600`)
  - `--eval JS` — run JavaScript in the page before capturing (promises are awaited, return value is printed). Use it to click through interactive states (e.g. play the hero game to its finished state) and screenshot the result.
- Each run prints the page height and flags horizontal overflow (`⚠ HORIZONTAL OVERFLOW`) with the elements wider than the viewport, plus any uncaught JavaScript exceptions or console errors (`⚠ N JS/console error(s)`). Treat either as a bug.
- The practice games open in an on-page player via `#play-<id>` links (e.g. `http://localhost:3000/site/#play-security`). Use `--eval` to click through a game and screenshot its play or results state.
- Check every change at desktop, `--mobile`, and `--dark`. Long mobile pages are easier to read in `--from`/`--top` slices.
- `screenshot.py` lives in the project root. Use it as-is.
- After screenshotting, read the PNG from `temporary screenshots/` with the Read tool — Claude can see and analyze the image directly.
- When comparing, be specific: "heading is 32px but reference shows ~24px", "card gap is 16px but should be 24px"
- Check: spacing/padding, font size/weight/line-height, colors (exact hex), alignment, border-radius, shadows, image sizing

## Output Defaults
- Single `index.html` file, all styles inline, unless user says otherwise
- Tailwind CSS via CDN: `<script src="https://cdn.tailwindcss.com"></script>`
- Placeholder images: `https://placehold.co/WIDTHxHEIGHT`
- Mobile-first responsive

## Brand Assets
- Always check the `brand_assets/` folder before designing. It may contain logos, color guides, style guides, or images.
- If assets exist there, use them. Do not use placeholders where real assets are available.
- If a logo is present, use it. If a color palette is defined, use those exact values — do not invent brand colors.

## Anti-Generic Guardrails
- **Colors:** Never use default Tailwind palette (indigo-500, blue-600, etc.). Pick a custom brand color and derive from it.
- **Shadows:** Never use flat `shadow-md`. Use layered, color-tinted shadows with low opacity.
- **Typography:** Never use the same font for headings and body. Pair a display/serif with a clean sans. Apply tight tracking (`-0.03em`) on large headings, generous line-height (`1.7`) on body.
- **Gradients:** Layer multiple radial gradients. Add grain/texture via SVG noise filter for depth.
- **Animations:** Only animate `transform` and `opacity`. Never `transition-all`. Use spring-style easing.
- **Interactive states:** Every clickable element needs hover, focus-visible, and active states. No exceptions.
- **Images:** Add a gradient overlay (`bg-gradient-to-t from-black/60`) and a color treatment layer with `mix-blend-multiply`.
- **Spacing:** Use intentional, consistent spacing tokens — not random Tailwind steps.
- **Depth:** Surfaces should have a layering system (base → elevated → floating), not all sit at the same z-plane.

## Hard Rules
- Do not add sections, features, or content not in the reference
- Do not "improve" a reference design — match it
- Do not stop after one screenshot pass
- Do not use `transition-all`
- Do not use default Tailwind blue/indigo as primary color

## Deploy (GitHub Pages)
- Repo: https://github.com/KayesAbdul1234/breakin-assessment-playbooks (branch `main`). Live site: https://kayesabdul1234.github.io/breakin-assessment-playbooks/
- Pages serves the `docs/` folder. Edit `site/index.html` (Artifact format), then run `python3 build.py` to regenerate `docs/index.html`. Never edit `docs/` by hand.
- Publish: `python3 build.py && git add -A && git commit -m "..." && git push`. This folder's git uses a repo-scoped deploy key (`~/.ssh/breakin_deploy_ed25519`, set via `core.sshCommand`). Pages rebuilds in about a minute.
