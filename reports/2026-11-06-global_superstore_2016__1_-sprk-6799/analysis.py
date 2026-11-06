
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pandas as pd, numpy as np
import sprk_dashboard as sd

INPUT_PATH = '/content/sprk/sprk-6799/input/global_superstore_2016__1_.xlsx'

# Load data

df = pd.read_excel(INPUT_PATH, sheet_name='Orders')

# Clean data
# Postal Code has many missing values, drop it
# Convert Order Date to year-month for aggregation

df = df.drop(columns=['Postal Code'])
df['YearMonth'] = df['Order Date'].dt.strftime('%Y-%m')

# KPIs
kpis = [
    ('Total Sales', f"${df['Sales'].sum():,.0f}"),
    ('Total Profit', f"${df['Profit'].sum():,.0f}"),
    ('Average Discount', f"{df['Discount'].mean():.2%}"),
    ('Total Quantity Sold', f"{df['Quantity'].sum():,}"),
    ('Total Shipping Cost', f"${df['Shipping Cost'].sum():,.0f}")
]

# Insights
insights = [
    f"Total sales reached ${df['Sales'].sum():,.0f} across {df['Category'].nunique()} categories.",
    f"Profit summed to ${df['Profit'].sum():,.0f} with an average discount of {df['Discount'].mean():.2%}.",
    f"The highest sales month was {df.groupby('YearMonth')['Sales'].sum().idxmax()}.",
    f"The most profitable category was {df.groupby('Category')['Profit'].sum().idxmax()}.",
    f"Orders shipped mostly by {df['Ship Mode'].mode()[0]} with {df['Ship Mode'].value_counts().max():,} shipments."
]

# Report 1: Total Sales by Category filtered by Segment
report1 = sd.bar_report(df, x='Category', y='Sales', agg='sum', filter_col='Segment', title='Total Sales by Category', caption='Filtered by Customer Segment')

# Report 2: Total Profit by Region filtered by Market
report2 = sd.bar_report(df, x='Region', y='Profit', agg='sum', filter_col='Market', title='Total Profit by Region', caption='Filtered by Market')

# Build dashboard

title = 'Global Superstore 2016 Sales Analysis'
subtitle = 'Sales and Profit Overview by Category and Region'

info = sd.build_dashboard(os.path.join(HERE, 'report.html'), title, subtitle, kpis, [report1, report2], insights, df)
print(info)
