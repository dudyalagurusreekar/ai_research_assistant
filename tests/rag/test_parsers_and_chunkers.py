"""Unit tests for Multi-Format Document Parsers and Semantic Chunkers."""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from core.rag.parsers.multiformat import parser_registry, HTMLMarkdownParser, CSVExcelJSONParser
from core.rag.chunking.chunker import SemanticChunker, TableStructureChunker
from core.rag.parsers.base import ParsedDocument, ParsedSection, ParsedTable


def test_markdown_parser_with_headings():
    parser = HTMLMarkdownParser()
    md_bytes = b"# Introduction\nQuantum computing uses qubits.\n## Hardware\nSuperconducting qubits are cooled to millikelvin temperatures."
    
    parsed = parser.parse(md_bytes, "quantum.md")
    assert parsed.title == "quantum.md"
    assert len(parsed.sections) == 2
    assert parsed.sections[0].heading == "Introduction"
    assert parsed.sections[1].heading == "Hardware"


def test_json_and_csv_parser():
    parser = CSVExcelJSONParser()
    json_bytes = b'{"name": "Quantum Survey", "domain": "Physics", "status": "active"}'
    
    parsed_json = parser.parse(json_bytes, "data.json")
    assert parsed_json.metadata["format"] == "json"
    assert "Quantum Survey" in parsed_json.raw_text

    csv_bytes = b"col1,col2\nval1,val2\nval3,val4"
    parsed_csv = parser.parse(csv_bytes, "table.csv")
    assert parsed_csv.metadata["format"] == "csv"
    assert len(parsed_csv.tables) == 1
    assert parsed_csv.tables[0].headers == ["col1", "col2"]


def test_semantic_chunker():
    chunker = SemanticChunker(max_tokens=10, overlap_tokens=2)
    doc = ParsedDocument(
        title="Test Doc",
        raw_text="",
        sections=[
            ParsedSection(heading="Sec 1", content="One two three four five six seven eight nine ten eleven twelve.", level=1)
        ],
    )
    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 2
    assert chunks[0].chunk_index == 0
    assert "Sec 1" in chunks[0].content


def test_table_structure_chunker():
    doc = ParsedDocument(
        title="Table Doc",
        raw_text="",
        tables=[ParsedTable(caption="Qubit Benchmarks", headers=["Qubit", "Coherence"], rows=[["Superconducting", "100us"], ["Trapped Ion", "1s"]])],
    )
    table_chunks = TableStructureChunker.chunk_tables(doc)
    assert len(table_chunks) == 1
    assert "| Qubit | Coherence |" in table_chunks[0].content
    assert table_chunks[0].metadata["is_table"] is True
