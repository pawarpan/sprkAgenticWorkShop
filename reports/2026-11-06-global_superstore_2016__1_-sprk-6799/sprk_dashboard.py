"""SPRK interactive dashboard builder - 2 basic, filterable bar-chart reports.

Usage (in analysis.py):
    import sprk_dashboard as sd
    r1 = sd.bar_report(df, x="Region", y="Sales", agg="sum", filter_col="Product",
                       title="Total sales by region", caption="Pick a product in the dropdown")
    r2 = sd.bar_report(df, x="Product", y=None, agg="count", filter_col="Region",
                       title="Orders by product", caption="Pick a region in the dropdown")
    sd.build_dashboard(out_path, title, subtitle, kpis, [r1, r2], insights, table_df)

    bar_report(df, x, y=None, agg="sum", filter_col=None, title=None, caption="", top_n=20)
        x          : category column for the bars (convert dates to e.g. a 'Month' text column first)
        y          : numeric column to aggregate; None means count rows
        agg        : "sum", "mean", "median", "min", "max" or "count"
        filter_col : category column used for the interactive dropdown filter
                     (None -> dropdown switches between Top 5 / Top 10 / Top N bars)
    build_dashboard needs EXACTLY 2 reports, both made by bar_report.
    kpis     : list of (label, value_text) tuples, 3-5 items
    insights : list of strings
    table_df : DataFrame shown as a searchable, sortable table (first 200 rows)

All HTML, CSS and JavaScript live in this module; analysis.py never writes HTML itself.
"""
import html as _html
import os

import plotly.graph_objects as go
import plotly.io as pio

MAX_POINTS_PER_CHART = 10000
REQUIRED_REPORTS = 2
MAX_FILTER_VALUES = 25


def bar_report(df, x, y=None, agg="sum", filter_col=None, title=None, caption="", top_n=20, wide=False):
    """Build one basic bar chart with an interactive dropdown filter."""
    for col in [c for c in (x, y, filter_col) if c is not None]:
        if col not in df.columns:
            raise KeyError("Column %r not found. Available columns: %s" % (col, list(df.columns)))
    if y is None:
        agg = "count"
    if agg not in ("sum", "mean", "median", "min", "max", "count"):
        raise ValueError("agg must be sum, mean, median, min, max or count")
    if agg != "count" and not str(df[y].dtype).startswith(("int", "float", "uint")):
        raise TypeError("Column %r is not numeric; use agg='count' or convert it first" % y)

    def aggregate(d):
        s = d.groupby(x).size() if agg == "count" else d.groupby(x)[y].agg(agg)
        return s.sort_values(ascending=False).head(top_n)

    y_label = "Count of rows" if agg == "count" else "%s of %s" % (agg.capitalize(), y)
    hover = "%{x}<br>" + y_label + ": %{y:,.2f}<extra></extra>"
    fig = go.Figure()
    buttons = []
    if filter_col is not None:
        values = list(df[filter_col].dropna().value_counts().index[:MAX_FILTER_VALUES])
        groups = [("All " + str(filter_col), df)] + [(str(v), df[df[filter_col] == v]) for v in values]
        dropdown_label = "Filter by " + str(filter_col)
    else:
        full = aggregate(df)
        groups = [("All %d" % len(full), len(full))] + [("Top %d" % k, k) for k in (10, 5, 3) if k < len(full)]
        dropdown_label = "Show"
    for i, (label, sub) in enumerate(groups):
        s = aggregate(sub) if filter_col is not None else full.head(sub)
        fig.add_bar(x=[str(v) for v in s.index], y=list(s.values), name=label,
                    visible=(i == 0), hovertemplate=hover)
    for i, (label, _) in enumerate(groups):
        buttons.append(dict(label=label, method="update",
                            args=[{"visible": [j == i for j in range(len(groups))]}]))
    fig.update_layout(
        showlegend=False, xaxis_title=str(x), yaxis_title=y_label, margin=dict(t=70),
        updatemenus=[dict(type="dropdown", buttons=buttons, showactive=True, active=0,
                          x=1, xanchor="right", y=1.2, yanchor="top")],
        annotations=[dict(text=dropdown_label + ":", x=1, xref="paper", xanchor="right",
                          xshift=-150, y=1.17, yref="paper", yanchor="top", showarrow=False)])
    return {"title": title or y_label + " by " + str(x), "caption": caption, "fig": fig,
            "wide": wide, "_bar_report": True}

_CSS = """
:root { --bg:#f5f7fb; --card:#ffffff; --ink:#1f2937; --muted:#6b7280; --line:#e5e7eb; --accent:#2563eb; }
* { box-sizing: border-box; }
body { margin:0; font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; background:var(--bg); color:var(--ink); }
header { padding:28px 24px 8px; max-width:1400px; margin:0 auto; }
header h1 { margin:0 0 6px; font-size:28px; }
header p { margin:0; color:var(--muted); }
main { max-width:1400px; margin:0 auto; padding:16px 24px 40px; }
.kpis { display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:14px; margin-bottom:20px; }
.kpi { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px 18px; }
.kpi .label { color:var(--muted); font-size:13px; text-transform:uppercase; letter-spacing:.04em; }
.kpi .value { font-size:26px; font-weight:700; margin-top:6px; }
.grid { display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:16px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px; min-width:0; }
.card h2 { margin:0 0 4px; font-size:17px; }
.card .caption { margin:0 0 8px; color:var(--muted); font-size:13px; }
.card.wide { grid-column:1 / -1; }
.insights ol { margin:8px 0 0; padding-left:20px; line-height:1.6; }
.table-tools { display:flex; gap:10px; align-items:center; margin:8px 0 10px; flex-wrap:wrap; }
.table-tools input { padding:8px 10px; border:1px solid var(--line); border-radius:8px; min-width:240px; font-size:14px; }
.table-tools span { color:var(--muted); font-size:13px; }
.table-wrap { overflow:auto; max-height:520px; border:1px solid var(--line); border-radius:8px; }
table.sprk-table { border-collapse:collapse; width:100%; font-size:13px; }
table.sprk-table th { position:sticky; top:0; background:#eef2ff; cursor:pointer; user-select:none; white-space:nowrap; }
table.sprk-table th, table.sprk-table td { padding:8px 10px; border-bottom:1px solid var(--line); text-align:left; }
table.sprk-table th.asc::after { content:" \\25B2"; font-size:10px; }
table.sprk-table th.desc::after { content:" \\25BC"; font-size:10px; }
table.sprk-table tbody tr:hover { background:#f9fafb; }
footer { text-align:center; color:var(--muted); font-size:12px; padding:20px; }
@media (max-width: 900px) { .grid { grid-template-columns:1fr; } header h1 { font-size:22px; } }
"""

_JS = """
(function () {
  var table = document.getElementById('sprk-table');
  if (!table) return;
  var tbody = table.tBodies[0];
  var rows = Array.prototype.slice.call(tbody.rows);
  var search = document.getElementById('sprk-search');
  var count = document.getElementById('sprk-count');
  function updateCount() {
    var shown = rows.filter(function (r) { return r.style.display !== 'none'; }).length;
    count.textContent = shown + ' of ' + rows.length + ' rows';
  }
  search.addEventListener('input', function () {
    var q = search.value.toLowerCase();
    rows.forEach(function (r) { r.style.display = r.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none'; });
    updateCount();
  });
  var headers = table.tHead.rows[0].cells;
  Array.prototype.forEach.call(headers, function (th, idx) {
    th.title = 'Click to sort';
    th.addEventListener('click', function () {
      var asc = !th.classList.contains('asc');
      Array.prototype.forEach.call(headers, function (h) { h.classList.remove('asc', 'desc'); });
      th.classList.add(asc ? 'asc' : 'desc');
      rows.sort(function (a, b) {
        var x = a.cells[idx].textContent.trim(), y = b.cells[idx].textContent.trim();
        var nx = parseFloat(x.replace(/,/g, '')), ny = parseFloat(y.replace(/,/g, ''));
        var cmp = (!isNaN(nx) && !isNaN(ny)) ? nx - ny : x.localeCompare(y);
        return asc ? cmp : -cmp;
      });
      rows.forEach(function (r) { tbody.appendChild(r); });
    });
  });
  updateCount();
})();
"""

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@TITLE@@</title>
<style>@@CSS@@</style>
</head>
<body>
<header><h1>@@TITLE@@</h1><p>@@SUBTITLE@@</p></header>
<main>
<section class="kpis">@@KPIS@@</section>
<section class="grid">@@REPORTS@@</section>
<section class="card wide insights" style="margin-top:16px"><h2>Key insights</h2><ol>@@INSIGHTS@@</ol></section>
<section class="card wide" style="margin-top:16px">
<h2>Data</h2>
<div class="table-tools"><input id="sprk-search" type="search" placeholder="Search rows..."><span id="sprk-count"></span></div>
<div class="table-wrap">@@TABLE@@</div>
</section>
</main>
<footer>Generated automatically by the SPRK agentic analysis workflow.</footer>
<script>@@JS@@</script>
</body>
</html>
"""


def add_category_filter(fig, label="All"):
    """Add a dropdown that shows all traces or one trace at a time.

    Works on figures that have one trace per category, e.g.
    px.line(df, x=..., y=..., color="Region") or px.bar(df, x=..., y=..., color="Region").
    """
    names = [t.name for t in fig.data]
    unique = [n for n in dict.fromkeys(names) if n not in (None, "")]
    if len(unique) < 2:
        return fig
    buttons = [dict(label=label, method="update", args=[{"visible": [True] * len(names)}])]
    for n in unique:
        buttons.append(dict(label=str(n), method="update",
                            args=[{"visible": [x == n for x in names]}]))
    fig.update_layout(updatemenus=[dict(type="dropdown", buttons=buttons, showactive=True,
                                        x=1, xanchor="right", y=1.22, yanchor="top")],
                      margin=dict(t=80))
    return fig


def add_time_controls(fig):
    """Add a range slider and quick range buttons to a figure whose x-axis is dates."""
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(buttons=[
            dict(count=1, label="1M", step="month", stepmode="backward"),
            dict(count=3, label="3M", step="month", stepmode="backward"),
            dict(count=6, label="6M", step="month", stepmode="backward"),
            dict(count=1, label="1Y", step="year", stepmode="backward"),
            dict(step="all", label="All"),
        ]))
    return fig


def _esc(v):
    return _html.escape("" if v is None else str(v))


def build_dashboard(out_path, title, subtitle, kpis, reports, insights, table_df, max_rows=200):
    """Write the interactive dashboard to out_path and return a small summary dict."""
    if len(reports) != REQUIRED_REPORTS:
        raise ValueError("build_dashboard needs exactly %d reports, got %d"
                         % (REQUIRED_REPORTS, len(reports)))
    for i, r in enumerate(reports):
        if not isinstance(r.get("fig"), go.Figure):
            raise TypeError("reports[%d]['fig'] must be a plotly Figure" % i)
        if not r.get("_bar_report") or any(t.type != "bar" for t in r["fig"].data):
            raise ValueError("Report %d must be a bar chart made with sd.bar_report(...)" % (i + 1))
        if not r["fig"].layout.updatemenus:
            raise ValueError("Report %d has no interactive filter; build it with sd.bar_report(...)" % (i + 1))
        points = 0
        for tr in r["fig"].data:
            sizes = [len(v) for v in (getattr(tr, "x", None), getattr(tr, "y", None)) if v is not None]
            points += max(sizes) if sizes else 0
        if points > MAX_POINTS_PER_CHART:
            raise ValueError(
                "Report %d (%r) plots %d raw data points; the limit is %d per chart. "
                "Aggregate first (groupby/resample, value_counts, or np.histogram + px.bar, "
                "df.sample(2000) for scatter) so the HTML stays small."
                % (i + 1, r.get("title"), points, MAX_POINTS_PER_CHART))

    kpi_html = "".join(
        '<div class="kpi"><div class="label">%s</div><div class="value">%s</div></div>'
        % (_esc(label), _esc(value)) for label, value in kpis)

    report_html = []
    for i, r in enumerate(reports):
        fig = r["fig"]
        fig.update_layout(template="plotly_white", height=r.get("height", 430),
                          margin=dict(l=40, r=20, b=40, t=fig.layout.margin.t or 40))
        div = pio.to_html(fig, full_html=False, include_plotlyjs="cdn" if i == 0 else False,
                          config={"responsive": True, "displaylogo": False})
        wide = " wide" if r.get("wide") else ""
        report_html.append('<div class="card%s"><h2>%s</h2><p class="caption">%s</p>%s</div>'
                           % (wide, _esc(r.get("title", "Report %d" % (i + 1))),
                              _esc(r.get("caption", "")), div))

    insight_html = "".join("<li>%s</li>" % _esc(s) for s in insights)
    table_html = table_df.head(max_rows).to_html(index=False, border=0, table_id="sprk-table",
                                                 classes="sprk-table", na_rep="", escape=True)

    page = (_PAGE.replace("@@CSS@@", _CSS).replace("@@JS@@", _JS)
                 .replace("@@TITLE@@", _esc(title)).replace("@@SUBTITLE@@", _esc(subtitle))
                 .replace("@@KPIS@@", kpi_html).replace("@@INSIGHTS@@", insight_html)
                 .replace("@@TABLE@@", table_html).replace("@@REPORTS@@", "".join(report_html)))

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    return {"path": out_path, "bytes": os.path.getsize(out_path),
            "charts": page.count('class="plotly-graph-div"')}
