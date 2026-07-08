import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os
import json
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(
    page_title="PromptLab",
    page_icon="icon.jpg",
    layout="wide"
)

# Database setup
def init_db():
    conn = sqlite3.connect("promptlab.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            task TEXT,
            prompt_label TEXT,
            prompt_text TEXT,
            output TEXT,
            clarity_score INTEGER,
            conciseness_score INTEGER,
            relevance_score INTEGER,
            total_score INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

def run_prompt(prompt_text, task_input):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": f"{prompt_text}\n\nInput: {task_input}"}
        ],
        temperature=0.3,
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

def score_output(output, task_input):
    scoring_prompt = f"""
You are an objective evaluator. Score the following AI output on three criteria.
Task input was: {task_input}
AI output: {output}

Score each criterion from 1 to 10:
- Clarity: Is the output clear and easy to understand?
- Conciseness: Is it appropriately concise without losing important information?
- Relevance: Does it directly address the task input?

Respond ONLY with a JSON object in this exact format, nothing else:
{{"clarity": 7, "conciseness": 8, "relevance": 9}}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": scoring_prompt}],
        temperature=0
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    scores = json.loads(raw)
    return scores

def save_result(task, label, prompt_text, output, scores):
    conn = sqlite3.connect("promptlab.db")
    conn.execute("""
        INSERT INTO evaluations
        (timestamp, task, prompt_label, prompt_text, output, clarity_score,
         conciseness_score, relevance_score, total_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        task,
        label,
        prompt_text,
        output,
        scores["clarity"],
        scores["conciseness"],
        scores["relevance"],
        scores["clarity"] + scores["conciseness"] + scores["relevance"]
    ))
    conn.commit()
    conn.close()

def load_history():
    conn = sqlite3.connect("promptlab.db")
    try:
        df = pd.read_sql("SELECT * FROM evaluations ORDER BY timestamp DESC", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# UI
st.title("PromptLab — Prompt Evaluation Framework")
st.markdown("Test multiple prompt variations against a task, score outputs automatically, and identify which prompts perform best.")
st.divider()

tab1, tab2 = st.tabs(["Run Evaluation", "Results Dashboard"])

with tab1:
    st.subheader("Define Your Task")
    
    task_name = st.text_input(
        "Task name",
        placeholder="e.g. Customer Complaint Summarization"
    )
    
    task_input = st.text_area(
        "Task input (the content the prompt will process)",
        placeholder="e.g. I have been waiting 3 weeks for my order and nobody is responding to my emails. This is completely unacceptable and I want a full refund immediately.",
        height=100
    )
    
    st.subheader("Define Prompt Variations")
    st.markdown("Write 3 different prompts for the same task. The app will run all 3 and score them.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        label1 = st.text_input("Prompt 1 label", value="Direct")
        prompt1 = st.text_area(
            "Prompt 1",
            value="Summarize the following customer complaint in one sentence.",
            height=150
        )
    
    with col2:
        label2 = st.text_input("Prompt 2 label", value="Structured")
        prompt2 = st.text_area(
            "Prompt 2",
            value="You are a customer service analyst. Extract: (1) the core issue, (2) the customer emotion, (3) the requested resolution. Be concise.",
            height=150
        )
    
    with col3:
        label3 = st.text_input("Prompt 3 label", value="Empathetic")
        prompt3 = st.text_area(
            "Prompt 3",
            value="You are a helpful assistant. Summarize this customer complaint with empathy, identify the main problem, and suggest one action the support team should take.",
            height=150
        )
    
    if st.button("Run Evaluation", type="primary"):
        if not task_name or not task_input:
            st.error("Please fill in both the task name and task input.")
        else:
            prompts = [
                (label1, prompt1),
                (label2, prompt2),
                (label3, prompt3)
            ]
            
            results = []
            
            for label, prompt in prompts:
                with st.spinner(f"Running prompt: {label}..."):
                    output = run_prompt(prompt, task_input)
                    scores = score_output(output, task_input)
                    save_result(task_name, label, prompt, output, scores)
                    results.append({
                        "label": label,
                        "output": output,
                        "scores": scores
                    })
            
            st.success("Evaluation complete.")
            st.divider()
            
            # Show results
            for r in results:
                total = sum(r["scores"].values())
                st.subheader(f"Prompt: {r['label']} — Total Score: {total}/30")
                st.markdown(f"**Output:** {r['output']}")
                
                score_cols = st.columns(3)
                score_cols[0].metric("Clarity", f"{r['scores']['clarity']}/10")
                score_cols[1].metric("Conciseness", f"{r['scores']['conciseness']}/10")
                score_cols[2].metric("Relevance", f"{r['scores']['relevance']}/10")
                st.divider()
            
            # Winner
            best = max(results, key=lambda x: sum(x["scores"].values()))
            st.success(f"Best performing prompt: {best['label']} with a total score of {sum(best['scores'].values())}/30")

with tab2:
    st.subheader("Evaluation History")
    
    df = load_history()
    
    if df.empty:
        st.info("No evaluations yet. Run an evaluation in the first tab.")
    else:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Evaluations", len(df))
        col2.metric("Unique Tasks", df["task"].nunique())
        col3.metric("Avg Total Score", f"{df['total_score'].mean():.1f}/30")
        
        st.divider()
        
        # Score comparison chart
        st.subheader("Score Comparison by Prompt")
        fig = px.bar(
            df,
            x="prompt_label",
            y="total_score",
            color="task",
            barmode="group",
            title="Total Scores by Prompt Variation"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed breakdown
        st.subheader("Score Breakdown")
        score_df = df[["prompt_label", "clarity_score", "conciseness_score", "relevance_score", "total_score", "task", "timestamp"]]
        st.dataframe(score_df, use_container_width=True)
        
        # Best prompt per task
        st.subheader("Best Prompt per Task")
        best_df = df.loc[df.groupby("task")["total_score"].idxmax()][["task", "prompt_label", "total_score"]]
        st.dataframe(best_df, use_container_width=True)

st.divider()
st.caption("Powered by Groq Llama 3 | Scores generated automatically by LLM evaluation")