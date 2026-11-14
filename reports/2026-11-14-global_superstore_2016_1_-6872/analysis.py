import html
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from string import Template
import os

WORK_DIR = "/content/sprk/run-6872"
FILE_PATH = os.path.join(WORK_DIR, "global_superstore_2016_1.xlsx")

df = pd.read_excel(FILE_PATH, sheet_name="Orders")
df = df.drop(columns=["Postal Code"])
df = df.fillna({col: 0 if np.issubdtype(dtype, np.number) else "" for col, dtype in df.dtypes.items()})

kpi_total_sales = df["Sales"].sum()
kpi_total_profit = df["Profit"].sum()
kpi_num_orders = df["Order ID"].nunique()
kpi_num_customers = df["Customer ID"].nunique()
kpi_avg_discount = df["Discount"].mean()

insights = [
    f"Total sales: ${kpi_total_sales:,.0f}",
    f"Total profit: ${kpi_total_profit:,.0f}",
    f"Number of unique orders: {kpi_num_orders}",
    f"Number of unique customers: {kpi_num_customers}",
    f"Average discount: {kpi_avg_discount:.2%}"
]

top_regions = df["Region"].value_counts().index[:10].tolist()
region_options = [r for r in top_regions if r]
bar1_data = []
bar1_buttons = []
for region in region_options:
    dff = df[df["Region"] == region]
    sales_by_cat = dff.groupby("Category")["Sales"].sum().sort_values(ascending=False)
    bar1_data.append(go.Bar(x=sales_by_cat.index.tolist(), y=sales_by_cat.values.tolist(), name=region))
    bar1_buttons.append(dict(label=region, method="update", args=[{"y": [sales_by_cat.values.tolist()], "x": [sales_by_cat.index.tolist()]}]))

top_markets = df["Market"].value_counts().index[:5].tolist()
market_options = [m for m in top_markets if m]
bar2_data = []
bar2_buttons = []
for market in market_options:
    dff = df[df["Market"] == market]
    profit_by_subcat = dff.groupby("Sub-Category")["Profit"].sum().sort_values(ascending=False)[:15]
    bar2_data.append(go.Bar(x=profit_by_subcat.index.tolist(), y=profit_by_subcat.values.tolist(), name=market))
    bar2_buttons.append(dict(label=market, method="update", args=[{"y": [profit_by_subcat.values.tolist()], "x": [profit_by_subcat.index.tolist()]}]))

data_preview = df.head(15).copy()
data_preview = data_preview[[col for col in df.columns[:12]]]
preview_html = data_preview.to_html(index=False, max_cols=12, max_rows=15, escape=True)

html_template = Template("""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>Global Superstore 2016 Dashboard</title>
    <script src=\"https://cdn.plot.ly/plotly-2.35.2.min.js\"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f8f8f8; }
        .container { max-width: 1200px; margin: 30px auto; background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px #ccc; }
        h1 { font-size: 2em; margin-bottom: 0.5em; }
        .kpis { display: flex; gap: 18px; margin-bottom: 24px; }
        .kpi { background: #f0f4f8; padding: 16px 24px; border-radius: 6px; font-size: 1.1em; flex: 1; text-align: center; }
        .charts { display: flex; gap: 20px; }
        .chart { flex: 1; min-width: 0; }
        .insights { margin: 24px 0 12px 0; }
        .preview { margin-top: 18px; }
    </style>
</head>
<body>
<div class=\"container\">
    <h1>Global Superstore 2016 Dashboard</h1>
    <div class=\"kpis\">
        <div class=\"kpi\">Total Sales<br><b>$${total_sales}</b></div>
        <div class=\"kpi\">Total Profit<br><b>$${total_profit}</b></div>
        <div class=\"kpi\">Orders<br><b>${num_orders}</b></div>
        <div class=\"kpi\">Customers<br><b>${num_customers}</b></div>
        <div class=\"kpi\">Avg Discount<br><b>${avg_discount}%</b></div>
    </div>
    <div class=\"charts\">
        <div class=\"chart\">
            <h3>Sales by Category (filter by Region)</h3>
            <div id=\"bar1\"></div>
        </div>
        <div class=\"chart\">
            <h3>Profit by Sub-Category (filter by Market)</h3>
            <div id=\"bar2\"></div>
        </div>
    </div>
    <div class=\"insights\">
        <h3>Key Insights</h3>
        <ul>
            $insights
        </ul>
    </div>
    <div class=\"preview\">
        <h3>Data Preview</h3>
        $preview_table
    </div>
</div>
<script>
// Bar 1: Sales by Category, filter by Region
var bar1_data = [
    {x: ${bar1_x}, y: ${bar1_y}, type: 'bar', name: '${bar1_region}'}
];
var bar1_layout = {margin: {t: 30, b: 80}, template: 'none', updatemenus: [{
    buttons: [
        ${bar1_buttons}
    ],
    direction: 'down',
    showactive: true,
    x: 0.5,
    xanchor: 'center',
    y: 1.15,
    yanchor: 'top'
}]};
Plotly.newPlot('bar1', bar1_data, bar1_layout, {displayModeBar: false});

// Bar 2: Profit by Sub-Category, filter by Market
var bar2_data = [
    {x: ${bar2_x}, y: ${bar2_y}, type: 'bar', name: '${bar2_market}'}
];
var bar2_layout = {margin: {t: 30, b: 120}, template: 'none', updatemenus: [{
    buttons: [
        ${bar2_buttons}
    ],
    direction: 'down',
    showactive: true,
    x: 0.5,
    xanchor: 'center',
    y: 1.15,
    yanchor: 'top'
}]};
Plotly.newPlot('bar2', bar2_data, bar2_layout, {displayModeBar: false});
</script>
</body>
</html>
")

bar1_x = [str(x) for x in df[df["Region"] == region_options[0]].groupby("Category")["Sales"].sum().sort_values(ascending=False).index.tolist()]
bar1_y = [float(y) for y in df[df["Region"] == region_options[0]].groupby("Category")["Sales"].sum().sort_values(ascending=False).values.tolist()]
bar1_region = region_options[0]
bar1_buttons_js = ",\n        ".join([
    f"{{label: '{r}', method: 'update', args: [{{y: [[float(y) for y in df[df['Region'] == r].groupby('Category')['Sales'].sum().sort_values(ascending=False).values.tolist()]], x: [[str(x) for x in df[df['Region'] == r].groupby('Category')['Sales'].sum().sort_values(ascending=False).index.tolist()]]}}]}}"
    for r in region_options
])

bar2_x = [str(x) for x in df[df["Market"] == market_options[0]].groupby("Sub-Category")["Profit"].sum().sort_values(ascending=False)[:15].index.tolist()]
bar2_y = [float(y) for y in df[df["Market"] == market_options[0]].groupby("Sub-Category")["Profit"].sum().sort_values(ascending=False)[:15].values.tolist()]
bar2_market = market_options[0]
bar2_buttons_js = ",\n        ".join([
    f"{{label: '{m}', method: 'update', args: [{{y: [[float(y) for y in df[df['Market'] == m].groupby('Sub-Category')['Profit'].sum().sort_values(ascending=False)[:15].values.tolist()]], x: [[str(x) for x in df[df['Market'] == m].groupby('Sub-Category')['Profit'].sum().sort_values(ascending=False)[:15].index.tolist()]]}}]}}"
    for m in market_options
])

insights_html = "\n".join([f"<li>{html.escape(i)}</li>" for i in insights])

html_out = html_template.substitute(
    total_sales=f"{kpi_total_sales:,.0f}",
    total_profit=f"{kpi_total_profit:,.0f}",
    num_orders=kpi_num_orders,
    num_customers=kpi_num_customers,
    avg_discount=f"{kpi_avg_discount*100:.2f}",
    bar1_x=bar1_x,
    bar1_y=bar1_y,
    bar1_region=bar1_region,
    bar1_buttons=bar1_buttons_js,
    bar2_x=bar2_x,
    bar2_y=bar2_y,
    bar2_market=bar2_market,
    bar2_buttons=bar2_buttons_js,
    insights=insights_html,
    preview_table=preview_html
)

with open(os.path.join(WORK_DIR, "report.html"), "w", encoding="utf-8") as f:
    f.write(html_out)
print("DONE", os.path.getsize(os.path.join(WORK_DIR, "report.html")))
