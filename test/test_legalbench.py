import requests
from pathlib import Path
from itertools import groupby
import random
import json


FOLDER = "datasets/LegalBench-RAG/corpus/"
DOMAIN = "http://localhost:8000"
DATASET = "legalbench"
SUMMARIES = "datasets/selected/summaries.json"
# contractnli : NDA agreements
# cuad : other agreements
# maud : merger agreement
# privacy_qa : privacy policy


def summarize_document(path: str, title: str):
    # This function takes a file path and a title, reads the content of the file,
    # and sends it to an API endpoint for summarization.
    with open(path, encoding="utf-8") as file:
        content = file.read()
        r = requests.post(
            DOMAIN + "/api/summarize",
            json={"text": content, "type": "text", "dataset": DATASET, "title": title},
        )
        print(r.json())


def upload_document(path: str, title: str):
    # This function takes a file path and a title, reads the content of the file, retrieves a summary from a local JSON file,
    # and sends the content along with the summary to an API endpoint for uploading.
    # The prompt for the API includes the title of the document and its text content.
    with open(SUMMARIES, "r") as s:
        d = json.load(s)
        summary = d[title]
        with open(path, encoding="utf-8") as file:
            content = file.read()
            r = requests.post(
                DOMAIN + "/api/documents",
                json={
                    "text": content,
                    "type": "text",
                    "dataset": DATASET,
                    "title": title,
                    "summary": summary,
                },
            )
            print(title)


def list_all_files(folder):
    return [
        (str(p).split("\\")[3], str(p), p.name)
        for p in Path(folder).rglob("*")
        if p.is_file()
    ]


def upload_files_1(n: None | int = None):
    # Old version of the upload function
    files = list_all_files(FOLDER)
    if n:
        files = files[:n]
    n = len(files)
    i = 0
    for path, name in files:
        i += 1
        upload_document(path, name)
        print(f"{i}/{n}")


def select_subset():
    # Select a random subset of files for each category.
    files = list_all_files(FOLDER)
    groups = [list(g) for k, g in groupby(files, lambda x: x[0])]
    size = 10
    groups = {l[0][0]: l if len(l) <= size else random.sample(l, size) for l in groups}
    with open("datasets/selected/legalbench.json", "w") as f:
        json.dump(groups, f)


def upload_files_2():
    # Old version of the upload function
    with open("datasets/selected/legalbench.json", "r") as f:
        groups = json.load(f)
        files = [i[1:] for l in groups.values() for i in l]
        n = len(files)
        i = 0
        for path, name in files:
            i += 1
            upload_document(path, name)
            print(f"{i}/{n}")


def retrieve_saved_summaries():
    # This function retrieves summaries from a local JSON file and updates it with any new summaries found in
    # the documents retrieved from an API endpoint.
    f_read = open(SUMMARIES, "r")

    d = json.load(f_read)
    r = requests.get(
        DOMAIN + "/api/documents",
    )
    content = r.json()
    for doc in content["docs"]:
        file = doc["metadata"]["source"]
        summary = doc["metadata"]["summary"]
        if file not in d:
            d[file] = summary
    f_read.close()
    f_write = open(SUMMARIES, "w")
    json.dump(d, f_write)
    f_write.close()
