import os
import pandas as pd
import numpy as np
import html
import json

# SETTINGS
WORK_DIR = '/content/sprk/run-6878'
INPUT_FILE = os.path.join(WORK_DIR, 'input.xlsx')
OUTPUT_FILE = os.path.join(WORK_DIR, 'report.html')

# LOAD DATA
orders = pd.read_excel(INPUT_FILE, sheet_name='Orders')

# KPIs
kpi_total_sales = orders['Sales'].sum()
kpi_total_profit = orders['Profit'].sum()
kpi_total_orders = orders['Order ID'].nunique()
kpi_total_customers = orders['Customer ID'].nunique()
kpi_avg_discount = orders['Discount'].mean()

# INSIGHTS
most_profitable_region = orders.groupby('Region')['Profit'].sum().idxmax()
most_profitable_region_profit = orders.groupby('Region')['Profit'].sum().max()
most_sales_category = orders.groupby('Category')['Sales'].sum().idxmax()
most_sales_category_sales = orders.groupby('Category')['Sales'].sum().max()
most_orders_country = orders['Country'].value_counts().idxmax()
most_orders_country_count = orders['Country'].value_counts().max()

insights = [
    f"Total sales: ${kpi_total_sales:,.0f}",
    f"Total profit: ${kpi_total_profit:,.0f}",
    f"Most profitable region: {most_profitable_region} (${most_profitable_region_profit:,.0f})",
    f"Category with highest sales: {most_sales_category} (${most_sales_category_sales:,.0f})",
    f"Country with most orders: {most_orders_country} ({most_orders_country_count:,} orders)"
]

# BAR CHART: Top 15 Sub-Category by Sales, filter by Category
bar_category_col = 'Sub-Category'
bar_value_col = 'Sales'
bar_filter_col = 'Category'
bar_filter_values = ['All'] + sorted(orders[bar_filter_col].unique())
bar_data = {}
for val in bar_filter_values:
    if val == 'All':
        df = orders
    else:
        df = orders[orders[bar_filter_col] == val]
    top = df.groupby(bar_category_col)[bar_value_col].sum().sort_values(ascending=False).head(15)
    bar_data[val] = {
        'x': [html.escape(str(x)) for x in top.index],
        'y': [float(y) for y in top.values]
    }

# PIE CHART: Market share by Region, filter by Segment
pie_category_col = 'Region'
pie_value_col = 'Sales'
pie_filter_col = 'Segment'
pie_filter_values = ['All'] + sorted(orders[pie_filter_col].unique())
pie_data = {}
for val in pie_filter_values:
    if val == 'All':
        df = orders
    else:
        df = orders[orders[pie_filter_col] == val]
    region_sales = df.groupby(pie_category_col)[pie_value_col].sum().sort_values(ascending=False)
    top7 = region_sales.head(7)
    other = region_sales.iloc[7:].sum()
    labels = [html.escape(str(x)) for x in top7.index]
    values = [float(y) for y in top7.values]
    if other > 0:
        labels.append('Other')
        values.append(float(other))
    pie_data[val] = {'labels': labels, 'values': values}

# PREVIEW TABLE
preview_cols = orders.columns[:10]
preview_rows = orders[preview_cols].head(10).fillna('').astype(str).applymap(html.escape).values.tolist()
preview_header = [html.escape(str(c)) for c in preview_cols]

# DATA BLOCK
chart_data = {
    'bar': {'data': bar_data, 'filter_col': bar_filter_col, 'filter_values': bar_filter_values},
    'pie': {'data': pie_data, 'filter_col': pie_filter_col, 'filter_values': pie_filter_values}
}

# HTML TEMPLATE
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Global Superstore 2016 Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f8f9fa; }
.container { max-width: 1200px; margin: 30px auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px #ccc; }
h1 { font-size: 2.2em; margin-bottom: 0.2em; }
h2 { font-size: 1.2em; color: #555; margin-top: 0; }
.kpis { display: flex; gap: 30px; margin: 30px 0; }
.kpi { background: #f1f3f6; padding: 18px 30px; border-radius: 8px; font-size: 1.2em; flex: 1; text-align: center; }
.charts { display: flex; gap: 30px; }
.chart-block { flex: 1; background: #f9fafb; padding: 18px 18px 10px 18px; border-radius: 8px; }
.insights { margin: 30px 0 10px 0; }
.insights ul { margin: 0; padding-left: 20px; }
.preview-table { border-collapse: collapse; width: 100%; margin-top: 18px; }
.preview-table th, .preview-table td { border: 1px solid #ddd; padding: 6px 10px; font-size: 0.97em; }
.preview-table th { background: #e9ecef; }
select { font-size: 1em; margin-bottom: 10px; padding: 4px 8px; }
@media (max-width: 900px) { .charts { flex-direction: column; } }
</style>
</head>
<body>
<div class="container">
<h1>__TITLE__</h1>
<h2>__SUBTITLE__</h2>
<div class="kpis">__KPIS__</div>
<div class="charts">
  <div class="chart-block">
    <label for="bar-filter">Filter by __BAR_FILTER__:</label>
    <select id="bar-filter"></select>
    <div id="bar-chart"></div>
  </div>
  <div class="chart-block">
    <label for="pie-filter">Filter by __PIE_FILTER__:</label>
    <select id="pie-filter"></select>
    <div id="pie-chart"></div>
  </div>
</div>
<div class="insights">
  <h3>Key Insights</h3>
  <ul>__INSIGHTS__</ul>
</div>
<h3>Preview of First 10 Rows</h3>
<table class="preview-table">
  <tr>__PREVIEW_HEADER__</tr>
  __PREVIEW_ROWS__
</table>
<script>
const chartData = __DATA__;
function fillDropdown(id, values) {
  const sel = document.getElementById(id);
  sel.innerHTML = '';
  values.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v; opt.textContent = v;
    sel.appendChild(opt);
  });
}
function drawBar(val) {
  const d = chartData.bar.data[val];
  Plotly.react('bar-chart', [{
    x: d.x, y: d.y, type: 'bar', marker: {color: '#0074D9'}
  }], {margin: {t: 30, l: 60, r: 10, b: 80}, title: 'Top 15 Sub-Categories by Sales', xaxis: {title: 'Sub-Category'}, yaxis: {title: 'Sales', tickprefix: '$'}, height: 400});
}
function drawPie(val) {
  const d = chartData.pie.data[val];
  Plotly.react('pie-chart', [{
    labels: d.labels, values: d.values, type: 'pie', textinfo: 'label+percent', hole: 0.3
  }], {margin: {t: 30, l: 10, r: 10, b: 10}, title: 'Sales Share by Region', height: 400});
}
document.addEventListener('DOMContentLoaded', function() {
  fillDropdown('bar-filter', chartData.bar.filter_values);
  fillDropdown('pie-filter', chartData.pie.filter_values);
  drawBar('All');
  drawPie('All');
  document.getElementById('bar-filter').addEventListener('change', e => drawBar(e.target.value));
  document.getElementById('pie-filter').addEventListener('change', e => drawPie(e.target.value));
});
</script>
</div>
</body>
</html>
'''

# Fill markers
html_out = html_template
html_out = html_out.replace('__TITLE__', 'Global Superstore 2016 Dashboard')
html_out = html_out.replace('__SUBTITLE__', 'Interactive dashboard for sales, profit and orders by category and region.')
html_out = html_out.replace('__KPIS__', ''.join(f'<div class="kpi">{html.escape(txt)}</div>' for txt in [
    f"Total Sales: ${kpi_total_sales:,.0f}",
    f"Total Profit: ${kpi_total_profit:,.0f}",
    f"Total Orders: {kpi_total_orders:,}",
    f"Total Customers: {kpi_total_customers:,}",
    f"Avg. Discount: {kpi_avg_discount:.2%}"
]))
html_out = html_out.replace('__BAR_FILTER__', html.escape(bar_filter_col))
html_out = html_out.replace('__PIE_FILTER__', html.escape(pie_filter_col))
html_out = html_out.replace('__INSIGHTS__', ''.join(f'<li>{html.escape(i)}</li>' for i in insights))
html_out = html_out.replace('__PREVIEW_HEADER__', ''.join(f'<th>{c}</th>' for c in preview_header))
html_out = html_out.replace('__PREVIEW_ROWS__', ''.join('<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>' for row in preview_rows))
html_out = html_out.replace('__DATA__', json.dumps(chart_data))

# Save
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(html_out)

print('DONE', os.path.getsize(OUTPUT_FILE), 'bytes')
