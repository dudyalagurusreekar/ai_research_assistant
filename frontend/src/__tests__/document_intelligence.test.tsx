import { useDocumentStore } from "@/store/use-document-store";
import { documentService } from "@/features/documents/services/document-service";

describe("Sprint F6: Document Intelligence Center Verification", () => {
  beforeEach(() => {
    useDocumentStore.setState({
      documents: [],
      selectedDocument: null,
      inspectorOpen: false,
      searchResults: [],
      isSearching: false,
    });
  });

  it("adds and inspects ingested documents", () => {
    const doc = {
      id: "doc_test_1",
      title: "Test_CRISPR_Paper.pdf",
      file_size: "1.5 MB",
      page_count: 10,
      chunk_count: 24,
      status: "indexed" as const,
      storage_path: "minio://documents/Test_CRISPR.pdf",
      created_at: new Date().toISOString(),
    };

    useDocumentStore.getState().addDocument(doc);
    expect(useDocumentStore.getState().documents).toHaveLength(1);

    useDocumentStore.getState().setSelectedDocument(doc);
    useDocumentStore.getState().setInspectorOpen(true);

    expect(useDocumentStore.getState().selectedDocument?.title).toBe("Test_CRISPR_Paper.pdf");
    expect(useDocumentStore.getState().inspectorOpen).toBe(true);
  });

  it("executes semantic search and returns vector matching chunks", async () => {
    const results = await documentService.performSemanticSearch("Cas9 cleavage specificity");
    expect(results.length).toBeGreaterThan(0);
    expect(results[0]).toHaveProperty("similarity_score");
    expect(results[0].similarity_score).toBeGreaterThan(0.8);
  });

  it("executes document reindexing pipeline", async () => {
    const success = await documentService.reindexDocument("doc_test_1");
    expect(success).toBe(true);
  });
});
