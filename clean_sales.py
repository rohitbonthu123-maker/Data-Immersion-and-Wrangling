import pandas as pd, numpy as np, json
from pathlib import Path

OUT = Path('/mnt/documents/intern_onboarding')
df = pd.read_csv(OUT/'sales_raw.csv')

# ---------- 1) Data Dictionary ----------
dictionary = [
    ('order_id', 'string', 'Unique identifier for each order', 'O100000'),
    ('order_date', 'date', 'Date the order was placed (mixed formats in raw)', '2024-05-28'),
    ('customer_id', 'string', 'Anonymous customer identifier', 'C0185'),
    ('customer_email', 'string', 'Customer email address (may be missing)', 'c0185@example.com'),
    ('region', 'category', 'Sales region: North/South/East/West', 'North'),
    ('channel', 'category', 'Sales channel: Online/Retail/Partner', 'Online'),
    ('sku', 'string', 'Product stock keeping unit', 'SKU-001'),
    ('product_name', 'string', 'Human-readable product name', 'Widget A'),
    ('unit_price', 'float', 'List price per unit in USD', '19.99'),
    ('quantity', 'int', 'Units ordered', '3'),
    ('discount', 'float', 'Fractional discount applied (0–1)', '0.10'),
    ('revenue', 'float', 'Net revenue = quantity * unit_price * (1 - discount)', '53.97'),
]
dd = pd.DataFrame(dictionary, columns=['column','type','description','example'])
dd.to_csv(OUT/'data_dictionary.csv', index=False)

# ---------- 2) Data Quality Assessment ----------
report = {}
report['shape'] = {'rows': int(df.shape[0]), 'cols': int(df.shape[1])}
report['missing_per_column'] = df.isna().sum().to_dict()
report['duplicate_rows'] = int(df.duplicated().sum())
report['duplicate_order_ids'] = int(df['order_id'].duplicated().sum())
report['region_values_raw'] = df['region'].value_counts(dropna=False).to_dict()
report['channel_values_raw'] = df['channel'].value_counts(dropna=False).to_dict()
report['negative_quantity'] = int((df['quantity']<0).sum())
# outliers via IQR on unit_price
q1,q3 = df['unit_price'].quantile([.25,.75]); iqr=q3-q1
hi = q3+3*iqr
report['unit_price_outliers_high'] = int((df['unit_price']>hi).sum())
report['unit_price_outlier_threshold'] = float(hi)
report['date_format_samples'] = df['order_date'].dropna().sample(5, random_state=0).tolist()

with open(OUT/'quality_report.json','w') as f:
    json.dump(report, f, indent=2, default=str)

# Markdown summary
lines = ["# Data Quality Report\n",
         f"- Rows: **{report['shape']['rows']}**, Columns: **{report['shape']['cols']}**",
         f"- Duplicate rows: **{report['duplicate_rows']}**",
         f"- Duplicate order_ids: **{report['duplicate_order_ids']}**",
         f"- Negative quantities: **{report['negative_quantity']}**",
         f"- Unit-price outliers (> {hi:.2f}): **{report['unit_price_outliers_high']}**",
         "\n## Missing values per column"]
for k,v in report['missing_per_column'].items():
    lines.append(f"- `{k}`: {v}")
lines.append("\n## Inconsistent categorical values")
lines.append(f"- region raw: {report['region_values_raw']}")
lines.append(f"- channel raw: {report['channel_values_raw']}")
lines.append("\n## Mixed date formats (samples)")
for s in report['date_format_samples']:
    lines.append(f"- `{s}`")
(OUT/'quality_report.md').write_text("\n".join(lines))

# ---------- 3) Clean & Transform ----------
c = df.copy()

# dedupe
c = c.drop_duplicates()

# standardize categoricals
c['region'] = c['region'].astype('string').str.strip().str.title()
c['channel'] = c['channel'].astype('string').str.strip().str.title()
c['region'] = c['region'].where(c['region'].isin(['North','South','East','West']))
c['channel'] = c['channel'].where(c['channel'].isin(['Online','Retail','Partner']))

# parse dates (mixed formats)
c['order_date'] = pd.to_datetime(c['order_date'], errors='coerce', format='mixed')

# fix negative quantities -> absolute (assumed entry error)
c['quantity'] = c['quantity'].abs()

# cap unit_price outliers at IQR upper fence
c.loc[c['unit_price']>hi, 'unit_price'] = hi

# recompute revenue where missing or implausible
calc_rev = (c['quantity']*c['unit_price']*(1-c['discount'])).round(2)
c['revenue'] = c['revenue'].fillna(calc_rev)

# fill missing email with placeholder flag
c['email_missing'] = c['customer_email'].isna()
c['customer_email'] = c['customer_email'].fillna('unknown@unknown')

# drop rows still missing critical fields
c = c.dropna(subset=['order_date','region','channel'])

# feature engineering
c['order_year']   = c['order_date'].dt.year
c['order_month']  = c['order_date'].dt.to_period('M').astype(str)
c['order_dow']    = c['order_date'].dt.day_name()
c['gross_revenue']= (c['quantity']*c['unit_price']).round(2)
c['discount_amt'] = (c['gross_revenue']-c['revenue']).round(2)

# customer-level aggregate feature
cust_tot = c.groupby('customer_id')['revenue'].transform('sum')
c['customer_lifetime_revenue'] = cust_tot.round(2)

c.to_csv(OUT/'sales_clean.csv', index=False)

# Excel workbook with all artifacts
with pd.ExcelWriter(OUT/'intern_onboarding.xlsx', engine='openpyxl') as w:
    dd.to_excel(w, sheet_name='Data Dictionary', index=False)
    pd.DataFrame(list(report['missing_per_column'].items()),
                 columns=['column','missing']).to_excel(w, sheet_name='Missing', index=False)
    c.head(500).to_excel(w, sheet_name='Clean Sample', index=False)

print('Raw:', df.shape, '-> Clean:', c.shape)
print('Files written to', OUT)
