# Data Quality Report

- Rows: **2030**, Columns: **12**
- Duplicate rows: **30**
- Duplicate order_ids: **30**
- Negative quantities: **41**
- Unit-price outliers (> 136.03): **14**

## Missing values per column
- `order_id`: 0
- `order_date`: 0
- `customer_id`: 0
- `customer_email`: 88
- `region`: 315
- `channel`: 356
- `sku`: 0
- `product_name`: 0
- `unit_price`: 0
- `quantity`: 0
- `discount`: 0
- `revenue`: 56

## Inconsistent categorical values
- region raw: {nan: 315, 'West': 305, 'north ': 290, 'SOUTH': 283, 'East': 281, 'North': 279, 'South': 277}
- channel raw: {'retail': 364, nan: 356, 'Retail': 333, 'Partner': 328, 'online': 326, 'Online': 323}

## Mixed date formats (samples)
- `04/25/2024`
- `23-Nov-2024`
- `2024-06-17`
- `21-Jul-2024`
- `26-May-2024`