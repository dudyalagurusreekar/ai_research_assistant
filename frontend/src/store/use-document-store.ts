import { create } from "zustand";

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  text_content: string;
  token_count: number;
  similarity_score?: number;
  embedding_vector_id?: string;
}

export interface DocumentCitation {
  id: string;
  source_title: string;
  doi?: string;
  url?: string;
  evidence_snippet: string;
}

export interface DocumentItem {
  id: string;
  title: string;
  file_size: string;
  page_count: number;
  chunk_count: number;
  status: "indexed" | "processing" | "failed";
  storage_path: string;
  created_at: string;
  chunks?: DocumentChunk[];
  citations?: DocumentCitation[];
}

export interface SearchResultItem {
  id: string;
  document_id: string;
  document_title: string;
  chunk_text: string;
  similarity_score: number;
  citation_doi?: string;
}

interface DocumentState {
  documents: DocumentItem[];
  selectedDocument: DocumentItem | null;
  inspectorOpen: boolean;
  searchResults: SearchResultItem[];
  isSearching: boolean;

  // Actions
  setDocuments: (docs: DocumentItem[]) => void;
  addDocument: (doc: DocumentItem) => void;
  removeDocument: (id: string) => void;
  setSelectedDocument: (doc: DocumentItem | null) => void;
  setInspectorOpen: (open: boolean) => void;
  setSearchResults: (results: SearchResultItem[]) => void;
  setIsSearching: (searching: boolean) => void;
}

export const useDocumentStore = create<DocumentState>((set) => ({
  documents: [
    {
      id: "doc_001",
      title: "CRISPR_Review_2025.pdf",
      file_size: "2.4 MB",
      page_count: 14,
      chunk_count: 36,
      status: "indexed",
      storage_path: "minio://documents/CRISPR_Review_2025.pdf",
      created_at: new Date(Date.now() - 7200000).toISOString(),
    },
    {
      id: "doc_002",
      title: "AlphaFold3_Multimer_Paper.pdf",
      file_size: "4.1 MB",
      page_count: 22,
      chunk_count: 58,
      status: "indexed",
      storage_path: "minio://documents/AlphaFold3_Multimer_Paper.pdf",
      created_at: new Date(Date.now() - 14400000).toISOString(),
    },
    {
      id: "doc_003",
      title: "OpenFDA_Adverse_Telemetry_2025.csv",
      file_size: "1.8 MB",
      page_count: 8,
      chunk_count: 24,
      status: "indexed",
      storage_path: "minio://documents/OpenFDA_Adverse_Telemetry_2025.csv",
      created_at: new Date(Date.now() - 28800000).toISOString(),
    },
  ],
  selectedDocument: null,
  inspectorOpen: false,
  searchResults: [
    {
      id: "res_001",
      document_id: "doc_001",
      document_title: "CRISPR_Review_2025.pdf",
      chunk_text: "High-fidelity SpCas9 (SpCas9-HF1) exhibits undetectable off-target cleavage at non-homologous genomic loci while maintaining on-target double-strand break efficiency >92%.",
      similarity_score: 0.96,
      citation_doi: "10.1038/nbt.4201",
    },
    {
      id: "res_002",
      document_id: "doc_002",
      document_title: "AlphaFold3_Multimer_Paper.pdf",
      chunk_text: "AlphaFold 3 joint structure prediction accurately models protein-DNA and protein-RNA complexes with atomic accuracy (pLDDT > 88.5 across binding interface residues).",
      similarity_score: 0.92,
      citation_doi: "10.1038/s41586-024-07487-w",
    },
  ],
  isSearching: false,

  setDocuments: (docs) => set({ documents: docs }),
  addDocument: (doc) => set((state) => ({ documents: [doc, ...state.documents] })),
  removeDocument: (id) => set((state) => ({ documents: state.documents.filter((d) => d.id !== id) })),
  setSelectedDocument: (doc) => set({ selectedDocument: doc }),
  setInspectorOpen: (open) => set({ inspectorOpen: open }),
  setSearchResults: (results) => set({ searchResults: results }),
  setIsSearching: (searching) => set({ isSearching: searching }),
}));
