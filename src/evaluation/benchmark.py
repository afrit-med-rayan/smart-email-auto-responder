"""
Performance Benchmark
"""
import time
import json
import os
import argparse
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def benchmark_inference(num_requests=100, mock=True):
    latencies = []
    
    logger.info(f"Starting benchmark with {num_requests} requests...")
    
    for i in range(num_requests):
        start_time = time.time()
        
        # Simulate inference
        if mock:
            # Simulate processing time between 50ms and 200ms
            time.sleep(np.random.uniform(0.05, 0.2))
        else:
            # TODO: Call actual inference function
            pass
            
        end_time = time.time()
        latencies.append((end_time - start_time) * 1000) # Convert to ms

    avg_latency = np.mean(latencies)
    p95_latency = np.percentile(latencies, 95)
    p99_latency = np.percentile(latencies, 99)
    throughput = num_requests / (sum(latencies) / 1000)
    
    return {
        "num_requests": num_requests,
        "avg_latency_ms": round(avg_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "p99_latency_ms": round(p99_latency, 2),
        "throughput_rps": round(throughput, 2),
        "latencies": latencies # Save all for histogram
    }

def main():
    parser = argparse.ArgumentParser(description="Benchmark Performance")
    parser.add_argument("--num_requests", type=int, default=100, help="Number of requests")
    parser.add_argument("--results_dir", type=str, default="results", help="Results directory")
    parser.add_argument("--mock", action="store_true", help="Use mock inference")
    args = parser.parse_args()

    os.makedirs(args.results_dir, exist_ok=True)
    
    results = benchmark_inference(args.num_requests, args.mock)
    
    logger.info(f"Benchmark Results: {results}")
    
    output_file = os.path.join(args.results_dir, "benchmark.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
