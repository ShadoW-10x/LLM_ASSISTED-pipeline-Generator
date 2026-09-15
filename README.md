# LLM-Assisted Pipeline Generator

Generates working [dlt](https://dlthub.com/) data ingestion pipelines from a
plain-English API description, using an LLM (openai/gpt-oss-120b via Groq, free).

Repo: https://github.com/ShadoW-10x/LLM_ASSISTED-pipeline-Generator

## How it works

```
CLI (local)  ->  API Gateway (AWS)  ->  Lambda (AWS, calls Groq)  ->  generated pipeline code
```

The backend is **hosted on AWS Lambda**, exposed through API Gateway. The CLI
sends an API description to the deployed endpoint and saves the returned
pipeline code locally - the LLM call itself runs on AWS, not on your machine.

## Project structure

```



LLM Assisted Pipeline Generator/cli.py                 # CLI frontend - calls the AWS-hosted backend
LLM Assisted Pipeline Generator/lambda_handler.py  # backend logic, deployed as a Lambda function
LLM Assisted Pipeline Generator/DEPLOY.md          # AWS deployment steps
requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

Get a free Groq API key: https://console.groq.com/keys

## Usage

**Via the deployed CLI (uses AWS Lambda backend):**
```bash
cd cli_app
python cli.py "Open-Meteo weather API, base url https://api.open-meteo.com, no auth, endpoint /v1/forecast, single JSON response with columnar hourly data (time, temperature_2m as parallel arrays), no pagination"
```

This writes `generated_pipeline.py` with the pipeline the LLM wrote.

## Deploying your own backend

See [`aws_backend/DEPLOY.md`](aws_backend/DEPLOY.md) for the full Lambda +
API Gateway setup. After deploying, set `API_URL` in `cli_app/cli.py` to your
API Gateway Invoke URL.
