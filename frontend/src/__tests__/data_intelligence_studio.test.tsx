import { useDataStore } from "@/store/use-data-store";
import { dataService } from "@/features/analytics/services/data-service";

describe("Sprint F8: Data Intelligence Studio Verification", () => {
  beforeEach(() => {
    useDataStore.setState({
      selectedDataset: null,
      sqlQuery: "SELECT * FROM test",
      queryResult: null,
      chartType: "bar",
      xAxisColumn: "target_gene",
      yAxisColumn: "off_target_rate",
      aiInsights: "",
      isAnalyzing: false,
    });
  });

  it("updates chart configuration parameters correctly", () => {
    useDataStore.getState().setChartType("line");
    useDataStore.getState().setXAxisColumn("cleavage_score");
    useDataStore.getState().setYAxisColumn("confidence_score");

    const state = useDataStore.getState();
    expect(state.chartType).toBe("line");
    expect(state.xAxisColumn).toBe("cleavage_score");
    expect(state.yAxisColumn).toBe("confidence_score");
  });

  it("executes in-memory SQL query and returns formatted result rows", async () => {
    const result = await dataService.executeSqlQuery("SELECT target_gene FROM crispr");
    expect(result.rows.length).toBeGreaterThan(0);
    expect(result).toHaveProperty("execution_time_ms");
  });

  it("fetches dataset schema profile cleanly", async () => {
    const profile = await dataService.fetchDatasetProfile("ds_crispr_01");
    expect(profile).toHaveProperty("columns");
    expect(profile.row_count).toBeGreaterThan(0);
  });
});
