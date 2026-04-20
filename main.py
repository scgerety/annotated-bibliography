#!/usr/bin/env python
"""
annotated-bibliography
version=0.0.1
author=scgerety
"""

import json
import os
import sys
import requests
import pandas as pd

CORE_api = os.getenv('CORE')
query = " ".join(sys.argv[1:])
this_dir = os.path.dirname(os.path.abspath(__file__))
result_json = os.path.join(this_dir, "result.json")
result_csv = os.path.join(this_dir, "result.csv")

def main():
    query()
    df = load_result()
    df = analyze_full_text(df)
    save_result(df)


def query(query=query, api_key=CORE_api):
    url = "https://api.core.ac.uk/v3/search/works"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "q": f"{query}", # Just use a basic query for CORE. Searching title or abstract
                         # seems to get useless results.
        "scroll": True,
        "limit": 100,
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            results = response.json()
            results = results["results"]
            with open(result_json, "w") as r:
                r.write(json.dumps(results, indent=4))
        else:
            print(f"Error: {response.status_code}: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def load_result():
    df = pd.read_json(result_json)
    df = df[[
        "id",
        "title",
        "authors",
        "abstract",
        "fullText",
    ]]
    return df


def analyze_full_text(df):
   df = df[[
        "id",
        "title",
        "authors",
        "abstract",
    ]] 
   df["topics"] = 0
   return df

def save_result(df):
    df.to_csv(result_csv)


if __name__ == "__main__":
    main()
