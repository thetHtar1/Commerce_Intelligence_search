# Raw Currency Reference Data

These snapshots are sourced from Unicode CLDR JSON release 49.0.0 and are used to build the project currency registry, aliases, and synthetic query examples.

| File | CLDR source |
| --- | --- |
| `cldr_49_currency_data.json` | `cldr-core/supplemental/currencyData.json` |
| `cldr_49_en_currencies.json` | `cldr-numbers-full/main/en/currencies.json` |
| `cldr_49_my_currencies.json` | `cldr-numbers-full/main/my/currencies.json` |
| `cldr_49_th_currencies.json` | `cldr-numbers-full/main/th/currencies.json` |

The complete JSON snapshots are retained here so dataset generation can be repeated. Their SHA-256 checksums are recorded in `data/training/currency_resolution/dataset_manifest.json`.

CLDR source repository: <https://github.com/unicode-org/cldr-json/tree/49.0.0>

License: see [`CLDR_LICENSE.txt`](CLDR_LICENSE.txt), copied from the CLDR JSON release. The upstream license is <https://github.com/unicode-org/cldr-json/blob/49.0.0/LICENSE>.
