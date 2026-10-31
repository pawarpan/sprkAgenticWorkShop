
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pandas as pd, numpy as np
import sprk_dashboard as sd

INPUT_PATH = '/content/sprk/sprk-4984/input/global_superstore_2016__1_.xlsx'

# Load data
# Only Orders sheet is relevant for analysis

df = pd.read_excel(INPUT_PATH, sheet_name='Orders')

# Clean data
# Postal Code has many nulls, drop it as not useful for grouping
# Convert Order Date to Year-Month for time series grouping
# Create Month column for bar charts

if 'Postal Code' in df.columns:
    df = df.drop(columns=['Postal Code'])

# Create Month column
# Using year-month string for categorical x axis

df['Month'] = df['Order Date'].dt.strftime('%Y-%m')

# KPIs
# Total Sales, Total Profit, Average Discount, Total Quantity, Total Shipping Cost

kpis = [
    ('Total Sales', f"${df['Sales'].sum():,.0f}"),
    ('Total Profit', f"${df['Profit'].sum():,.0f}"),
    ('Average Discount', f"{df['Discount'].mean():.2%}"),
    ('Total Quantity Sold', f"{df['Quantity'].sum():,}"),
    ('Total Shipping Cost', f"${df['Shipping Cost'].sum():,.0f}")
]

# Insights
# 1. Most profitable Category
# 2. Most sales by Region
# 3. Highest average discount by Segment
# 4. Month with highest sales
# 5. Most frequent Ship Mode

most_profitable_category = df.groupby('Category')['Profit'].sum().idxmax()
most_profitable_category_profit = df.groupby('Category')['Profit'].sum().max()

region_sales = df.groupby('Region')['Sales'].sum()
top_region = region_sales.idxmax()
top_region_sales = region_sales.max()

segment_discount = df.groupby('Segment')['Discount'].mean()
highest_discount_segment = segment_discount.idxmax()
highest_discount_value = segment_discount.max()

month_sales = df.groupby('Month')['Sales'].sum()
top_month = month_sales.idxmax()
top_month_sales = month_sales.max()

ship_mode_counts = df['Ship Mode'].value_counts()
top_ship_mode = ship_mode_counts.idxmax()
top_ship_mode_count = ship_mode_counts.max()

insights = [
    f"Most profitable category: {most_profitable_category} with profit ${most_profitable_category_profit:,.0f}",
    f"Region with highest sales: {top_region} with sales ${top_region_sales:,.0f}",
    f"Segment with highest average discount: {highest_discount_segment} at {highest_discount_value:.2%}",
    f"Month with highest sales: {top_month} totaling ${top_month_sales:,.0f}",
    f"Most frequent shipping mode: {top_ship_mode} with {top_ship_mode_count:,} orders"
]

# Reports
# Report 1: Total Sales by Category, filtered by Segment
# Report 2: Total Profit by Region, filtered by Market

report1 = sd.bar_report(df, x='Category', y='Sales', agg='sum', filter_col='Segment', title='Total Sales by Category', caption='Filtered by Segment')
report2 = sd.bar_report(df, x='Region', y='Profit', agg='sum', filter_col='Market', title='Total Profit by Region', caption='Filtered by Market')

# Build dashboard

title = 'Global Superstore 2016 Sales Analysis'
subtitle = 'Sales, Profit and Discounts across Categories, Regions and Segments'

info = sd.build_dashboard(os.path.join(HERE, 'report.html'), title, subtitle, kpis, [report1, report2], insights, df)

print(info)
