# quicken-mac-to-actual-budget
A data transformation tool to easily move transactions from Quicken Mac to Actual Budget. At a high level, this will take a single CSV export from Quicken and split it into separated and reformatted files for each account you have in Actual, which can be manually imported to the Actual instance.

## High Level Disclaimer
As of today, this is not intended to be plug-and-play. It is a manual process and there is some configuration which needs to happen which will make your implementation look different than `main`. With that said, I've been using this script for over a year without a hitch.

## How I leverage this tool
The use case for this python script is somewhat niche. I use Quicken Mac for my full financial picture and I use Actual Budget for [envelope] budgeting. Quicken is my source of truth, Actual is a copy of the Quicken data. As such, I run this once or twice a week to sync my Quicken data over to Actual. As a note, Actual Budget only includes my "Banking" accounts (Checking, Savings, Credit Cards).

### An example of how my Quicken Mac and Actual Budget implementations differ
My Quicken Mac transactions are categorized at a granular level (Groceries, Electricity, State Tax, Clothing, etc.) and tagged pertaining their broader category (the trip associated, the person who the purchase was for, the property the purchase was for, etc.).

In Actual Budget, most categories map to the same category or something more general (like Groceries -> Groceries or Clothing -> Shopping), based on how I would treat the budgeting category. The biggest difference is Actual is categorized based on one time purchases or trips, which would typically be tags in Quicken.

## File Overview
### `Pipfile`
This script uses [Pipenv](https://github.com/pypa/pipenv), which can be installed by following the instructions [here](https://github.com/pypa/pipenv?tab=readme-ov-file#installation). This can be replaced by a trusty `venv`, if preferred. I run the script on Python 3.11, but it would likely work on any version after 3.9 (untested).
- `notebook` could be omitted if you don't want to run the `csv_manipulation.py` file as a jupyter notebook.

### `src/config/config.yaml`
Three sections of this file provide metadata for the `csv_manipulation.py` script.
- `columns` is a dictionary of columns and their datatypes in the export from Quicken.
- `accounts` is a list of the names of the accounts to pay attention to in the export from Quicken.
- `groupby_payees` is a list of dictionaries defining payees from Quicken which are typically split transactions and groups them to a single transaction in Actual, applying the specified `category`, `notes`, and `tags`.
  - _Note: I use this to group Paychecks which are split into income, taxes, and transfers and group it to a single Income record in Actual._

### `src/csv_manipulation.py`
This is the meat of the repo! It takes the Quicken CSV export and transforms it to account-specific importable CSVs in Actual.

### `src/data/raw_banking_export`
This is the directory where you'll move the Quicken export to. More on this [here](exporting-from-quicken).

## Getting Started
### Clone this repo
Clone the repo with `git clone git@github.com:slimslickner/quicken-mac-to-actual-budget.git`.

### Set up the `pipenv` environment
Install the environment using `pipenv install`.

### Exporting from Quicken
I only include my Banking accounts in Actual, so the way I generate the export from Quicken is go to the Banking section on Quicken, remove all filters, and `File -> Export -> Register Transactions to CSV File...`.
- My Banking view includes the following columns: `Account`, `Amount`, `Attachments`, `Category`, `Clear`, `FITID`, `Memo/Notes`, `Modified`, `Payee`, `Status`, and `Tags`.
- `Attachments` and `Modified` are not required in your export.

Take the downloaded CSV file and move it to the `src/data/raw_banking_export` directory. I typically keep the default file name, which includes the date, because the script will grab the latest-dated file.

### Setting up `config.py`
| Key | Description |
| --- | --- |
| `start_date` | String value of the date you want to start exporting from Quicken in yyyy-mm-dd format. |
| `columns` | Dictionary of the columns in the Quicken export defining the datatype of each column. |
| `accounts` | A list of accounts to be processed for import into Actual. Each account will get its own file for importing. The account name here should match the Quicken account name exactly. |
| `groupby_payees` | A list of dictionaries with the following keys:<ul><li>`payee` - the payee in Quicken which should be grouped</li><li>`category` - the category which should be assigned after grouping</li><li>`notes` - the note which should be put on the transaction after grouping</li><li>`tags` - an Actual "tag" which should be prepended to the notes</li></ul> |

### Running the `csv_manipulation.py` file
I typically run the script within VSCode as a Jupyter notebook, which is why `notebook` is in the Pipfile.

Alternatively, the script can be run by navigating your terminal to the `src` directory and executing `pipenv run python csv_manipulation.py`.

_Note: The `working/working.csv` is a pre-processed file which removes some of the Quicken headers, so the dataset can be processed as a Pandas DataFrame._

### Importing to Actual
The output of `csv_manipulation.py` is a handful of files. Each account specified in the `config.yaml` file will get its own CSV file. From Actual Budget, you can navigate to an account, click "Import" at the top left, and select the corresponding file located in the `src/data/processed` directory after running `csv_manipulation.py`.

If you run this script week after week, Actual will be smart enough to only import "new" transactions.
