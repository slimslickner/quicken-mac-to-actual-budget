# %%
# Imports
import csv
from pathlib import Path
import pandas as pd
import yaml
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# %%
# Setup Reference Variables
path_to_raw_csv = Path("data/raw_banking_export/")
source_file = sorted(path_to_raw_csv.iterdir(), reverse=True)[0]
logging.info(f"Source file: {source_file}")
working_filepath = Path("data/working/working.csv")

config_path = Path("config/config.yaml")
start_date = "2024-02-29"

# %%
# Read Config
with open(config_path, "r") as f:
    config = yaml.safe_load(f)
logging.info("Config file loaded")

# %%
# Reformat the exported transactions to only have meaningful data
with open(source_file, "r") as f:
    csv_reader = csv.reader(f)
    with open(working_filepath, "w", newline="") as fw:
        csv_writer = csv.writer(fw)
        writing = False
        for r in csv_reader:
            if "Account" in r:
                writing = True
            if writing:
                csv_writer.writerow(r[1:])
logging.info("Reformatted transactions written to working CSV")

# %%
# Read in the working CSV that was just created
df = pd.read_csv(working_filepath, na_values=["0", "NULL", "NA"])
logging.info("Working CSV read into DataFrame")

# Rename headers
df = df.rename(
    columns={
        "Date": "date",
        "Account": "account",
        "Payee": "payee",
        "Memo/Notes": "notes",
        "Category": "category",
        "Amount": "amount",
        "FITID": "fitid",
        "Clr": "clr",
        "Tags": "tags",
    }
)
logging.info("Headers renamed")

# Convert Datatypes
df["amount"] = df["amount"].str.replace(",", "").astype(float)
df["date"] = pd.to_datetime(df["date"], format="mixed")
logging.info("Data types converted")

# %%
# Get config payee groups
df_groupby_payees = pd.DataFrame(config["groupby_payees"])
income_payees = df_groupby_payees[df_groupby_payees["category"] == "Income"][
    "payee"
].to_list()
logging.info("Config payee groups loaded")

# %%
# Get only dates after 2/29/24
df = df[df["date"] >= pd.to_datetime(start_date)]
logging.info("Filtered transactions by date")

# %%
# Get only transactions from relevant accounts
account_list = config["accounts"]
df = df[df["account"].isin(account_list)]
logging.info("Filtered transactions by relevant accounts")

# %%
# Get only cleared transactions
df = df[df["clr"] == "R"]
logging.info("Filtered cleared transactions")

# %%
# Clean data
df["notes"] = df["notes"].fillna("")
df["fitid"] = df["fitid"].fillna("")
df["payee"] = df["payee"].str.replace("{", " - ").str.replace("}", "")
df["Split"] = df["Split"].fillna("")
df["Scheduled"] = df["Scheduled"].fillna("")
df["tags"] = df["tags"].fillna("")
logging.info("Cleaned data")

# %%
# Set the category to the last item in the split on :
df["category"] = df["category"].str.split(":").str[-1]
logging.info("Set category to the last item in the split")

# %%
# Change tags from comma separated to hashtags
df["tags"] = df["tags"].apply(
    lambda tags: "".join([f"#{tag}" for tag in tags.split(", ")])
)
logging.info("Transformed tags to hashtags")

# %%
# Add tags to the notes line
df["notes"] = df.apply(
    lambda x: (
        f"{x['tags']} {x['notes']}".strip()
        if x["notes"] and x["tags"]
        else x["notes"] or x["tags"]
    ),
    axis="columns",
)
logging.info("Added tags to notes")

# %%
# Update the groupby payees
df = df.merge(df_groupby_payees, on="payee", how="left", suffixes=("", "_groupby"))
df["category"] = df["category_groupby"].combine_first(df["category"])
df["notes"] = df["notes_groupby"].combine_first(df["notes"])
df["tags"] = df["tags_groupby"].combine_first(df["tags"])
df = df.drop(["category_groupby", "notes_groupby", "tags_groupby"], axis=1)
logging.info("Updated groupby payees")

# %%
# Group by fitid to resolve Splits, this should really only merge income payees
df = (
    df.groupby(["date", "account", "payee", "category", "notes", "fitid"])
    .agg({"amount": "sum"})
    .reset_index()
    .round(2)
)
logging.info("Grouped by fitid to resolve splits")

# %%
# Write the new full dataset to CSV
output_dir = Path("data/processed/")
output_dir.mkdir(parents=True, exist_ok=True)
df.to_csv(output_dir / "full.csv", index=False)
logging.info("Full dataset written to CSV")

# Write individual files out
for account in df["account"].unique():
    new_df = df[df["account"] == account]
    final_df = new_df[["date", "payee", "notes", "category", "amount"]]
    stripped_account = account.replace(" ", "").replace("'", "")
    final_df.to_csv(output_dir / f"{stripped_account}.csv", index=False)
    logging.info(f"Processed account: {account}")

logging.info(f"Processed {source_file}")

# %%
