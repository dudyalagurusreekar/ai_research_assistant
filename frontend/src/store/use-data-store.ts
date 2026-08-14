import { create } from "zustand";

export interface ColumnProfile {
  name: string;
  data_type: "numeric" | "categorical" | "datetime" | "string";
  null_count: number;
  null_percentage: number;
  unique_count: number;
  mean?: number;
  std?: number;
  min?: number;
  max?: number;
}

export interface DatasetProfile {
  id: string;
  name: string;
  row_count: number;
  column_count: number;
  file_size: string;
  columns: ColumnProfile[];
  sample_rows: Record<string, any>[];
  anomalies_detected: number;
}

export interface QueryResult {
  columns: string[];
  rows: Record<string, any>[];
  execution_time_ms: number;
}

interface DataState {
  datasets: DatasetProfile[];
  selectedDataset: DatasetProfile | null;
  sqlQuery: string;
  queryResult: QueryResult | null;
  chartType: "bar" | "line" | "scatter" | "pie";
  xAxisColumn: string;
  yAxisColumn: string;
  aiInsights: string;
  isAnalyzing: boolean;

  // Actions
  setDatasets: (datasets: DatasetProfile[]) => void;
  setSelectedDataset: (dataset: DatasetProfile | null) => void;
  setSqlQuery: (query: string) => void;
  setQueryResult: (result: QueryResult | null) => void;
  setChartType: (type: "bar" | "line" | "scatter" | "pie") => void;
  setXAxisColumn: (col: string) => void;
  setYAxisColumn: (col: string) => void;
  setAiInsights: (insights: string) => void;
  setIsAnalyzing: (analyzing: boolean) => void;
}

export const useDataStore = create<DataState>((set) => ({
  datasets: [
    {
      id: "ds_crispr_01",
      name: "CRISPR_Assay_Results.csv",
      row_count: 2400,
      column_count: 5,
      file_size: "1.2 MB",
      anomalies_detected: 2,
      columns: [
        { name: "target_gene", data_type: "categorical", null_count: 0, null_percentage: 0, unique_count: 14 },
        { name: "off_target_rate", data_type: "numeric", null_count: 0, null_percentage: 0, unique_count: 480, mean: 0.042, std: 0.018, min: 0.001, max: 0.48 },
        { name: "confidence", data_type: "numeric", null_count: 0, null_percentage: 0, unique_count: 120, mean: 0.965, std: 0.02, min: 0.81, max: 0.999 },
      ],
      sample_rows: [
        { target_gene: "EMX1", off_target_rate: 0.012, confidence: 0.985, read_depth: 45000, cell_line: "HEK293T" },
        { target_gene: "VEGFA", off_target_rate: 0.048, confidence: 0.942, read_depth: 52000, cell_line: "HEK293T" },
        { target_gene: "FANCF", off_target_rate: 0.008, confidence: 0.991, read_depth: 48000, cell_line: "U2OS" },
      ],
    },
  ],
  selectedDataset: null,
  sqlQuery: 'SELECT target_gene, AVG(off_target_rate) as avg_off_target FROM "dataset" GROUP BY target_gene',
  queryResult: {
    columns: ["target_gene", "avg_off_target", "max_confidence", "assay_count"],
    rows: [
      { target_gene: "EMX1", avg_off_target: 0.012, max_confidence: 0.985, assay_count: 120 },
      { target_gene: "VEGFA", avg_off_target: 0.048, max_confidence: 0.942, assay_count: 95 },
      { target_gene: "FANCF", avg_off_target: 0.008, max_confidence: 0.991, assay_count: 140 },
    ],
    execution_time_ms: 18,
  },
  chartType: "bar",
  xAxisColumn: "target_gene",
  yAxisColumn: "avg_off_target",
  aiInsights: "Multivariate Z-score analysis identifies 2 off-target rate anomalies in VEGFA locus assay replicates. Recommended filter: off_target_rate < 0.05.",
  isAnalyzing: false,

  setDatasets: (datasets) => set({ datasets }),
  setSelectedDataset: (dataset) => set({ selectedDataset: dataset }),
  setSqlQuery: (query) => set({ sqlQuery: query }),
  setQueryResult: (result) => set({ queryResult: result }),
  setChartType: (type) => set({ chartType: type }),
  setXAxisColumn: (col) => set({ xAxisColumn: col }),
  setYAxisColumn: (col) => set({ yAxisColumn: col }),
  setAiInsights: (insights) => set({ aiInsights: insights }),
  setIsAnalyzing: (analyzing) => set({ isAnalyzing: analyzing }),
}));
