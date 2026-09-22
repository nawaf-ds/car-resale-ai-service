# Dataset Provenance

## Selected snapshot

- Dataset: **US Sales Cars Dataset**, version 2
- Publisher: Juan Merino
- Official catalog: <https://www.kaggle.com/datasets/juanmerinobermejo/us-sales-cars-dataset>
- Upstream cleaning repository: <https://github.com/juanmerino89/cars-data-cleaning>
- Snapshot release/update: 2024-03-31
- Snapshot archive SHA-256: `5b259cbb8c0a63cb6ff0defa52f9abc54c1783a610cbd2a506d5c3f254808d55`
- `cars.csv` SHA-256: `25854afc3ef8b6c6a0349bf7f422c40dacb9bec60a8b318462737ebf9edcc5ea`
- License: Apache License 2.0, as declared by the official Kaggle dataset metadata
- Market: United States, Cars.com listings
- Currency: US dollars
- Mileage unit: miles
- Raw shape: 144,867 rows and 7 columns
- Columns: `Brand`, `Model`, `Year`, `Status`, `Mileage`, `Dealer`, `Price`

The publisher's repository states that the source files came from web scraping Cars.com. It does not document exact scrape start/end dates. The Kaggle catalog records an initial release on 2023-10-11 and version 2 on 2024-03-31. This missing collection-window detail is a provenance limitation and must not be inferred from vehicle model years.

`Price` is an advertised listing price, not a completed transaction price. Therefore, the model estimates listing-market value and cannot claim sale-price accuracy.

## Selection and preparation

Training uses only `Used` and `Certified` records with non-null mileage and price. It removes exact duplicate rows before splitting and applies documented plausibility filters in `scripts/train.py`. `Dealer` is excluded because it is high-cardinality and may encode source-specific effects. The seller's submitted asking price is never a model feature.

The snapshot is committed so training remains reproducible even when the upstream catalog changes. Attribution and this provenance record must remain with redistributed copies.

