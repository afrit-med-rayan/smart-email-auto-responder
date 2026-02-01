import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Email Auto-Responder Evaluation", layout="wide")

st.title("📊 Email Auto-Responder Evaluation Dashboard")

RESULTS_DIR = "results"

def load_json(filename):
    path = os.path.join(RESULTS_DIR, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

# --- Classification Metrics ---
st.header("1. Classification Metrics")
class_metrics = load_json("classification_metrics.json")

if class_metrics:
    cols = st.columns(len(class_metrics))
    for i, metric in enumerate(class_metrics):
        with cols[i]:
            st.subheader(metric["target"].replace("label_", "").title())
            st.metric("Accuracy", f"{metric['accuracy']:.2%}")
            st.metric("F1 Score", f"{metric['f1']:.2f}")
            
    # Detailed Table
    st.dataframe(pd.DataFrame(class_metrics))
else:
    st.warning("No classification metrics found. Run `src/evaluation/metrics_classifier.py`.")

# --- Generation Metrics ---
st.header("2. Generation Metrics")
gen_metrics = load_json("generation_metrics.json")

if gen_metrics:
    col1, col2, col3 = st.columns(3)
    col1.metric("BERTScore F1", f"{gen_metrics['bertscore_f1']:.4f}")
    col2.metric("ROUGE-L", f"{gen_metrics['rougeL']:.4f}")
    col3.metric("BLEU", f"{gen_metrics['bleu']:.4f}")
    
    st.json(gen_metrics)
else:
    st.warning("No generation metrics found. Run `src/evaluation/metrics_generator.py`.")

# --- Performance Benchmark ---
st.header("3. System Performance")
bench_results = load_json("benchmark.json")

if bench_results:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Throughput", f"{bench_results['throughput_rps']} RPS")
    c2.metric("Avg Latency", f"{bench_results['avg_latency_ms']} ms")
    c3.metric("P95 Latency", f"{bench_results['p95_latency_ms']} ms")
    c4.metric("P99 Latency", f"{bench_results['p99_latency_ms']} ms")
    
    # Latency Histogram
    if "latencies" in bench_results:
        fig = px.histogram(bench_results["latencies"], nbins=20, title="Latency Distribution (ms)")
        st.plotly_chart(fig)
else:
    st.warning("No benchmark results found. Run `src/evaluation/benchmark.py`.")
