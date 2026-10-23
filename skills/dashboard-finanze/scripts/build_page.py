"""Build the dashboard as ONE self-contained HTML page, for sessions without a Dashboard
artifact type (or to keep a copy). Same page code as the Dashboard version.

Usage:
  python3 build_page.py PAGE.html DATA_DIR OUT.html [--title "Finanze di casa"]
      [--lang it] [--params '{"name": value}'] [--d3 path/to/d3.min.js]

PAGE.html   the page (templates/dashboard-page.html, edited for the person)
DATA_DIR    the CSVs from dashboard_data.py; each file becomes dataset <name>
The page loads d3 from cdnjs; everything else, data included, is inside the file. If the
page must work offline or cdnjs is blocked, pass --d3 with a local d3 v7 build (e.g. from
`npm install d3@7`: node_modules/d3/dist/d3.min.js) to put it inside the file too.
It holds only totals, like the Dashboard version: no single transactions.
"""
import argparse
import csv
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SHIM = os.path.join(HERE, "..", "templates", "standalone-shim.js")

TOKENS = """
:root{
  --font-anthropic-sans: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-anthropic-serif: ui-serif, Georgia, "Times New Roman", serif;
  --color-fg:#1d1d1b; --color-fg-muted:#6b6a65; --color-bg:#faf9f5; --color-panel:#ffffff;
  --color-border-line:#e6e3da; --color-ok:#2f7d4f; --color-warn:#a86411; --color-bad:#b3261e;
  --cds-font-size-caption:.8125rem; --cds-font-size-body:.9375rem; --cds-font-size-heading:1.125rem; --cds-font-size-title:1.75rem;
  --cds-font-weight-medium:550;
  --cds-gap-xs:.25rem; --cds-gap-sm:.5rem; --cds-gap-md:1rem; --cds-gap-lg:1.5rem; --cds-gap-xl:2.25rem;
  --cds-pad-xs:.25rem; --cds-pad-sm:.5rem; --cds-pad-md:.75rem; --cds-pad-lg:1rem;
  --cds-radius:10px; --cds-dur-slow:.3s;
  --cds-border:#e0ddd3; --cds-surface-popover:#ffffff; --cds-shadow-popover:0 4px 16px rgba(0,0,0,.12);
  --cds-text-secondary:#6b6a65;
  --cds-chart-grid:#ecebe6; --cds-chart-axis:#c9c6bc; --cds-chart-reference:#8a877d; --cds-chart-muted:#cfccc2;
  --cds-chart-status-critical:#c4372b;
  --series-1:#3b6fd8; --series-2:#d9822b; --series-3:#2f9e83; --series-4:#9a5bd0;
  --series-5:#d4a72c; --series-6:#d0548a; --series-7:#5a8f2e; --series-8:#6f7a8c;
}
@media (prefers-color-scheme: dark){:root{
  --color-fg:#f0eee8; --color-fg-muted:#a9a69c; --color-bg:#1c1c1a; --color-panel:#262624;
  --color-border-line:#3a3936; --color-ok:#6cc08b; --color-warn:#e0a458; --color-bad:#ef7f74;
  --cds-border:#3f3e3a; --cds-surface-popover:#2e2e2b; --cds-shadow-popover:0 4px 16px rgba(0,0,0,.5);
  --cds-text-secondary:#a9a69c;
  --cds-chart-grid:#33322f; --cds-chart-axis:#4a4945; --cds-chart-reference:#8c897f; --cds-chart-muted:#55534e;
  --cds-chart-status-critical:#ef7f74;
  --series-1:#7aa2f7; --series-2:#f0a35e; --series-3:#5cc8a8; --series-4:#b98be6;
  --series-5:#e8c35a; --series-6:#ea86b0; --series-7:#8cc265; --series-8:#9aa4b5;
}}
body{margin:0;background:var(--color-bg);color:var(--color-fg);}
#dash-root{max-width:1200px;margin:0 auto;padding:24px 16px 48px;}
.dash-skeleton{color:transparent!important;background:var(--cds-chart-grid);border-radius:6px;}
"""


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        r = csv.DictReader(fh)
        rows = list(r)
        return {"columns": r.fieldnames or [], "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("data_dir")
    ap.add_argument("out")
    ap.add_argument("--title", default="Finanze")
    ap.add_argument("--lang", default="it")
    ap.add_argument("--params", default="{}")
    ap.add_argument("--d3", help="local d3.min.js to inline instead of loading it from cdnjs")
    a = ap.parse_args()
    data = {os.path.splitext(os.path.basename(p))[0]: load_csv(p)
            for p in sorted(glob.glob(os.path.join(a.data_dir, "*.csv")))}
    page = open(a.page, encoding="utf-8").read()
    shim = open(SHIM, encoding="utf-8").read()
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    d3tag = ('<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>' if not a.d3
             else "<script>" + open(a.d3, encoding="utf-8").read().replace("</script", "<\\/script") + "</script>")
    html = f"""<!doctype html>
<html lang="{a.lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{a.title}</title>
<style>{TOKENS}</style>
{d3tag}
<script>window.__DASH_DATA__ = {blob};
window.__DASH_PARAMS__ = {json.dumps(json.loads(a.params))};</script>
<script>{shim}</script>
</head>
<body>
<main id="dash-root">
{page}
</main>
</body>
</html>
"""
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"wrote {a.out}: {len(data)} datasets, {len(html) // 1024} KB")


if __name__ == "__main__":
    main()
