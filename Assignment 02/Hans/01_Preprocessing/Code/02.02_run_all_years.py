"""
Run notebook 02 for many years, one after the other.

Why: notebook 02 does everything for ONE year (set by YEAR). Instead of changing YEAR by hand and
clicking "run all" 21 times, this script runs the notebook once per year. Each year gets its own
fresh Python process, so memory is freed between the years.

How to use (in a terminal, in this Code folder, with the same Python you use for the notebooks):

    python 02.02_run_all_years.py                    # 2006 to 2026, development users
    python 02.02_run_all_years.py 2010 2011 2012     # only these years (also how you continue after a failure)
    python 02.02_run_all_years.py --all-users        # all users instead of the development users

The notebook itself is not changed by this: the results are the files notebook 02 always saves
(song table in Output_dev/data/parquets/songs/, genre counts and coverage in Output_dev/genre_counts/<year>/).
If a year fails (for example the check "listens add up" does not hold), the script prints the error,
goes on with the next year, and lists the failed years at the end.

Needs: pip install nbclient nbformat ipykernel
"""
import argparse
import os
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient

CODE_DIR = Path(__file__).resolve().parent
NOTEBOOK = CODE_DIR / "02_From_listens_to_genres.ipynb"

parser = argparse.ArgumentParser(description="Run notebook 02 for several years.")
parser.add_argument("years", nargs="*", type=int, help="the years to run (default: 2006 to 2026)")
parser.add_argument("--all-users", action="store_true", help="all users instead of the development users (bucket 0-9)")
args = parser.parse_args()

years = args.years or list(range(2006, 2027))
os.environ["DEV_ONLY"] = "0" if args.all_users else "1"      # the notebook reads this (see its setup cell)

print(f"running notebook 02 for {len(years)} years: {years[0]} ... {years[-1]}")
print("users:", "all users" if args.all_users else "development users (bucket 0-9)")

failed = []
total_start = time.time()
for year in years:
    os.environ["YEAR"] = str(year)                           # the notebook reads this too
    start = time.time()
    print(f"  {year}: starting ...", flush=True)
    nb = nbformat.read(NOTEBOOK, as_version=4)               # read a fresh copy of the notebook every year
    kernel = nb.metadata.get("kernelspec", {}).get("name", "python3")
    client = NotebookClient(nb, timeout=None, kernel_name=kernel,
                            resources={"metadata": {"path": str(CODE_DIR)}})   # run it as if it sat in the Code folder
    try:
        client.execute()
        print(f"  {year}: done in {(time.time() - start) / 60:.1f} min", flush=True)
    except Exception as error:                               # a failing cell, a crashed kernel, ...
        failed.append(year)
        print(f"  {year}: FAILED after {(time.time() - start) / 60:.1f} min\n{str(error)[-1200:]}", flush=True)

print(f"\nall done in {(time.time() - total_start) / 60:.0f} min")
print("failed years:", failed if failed else "none")
