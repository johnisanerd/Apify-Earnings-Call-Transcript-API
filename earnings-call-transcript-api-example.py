"""
Earnings Call Transcript API: A Quick Start Example
See more at: https://apify.com/johnvc/earnings-call-transcript-api?fpr=9n7kx3
Input schema: https://apify.com/johnvc/earnings-call-transcript-api/input-schema?fpr=9n7kx3

This script shows how to call the Earnings Call Transcript API on Apify from
Python and read its structured JSON output: speaker-tagged earnings call
transcripts with Q&A pairs, and SEC 8-K filings parsed item by item. It
exercises several input parameters so you can see what is configurable, while
keeping the run small so your first call stays cheap.

Get your free Apify API key at: https://apify.com?fpr=9n7kx3
"""

import os
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

# Initialize the Apify client with your API token (read from .env)
client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

# Build the Actor input.
# Inputs are kept small (one ticker, 2 filings, 1 transcript) to keep this
# first run inexpensive; at the pay-per-record price this run costs well under
# a cent. Raise the limits once you know your budget.
run_input = {
    "tickers": ["AAPL"],            # stock symbols or CIK numbers
    "dataType": "both",             # "filings", "transcripts", or "both"
    "filingsLimit": 2,              # max 8-K filings per ticker (1-200)
    "transcriptsLimit": 1,          # max earnings call transcripts per ticker (1-40)
    "includeFullText": False,       # structured fields only; flip on for full documents
    # Other useful options (see the input schema for all of them):
    # "eventCategories": ["earnings", "executive_changes"],
    # "itemCodes": ["2.02"],
    # "dateFrom": "2026-01-01", "dateTo": "2026-06-30",
    # "searchKeyword": "guidance withdrawal",  # full-text search across ALL US filers
    # "onlyNew": True,                          # monitoring mode with a schedule
}

# Run the Actor and wait for it to finish
run = client.actor("johnvc/earnings-call-transcript-api").call(run_input=run_input)
if run is None:
    raise SystemExit("The Actor run did not return a result.")

# Read structured results from the run's default dataset
# (apify-client 3.x returns a Run object; use .default_dataset_id, not run["..."])
items = list(client.dataset(run.default_dataset_id).iterate_items())
print(f"Returned {len(items)} record(s).\n")

for item in items:
    kind = item.get("recordType")
    if kind == "filing":
        print(f"8-K FILING | {item.get('ticker')} | {item.get('filedDate')} | items {item.get('itemCodes')}")
        print(f"  {item.get('title')}")
        if item.get("pressRelease"):
            print(f"  Press release: {item['pressRelease'].get('headline')}")
        for sentence in (item.get("guidanceSentences") or [])[:2]:
            print(f"  Guidance: {sentence[:120]}")
        print(f"  Sentiment (net): {item.get('sentimentNet')} | EDGAR: {item.get('url')}\n")
    elif kind == "transcript":
        print(f"TRANSCRIPT | {item.get('ticker')} | {item.get('fiscalQuarter')} | {item.get('callDate')}")
        print(f"  {item.get('title')}")
        print(f"  Speakers: {item.get('speakerCount')} | Analyst questions: {item.get('questionCount')}")
        qa = (item.get("qaPairs") or [])
        if qa:
            q = qa[0]["question"]
            print(f"  First question ({q.get('speaker')}, {q.get('affiliation')}): {q.get('text', '')[:120]}")
        for sentence in (item.get("guidanceSentences") or [])[:2]:
            print(f"  Guidance: {sentence[:120]}")
        print(f"  Sentiment (net): {item.get('sentimentNet')}\n")
    elif kind == "error":
        # Error rows explain missing data (for example, no transcript for a
        # micro cap); they are never charged.
        print(f"NOTE | {item.get('errorMessage')}\n")
