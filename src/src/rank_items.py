from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


DEFAULT_SCORE_COLS = ["score_quality", "score_cost", "score_reliability"]


def parse_weights(score_cols: list[str], weights_str: str | None) -> dict[str, float]:
    """
    Parses weights like: "score_quality=0.5,score_cost=0.2,score_reliability=0.3"
    If not provided, uses equal weights.
    """
    if not weights_str:
        w = 1.0 / len(score_cols)
        return {c: w for c in score_cols}

    weights: dict[str, float] = {}
    parts = [p.strip() for p in weights_str.split(",") if p.strip()]
    for p in parts:
        if "=" not in p:
            raise ValueError(f"Invalid weights format near '{p}'. Use col=weight.")
        col, val = p.split("=", 1)
        col = col.strip()
        val = float(val.strip())
        weights[col] = val

    # Validate all required columns exist in weights
    missing = [c for c in score_cols if c not in weights]
    if missing:
        raise ValueError(f"Missing weights for columns: {missing}")

    # Normalize weights to sum to 1
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("Sum of weights must be > 0")
    return {k: v / total for k, v in weights.items()}


def minmax_normalize(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """
    Normalizes columns to [0,1] using min-max scaling.
    Useful when score ranges differ.
    """
    out = df.copy()
    for c in cols:
        mn, mx = out[c].min(), out[c].max()
        if mx == mn:
            out[c] = 0.0  # all same value
        else:
            out[c] = (out[c] - mn) / (mx - mn)
    return out


def rank_items(csv_path: Path, score_cols: list[str], weights: dict[str, float], normalize: bool) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    # Basic validation
    missing_cols = [c for c in ["item_id", *score_cols] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"CSV is missing required columns: {missing_cols}")

    working = df.copy()
    if normalize:
        working = minmax_normalize(working, score_cols)

    # Weighted score
    working["final_score"] = 0.0
    for c in score_cols:
        working["final_score"] += working[c] * weights[c]

    ranked = working.sort_values(by="final_score", ascending=False).reset_index(drop=True)
    return ranked


def main():
    parser = argparse.ArgumentParser(description="Rank items from a CSV using weighted scoring.")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input CSV (default: data/sample_data.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="ranked_output.csv",
        help="Output CSV filename (saved at repo root by default).",
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=None,
        help='Weights like "score_quality=0.5,score_cost=0.2,score_reliability=0.3" (default: equal weights)',
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Apply min-max normalization to score columns before ranking.",
    )
    args = parser.parse_args()

    # Resolve repo root reliably: src/rank_items.py -> repo_root is parent of src
    repo_root = Path(__file__).resolve().parents[1]
    default_input = repo_root / "data" / "sample_data.csv"
    input_path = Path(args.input).expanduser().resolve() if args.input else default_input

    score_cols = DEFAULT_SCORE_COLS
    weights = parse_weights(score_cols, args.weights)

    ranked = rank_items(input_path, score_cols, weights, normalize=args.normalize)

    # Print clean output
    print("\nTop ranked items:\n")
    print(ranked[["item_id", "final_score"]].head(10).to_string(index=False))

    # Save output
    out_path = (repo_root / args.output).resolve()
    ranked.to_csv(out_path, index=False)
    print(f"\nSaved full ranked results to: {out_path}\n")


if __name__ == "__main__":
    main()
