# %%
import csv
import os
import pandas as pd
import yaml

# %%
# Setup Reference Variables
path_to_raw_csv = "data/raw_banking_export/"
source_file = sorted(os.listdir(os.path.abspath(path_to_raw_csv)), reverse=True)[0]
print(source_file)
full_source_path = f"{path_to_raw_csv}/{source_file}"
print(full_source_path)
working_filepath = "data/working/working.csv"

config_path = "config/config.yaml"
start_date = "2024-02-29"

# %%
# Read Config
config = {}
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

# %%
# Reformat the exported transactions to only have meaningful data
with open(full_source_path, "r") as f:
    csv_reader = csv.reader(f)
    with open(working_filepath, "w") as fw:
        csv_writer = csv.writer(fw)
        writing = False
        for r in csv_reader:
            if "Account" in r:
                writing = True

            if writing:
                csv_writer.writerow(r[1:])


# %%
# Read in the working CSV that was just created
df = pd.read_csv(working_filepath, na_values=["0", "NULL", "NA"])

# rename headers
df = df.rename(columns={
    "Date": "date",
    "Account": "account",
    "Payee": "payee",
    "Memo/Notes": "notes",
    "Category": "category",
    "Amount": "amount",
    "FITID": "fitid",
    "Clr": "clr",
    "Tags": "tags"
    })

# Convert Datatypes
df["amount"] = df["amount"].str.replace(",", "")
df["amount"] = pd.to_numeric(df["amount"])
df["date"] = pd.to_datetime(df["date"], format="mixed")

# df.head()

# %%
# Get config payee groups
df_groupby_payees = pd.DataFrame(config["groupby_payees"])

income_payees = df_groupby_payees[df_groupby_payees["category"] == "Income"]["payee"].to_list()

# %%
# Get only dates after 2/29/24
df = df[df["date"] >= pd.to_datetime(start_date)]

# df.sort_values(by=["date"], ascending=False).head(20)

# %%
# Get only transactions from relevant accounts
account_list = config["accounts"]
df = df[df["account"].isin(account_list)]

# df.head()

# %%
# Get only cleared transactions
df = df[df["clr"] == "R"]

# df.head()

# %%
# Clean data
df["notes"] = df["notes"].fillna("")
df["fitid"] = df["fitid"].fillna("")
df["payee"] = df["payee"].str.replace("{", " - ").str.replace("}", "")
df["Split"] = df["Split"].fillna("")
df["Scheduled"] = df["Scheduled"].fillna("")
df["tags"] = df["tags"].fillna("")

# df.head(20)

# %%
# Set the category to the last item in the split on :
df["category"] = df["category"].str.split(":").str[-1]

# df.head()


# %%
# Change tags from comma separated to hashtags
def transform_tags(tags):
    # Split the string into a list
    tag_list = tags.split(", ")
    # Prepend "#" to each tag and join back into a single string
    transformed_tags = "".join([f"#{tag}" for tag in tag_list])
    return transformed_tags


# Apply the transformation to the "tags" column
df["tags"] = df["tags"].apply(transform_tags)

# %%
# Add tags to the notes line
df["notes"] = df.apply(
    lambda x: (
        f"{x['notes']} {x['tags']}".strip()
        if x["notes"] and x["tags"]
        else x["notes"] or x["tags"]
    ),
    axis="columns"
)

# %%
# Update the groupby payees
df = df.merge(df_groupby_payees, on="payee", how="left", suffixes=("", "_groupby"))
# df_groupby_merge.head()
df["category"] = df["category_groupby"].combine_first(df["category"])
df["notes"] = df["notes_groupby"].combine_first(df["notes"])
df["tags"] = df["tags_groupby"].combine_first(df["tags"])
# df.head(40)
df = df.drop(["category_groupby", "notes_groupby", "tags_groupby"], axis=1)

# %%
# Create a column to be used in split aggs
# df["notes"] = df.apply(
#     lambda x: (
#         f"{x['category']} {x['amount']} ({x['notes']})"
#         if x['Split'] == "S" and x['notes']
#         else f"{x['category']} {x['amount']}"
#         if x['Split'] == "S"
#         else x['notes']
#     ),
#     axis="columns"
# )

# df.head(20)

# %%
# Set category for income payees
# df["category"] = df.apply(
#     lambda x: "Income" if x["payee"] in income_payees else x["category"],
#     axis="columns"
# )

# # Set notes for income payees
# df["notes"] = df.apply(
#     lambda x: "Paycheck" if x["payee"] in income_payees else x["notes"],
#     axis="columns"
# )

# df.head(20)

# %%
# Group by fitid to resolve Splits, this should really only merge income payees
df = df.groupby(["date", "account", "payee", "category", "notes", "fitid"]) \
    .agg({
        # "notes": "|".join,
        "amount": "sum"
        }) \
    .reset_index() \
    .round(2)

df.head(20)
# df.sort_values(by=["date"], ascending=False).head(50)


# %%
# Write the new full dataset to CSV
print(f"{os.path.abspath('data/processed/')}/full.csv")
df.to_csv(f"{os.path.abspath('data/processed/')}/full.csv", index=False)

# Write individual files out
for account in df["account"].unique():
    print(account)
    new_df = df[df["account"] == account]
    final_df = new_df[["date", "payee", "notes", "category", "amount"]]
    final_df.to_csv(f"{os.path.abspath('data/processed/')}/{account}.csv".replace(" ", "").replace("'", ""), index=False)

print()
print(f"Processed {source_file}")

# %%
