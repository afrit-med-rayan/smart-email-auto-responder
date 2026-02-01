"""
Update Results Report
"""
import json
import os
import datetime

RESULTS_DIR = "results"
REPORT_FILE = "EVALUATION.md"

def load_json(filename):
    path = os.path.join(RESULTS_DIR, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

def generate_report():
    report = f"# Evaluation Report\n\nGenerated on: {datetime.datetime.now()}\n\n"
    
    # Classification
    class_metrics = load_json("classification_metrics.json")
    if class_metrics:
        report += "## 1. Classification Metrics\n\n"
        report += "| Target | Accuracy | Precision | Recall | F1 |\n"
        report += "|---|---|---|---|---|\n"
        for m in class_metrics:
            report += f"| {m['target']} | {m['accuracy']:.2%} | {m['precision']:.2f} | {m['recall']:.2f} | {m['f1']:.2f} |\n"
        report += "\n"
        
    # Generation
    gen_metrics = load_json("generation_metrics.json")
    if gen_metrics:
        report += "## 2. Generation Metrics\n\n"
        report += f"- **BERTScore F1**: {gen_metrics['bertscore_f1']:.4f}\n"
        report += f"- **ROUGE-L**: {gen_metrics['rougeL']:.4f}\n"
        report += f"- **BLEU**: {gen_metrics['bleu']:.4f}\n\n"

    # Benchmark
    bench = load_json("benchmark.json")
    if bench:
        report += "## 3. Performance Benchmark\n\n"
        report += f"- **Throughput**: {bench['throughput_rps']} req/sec\n"
        report += f"- **Avg Latency**: {bench['avg_latency_ms']} ms\n"
        report += f"- **P95 Latency**: {bench['p95_latency_ms']} ms\n"
        
    with open(REPORT_FILE, "w") as f:
        f.write(report)
        
    print(f"Report generated: {REPORT_FILE}")

if __name__ == "__main__":
    generate_report()
