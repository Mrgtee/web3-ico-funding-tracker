# Web3 ICO & Funding Tracker Agent

This repository contains a **self-hosted LangGraph agent** built to run inside the **Warden App**.

The agent tracks **Web3 funding rounds, ICOs, token sales, TGEs, token claims, and crypto news** using **live, verifiable data**.
If information cannot be confirmed, the agent clearly says so.

---

## What This Agent Does

The agent can answer questions about:

* Web3 and crypto funding rounds
* ICO / IDO / IEO / presale announcements
* Token Generation Events (TGEs)
* Token claim / airdrop timelines (when officially announced)
* Crypto news (via CryptoPanic)

All answers are based on **live sources** and include links when available.

---

## What This Agent Does NOT Do

* No speculation or predictions
* No invented funding amounts, dates, or investors
* No fake “upcoming ICOs” without official announcements
* No hallucinated answers

If data is unavailable or unverified, the agent will say so explicitly.

---

## Model & Tools

* **LLM:** gemini-2.5-flash
* **Search Tool:** Tavily (live web search)
* **News Tool:** CryptoPanic API

The agent uses tools only when necessary and prioritizes official sources.

---

## How the Agent Runs

* Fully **self-hosted**
* Runs as a **LangGraph server**
* Docker-based
* Compatible with **Warden App streaming**
* No custom FastAPI layer

---

## Environment Variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key
CRYPTOPANIC_API_KEY=your_cryptopanic_api_key
LANGSMITH_TRACING=false
```

Secrets are not committed to the repository.

---

## Run with Docker

Build the image:

```bash
docker build -t web3-funding-tracker .
```

Run the container:

```bash
docker run -p 2024:2024 --env-file .env web3-funding-tracker
```

Health check:

```bash
curl http://127.0.0.1:2024/ok
```

---

## LangGraph Endpoints

The agent exposes standard LangGraph endpoints, including:

* `/assistants`
* `/threads`
* `/threads/{id}/runs/stream`
* `/ok`
* `/docs`

These endpoints are compatible with the Warden App runtime.

---

## Example Reviewer Prompts

```
Hello
What do you do?
Give me the latest crypto news today. Include links
Give me the latest crypto news for BTC. Include links
List recent Web3 funding rounds
Any ICO announcements in the last 24 hours?
When was the Cysic token claim?
```

Expected behavior:

* Uses live sources
* Includes links
* Refuses when information is not confirmed

---

## Design Principles

* Accuracy over completeness
* Refusal over hallucination
* Official sources over aggregators

This behavior is intentional and by design.

---

## Warden Compatibility

This agent:

* Is self-hosted
* Uses LangGraph standard APIs
* Supports streaming
* Has been tested with agentchat.vercel.app

---

## License

MIT

