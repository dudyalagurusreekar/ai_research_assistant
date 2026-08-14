import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { ChatMessage } from "../../src/components/chat/ChatMessage";
import { CitationCard } from "../../src/components/chat/CitationCard";
import { ChatMessageItem } from "../../src/stores/researchStore";

describe("Chat Components Suite", () => {
  it("renders ChatMessage with text content and sender", () => {
    const message: ChatMessageItem = {
      id: "msg_1",
      sender_type: "ASSISTANT",
      content: "Cas12a shows **0.02%** off-target mutation rate [1].",
      timestamp: new Date().toISOString(),
      citations: [
        {
          id: "cit_1",
          source_title: "Nature Genetics 2025",
          snippet: "High specificity observed.",
          similarity_score: 0.98,
        },
      ],
    };

    render(<ChatMessage message={message} />);
    expect(screen.getByText("ARA Research Assistant")).toBeDefined();
    expect(screen.getByText(/0.02%/i)).toBeDefined();
  });

  it("renders CitationCard with title and similarity score", () => {
    const citation = {
      id: "cit_100",
      source_title: "Genome Biology Paper",
      snippet: "Experimental evidence confirms Cas12a specificity.",
      similarity_score: 0.965,
      page_number: 12,
    };

    render(<CitationCard citation={citation} />);
    expect(screen.getByText("Genome Biology Paper")).toBeDefined();
    expect(screen.getByText(/Page 12/i)).toBeDefined();
  });
});
