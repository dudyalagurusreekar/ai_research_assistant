import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { Button } from "../../src/components/ui/button";
import { Badge } from "../../src/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "../../src/components/ui/card";

describe("UI Components Library", () => {
  it("renders Button component with children", () => {
    render(<Button>Execute DAG</Button>);
    expect(screen.getByRole("button", { name: /Execute DAG/i })).toBeDefined();
  });

  it("renders Badge component with variant text", () => {
    render(<Badge variant="success">COMPLETED</Badge>);
    expect(screen.getByText("COMPLETED")).toBeDefined();
  });

  it("renders Card component with title and content", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>GraphRAG Explorer</CardTitle>
        </CardHeader>
        <CardContent>Entity Node Details</CardContent>
      </Card>
    );
    expect(screen.getByText("GraphRAG Explorer")).toBeDefined();
    expect(screen.getByText("Entity Node Details")).toBeDefined();
  });
});
