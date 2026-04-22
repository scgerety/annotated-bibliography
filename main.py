#!/usr/bin/env python
"""
annotated-bibliography
version=0.0.1
author=scgerety
"""

import json
import os
import requests
import sys
from top2vec import Top2Vec


CORE_api = os.getenv('CORE')
HF_TOKEN = os.getenv('HF_TOKEN')
query = " ".join(sys.argv[1:])
this_dir = os.path.dirname(os.path.abspath(__file__))
result_json = os.path.join(this_dir, "result.json")
result_csv = os.path.join(this_dir, "result.csv")
model_file = os.path.join(this_dir, "bib.model")


def main():
    query() # Needed once every new query.
    data = load_result()
    train_model(data) # Needed only during setup stage. Not for every query.
    theme_list = analyze_full_text()
    document_summaries = assign_topic_relevance()
    save_result(data, document_summaries, theme_list)


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
            results = [doc for doc in results["results"] if "language" in doc.keys() and doc["language"]["code"] == "en"]
            # Only focus on results for purpose of
            # training. Everything else is noise.
            # Also, filter only for english, since 
            # not using multilingual language model.
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
        } for doc in data if doc["language"]["code"] == "en"]
    return data


def train_model(data):
    docs = [doc["fullText"] for doc in data]
    model = Top2Vec(docs,
                    speed="deep-learn",
                    workers=8,
                    ngram_vocab=True,
                    contextual_top2vec=True,
                    )
    model.save(model_file)


def analyze_full_text():
    model = Top2Vec.load(model_file)
    
    topic_summaries = model.get_topics()
    themes = [model.similar_words(topic, 5) for topic in topic_summaries[0]]
    theme_list = []
    for theme, topic, score, idx in zip(themes, topic_summaries[0], topic_summaries[1], topic_summaries[2]):
        theme_list.append(",".join(word for word in theme[0]))
        theme = "_".join(word for word in theme[0]).replace(" ", "-")
        with open(f"{idx:02d}.{theme}.csv", "w") as d:
            d.write(f"{idx}\n{theme}\n")
            d.write("word|score\n")
            for word, word_score in zip(topic, score):
                d.write(f"{word}|{word_score}\n")
    return theme_list


def assign_topic_relevance():
    model = Top2Vec.load(model_file)
    document_summaries = model.get_document_topic_relevance()
    return document_summaries


def save_result(data, document_summaries, theme_list):
    with open(result_csv, "a") as token_list:
        token_list.write(
                f'id|authors|title|publishedDate|abstract|{"|".join(theme_list)}\n'
                ) # Delimiter is | (pipe). If using pandas, use sep="|" param.
        for row, topics in zip(data, document_summaries):
            if type(row["abstract"]) is str:
                row["abstract"] = row["abstract"].replace("\n", " ") # Not losing any data here.
            row["authors"] = [author["name"] for author in row["authors"]] # The author column is a list of dictionaries with one key: "name"
            topics = [str(relevance_score) for relevance_score in topics]
            token_list.write(
                f'{row["id"]}|{row["authors"]}|{row["title"]}|{row["publishedDate"]}|"{row["abstract"]}"|{"|".join(topics)}\n'
                )


if __name__ == "__main__":
    main()
