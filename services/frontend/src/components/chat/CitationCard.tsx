"use client";

import * as React from "react";
import { Citation, useResearchStore } from "@/stores/researchStore";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, ExternalLink, X, BookOpen } from "lucide-react";

export function CitationCard({ citation }: { citation: Citation }) {
  const { setActiveCitation } = useResearchStore();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
      <Card className="w-full max-w-lg glass-panel border-primary/40 shadow-2xl relative">
        <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-border/50">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/20 text-primary">
              <BookOpen className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-sm font-semibold truncate max-w-xs">{citation.source_title}</CardTitle>
              {citation.author && <p className="text-[11px] text-muted-foreground">{citation.author}</p>}
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setActiveCitation(null)}
            className="h-8 w-8 rounded-full"
          >
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>

        <CardContent className="pt-4 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <Badge variant="success">
              Similarity: {((citation.similarity_score || 0.94) * 100).toFixed(1)}%
            </Badge>
            {citation.page_number && (
              <span className="text-muted-foreground">Page {citation.page_number}</span>
            )}
          </div>

          <div className="rounded-lg border border-border/60 bg-secondary/30 p-3.5 text-xs italic text-foreground leading-relaxed">
            &quot;{citation.snippet}&quot;
          </div>

          {citation.url && (
            <div className="pt-2 flex justify-end">
              <a
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline"
              >
                View Full Document Source <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
