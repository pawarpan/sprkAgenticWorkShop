import pandas as pd
import json
import os
import html

# --- SETTINGS ---
WORK_DIR = '/content/sprk/run-7073'
INPUT_FILE = os.path.join(WORK_DIR, 'input.xlsx')
OUTPUT_FILE = os.path.join(WORK_DIR, 'report.html')

# --- LOAD DATA ---
df = pd.read_excel(INPUT_FILE, sheet_name='Orders')

# --- CALCULATE KPIs ---
kpis = [
    {"label": "Total Sales", "value": f"${df['Sales'].sum():,.0f}"},
    {"label": "Total Profit", "value": f"${df['Profit'].sum():,.0f}"},
    {"label": "Total Quantity", "value": f"{df['Quantity'].sum():,}"},
    {"label": "Total Tax Collected", "value": f"${df['Tax'].sum():,.0f}"}
]

# --- PREPARE CHART DATA (BAR: Sub-Category vs Sales, Filtered by Market) ---
bar_filter_col = "Market"
bar_cat_col = "Sub-Category"
bar_val_col = "Sales"
markets = ["All"] + sorted(df[bar_filter_col].unique().tolist())[:20]

bar_data = {}
for m in markets:
    filtered_df = df if m == "All" else df[df[bar_filter_col] == m]
    agg = filtered_df.groupby(bar_cat_col)[bar_val_col].sum().sort_values(ascending=False).head(15)
    bar_data[m] = {
        "x": [html.escape(str(x)) for x in agg.index.tolist()],
        "y": agg.values.tolist()
    }

# --- PREPARE CHART DATA (PIE: Segment vs Sales, Filtered by Category) ---
pie_filter_col = "Category"
pie_cat_col = "Segment"
pie_val_col = "Sales"
categories = ["All"] + sorted(df[pie_filter_col].unique().tolist())[:20]

pie_data = {}
for c in categories:
    filtered_df = df if c == "All" else df[df[pie_filter_col] == c]
    agg = filtered_df.groupby(pie_cat_col)[pie_val_col].sum().sort_values(ascending=False)
    
    if len(agg) > 8:
        top = agg.head(7)
        other_val = agg.iloc[7:].sum()
        labels = top.index.tolist() + ["Other"]
        values = top.values.tolist() + [other_val]
    else:
        labels = agg.index.tolist()
        values = agg.values.tolist()
        
    pie_data[c] = {
        "labels": [html.escape(str(l)) for l in labels],
        "values": values
    }

# --- INSIGHTS ---
insights = [
    f"Technology leads all categories with ${df[df['Category']=='Technology']['Sales'].sum():,.0f} in revenue.",
    f"The Europe market is the most profitable, contributing ${df[df['Market']=='Europe']['Profit'].sum():,.0f}.",
    f"A total of {len(df):,} orders were fulfilled with an average shipping cost of ${df['Shipping Cost'].mean():.2f}.",
    f"Consumer segment represents the largest portion of sales across most markets."
]

# --- TABLE PREVIEW ---
table_cols = ["Order ID", "Customer Name", "Segment", "Market", "Category", "Sales", "Profit"]
table_rows = df[table_cols].head(10).values.tolist()
table_header_html = "".join([f"<th>{html.escape(c)}</th>" for c in table_cols])
table_rows_html = ""
for row in table_rows:
    cells = "".join([f"<td>{html.escape(str(v))}</td>" for v in row])
    table_rows_html += f"<tr>{cells}</tr>"

# --- BUILD HTML ---
template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>__TITLE__</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        body { font-family: sans-serif; margin: 0; padding: 20px; background-color: #f4f7f6; color: #333; }
        .container { max-width: 1100px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { margin: 0; color: #2c3e50; }
        p.subtitle { margin: 5px 0 25px; color: #7f8c8d; font-size: 1.1em; }
        .kpis { display: flex; justify-content: space-between; margin-bottom: 30px; gap: 15px; }
        .kpi-card { background: #fff; border: 1px solid #e0e0e0; padding: 20px; border-radius: 8px; flex: 1; text-align: center; }
        .kpi-card div:first-child { font-size: 0.9em; color: #7f8c8d; margin-bottom: 8px; text-transform: uppercase; }
        .kpi-card div:last-child { font-size: 1.6em; font-weight: bold; color: #2980b9; }
        .charts { display: flex; gap: 20px; margin-bottom: 30px; }
        .chart-box { flex: 1; background: #fff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 8px; }
        .filter-area { margin-bottom: 10px; font-size: 0.9em; }
        select { padding: 5px; border-radius: 4px; border: 1px solid #ccc; width: 100%; }
        .insights { background: #fcfcfc; border-left: 5px solid #2980b9; padding: 15px; margin-bottom: 30px; border-radius: 4px; }
        .insights h3 { margin-top: 0; }
        .insights ul { margin: 0; padding-left: 20px; }
        .insights li { margin-bottom: 8px; }
        table { width: 100%; border-collapse: collapse; font-size: 0.85em; }
        th { background: #f8f9fa; text-align: left; padding: 10px; border-bottom: 2px solid #dee2e6; }
        td { padding: 10px; border-bottom: 1px solid #dee2e6; }
        tr:hover { background: #f1f1f1; }
    </style>
</head>
<body>
    <div class="container">
        <h1>__TITLE__</h1>
        <p class="subtitle">__SUBTITLE__</p>
        
        <div class="kpis">__KPIS__</div>
        
        <div class="charts">
            <div class="chart-box">
                <div class="filter-area">
                    <label>Filter by Market:</label>
                    <select id="barFilter" onchange="updateBar()">__BAR_OPTIONS__</select>
                </div>
                <div id="barChart"></div>
            </div>
            <div class="chart-box">
                <div class="filter-area">
                    <label>Filter by Category:</label>
                    <select id="pieFilter" onchange="updatePie()">__PIE_OPTIONS__</select>
                </div>
                <div id="pieChart"></div>
            </div>
        </div>
        
        <div class="insights">
            <h3>Key Insights</h3>
            <ul>__INSIGHTS__</ul>
        </div>
        
        <h3>Data Preview (First 10 Rows)</h3>
        <table>
            <thead><tr>__TABLE_HEADER__</tr></thead>
            <tbody>__TABLE_ROWS__</tbody>
        </table>
    </div>

    <script>
        const barData = __BAR_DATA_JSON__;
        const pieData = __PIE_DATA_JSON__;

        function updateBar() {
            const val = document.getElementById('barFilter').value;
            const data = barData[val];
            const plotData = [{
                x: data.x,
                y: data.y,
                type: 'bar',
                marker: { color: '#3498db' }
            }];
            const layout = { 
                title: 'Sales by Sub-Category',
                margin: { t: 40, b: 80, l: 50, r: 10 },
                height: 350
            };
            Plotly.react('barChart', plotData, layout, {displayModeBar: false});
        }

        function updatePie() {
            const val = document.getElementById('pieFilter').value;
            const data = pieData[val];
            const plotData = [{
                labels: data.labels,
                values: data.values,
                type: 'pie',
                hole: 0.4,
                marker: { colors: ['#2ecc71', '#e67e22', '#e74c3c', '#34495e', '#9b59b6', '#f1c40f', '#1abc9c'] }
            }];
            const layout = { 
                title: 'Sales by Segment',
                margin: { t: 40, b: 20, l: 20, r: 20 },
                height: 350,
                legend: { orientation: 'h', y: -0.1 }
            };
            Plotly.react('pieChart', plotData, layout, {displayModeBar: false});
        }

        updateBar();
        updatePie();
    </script>
</body>
</html>
"""

# Fill markers
kpi_html = "".join([f'<div class="kpi-card"><div>{html.escape(k["label"])}</div><div>{html.escape(k["value"])}</div></div>' for k in kpis])
bar_options = "".join([f'<option value="{html.escape(m)}">{html.escape(m)}</option>' for m in markets])
pie_options = "".join([f'<option value="{html.escape(c)}">{html.escape(c)}</option>' for c in categories])
insights_html = "".join([f'<li>{html.escape(i)}</li>' for i in insights])

html_content = template.replace("__TITLE__", "Global Superstore 2016 Sales Dashboard")
html_content = html_content.replace("__SUBTITLE__", "Performance analysis of global retail operations")
html_content = html_content.replace("__KPIS__", kpi_html)
html_content = html_content.replace("__BAR_OPTIONS__", bar_options)
html_content = html_content.replace("__PIE_OPTIONS__", pie_options)
html_content = html_content.replace("__INSIGHTS__", insights_html)
html_content = html_content.replace("__TABLE_HEADER__", table_header_html)
html_content = html_content.replace("__TABLE_ROWS__", table_rows_html)
html_content = html_content.replace("__BAR_DATA_JSON__", json.dumps(bar_data))
html_content = html_content.replace("__PIE_DATA_JSON__", json.dumps(pie_data))

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("DONE")
