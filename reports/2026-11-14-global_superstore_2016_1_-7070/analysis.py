import os
import pandas as pd
import json
import html

# --- Settings ---
WORK_DIR = '/content/sprk/run-7070'
INPUT_FILE = os.path.join(WORK_DIR, 'input.xlsx')
OUTPUT_FILE = os.path.join(WORK_DIR, 'report.html')

def build_dashboard():
    # 1. Load Data
    df = pd.read_excel(INPUT_FILE, sheet_name='Orders')
    
    # 2. KPIs
    total_sales = df['Sales'].sum()
    total_profit = df['Profit'].sum()
    total_qty = df['Quantity'].sum()
    order_count = df['Order ID'].nunique()
    
    kpis = [
        {"label": "Total Revenue", "value": f"${total_sales:,.0f}"},
        {"label": "Total Profit", "value": f"${total_profit:,.0f}"},
        {"label": "Units Sold", "value": f"{total_qty:,}"},
        {"label": "Total Orders", "value": f"{order_count:,}"}
    ]
    
    # 3. Bar Chart Data (Sub-Category vs Sales, Filtered by Category)
    # Prepare data for "All" and each Category
    bar_data = {}
    
    def get_bar_stats(data):
        stats = data.groupby('Sub-Category')['Sales'].sum().sort_values(ascending=False).head(15)
        return {"x": stats.index.tolist(), "y": stats.values.tolist()}
    
    bar_data["All"] = get_bar_stats(df)
    categories = sorted(df['Category'].dropna().unique().tolist())
    for cat in categories:
        bar_data[cat] = get_bar_stats(df[df['Category'] == cat])
        
    # 4. Pie Chart Data (Segment vs Sales, Filtered by Market)
    pie_data = {}
    
    def get_pie_stats(data):
        stats = data.groupby('Segment')['Sales'].sum().sort_values(ascending=False)
        # Top 7 plus Other (though Segment only has 3, we follow the rule)
        if len(stats) > 7:
            top = stats.head(7)
            other = pd.Series({"Other": stats.iloc[7:].sum()})
            stats = pd.concat([top, other])
        return {"labels": stats.index.tolist(), "values": stats.values.tolist()}
    
    pie_data["All"] = get_pie_stats(df)
    markets = sorted(df['Market'].dropna().unique().tolist())
    for mkt in markets:
        pie_data[mkt] = get_pie_stats(df[df['Market'] == mkt])
        
    # 5. Insights
    avg_discount = df['Discount'].mean()
    shipping_ratio = df['Shipping Cost'].sum() / total_sales
    top_cat = df.groupby('Category')['Sales'].sum().idxmax()
    top_cat_val = df.groupby('Category')['Sales'].sum().max()
    top_market = df.groupby('Market')['Profit'].sum().idxmax()
    top_market_val = df.groupby('Market')['Profit'].sum().max()
    
    insights = [
        f"<b>Technology</b> leads sales with <b>${top_cat_val:,.0f}</b> in total revenue.",
        f"<b>{top_market}</b> is the most profitable market, contributing <b>${top_market_val:,.0f}</b>.",
        f"The average discount across all orders is <b>{avg_discount:.2%}</b>.",
        f"Shipping costs account for <b>{shipping_ratio:.2%}</b> of total sales revenue.",
        f"A total of <b>{order_count:,}</b> unique orders were processed globally."
    ]
    
    # 6. Preview Table (First 10 rows)
    preview_cols = ['Order ID', 'Order Date', 'Customer Name', 'Segment', 'Country', 'Category', 'Sales', 'Profit']
    preview_df = df[preview_cols].head(10)
    preview_html = preview_df.to_html(index=False, classes='preview-table')
    
    # 7. Build HTML
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>__TITLE__</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        body { font-family: sans-serif; margin: 20px; background-color: #f4f7f6; color: #333; }
        .header { text-align: center; margin-bottom: 30px; }
        .kpi-container { display: flex; justify-content: space-around; margin-bottom: 30px; }
        .kpi-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; flex: 1; margin: 0 10px; }
        .kpi-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .kpi-label { font-size: 14px; color: #7f8c8d; margin-top: 5px; }
        .charts-row { display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 30px; }
        .chart-box { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); flex: 1; min-width: 450px; }
        .filter-container { margin-bottom: 15px; }
        .insights-box { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .insights-box h3 { margin-top: 0; }
        .preview-box { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow-x: auto; }
        .preview-table { width: 100%; border-collapse: collapse; font-size: 12px; }
        .preview-table th, .preview-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .preview-table th { background-color: #f8f9fa; }
        select { padding: 5px; border-radius: 4px; border: 1px solid #ccc; }
    </style>
</head>
<body>
    <div class="header">
        <h1>__TITLE__</h1>
        <p>__SUBTITLE__</p>
    </div>

    <div class="kpi-container">
        __KPIS__
    </div>

    <div class="charts-row">
        <div class="chart-box">
            <div class="filter-container">
                <label>Filter by Category: </label>
                <select id="barFilter" onchange="updateBarChart()">
                    <option value="All">All Categories</option>
                    __BAR_OPTIONS__
                </select>
            </div>
            <div id="barChart" style="height: 400px;"></div>
        </div>
        <div class="chart-box">
            <div class="filter-container">
                <label>Filter by Market: </label>
                <select id="pieFilter" onchange="updatePieChart()">
                    <option value="All">All Markets</option>
                    __PIE_OPTIONS__
                </select>
            </div>
            <div id="pieChart" style="height: 400px;"></div>
        </div>
    </div>

    <div class="insights-box">
        <h3>Key Insights</h3>
        <ul>
            __INSIGHTS__
        </ul>
    </div>

    <div class="preview-box">
        <h3>Data Preview (First 10 Rows)</h3>
        __PREVIEW__
    </div>

    <script>
        const barData = __BAR_DATA__;
        const pieData = __PIE_DATA__;

        function updateBarChart() {
            const val = document.getElementById('barFilter').value;
            const data = barData[val];
            const trace = {
                x: data.x,
                y: data.y,
                type: 'bar',
                marker: { color: '#3498db' }
            };
            const layout = {
                title: 'Sales by Sub-Category',
                margin: { t: 40, b: 80, l: 60, r: 20 },
                xaxis: { tickangle: -45 }
            };
            Plotly.react('barChart', [trace], layout);
        }

        function updatePieChart() {
            const val = document.getElementById('pieFilter').value;
            const data = pieData[val];
            const trace = {
                labels: data.labels,
                values: data.values,
                type: 'pie',
                hole: 0.4,
                marker: { colors: ['#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#34495e', '#1abc9c', '#e67e22'] }
            };
            const layout = {
                title: 'Sales by Customer Segment',
                margin: { t: 40, b: 20, l: 20, r: 20 }
            };
            Plotly.react('pieChart', [trace], layout);
        }

        // Initial render
        updateBarChart();
        updatePieChart();
    </script>
</body>
</html>
"""
    
    # Fill Markers
    title = "Global Superstore Sales Performance"
    subtitle = "Analysis of sales, profit, and customer segments across global markets"
    
    kpi_html = ""
    for k in kpis:
        kpi_html += f'<div class="kpi-card"><div class="kpi-value">{{k["value"]}}</div><div class="kpi-label">{{k["label"]}}</div></div>'
        
    bar_options = "".join([f'<option value="{{html.escape(c)}}">{{html.escape(c)}}</option>' for c in categories])
    pie_options = "".join([f'<option value="{{html.escape(m)}}">{{html.escape(m)}</option>' for m in markets])
    
    insights_html = "".join([f'<li>{{ins}}</li>' for ins in insights])
    
    final_html = html_template.replace("__TITLE__", html.escape(title))
    final_html = final_html.replace("__SUBTITLE__", html.escape(subtitle))
    final_html = final_html.replace("__KPIS__", kpi_html)
    final_html = final_html.replace("__BAR_OPTIONS__", bar_options)
    final_html = final_html.replace("__PIE_OPTIONS__", pie_options)
    final_html = final_html.replace("__INSIGHTS__", insights_html)
    final_html = final_html.replace("__PREVIEW__", preview_html)
    final_html = final_html.replace("__BAR_DATA__", json.dumps(bar_data))
    final_html = final_html.replace("__PIE_DATA__", json.dumps(pie_data))
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write(final_html)
        
    print(f"DONE: {os.path.getsize(OUTPUT_FILE)} bytes")

if __name__ == "__main__":
    build_dashboard()
