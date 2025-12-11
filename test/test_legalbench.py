import os
import requests

FOLDER = "datasets/LegalBench-RAG/corpus/"
DOMAIN = "http://localhost:8000"
DATASET = "legalbench"


def upload_document(path: str):
    with open(path, encoding="utf-8") as file:
        content = file.read()
        r = requests.post(
            DOMAIN + "/api/documents",
            json={"text": content, "type": "text", "dataset": DATASET},
        )
        print(r.text)


upload_document(FOLDER + "privacy_qa/23andMe.txt")
