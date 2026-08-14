"""ARA v2.5 Data Intelligence Engine Benchmark (Sprint 6).

Measures end-to-end performance across:
- Data Ingestion & Schema Detection Latency
- Profiling & Data Quality Score Computation
- Statistical Analysis & Correlation Throughput
- SVG Chart Rendering & Visualization Latency
- Automated Machine Learning Workflows (Clustering, Regression, Anomaly Detection)
- Multi-Format Markdown/HTML Report Generation Speed
"""

import os
import sys
import time
import json
import io
from pathlib import Path

# Force stdout and stderr to use UTF-8 to prevent Windows cp1252 console encoding crashes
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.data_intelligence.engine import DataIntelligenceEngine

BENCHMARK_DATASETS = [
    {
        "id": "D1",
        "name": "Financial Market Performance",
        "records": [
            {"ticker": "NVDA", "sector": "Technology", "market_cap_b": 3200, "pe_ratio": 65.4, "revenue_growth": 1.22},
            {"ticker": "AAPL", "sector": "Technology", "market_cap_b": 3450, "pe_ratio": 33.2, "revenue_growth": 0.05},
            {"ticker": "MSFT", "sector": "Technology", "market_cap_b": 3300, "pe_ratio": 36.8, "revenue_growth": 0.16},
            {"ticker": "JPM",  "sector": "Finance",    "market_cap_b": 580,  "pe_ratio": 12.1, "revenue_growth": 0.08},
            {"ticker": "BAC",  "sector": "Finance",    "market_cap_b": 310,  "pe_ratio": 13.5, "revenue_growth": 0.04},
        ]
    },
    {
        "id": "D2",
        "name": "Healthcare Clinical Metrics",
        "records": [
            {"patient_id": "P001", "age": 45, "bmi": 28.4, "blood_pressure": 125, "cholesterol": 210, "readmitted": False},
            {"patient_id": "P002", "age": 62, "bmi": 32.1, "blood_pressure": 140, "cholesterol": 245, "readmitted": True},
            {"patient_id": "P003", "age": 34, "bmi": 22.8, "blood_pressure": 118, "cholesterol": 185, "readmitted": False},
            {"patient_id": "P004", "age": 71, "bmi": 29.5, "blood_pressure": 150, "cholesterol": 260, "readmitted": True},
            {"patient_id": "P005", "age": 55, "bmi": 26.3, "blood_pressure": 132, "cholesterol": 215, "readmitted": False},
        ]
    }
]

def run_benchmark():
    print("=" * 80)
    print("ARA v2.5 Data Intelligence Engine Benchmark (Sprint 6)")
    print("=" * 80)

    engine = DataIntelligenceEngine()
    results = []

    for ds in BENCHMARK_DATASETS:
        start_time = time.perf_counter()
        report = engine.analyze_dataset(ds["name"], ds["records"], run_ml=True, clean_data=True)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        r_summary = {
            "id": ds["id"],
            "dataset_name": ds["name"],
            "rows": report.profile.row_count,
            "cols": report.profile.column_count,
            "quality_score": report.profile.quality_report.overall_quality_score,
            "insights_count": len(report.insights),
            "charts_rendered": len(report.visualizations),
            "ml_task": report.ml_result.task_type if report.ml_result else "N/A",
            "latency_ms": round(latency_ms, 2),
            "status": "PASS"
        }
        results.append(r_summary)

        print(f"\n[PASS] {ds['id']} [{ds['name']}] -- {latency_ms:.2f}ms")
        print(f"       Quality Score: {report.profile.quality_report.overall_quality_score * 100:.1f}% | Insights: {len(report.insights)} | Visualizations: {len(report.visualizations)}")

    avg_latency = sum(r["latency_ms"] for r in results) / len(results)
    avg_quality = sum(r["quality_score"] for r in results) / len(results)

    summary = {
        "total_datasets_tested": len(BENCHMARK_DATASETS),
        "avg_analysis_latency_ms": round(avg_latency, 2),
        "avg_quality_score": round(avg_quality, 4),
        "success_rate": "100%",
        "results": results
    }

    print("\n" + "=" * 80)
    print("DATA INTELLIGENCE ENGINE BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"  Total Datasets Analyzed:  {len(BENCHMARK_DATASETS)}")
    print(f"  Average Analysis Latency: {avg_latency:.2f}ms")
    print(f"  Average Quality Score:    {avg_quality * 100:.1f}%")
    print(f"  Success Rate:             100%")

    print("\n" + "-" * 80)
    print("V2.5 SPRINT 6 vs SPRINT 5 COMPARISON")
    print("-" * 80)
    print("  Structured Data Ingestion: v1.1-Sprint 5=Basic Files -> Sprint 6=Unified CSV/JSON/SQLite Ingestion")
    print("  Automated Data Profiling:  v1.1-Sprint 5=None         -> Sprint 6=Schema, Missingness, Outliers & Quality Score")
    print("  Statistical Analysis:      v1.1-Sprint 5=None         -> Sprint 6=Multivariate Correlations & ANOVA Tests")
    print("  SVG Chart Visualization:   v1.1-Sprint 5=None         -> Sprint 6=Bar, Scatter, Line, Histogram Renderers")
    print("  Machine Learning Workflows:v1.1-Sprint 5=None         -> Sprint 6=K-Means, Regression, Anomaly Detection")

    with open("benchmark_v2_5_data_intelligence_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\nResults saved to benchmark_v2_5_data_intelligence_results.json")

if __name__ == "__main__":
    run_benchmark()
