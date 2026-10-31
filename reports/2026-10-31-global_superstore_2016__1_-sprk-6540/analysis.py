
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pandas as pd, numpy as np
import sprk_dashboard as sd

INPUT_PATH = '/content/sprk/sprk-6540/input/global_superstore_2016__1_.xlsx'

# Load data

df = pd.read_excel(INPUT_PATH, sheet_name='Orders')

# Clean data - no major cleaning needed, but create Month column for time aggregation
# and filter out any rows with negative or zero sales (if any)
df = df[df['Sales'] > 0].copy()
df['Month'] = df['Order Date'].dt.strftime('%Y-%m')

# KPIs
kpis = []
total_sales = df['Sales'].sum()
kpis.append(('Total Sales', f"${total_sales:,.0f}"))
total_profit = df['Profit'].sum()
kpis.append(('Total Profit', f"${total_profit:,.0f}"))
unique_customers = df['Customer ID'].nunique()
kpis.append(('Unique Customers', f"{unique_customers:,}"))
total_orders = df['Order ID'].nunique()
kpis.append(('Total Orders', f"{total_orders:,}"))
avg_discount = df['Discount'].mean()
kpis.append(('Avg Discount', f"{avg_discount:.2%}"))

# Insights
insights = []
max_profit = df['Profit'].max()
insights.append(f"Max single order profit: ${max_profit:,.0f}")
max_loss = df['Profit'].min()
insights.append(f"Max single order loss: ${max_loss:,.0f}")
max_sales = df['Sales'].max()
insights.append(f"Max single order sales: ${max_sales:,.0f}")
max_quantity = df['Quantity'].max()
insights.append(f"Max quantity in single order: {max_quantity}")
max_discount = df['Discount'].max()
insights.append(f"Max discount given: {max_discount:.0%}")

# Report 1: Total Sales by Category filtered by Segment
report1 = sd.bar_report(df, x='Category', y='Sales', agg='sum', filter_col='Segment', title='Total Sales by Category', caption='Filtered by Customer Segment')

# Report 2: Total Profit by Region filtered by Market
report2 = sd.bar_report(df, x='Region', y='Profit', agg='sum', filter_col='Market', title='Total Profit by Region', caption='Filtered by Market')

# Build dashboard

title = 'Global Superstore 2016 Sales Analysis'
subtitle = 'Sales and Profit Analysis by Category and Region with Filters'

info = sd.build_dashboard(os.path.join(HERE, 'report.html'), title, subtitle, kpis, [report1, report2], insights, df)
print(info)
