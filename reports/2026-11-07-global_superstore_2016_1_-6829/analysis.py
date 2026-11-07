
import json, html, string

PAGE = string.Template("""<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>$title</title><script src=\"https://cdn.plot.ly/plotly-2.35.2.min.js\"></script>
<style>body{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f5f7fb;color:#1f2937}header{background:#102542;color:#fff;padding:20px 28px}
h1{margin:0 0 4px;font-size:24px}main{max-width:1200px;margin:auto;padding:20px}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px}.kpi span{color:#6b7280;font-size:13px}.kpi b{display:block;font-size:24px;margin-top:4px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}@media(max-width:800px){.grid{grid-template-columns:1fr}}
h3{margin:0 0 6px}label{font-size:13px;color:#6b7280}select{padding:6px;margin:6px 0 4px;border-radius:6px}
table{border-collapse:collapse;width:100%;font-size:13px}td,th{border-bottom:1px solid #eee;padding:6px;text-align:left}th{background:#eef2ff}</style></head>
<body><header><h1>$title</h1><div>$subtitle</div></header><main>
<div class=\"kpis\">$kpis</div><div class=\"grid\">$charts</div>
<div class=\"card\" style=\"margin-top:16px\"><h3>Key insights</h3><ol>$insights</ol></div>
<div class=\"card\" style=\"margin-top:16px\"><h3>Data preview</h3><div style=\"overflow:auto\">$table</div></div></main>
<script>const R=$data;R.forEach((r,i)=>{const s=document.getElementById('f'+i);Object.keys(r.series).forEach(k=>s.add(new Option(k,k)));
const draw=()=>{const d=r.series[s.value];Plotly.react('c'+i,[{type:'bar',x:d[0],y:d[1],marker:{color:'#1A8FD0'}}],
{margin:{t:10,l:60,r:10,b:90},yaxis:{title:{text:r.ylabel}},xaxis:{title:{text:r.xlabel}}},{responsive:true,displaylogo:false})};s.onchange=draw;draw()});</script>
</body></html>""")


def bar_report(df, x, y=None, agg="sum", filter_col=None, title="", top_n=15):
    """One bar chart (x = category column). y=None counts rows. filter_col adds a dropdown filter."""
    def series(d):
        s = d.groupby(x).size() if y is None else d.groupby(x)[y].agg(agg)
        s = s.sort_values(ascending=False).head(top_n)
        return [[str(v) for v in s.index], [round(float(v), 2) for v in s.values]]
    out = {"All": series(df)}
    if filter_col:
        for v in df[filter_col].dropna().value_counts().index[:20]:
            out[str(v)] = series(df[df[filter_col] == v])
    return {"title": title, "filter": filter_col or "", "xlabel": str(x),
            "ylabel": "Count of rows" if y is None else f"{agg} of {y}", "series": out}


def build_dashboard(path, title, subtitle, kpis, reports, insights, df):
    """kpis: list of (label, value_text). reports: exactly 2 bar_report results. insights: list of strings."""
    assert len(reports) == 2, "exactly 2 reports"
    e = lambda t: html.escape(str(t))
    charts = "".join(
        f'<div class="card"><h3>{e(r["title"])}'</div><label>Filter by {e(r["filter"] or "view")}: </label>'
        f'<select id="f{i}"></select><div id="c{i}" style="height:380px"></div></div>' for i, r in enumerate(reports))
    page = PAGE.substitute(
        title=e(title), subtitle=e(subtitle),
        kpis="".join(f'<div class="card kpi"><span>{e(a)}</span><b>{e(b)}</b></div>' for a, b in kpis),
        charts=charts, insights="".join(f"<li>{e(t)}</li>" for t in insights),
        table=df.iloc[:15, :12].to_html(index=False, border=0, na_rep=""),
        data=json.dumps(reports, separators=(",", ":")).replace("</", "<\/"))
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return len(page.encode("utf-8"))

import pandas as pd
INPUT = "/content/sprk/run-6829/input.xlsx"
# Load the main Orders sheet
df = pd.read_excel(INPUT, sheet_name="Orders")
# Clean data: fill missing Postal Code with -1, ensure numeric columns are correct
df["Postal Code"] = df["Postal Code"].fillna(-1).astype(int)
df["Order Date"] = pd.to_datetime(df["Order Date"])
df["Ship Date"] = pd.to_datetime(df["Ship Date"])
# KPIs
kpis = [
    ("Total Orders", f"{len(df):,}"),
    ("Total Sales", f"${df['Sales'].sum():,.2f}"),
    ("Total Profit", f"${df['Profit'].sum():,.2f}"),
    ("Unique Customers", f"{df['Customer ID'].nunique():,}"),
    ("Countries", f"{df['Country'].nunique()}"),
]
# Insights
insights = [
    f"Top country by sales: {df.groupby('Country')['Sales'].sum().idxmax()} (${df.groupby('Country')['Sales'].sum().max():,.2f})",
    f"Most common segment: {df['Segment'].mode()[0]} ({df['Segment'].value_counts().max():,} orders)",
    f"Highest profit product: {df.groupby('Product Name')['Profit'].sum().idxmax()} (${df.groupby('Product Name')['Profit'].sum().max():,.2f})",
    f"Average discount: {df['Discount'].mean():.2%}",
    f"Most used ship mode: {df['Ship Mode'].mode()[0]} ({df['Ship Mode'].value_counts().max():,} orders)",
]
# Report 1: Sales by Category, filter by Region
r1 = bar_report(df, x="Category", y="Sales", agg="sum", filter_col="Region", title="Sales by Category (filter by Region)")
# Report 2: Orders by Country, filter by Segment
r2 = bar_report(df, x="Country", y=None, agg="count", filter_col="Segment", title="Order Count by Country (filter by Segment)")
title = "Global Superstore 2016 Orders Analysis"
subtitle = "Analysis of 51,292 orders from the Global Superstore dataset."
size = build_dashboard("/content/sprk/run-6829/report.html", title, subtitle, kpis, [r1, r2], insights, df)
print("DONE", size)
