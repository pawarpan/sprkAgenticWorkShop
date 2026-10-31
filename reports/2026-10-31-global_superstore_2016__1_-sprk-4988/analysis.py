
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pandas as pd, numpy as np
import sprk_dashboard as sd

INPUT_PATH = '/content/sprk/sprk-4988/input/global_superstore_2016__1_.xlsx'

# Load data

df = pd.read_excel(INPUT_PATH, sheet_name='Orders')

# Clean data
# Postal Code has many nulls, drop it
# Convert Order Date to Year-Month for time series grouping
# Filter columns for dashboard

# Add Year-Month column for time grouping

df['YearMonth'] = df['Order Date'].dt.strftime('%Y-%m')

# KPIs
kpis = []
total_sales = df['Sales'].sum()
total_profit = df['Profit'].sum()
total_quantity = df['Quantity'].sum()
unique_customers = df['Customer ID'].nunique()
avg_discount = df['Discount'].mean()

kpis.append(('Total Sales', f"${total_sales:,.0f}"))
kpis.append(('Total Profit', f"${total_profit:,.0f}"))
kpis.append(('Total Quantity Sold', f"{total_quantity:,}"))
kpis.append(('Unique Customers', f"{unique_customers:,}"))
kpis.append(('Average Discount', f"{avg_discount:.2%}"))

# Insights
insights = []
insights.append(f"Total sales reached ${total_sales:,.0f} across {df['YearMonth'].nunique()} months.")
insights.append(f"Total profit was ${total_profit:,.0f}, with an average profit per order of ${df['Profit'].mean():,.2f}.")
insights.append(f"The dataset includes {unique_customers:,} unique customers.")
insights.append(f"Average discount given was {avg_discount:.2%}.")
insights.append(f"Orders were shipped using 4 ship modes and belong to 3 segments.")

# Report 1: Total Sales by Category filtered by Segment
report1 = sd.bar_report(df, x='Category', y='Sales', agg='sum', filter_col='Segment', title='Total Sales by Category', caption='Filtered by Segment')

# Report 2: Total Profit by Region filtered by Market
report2 = sd.bar_report(df, x='Region', y='Profit', agg='sum', filter_col='Market', title='Total Profit by Region', caption='Filtered by Market')

# Build dashboard

title = 'Global Superstore 2016 Sales Analysis'
subtitle = 'Sales and Profit Overview by Category and Region with Filters'

info = sd.build_dashboard(os.path.join(HERE, 'report.html'), title, subtitle, kpis, [report1, report2], insights, df)
print(info)
