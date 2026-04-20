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
    show_all()

def query(query=query, api_key=CORE_api):
    url = "https://api.core.ac.uk/v3/search/works"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"q": {"title": f"{query}"}, "scroll": True, "limit": 100}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            with open(result_json, "w") as r:
                json.dump(response.json(), r)
        else:
            print(f"Error: {response.status_code}: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def show_all():

    df = pd.read_json(result_json)


if __name__ == "__main__":
    main()
