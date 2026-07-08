# PromptLab — Prompt Evaluation Framework

A systematic prompt engineering tool that runs multiple prompt variations against a task, scores each output automatically using a second LLM call, logs results to a database, and visualizes which prompts perform best.

## Live Demo
[View the app here](https://awab-promptlab.streamlit.app)

## The Problem It Solves
Most teams using AI pick prompts by guessing or using whatever was written first. PromptLab makes prompt selection data-driven by running controlled evaluations and scoring outputs on defined criteria.

## What It Does
- Accepts a business task and up to 3 prompt variations as input
- Runs each prompt against Llama 3 via Groq API and collects outputs
- Scores each output automatically on clarity, conciseness, and relevance out of 10
- Logs all results to a SQLite database for historical tracking
- Displays a comparison dashboard showing scores, trends, and the best performing prompt

## Tech Stack
- Python
- Groq API and Llama 3 (prompt execution and automated scoring)
- SQLite (evaluation logging and persistence)
- Pandas (data manipulation and history queries)
- Plotly (score comparison charts)
- Streamlit (web app interface)

## How It Works
1. User defines a task name and input text
2. User writes 3 prompt variations for