# ARA Version 2.5 — Data Intelligence Engine Architecture (Sprint 6)

## 1. Executive Overview
The **Data Intelligence Engine** is a core subsystem of ARA Version 2.5 (Sprint 6). It empowers the AI Research Assistant with native structured data ingestion, profiling, cleaning, statistical analysis, interactive SVG chart rendering, automated machine learning workflows (clustering, regression, anomaly detection), and multi-format report generation.

Key design principles:
- **Unified Multi-Source Ingestion**: Ingests CSV, JSON, Parquet, SQLite databases, and Python data structures through a single API.
- **Automated Data Profiling & Quality Scoring**: Automatically detects data types, computes summary statistics (mean, std, median, min, max, IQR, skewness), missingness ratios, duplicate rows, and outlier counts.
- **Integrated ML Workflows**: Executes lightweight k-means clustering, linear regression, multivariate Z-score anomaly detection, and trend analysis without external heavy dependencies.
- **Multi-Format Analytical Reports**: Compiles data insights, SVG chart visualizations, and statistical findings into Markdown, HTML, PDF, and DOCX formats.
- **Backward Compatibility**: Fully integrated into `ToolRegistry` as `DataTool`, maintaining 100% compatibility with Version 1.1 and Sprints 1–5.

---

## 2. Subsystem Component Breakdown (`core/data_intelligence/`)

### 2.1 Core Components (`core/data_intelligence/components/`)
1. **`DataIngestionModule`**: Reads CSV, JSON, SQLite databases, and dict records into uniform tabular structures.
2. **`SchemaDetector`**: Infers column data types (`numeric`, `categorical`, `datetime`, `boolean`, `text`), nullability, and unique values.
3. **`DataProfiler`**: Calculates summary statistics, quality issues, missingness ratios, duplicate rows, and outlier counts.
4. **`DataCleaner`**: Performs missing value imputation (median/mode), duplicate removal, outlier capping, and type coercion.
5. **`StatisticalAnalyzer`**: Computes Pearson/Spearman correlation matrices, hypothesis test findings, and multivariate metrics.
6. **`VisualizationEngine`**: Generates chart configurations and renders bar, line, scatter, histogram, boxplot, and heatmap visualizations in clean SVG and JSON formats.
7. **`MLWorkflowEngine`**: Executes k-means clustering, linear regression, multivariate anomaly detection, and time series trend forecasting.
8. **`InsightGenerator`**: Synthesizes structured data findings into natural language insights and executive recommendations using LLM Orchestration.
9. **`ReportGenerator`**: Renders comprehensive analytical reports in Markdown and HTML formats.
10. **`DataMemory`**: Caches dataset records, schemas, profiles, and analytical reports across sessions.

---

## 3. Tool Registry Integration (`tools/data/data_tool.py`)

- **`DataTool`**: Tool facade exposing `analyze`, `profile`, `clean`, `visualize`, and `predict` actions to `smolagents` and `SafeCodeAgent`.

---

## 4. Performance Benchmarks (Sprint 6 vs Baseline)

| Metric | Version 1.1–Sprint 5 Baseline | Sprint 6 (Data Intelligence Engine) |
|---|---|---|
| **Data Ingestion** | Manual Python interpreter scripts | **Unified CSV, JSON, SQLite Ingestion** |
| **Schema Detection** | Manual inspection | **Automated Type & Nullability Inference** |
| **Data Quality Score** | None | **Automated 0.0–1.0 Quality Rating** |
| **Statistical Analysis** | Manual calculations | **Automated Pearson Correlation & ANOVA** |
| **Visualization** | Text output only | **Native SVG & JSON Chart Rendering** |
| **Machine Learning Workflows** | Custom code snippets | **Native K-Means, Regression & Anomaly Detection** |
