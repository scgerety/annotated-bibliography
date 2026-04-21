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
from top2vec import Top2Vec

CORE_api = os.getenv('CORE')
HF_TOKEN = os.getenv('HF_TOKEN')
query = " ".join(sys.argv[1:])
this_dir = os.path.dirname(os.path.abspath(__file__))
result_json = os.path.join(this_dir, "result.json")
result_csv = os.path.join(this_dir, "result.csv")

def main():
    # query() # Needed once every new query.
    data = load_result()
    # train_model(data) # Needed only during setup stage. Not for every query.
    doc_tokens = analyze_full_text()
    save_result(data, doc_tokens)


def query(query=query, api_key=CORE_api):
    url = "https://api.core.ac.uk/v3/search/works"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "q": f"{query}", # Just use a basic query for CORE. Searching title or
                         # abstract seems to get useless results.
        "scroll": True,
        "limit": 100,
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            results = response.json()
            results = results["results"] # Only focus on results for purpose of
                                         # training. Everything else is noise.
            with open(result_json, "w") as r:
                r.write(json.dumps(results, indent=4))
        else:
            print(f"Error: {response.status_code}: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def load_result():
    with open(result_json) as j:
        data = json.load(j)
    data = [{
        "id": doc["id"],
        "authors": doc["authors"],
        "title": doc["title"],
        "publishedDate": doc["publishedDate"] if "publishedDate" in doc.keys() else None,
        "abstract": doc["abstract"],
        "fullText": doc["fullText"],
        } for doc in data]
    return data


def train_model(data):
    docs = [doc["fullText"] for doc in data]
    model = Top2Vec(docs,
                    speed="deep-learn",
                    workers=8,
                    ngram_vocab=True,
                    contextual_top2vec=True,
                    )

    model.save("bib.model")


def analyze_full_text():
    model = Top2Vec.load("bib.model")
    doc_tokens = [doc for doc in model.get_document_tokens()]
    return doc_tokens


def save_result(data, doc_tokens):
    with open(result_csv, "a") as token_list:
        token_list.write("id|authors|title|publishedDate|abstract|tokens\n") # Delimiter is | (pipe). If using pandas,
                                                                             # use sep="|" param.
        for row, tokens in zip(data, doc_tokens):
            if type(row["abstract"]) is str:
                row["abstract"] = row["abstract"].replace("\n", " ") # Not losing any data here.
            token_list.write(f'{row["id"]}|{row["authors"]}|{row["title"]}|{row["publishedDate"]}|"{row["abstract"]}"|')
            token_list.write("-".join(tokens))
            token_list.write("\n")


if __name__ == "__main__":
    main()
