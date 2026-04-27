# pipesight

> A lightweight CLI for visualizing and profiling pandas/polars data pipeline bottlenecks in real time.

---

## Installation

```bash
pip install pipesight
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add pipesight
```

---

## Usage

Wrap your pipeline steps with `pipesight` to get instant profiling output in your terminal:

```python
import pandas as pd
from pipesight import track

@track
def clean(df):
    return df.dropna().reset_index(drop=True)

@track
def transform(df):
    return df.assign(total=df["price"] * df["qty"])

df = pd.read_csv("orders.csv")
df = clean(df)
df = transform(df)
```

Then run from the CLI:

```bash
pipesight run pipeline.py
```

**Example output:**

```
Step          Duration    Rows In    Rows Out   Memory Δ
──────────────────────────────────────────────────────
clean         0.42s       120,000    98,312     -1.8 MB
transform     0.87s       98,312     98,312     +4.2 MB
```

Use `--export` to save results as JSON or CSV:

```bash
pipesight run pipeline.py --export report.json
```

---

## License

[MIT](LICENSE) © 2024 pipesight contributors