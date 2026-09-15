"""
AWS Lambda handler for the pipeline generator backend.

Deployed behind API Gateway. Receives a POST request with an API
description, calls Groq's LLM, returns generated dlt pipeline code.

"""

import json
import os
import re
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])  # set as a Lambda env var

SCAFFOLD_REST_API = '''
PATTERN A — use for APIs that return a LIST of records, optionally paginated:

from dlt.sources.rest_api import rest_api_source
import dlt

def build_source():
    return rest_api_source({
        "client": {
            "base_url": "<BASE_URL>",
            "auth": {"type": "<none | bearer_token | api_key>"},
        },
        "resources": [
            {
                "name": "<resource_name>",
                "endpoint": {
                    "path": "<endpoint path>",
                    "params": {"per_page": 100},
                    "paginator": {"type": "<page_number | cursor | offset | none>"},
                },
                "write_disposition": "merge",
                "primary_key": "id",
            },
        ],
    })

def run():
    pipeline = dlt.pipeline(pipeline_name="<name>_pipeline", destination="duckdb", dataset_name="<name>_data")
    load_info = pipeline.run(build_source())
    print(load_info)

if __name__ == "__main__":
    run()
'''

SCAFFOLD_CUSTOM_RESOURCE = '''
PATTERN B — use for a single JSON response that is NOT a flat list of records
(e.g. columnar data, nested objects that need reshaping into rows, no
pagination). Write a plain @dlt.resource generator function that fetches
the data with `requests` and yields one dict per row:

import dlt
import requests

@dlt.resource(write_disposition="<append | merge>", name="<resource_name>")
def fetch_data(<params with sensible defaults>):
    response = requests.get("<BASE_URL + path>", params={...})
    response.raise_for_status()
    data = response.json()

    for row in <reshaped rows>:
        yield row

def run():
    pipeline = dlt.pipeline(pipeline_name="<name>_pipeline", destination="duckdb", dataset_name="<name>_data")
    load_info = pipeline.run(fetch_data())
    print(load_info)

if __name__ == "__main__":
    run()
'''

SYSTEM_PROMPT = f"""You are a data engineer who writes dlt (data load tool) pipelines.
You ONLY output a complete, runnable Python file. No explanations, no markdown fences.

You will be given a description of an API. First decide which pattern fits:

{SCAFFOLD_REST_API}

{SCAFFOLD_CUSTOM_RESOURCE}

Rules:
- If the API returns a paginated list of records -> use Pattern A.
- If the API returns a single response that needs reshaping (columnar data,
  nested structures, no pagination) -> use Pattern B.
- Pick the correct auth type. If the API needs a key, read it from
  dlt.secrets.value instead of hardcoding it.
- Keep primary_key and write_disposition sensible for the data described.
- Output ONLY valid Python code, nothing else — no markdown fences, no commentary.
"""


def generate_pipeline(api_description: str) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Write a dlt pipeline for this API:\n\n{api_description}"},
        ],
        temperature=0.2,
    )
    code = response.choices[0].message.content
    code = re.sub(r"^```(?:python)?\n?", "", code.strip())
    code = re.sub(r"\n?```$", "", code.strip())
    return code


def lambda_handler(event, context):
    """
    Entry point AWS Lambda calls. `event` is the API Gateway request.
    Expects JSON body: {"description": "..."}
    """
    try:
        body = json.loads(event.get("body") or "{}")
        description = body.get("description", "").strip()

        if not description:
            return _response(400, {"error": "Missing 'description' in request body"})

        code = generate_pipeline(description)
        return _response(200, {"code": code})

    except Exception as e:
        return _response(500, {"error": str(e)})


def _response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
