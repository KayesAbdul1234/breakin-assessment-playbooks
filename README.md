# BreakIn Assessment Playbooks

Practice platform for BreakIn mentees preparing for the **Arctic Shores** game-based assessment used by apprenticeship employers.

All 14 reported tasks are playable on one page, each with:

- a plain-English how-to and worked example
- practice mode with hints, and a full-length mode matching the real round counts and timing
- a practice target, personal coaching after every run, and progress saved in the mentee's browser

The games are practice versions built from candidate reports and prep guides. They are not the real test, and BreakIn is not affiliated with Arctic Shores.

## Project layout

| Path | What it is |
|---|---|
| `site/index.html` | The page source (Artifact format: no `<!doctype>`/`<head>` wrapper) |
| `docs/` | The built site that GitHub Pages serves. Generated, don't edit by hand |
| `build.py` | Wraps `site/index.html` into a full HTML document at `docs/index.html` |
| `serve.py` | Local dev server at http://localhost:3000 |
| `screenshot.py` | Headless Chrome screenshots, overflow and JS-error checks |
| `Brand_assets/` | BreakIn logo files |

## Making a change

```sh
# 1. edit site/index.html
python3 serve.py                                            # preview at http://localhost:3000/site/
python3 screenshot.py http://localhost:3000/site/ --mobile  # check it
# 2. rebuild the Pages copy and commit both
python3 build.py
git add -A && git commit -m "Describe the change" && git push
```

GitHub Pages publishes from the `docs/` folder on `main`.
