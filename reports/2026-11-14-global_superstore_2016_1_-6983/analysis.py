import os
import pandas as pd
import numpy as np
import json
import html

# === SETTINGS ===
WORK_DIR = '/content/sprk/run-6983'
INPUT_FILE = os.path.join(WORK_DIR, 'input.xlsx')
OUTPUT_FILE = os.path.join(WORK_DIR, 'report.html')

# === LOAD DATA ===
orders = pd.read_excel(INPUT_FILE, sheet_name='Orders')
returns = pd.read_excel(INPUT_FILE, sheet_name='Returns')

# === KPIs ===
total_sales = orders['Sales'].sum()
total_profit = orders['Profit'].sum()
num_orders = orders['Order ID'].nunique()
avg_discount = orders['Discount'].mean()
num_returns = returns['Order ID'].nunique()

# === Insights ===
best_subcat = orders.groupby('Sub-Category')['Sales'].sum().idxmax()
best_subcat_sales = orders.groupby('Sub-Category')['Sales'].sum().max()
most_prof_segment = orders.groupby('Segment')['Profit'].sum().idxmax()
most_prof_segment_profit = orders.groupby('Segment')['Profit'].sum().max()
return_rate = num_returns / num_orders * 100
max_region = orders.groupby('Region')['Sales'].sum().idxmax()
max_region_sales = orders.groupby('Region')['Sales'].sum().max()

insights = [
    f"Best-selling sub-category: {html.escape(str(best_subcat))} (${best_subcat_sales:,.0f} in sales)",
    f"Most profitable segment: {html.escape(str(most_prof_segment))} (${most_prof_segment_profit:,.0f} in profit)",
    f"Return rate: {return_rate:.2f}% of orders were returned",
    f"Region with highest sales: {html.escape(str(max_region))} (${max_region_sales:,.0f})",
]

# === BAR CHART DATA ===
bar_category = 'Sub-Category'
bar_value = 'Sales'
bar_filter = 'Region'
bar_filter_values = ['All'] + sorted(orders[bar_filter].dropna().unique().tolist())[:20]
bar_data = {}
for region in bar_filter_values:
    if region == 'All':
        df = orders
    else:
        df = orders[orders[bar_filter] == region]
    top = df.groupby(bar_category)[bar_value].sum().sort_values(ascending=False).head(15)
    bar_data[region] = {
        'labels': [html.escape(str(x)) for x in top.index],
        'values': [float(x) for x in top.values],
    }

# === PIE CHART DATA ===
pie_category = 'Segment'
pie_value = 'Profit'
pie_filter = 'Order Priority'
pie_filter_values = ['All'] + sorted(orders[pie_filter].dropna().unique().tolist())[:20]
pie_data = {}
for priority in pie_filter_values:
    if priority == 'All':
        df = orders
    else:
        df = orders[orders[pie_filter] == priority]
    seg = df.groupby(pie_category)[pie_value].sum().sort_values(ascending=False)
    seg = seg.head(7)
    other = df[pie_value].sum() - seg.sum()
    labels = [html.escape(str(x)) for x in seg.index]
    values = [float(x) for x in seg.values]
    if other > 0 and len(seg) == 7:
        labels.append('Other')
        values.append(float(other))
    pie_data[priority] = {
        'labels': labels,
        'values': values,
    }

# === PREVIEW TABLE ===
preview_cols = orders.columns.tolist()
preview_rows = orders.head(10).fillna('').values.tolist()
preview_table = {
    'columns': [html.escape(str(c)) for c in preview_cols],
    'rows': [[html.escape(str(cell)) for cell in row] for row in preview_rows],
}

# === DATA BLOCK ===
data_block = json.dumps({
    'bar_data': bar_data,
    'bar_filter_values': bar_filter_values,
    'pie_data': pie_data,
    'pie_filter_values': pie_filter_values,
    'kpis': [
        {'label': 'Total Sales', 'value': f"${total_sales:,.0f}"},
        {'label': 'Total Profit', 'value': f"${total_profit:,.0f}"},
        {'label': 'Number of Orders', 'value': f"{num_orders:,}"},
        {'label': 'Average Discount', 'value': f"{avg_discount:.2%}"},
        {'label': 'Returned Orders', 'value': f"{num_returns:,}"},
    ],
    'insights': insights,
    'preview_table': preview_table,
})

# === HTML PAGE ===
page = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Global Superstore 2016 Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f8f9fa; }
.container { max-width: 1200px; margin: 30px auto; background: #fff; padding: 24px 32px 32px 32px; border-radius: 12px; box-shadow: 0 2px 12px #0001; }
h1 { font-size: 2.2em; margin-bottom: 0.2em; }
h2 { font-size: 1.3em; margin-top: 2em; }
.subtitle { color: #666; margin-bottom: 1.5em; }
.kpis { display: flex; gap: 24px; margin-bottom: 2em; }
.kpi { background: #f1f3f6; border-radius: 8px; padding: 18px 24px; flex: 1; text-align: center; }
.kpi-label { color: #888; font-size: 1em; }
.kpi-value { font-size: 1.5em; font-weight: bold; margin-top: 0.2em; }
.charts { display: flex; gap: 32px; }
.chart-block { flex: 1; background: #f9fafb; border-radius: 8px; padding: 18px 18px 12px 18px; }
.dropdown { margin-bottom: 10px; }
ul.insights { margin: 1em 0 2em 1.2em; color: #333; }
table.preview { border-collapse: collapse; width: 100%; margin-top: 1em; }
table.preview th, table.preview td { border: 1px solid #ddd; padding: 6px 8px; }
table.preview th { background: #f1f3f6; }
@media (max-width: 900px) { .charts { flex-direction: column; } }
</style>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
</head>
<body>
<div class="container">
<h1>__TITLE__</h1>
<div class="subtitle">__SUBTITLE__</div>
<div class="kpis">__KPIS__</div>
<div class="charts">
  <div class="chart-block">
    <div><label for="bar-filter">Filter by Region:</label>
      <select id="bar-filter" class="dropdown"></select></div>
    <div id="bar-chart" style="height:370px;"></div>
  </div>
  <div class="chart-block">
    <div><label for="pie-filter">Filter by Order Priority:</label>
      <select id="pie-filter" class="dropdown"></select></div>
    <div id="pie-chart" style="height:370px;"></div>
  </div>
</div>
<h2>Key Insights</h2>
<ul class="insights">__INSIGHTS__</ul>
<h2>Preview of Data</h2>
<table class="preview">
<thead><tr>__PREVIEW_HEADER__</tr></thead>
<tbody>__PREVIEW_ROWS__</tbody>
</table>
</div>
<script>
const DATA = __DATA__;
function fillDropdown(id, values) {
  const sel = document.getElementById(id);
  sel.innerHTML = '';
  for (const v of values) {
    const opt = document.createElement('option');
    opt.value = v; opt.textContent = v;
    sel.appendChild(opt);
  }
}
function drawBar(region) {
  const d = DATA.bar_data[region];
  Plotly.react('bar-chart', [{
    x: d.labels,
    y: d.values,
    type: 'bar',
    marker: {color: '#4e79a7'},
  }], {
    title: 'Top 15 Sub-Categories by Sales',
    xaxis: {title: 'Sub-Category'},
    yaxis: {title: 'Sales', tickprefix: '$'},
    margin: {t: 40, l: 60, r: 10, b: 90},
  }, {responsive: true});
}
function drawPie(priority) {
  const d = DATA.pie_data[priority];
  Plotly.react('pie-chart', [{
    labels: d.labels,
    values: d.values,
    type: 'pie',
    textinfo: 'label+percent',
    marker: {colors: ['#f28e2b','#e15759','#76b7b2','#59a14f','#edc949','#af7aa1','#ff9da7','#9c755f']},
  }], {
    title: 'Profit by Segment',
    margin: {t: 40, l: 10, r: 10, b: 10},
    legend: {orientation: 'h'},
  }, {responsive: true});
}
document.addEventListener('DOMContentLoaded', function() {
  fillDropdown('bar-filter', DATA.bar_filter_values);
  fillDropdown('pie-filter', DATA.pie_filter_values);
  drawBar(DATA.bar_filter_values[0]);
  drawPie(DATA.pie_filter_values[0]);
  document.getElementById('bar-filter').onchange = e => drawBar(e.target.value);
  document.getElementById('pie-filter').onchange = e => drawPie(e.target.value);
});
</script>
</body>
</html>
'''

# Fill markers
page = page.replace('__TITLE__', 'Global Superstore 2016 Dashboard')
page = page.replace('__SUBTITLE__', 'Interactive summary of sales, profit, and returns by product, region, and segment.')
# KPIs
kpi_html = ''.join([f'<div class="kpi"><div class="kpi-label">{html.escape(k["label"])}</div><div class="kpi-value">{html.escape(str(k["value"]))}</div></div>' for k in json.loads(data_block)['kpis']])
page = page.replace('__KPIS__', kpi_html)
# Insights
insights_html = ''.join([f'<li>{html.escape(i)}</li>' for i in json.loads(data_block)['insights']])
page = page.replace('__INSIGHTS__', insights_html)
# Preview table
preview = json.loads(data_block)['preview_table']
header_html = ''.join([f'<th>{c}</th>' for c in preview['columns']])
rows_html = ''.join(['<tr>' + ''.join([f'<td>{cell}</td>' for cell in row]) + '</tr>' for row in preview['rows']])
page = page.replace('__PREVIEW_HEADER__', header_html)
page = page.replace('__PREVIEW_ROWS__', rows_html)
# Data block
page = page.replace('__DATA__', data_block)

# === SAVE ===
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(page)
size = os.path.getsize(OUTPUT_FILE)
print(f"DONE {size} bytes")
