# Real Estate Sales / Demand Forecasting

## Business problem

Real-estate teams need to anticipate how much market activity is likely to occur so they can plan sales capacity, inventory, marketing activity, and development decisions. This project forecasts the number of recorded property sales in New York City each month.

The project forecasts demand volume, not the price of an individual property.

## Dataset and source

The project uses the official [NYC Open Data Citywide Annualized Calendar Sales Update](https://data.cityofnewyork.us/City-Government/NYC-Citywide-Annualized-Calendar-Sales-Update/w2pb-icbu). The source contains transaction-level property-sale records. The included local snapshot is an aggregation of records with `sale_price > 0` into one row per month and borough.

- Local snapshot: `nyc_property_sales_monthly_by_borough.csv`
- Snapshot rows: 600 monthly-by-borough aggregates
- Coverage: January 2016 through December 2025
- Important fields: month, borough, sales count, and median sale price for context
- Target: citywide monthly `sales_count`, created by summing the five borough rows
- Borough codes: 1 Manhattan, 2 Bronx, 3 Brooklyn, 4 Queens, 5 Staten Island

The snapshot is included so the notebook runs without a live API request. NYC Open Data can revise historical records, so `download_data.py` is provided to refresh the aggregation when needed; a refreshed download may produce different results than the included dated snapshot.

## Method

The notebook covers:

1. Source audit and data cleaning
2. Trend, seasonality, and borough-level exploration
3. Leakage-safe lag, rolling, and calendar features
4. Chronological train/validation/test splitting
5. Seasonal-naive baseline
6. Ridge regression and gradient boosting candidates
7. Twelve-configuration randomized tuning with four expanding-window `TimeSeriesSplit` folds
8. Final evaluation, error analysis, and permutation-based interpretation

The train period is 2017–2022, validation is 2023–2024, and the final test period is January–December 2025. The final test period is not used for model selection or tuning.

## Final test results

The selected model was Ridge regression. Its hyperparameter search selected `alpha=30` using only the development period.

| Model | MAE | RMSE | R² |
| --- | ---: | ---: | ---: |
| Seasonal naive | 322.08 | 349.23 | -0.12 |
| Tuned Ridge | 226.03 | 299.36 | 0.18 |

MAE is the average absolute miss in sales. RMSE penalizes larger misses more heavily. R² is included as a descriptive measure of explained variation; it is not a causal or business-impact measure.

## Key findings

- June had the highest average monthly demand in the snapshot, at about 5,510 recorded sales.
- February had the lowest average monthly demand, at about 4,291 recorded sales.
- Borough 4 (Queens) had the largest total recorded sales volume over the period.
- Average monthly recorded sales decreased from about 5,183 in 2016 to about 4,602 in 2025.
- The final model improved test RMSE over the seasonal-naive baseline, but the 12-month test window is short and the forecast should be used with contingency planning.

These are descriptive findings. They do not establish that month, borough, or any model feature causes demand to change.

## Limitations

- The data covers New York City only and measures recorded transactions, not all buyer intent or unrecorded activity.
- The source does not include interest rates, mortgage availability, employment, listings, economic conditions, or marketing activity.
- Historical patterns may not continue after December 2025.
- The final test year contains only twelve observations.
- Aggregation removes property-level detail; this project is not an individual property valuation model.

## Repository structure

```text
.
├── .gitignore
├── README.md
├── download_data.py
├── nyc_property_sales_monthly_by_borough.csv
├── snapshot_metadata.json
├── real_estate_sales_demand_forecasting.ipynb
└── requirements.txt
```

## How to run

From the repository root:

```bash
python -m pip install -r requirements.txt
jupyter notebook real_estate_sales_demand_forecasting.ipynb
```

The notebook loads the included local snapshot. To refresh the snapshot from the official API first, run:

```bash
python download_data.py
```

Refreshing the live source can change the data period or values, so record the new `snapshot_metadata.json` when publishing refreshed results.
