import json
from datetime import datetime

response = {"message": "Hello"}
now = datetime.now()
with open(f'logs/{now.astimezone().strftime("%Y-%m-%d %H-%M-%S")} logs.json', "w") as f:
    json.dump(response, f)
