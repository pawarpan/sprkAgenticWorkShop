import pandas as pd
import numpy as np
import plotly.graph_objs as go
import html
from string import Template
import os
import json

WORK_DIR = "/content/sprk/run-6837"
FILE_PATH = os.path.join(WORK_DIR, "global_superstore_2016_1.xlsx")
df = pd.read_excel(FILE_PATH, sheet_name="Orders")
df = df.drop(columns=["Postal Code"])
df = df.fillna(0)
kpi_total_sales = df["Sales"].sum()
kpi_total_profit = df["Profit"].sum()
kpi_total_orders = df["Order ID"].nunique()
kpi_total_customers = df["Customer ID"].nunique()
kpi_avg_discount = df["Discount"].mean()
insights = [
    f"Total sales: ${kpi_total_sales:,.0f}",
    f"Total profit: ${kpi_total_profit:,.0f}",
    f"Number of unique orders: {kpi_total_orders}",
    f"Number of unique customers: {kpi_total_customers}",
    f"Average discount: {kpi_avg_discount:.2%}"
]
top_regions = df["Region"].value_counts().index[:10]
region_options = list(top_regions)
bar1_data = []
bar1_buttons = []
for region in region_options:
    dfr = df[df["Region"] == region]
    sales_by_cat = dfr.groupby("Category")["Sales"].sum().sort_values(ascending=False)
    bar1_data.append(go.Bar(x=sales_by_cat.index, y=sales_by_cat.values, name=region))
    bar1_buttons.append(dict(
        method="update",
        label=region,
        args=[{"visible": [i == region_options.index(region) for i in range(len(region_options))]},
              {"title": f"Sales by Category in {region}"}]
    ))
top_segments = list(df["Segment"].unique())
bar2_data = []
bar2_buttons = []
for segment in top_segments:
    dfs = df[df["Segment"] == segment]
    profit_by_subcat = dfs.groupby("Sub-Category")["Profit"].sum().sort_values(ascending=False)[:15]
    bar2_data.append(go.Bar(x=profit_by_subcat.index, y=profit_by_subcat.values, name=segment))
    bar2_buttons.append(dict(
        method="update",
        label=segment,
        args=[{"visible": [i == top_segments.index(segment) for i in range(len(top_segments))]},
              {"title": f"Profit by Sub-Category for {segment}"}]
    ))
data_preview = df.head(15).copy()
data_preview = data_preview[[c for c in data_preview.columns[:12]]]
preview_html = data_preview.to_html(index=False, escape=True, max_cols=12, max_rows=15)
html_template = Template("""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>Global Superstore 2016 Dashboard</title>
    <script src=\"https://cdn.plot.ly/plotly-2.35.2.min.js\"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f9f9f9; }
        h1 { font-size: 2em; }
        .kpis { display: flex; gap: 20px; margin-bottom: 20px; }
        .kpi { background: #fff; padding: 16px 24px; border-radius: 8px; box-shadow: 0 2px 6px #0001; min-width: 160px; }
        .charts { display: flex; gap: 20px; }
        .chart { background: #fff; padding: 10px; border-radius: 8px; box-shadow: 0 2px 6px #0001; flex: 1; }
        .insights { margin: 20px 0; }
        .preview { background: #fff; padding: 10px; border-radius: 8px; box-shadow: 0 2px 6px #0001; }
    </style>
</head>
<body>
    <h1>Global Superstore 2016 Dashboard</h1>
    <div class=\"kpis\">
        <div class=\"kpi\"><b>Total Sales</b><br>$${total_sales}</div>
        <div class=\"kpi\"><b>Total Profit</b><br>$${total_profit}</div>
        <div class=\"kpi\"><b>Unique Orders</b><br>${total_orders}</div>
        <div class=\"kpi\"><b>Unique Customers</b><br>${total_customers}</div>
        <div class=\"kpi\"><b>Avg. Discount</b><br>${avg_discount}</div>
    </div>
    <div class=\"charts\">
        <div class=\"chart\">
            <div id=\"bar1\"></div>
        </div>
        <div class=\"chart\">
            <div id=\"bar2\"></div>
        </div>
    </div>
    <div class=\"insights\">
        <h2>Key Insights</h2>
        <ul>
        $insights
        </ul>
    </div>
    <div class=\"preview\">
        <h2>Data Preview</h2>
        $preview_html
    </div>
    <script>
        var bar1_data = $bar1_data;
        var bar2_data = $bar2_data;
        Plotly.newPlot('bar1', bar1_data, {
            title: 'Sales by Category',
            updatemenus: [{
                buttons: $bar1_buttons,
                direction: 'down',
                showactive: true,
                x: 0.1,
                xanchor: 'left',
                y: 1.2,
                yanchor: 'top'
            }],
            template: 'none',
            margin: {t: 60, l: 40, r: 10, b: 60}
        });
        Plotly.newPlot('bar2', bar2_data, {
            title: 'Profit by Sub-Category',
            updatemenus: [{
                buttons: $bar2_buttons,
                direction: 'down',
                showactive: true,
                x: 0.1,
                xanchor: 'left',
                y: 1.2,
                yanchor: 'top'
            }],
            template: 'none',
            margin: {t: 60, l: 40, r: 10, b: 60}
        });
    </script>
</body>
</html>
""")
bar1_data_json = json.dumps([dict(type="bar", x=trace.x.tolist(), y=trace.y.tolist(), name=trace.name) for trace in bar1_data])
bar2_data_json = json.dumps([dict(type="bar", x=trace.x.tolist(), y=trace.y.tolist(), name=trace.name) for trace in bar2_data])
bar1_buttons_json = json.dumps(bar1_buttons)
bar2_buttons_json = json.dumps(bar2_buttons)
insights_html = "\n".join(f"<li>{html.escape(i)}</li>" for i in insights)
html_out = html_template.substitute(
    total_sales=f"{kpi_total_sales:,.0f}",
    total_profit=f"{kpi_total_profit:,.0f}",
    total_orders=kpi_total_orders,
    total_customers=kpi_total_customers,
    avg_discount=f"{kpi_avg_discount:.2%}",
    insights=insights_html,
    preview_html=preview_html,
    bar1_data=bar1_data_json,
    bar2_data=bar2_data_json,
    bar1_buttons=bar1_buttons_json,
    bar2_buttons=bar2_buttons_json
)
with open(os.path.join(WORK_DIR, "report.html"), "w", encoding="utf-8") as f:
    f.write(html_out)
print("DONE", os.path.getsize(os.path.join(WORK_DIR, "report.html")))
