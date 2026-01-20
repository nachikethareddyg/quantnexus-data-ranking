import pandas as pd

def rank_items(csv_path: str):
    """
    Reads a CSV file and ranks items based on
    the average of multiple score columns.
    """
    df = pd.read_csv(csv_path)

    score_columns = [
        "score_quality",
        "score_cost",
        "score_reliability"
    ]

    df["final_score"] = df[score_columns].mean(axis=1)
    ranked_df = df.sort_values(by="final_score", ascending=False)

    return ranked_df


if __name__ == "__main__":
    ranked_items = rank_items("../data/sample_data.csv")
    print(ranked_items[["item_id", "final_score"]])
