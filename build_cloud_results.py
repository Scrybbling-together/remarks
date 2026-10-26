"""This script in particular was made with AI."""

import json
import math
from pathlib import Path
from statistics import mean, median, pstdev

import plotly.graph_objects as go
from plotly.offline import get_plotlyjs

DATA_DIR = Path(__file__).resolve().parent / "tests" / "out" / "cloud_download_results"
OUTPUT_FILE = DATA_DIR / "results.html"

FILES = {
    "errors": "errored_files.json",
    "page_lines": "line_counts_individual.json",
    "doc_lines": "line_counts.json",
    "metadata_load": "load_doc_times.json",
    "page_load": "load_rm_times_individual.json",
    "document_load": "load_rm_times.json",
    "process": "process_times.json",
}


def read_json(name, default):
    path = DATA_DIR / name
    if not path.exists():
        print(f"Warning: missing {path.name}; continuing with empty data.")
        return default
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Warning: could not read {path.name}: {exc}")
        return default


def numeric_mapping(value):
    """Keep finite numeric values and normalize them to float."""
    if not isinstance(value, dict):
        return {}
    result = {}
    for key, item in value.items():
        try:
            number = float(item)
            if math.isfinite(number):
                result[str(key)] = number
        except (TypeError, ValueError):
            continue
    return result


def split_page_key(key):
    """Split doc_uuid/page_uuid once; UUIDs themselves contain no slash."""
    if "/" not in key:
        return key, None
    return key.split("/", 1)


def stats(values):
    values = [float(v) for v in values if math.isfinite(float(v))]
    if not values:
        return None
    ordered = sorted(values)

    def percentile(p):
        if len(ordered) == 1:
            return ordered[0]
        position = (len(ordered) - 1) * p
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return ordered[lower]
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

    return {
        "n": len(ordered),
        "mean": mean(ordered),
        "median": median(ordered),
        "std": pstdev(ordered),
        "min": ordered[0],
        "p95": percentile(0.95),
        "max": ordered[-1],
    }


def fmt(value, digits=3):
    if value is None:
        return "—"
    return f"{value:,.{digits}f}"


def metric_stats_table(metrics):
    rows = []
    for label, values, unit in metrics:
        s = stats(values)
        if not s:
            continue
        rows.append(
            "<tr>"
            f"<td>{label}</td><td>{s['n']:,}</td>"
            f"<td>{fmt(s['mean'])} {unit}</td>"
            f"<td>{fmt(s['median'])} {unit}</td>"
            f"<td>{fmt(s['std'])} {unit}</td>"
            f"<td>{fmt(s['min'])} {unit}</td>"
            f"<td>{fmt(s['p95'])} {unit}</td>"
            f"<td>{fmt(s['max'])} {unit}</td>"
            "</tr>"
        )
    if not rows:
        return (
            '<tr><td colspan="8" class="empty">No numeric measurements found.</td></tr>'
        )
    return "".join(rows)


def make_histogram(values, label, color):
    fig = go.Figure()
    if values:
        fig.add_trace(
            go.Histogram(x=values, name=label, marker_color=color, opacity=0.78)
        )
    fig.update_layout(
        title=label,
        template="plotly_white",
        margin=dict(l=45, r=20, t=55, b=45),
        xaxis_title=label,
        yaxis_title="Measurements",
        bargap=0.08,
        showlegend=False,
    )
    return fig


def make_scatter(x, y, label, x_label, y_label, custom=None):
    fig = go.Figure()
    if x and y:
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                name=label,
                marker=dict(size=7, opacity=0.7),
                text=custom,
                hovertemplate=(
                    "%{text}<br>"
                    + x_label
                    + ": %{x}<br>"
                    + y_label
                    + ": %{y}<extra></extra>"
                    if custom
                    else x_label + ": %{x}<br>" + y_label + ": %{y}<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        title=label,
        template="plotly_white",
        margin=dict(l=55, r=20, t=55, b=50),
        xaxis_title=x_label,
        yaxis_title=y_label,
    )
    return fig


def chart_div(fig, div_id, include_js=False):
    return fig.to_html(
        full_html=False,
        include_plotlyjs=include_js,
        div_id=div_id,
        config={"responsive": True, "displaylogo": False},
    )


def main():
    if not DATA_DIR.exists():
        raise SystemExit(
            f"Data directory not found: {DATA_DIR}\n"
            "Place this script beside the tests/ directory, or update DATA_DIR."
        )

    raw = {
        key: read_json(filename, [] if key == "errors" else {})
        for key, filename in FILES.items()
    }
    doc_lines = numeric_mapping(raw["doc_lines"])
    metadata_load = numeric_mapping(raw["metadata_load"])
    document_load = numeric_mapping(raw["document_load"])
    process = numeric_mapping(raw["process"])
    page_lines_raw = numeric_mapping(raw["page_lines"])
    page_load_raw = numeric_mapping(raw["page_load"])

    page_lines = {}
    page_load = {}
    for key, value in page_lines_raw.items():
        doc_id, page_id = split_page_key(key)
        if page_id is not None:
            page_lines[key] = value
    for key, value in page_load_raw.items():
        doc_id, page_id = split_page_key(key)
        if page_id is not None:
            page_load[key] = value

    page_line_by_key = page_lines
    paired_page_keys = sorted(set(page_line_by_key) & set(page_load))
    paired_page_lines = [page_line_by_key[k] for k in paired_page_keys]
    paired_page_load = [page_load[k] for k in paired_page_keys]
    paired_page_labels = [k for k in paired_page_keys]

    # Count pages from load_rm_times_individual.json specifically.
    # These are the pages for which an individual binary-load measurement exists.
    page_keys = set(page_load)
    page_counts = {}
    for key in page_keys:
        doc_id, page_id = split_page_key(key)
        if page_id is not None:
            page_counts[doc_id] = page_counts.get(doc_id, 0) + 1

    # Join document-level metrics by document UUID, retaining documents present in any metric.
    all_doc_ids = sorted(
        set(doc_lines)
        | set(metadata_load)
        | set(document_load)
        | set(process)
        | set(page_counts)
    )
    doc_rows = []
    for doc_id in all_doc_ids:
        doc_rows.append(
            {
                "id": doc_id,
                "lines": doc_lines.get(doc_id),
                "pages": page_counts.get(doc_id),
                "metadata": metadata_load.get(doc_id),
                "binary_load": document_load.get(doc_id),
                "process": process.get(doc_id),
            }
        )

    # Scatter arrays are aligned by document ID, never by JSON insertion order.
    scatter_doc_ids = [d for d in all_doc_ids if d in doc_lines and d in process]
    scatter_lines = [doc_lines[d] for d in scatter_doc_ids]
    scatter_process = [process[d] for d in scatter_doc_ids]
    scatter_process_labels = scatter_doc_ids

    load_doc_ids = [d for d in all_doc_ids if d in doc_lines and d in document_load]
    load_lines = [doc_lines[d] for d in load_doc_ids]
    load_seconds = [document_load[d] for d in load_doc_ids]

    metadata_ids = [d for d in all_doc_ids if d in doc_lines and d in metadata_load]
    metadata_lines = [doc_lines[d] for d in metadata_ids]
    metadata_seconds = [metadata_load[d] for d in metadata_ids]

    errors = raw["errors"]
    if not isinstance(errors, list):
        errors = [{"error": str(errors)}]

    metrics = [
        ("Pages per document", list(page_counts.values()), "pages"),
        ("Lines per document", list(doc_lines.values()), "lines"),
        ("Metadata read time", list(metadata_load.values()), "s"),
        ("Binary load time per document", list(document_load.values()), "s"),
        ("Combined process time", list(process.values()), "s"),
        ("Lines per page", list(page_lines.values()), "lines"),
        ("Binary load time per page", list(page_load.values()), "s"),
    ]

    figures = [
        (
            "doc-pages",
            make_histogram(list(page_counts.values()), "Pages per document", "#636EFA"),
            "Documents",
        ),
        (
            "doc-lines",
            make_histogram(list(doc_lines.values()), "Lines per document", "#636EFA"),
            "Documents",
        ),
        (
            "metadata-hist",
            make_histogram(
                list(metadata_load.values()), "Metadata read time (s)", "#00CC96"
            ),
            "Document timings",
        ),
        (
            "document-load-hist",
            make_histogram(
                list(document_load.values()),
                "Binary load time per document (s)",
                "#AB63FA",
            ),
            "Document timings",
        ),
        (
            "process-hist",
            make_histogram(
                list(process.values()),
                "Combined read + load + render time (s)",
                "#EF553B",
            ),
            "Document timings",
        ),
        (
            "page-lines-hist",
            make_histogram(list(page_lines.values()), "Lines per page", "#FFA15A"),
            "Pages",
        ),
        (
            "page-load-hist",
            make_histogram(
                list(page_load.values()), "Binary load time per page (s)", "#19D3F3"
            ),
            "Pages",
        ),
        (
            "process-vs-lines",
            make_scatter(
                scatter_lines,
                scatter_process,
                "Combined process time vs document lines",
                "Lines per document",
                "Process time (s)",
                scatter_process_labels,
            ),
            "Relationships",
        ),
        (
            "load-vs-lines",
            make_scatter(
                load_lines,
                load_seconds,
                "Binary load time vs document lines",
                "Lines per document",
                "Binary load time (s)",
                load_doc_ids,
            ),
            "Relationships",
        ),
        (
            "metadata-vs-lines",
            make_scatter(
                metadata_lines,
                metadata_seconds,
                "Metadata read time vs document lines",
                "Lines per document",
                "Metadata read time (s)",
                metadata_ids,
            ),
            "Relationships",
        ),
        (
            "page-load-vs-lines",
            make_scatter(
                paired_page_lines,
                paired_page_load,
                "Page binary load time vs page lines",
                "Lines per page",
                "Page load time (s)",
                paired_page_labels,
            ),
            "Relationships",
        ),
    ]

    document_table_rows = []
    for row in doc_rows:
        document_table_rows.append(
            "<tr>"
            f"<td class='uuid'>{row['id']}</td>"
            f"<td>{fmt(row['pages'], 0) if row['pages'] is not None else '—'}</td>"
            f"<td>{fmt(row['lines'], 0) if row['lines'] is not None else '—'}</td>"
            f"<td>{fmt(row['metadata']) if row['metadata'] is not None else '—'}</td>"
            f"<td>{fmt(row['binary_load']) if row['binary_load'] is not None else '—'}</td>"
            f"<td>{fmt(row['process']) if row['process'] is not None else '—'}</td>"
            "</tr>"
        )
    if not document_table_rows:
        document_table_rows.append(
            '<tr><td colspan="6" class="empty">No document-level data found.</td></tr>'
        )

    error_rows = []
    for error in errors:
        error_rows.append(
            "<tr><td class='uuid'>"
            + str(error).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            + "</td></tr>"
        )
    if not error_rows:
        error_rows.append('<tr><td class="empty">No errors recorded 🎉</td></tr>')

    total_docs = len(all_doc_ids)
    total_pages = len(page_keys)
    cards = [
        ("Documents measured", f"{total_docs:,}"),
        ("Pages measured", f"{total_pages:,}"),
        (
            "Mean pages per document",
            (
                fmt(stats(page_counts.values())["mean"], 1)
                if stats(page_counts.values())
                else "—"
            ),
        ),
        ("Errored entries", f"{len(errors):,}"),
        (
            "Mean process time",
            (
                f"{fmt(stats(process.values())['mean'])} s"
                if stats(process.values())
                else "—"
            ),
        ),
        (
            "Mean document lines",
            (
                fmt(stats(doc_lines.values())["mean"], 1)
                if stats(doc_lines.values())
                else "—"
            ),
        ),
        ("Paired page measurements", f"{len(paired_page_keys):,}"),
    ]
    cards_html = "".join(
        f'<div class="stat-card"><div class="stat-label">{label}</div><div class="stat-value">{value}</div></div>'
        for label, value in cards
    )

    chart_cards = []
    for index, (div_id, fig, category) in enumerate(figures):
        chart_cards.append(
            f'<section class="chart-card" data-category="{category}">'
            f'<div id="{div_id}" class="chart"></div>'
            f"</section>"
        )
    charts_html = "".join(chart_cards)

    plotly_js = get_plotlyjs()
    chart_scripts = []
    for div_id, fig, category in figures:
        chart_scripts.append(
            f"Plotly.newPlot('{div_id}', {fig.to_json()}, "
            "{responsive:true, displaylogo:false});"
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Document Benchmark Results</title>
<style>
:root {{ color-scheme: light dark; --bg:#f4f6fb; --panel:#fff; --text:#202536; --muted:#687086; --border:#e2e6f0; --accent:#635bff; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#11131a; --panel:#1b1e29; --text:#edf0fa; --muted:#a2a9bf; --border:#303546; --accent:#9b95ff; }}
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font:15px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
header {{ padding:32px max(20px,calc((100vw - 1500px)/2)); background:#34304f; color:white; }}
header h1 {{ margin:0 0 6px; font-size:clamp(1.7rem,3vw,2.5rem); }}
header p {{ margin:0; opacity:.85; }}
main {{ max-width:1540px; margin:0 auto; padding:24px; }}
.section-title {{ display:flex; align-items:center; justify-content:space-between; gap:16px; margin:28px 0 14px; }}
.section-title h2 {{ font-size:1.25rem; margin:0; }}
.stat-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; }}
.stat-card,.panel,.chart-card {{ background:var(--panel); border:1px solid var(--border); border-radius:14px; box-shadow:none; }}
.stat-card {{ padding:18px; }}
.stat-label {{ color:var(--muted); font-size:.85rem; }}
.stat-value {{ font-size:1.7rem; font-weight:750; margin-top:4px; overflow-wrap:anywhere; }}
.filters {{ display:flex; flex-wrap:wrap; gap:10px; }}
.filters label {{ display:flex; align-items:center; gap:7px; background:var(--panel); border:1px solid var(--border); padding:8px 12px; border-radius:999px; cursor:pointer; }}
.filters input {{ accent-color:var(--accent); }}
.chart-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,460px),1fr)); gap:14px; }}
.chart-card {{ min-width:0; padding:8px; overflow:hidden; }}
.chart {{ width:100%; min-height:350px; }}
.panel {{ padding:18px; overflow:hidden; }}
.table-wrap {{ overflow:auto; max-height:650px; }}
table {{ border-collapse:collapse; width:100%; white-space:nowrap; font-size:.9rem; }}
th,td {{ padding:10px 12px; border-bottom:1px solid var(--border); text-align:right; }}
th {{ position:sticky; top:0; background:var(--panel); color:var(--muted); font-weight:650; }}
.sort-button {{ border:0; padding:0; background:transparent; color:inherit; font:inherit; white-space:nowrap; }}
.sort-button:hover {{ color:var(--accent); }}
th:first-child,td:first-child {{ text-align:left; }}
td.uuid {{ text-align:left; font-family:ui-monospace,SFMono-Regular,monospace; font-size:.82rem; }}
.empty {{ text-align:left; color:var(--muted); }}
.toolbar {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; }}
button {{ border:1px solid var(--border); border-radius:8px; padding:8px 12px; background:var(--panel); color:var(--text); cursor:pointer; }}
button:hover {{ border-color:var(--accent); }}
input[type=search] {{ padding:9px 12px; border:1px solid var(--border); border-radius:8px; background:var(--panel); color:var(--text); min-width:230px; }}
details summary {{ cursor:pointer; font-weight:650; }}
.error-list {{ max-height:280px; overflow:auto; }}
footer {{ color:var(--muted); padding:28px 0 12px; font-size:.85rem; }}
@media(max-width:600px) {{ main {{ padding:14px; }} .chart {{ min-height:300px; }} .stat-value {{ font-size:1.35rem; }} }}
</style>
</head>
<body>
<header>
  <h1>Document Benchmark Results</h1>
  <p>Load, render, and line-count measurements · generated from your JSON benchmark output</p>
</header>
<main>
  <div class="stat-grid">{cards_html}</div>

  <div class="section-title"><h2>Explore charts</h2></div>
  <div class="filters" id="chart-filters">
    <label><input type="checkbox" value="Documents" checked> Document metrics</label>
    <label><input type="checkbox" value="Document timings" checked> Document timings</label>
    <label><input type="checkbox" value="Pages" checked> Page metrics</label>
    <label><input type="checkbox" value="Relationships" checked> Relationships</label>
  </div>
  <div class="chart-grid" id="chart-grid">{charts_html}</div>

  <div class="section-title"><h2>Statistical summary</h2></div>
  <div class="panel table-wrap">
    <table>
      <thead><tr><th>Metric</th><th>Samples</th><th>Mean</th><th>Median</th><th>Std. dev.</th><th>Min</th><th>95th percentile</th><th>Max</th></tr></thead>
      <tbody>{metric_stats_table(metrics)}</tbody>
    </table>
  </div>

  <div class="section-title"><h2>Document measurements</h2><div class="toolbar">
    <input id="doc-search" type="search" placeholder="Filter by document UUID…">
    <button id="download-csv">Export CSV</button>
  </div></div>
  <div class="panel table-wrap">
    <table id="documents-table">
      <thead><tr>
        <th><button class="sort-button" data-sort="text" aria-label="Sort by document UUID">Document UUID ↕</button></th>
        <th><button class="sort-button" data-sort="number" aria-label="Sort by pages">Pages ↕</button></th>
        <th><button class="sort-button" data-sort="number" aria-label="Sort by lines">Lines ↕</button></th>
        <th><button class="sort-button" data-sort="number" aria-label="Sort by metadata read time">Metadata read (s) ↕</button></th>
        <th><button class="sort-button" data-sort="number" aria-label="Sort by binary load time">Binary load (s) ↕</button></th>
        <th><button class="sort-button" data-sort="number" aria-label="Sort by process time">Process (s) ↕</button></th>
      </tr></thead>
      <tbody>{''.join(document_table_rows)}</tbody>
    </table>
  </div>

  <div class="section-title"><h2>Errors</h2></div>
  <div class="panel">
    <details>
      <summary>{len(errors):,} error entr{'y' if len(errors) == 1 else 'ies'} (expand to inspect)</summary>
      <div class="error-list"><table><tbody>{''.join(error_rows)}</tbody></table></div>
    </details>
  </div>
  <footer>Times are shown in seconds. Missing measurements are displayed as — and are excluded from statistics. Page-level relationships include only keys present in both page JSON files.</footer>
</main>
<script>{plotly_js}</script>
<script>
{''.join(chart_scripts)}
document.querySelectorAll('#chart-filters input').forEach(input => {{
  input.addEventListener('change', () => {{
    const enabled = new Set([...document.querySelectorAll('#chart-filters input:checked')].map(el => el.value));
    document.querySelectorAll('.chart-card').forEach(card => {{
      card.hidden = !enabled.has(card.dataset.category);
    }});
    window.dispatchEvent(new Event('resize'));
  }});
}});
document.getElementById('doc-search').addEventListener('input', event => {{
  const query = event.target.value.toLowerCase();
  document.querySelectorAll('#documents-table tbody tr').forEach(row => {{
    row.hidden = !row.cells[0].textContent.toLowerCase().includes(query);
  }});
}});

const documentTableBody = document.querySelector('#documents-table tbody');
document.querySelectorAll('#documents-table .sort-button').forEach((button, columnIndex) => {{
  let ascending = true;
  button.addEventListener('click', () => {{
    const rows = [...documentTableBody.querySelectorAll('tr')];
    rows.sort((a, b) => {{
      const aText = a.cells[columnIndex]?.textContent.trim() ?? '';
      const bText = b.cells[columnIndex]?.textContent.trim() ?? '';
      let comparison;
      if (button.dataset.sort === 'number') {{
        const aValue = aText === '—' ? Number.NEGATIVE_INFINITY : Number(aText.replaceAll(',', ''));
        const bValue = bText === '—' ? Number.NEGATIVE_INFINITY : Number(bText.replaceAll(',', ''));
        comparison = aValue - bValue;
      }} else {{
        comparison = aText.localeCompare(bText, undefined, {{numeric:true, sensitivity:'base'}});
      }}
      return ascending ? comparison : -comparison;
    }});
    rows.forEach(row => documentTableBody.appendChild(row));
    document.querySelectorAll('#documents-table .sort-button').forEach(other => {{
      other.textContent = other.textContent.replace(/[↑↓↕]/g, '').trim() + ' ↕';
    }});
    button.textContent = button.textContent.replace(/[↑↓↕]/g, '').trim() + (ascending ? ' ↑' : ' ↓');
    ascending = !ascending;
  }});
}});

document.getElementById('download-csv').addEventListener('click', () => {{
  const rows = [...document.querySelectorAll('#documents-table tr')].filter(row => !row.hidden);
  const csv = rows.map(row => [...row.cells].map(cell => '"' + cell.textContent.trim().replaceAll('"','""') + '"').join(',')).join('\\r\\n');
  const blob = new Blob([csv], {{type:'text/csv;charset=utf-8;'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'document_measurements.csv'; a.click();
  URL.revokeObjectURL(url);
}});
</script>
</body>
</html>
"""
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Built {OUTPUT_FILE}")
    print(
        f"Documents: {total_docs:,} | Pages: {total_pages:,} | Errors: {len(errors):,}"
    )


if __name__ == "__main__":
    main()
