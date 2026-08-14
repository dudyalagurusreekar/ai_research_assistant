"use client";

import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Dna, Search, ShieldCheck, Activity, AlertTriangle, ExternalLink, Sparkles, Database } from "lucide-react";

export default function GenomicsVariantPage() {
  const [variantInput, setVariantInput] = useState("chr12:25245350:C>T");
  const [activeTab, setActiveTab] = useState<"variant" | "expression" | "splice">("variant");
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const mockVariantResult = {
    rsid: "rs121913529",
    coordinate: "chr12:25245350 (GRCh38)",
    ref_alt: "C > T",
    gene_symbol: "KRAS",
    consequence: "Missense Variant (p.Gly12Asp)",
    pathogenicity: "Pathogenic (ClinVar ID: 12582)",
    gnomad_af: "0.0000312 (Rare Variant)",
    alphagenome_score: 0.942,
    eqtl_tissues: [
      { tissue: "Lung", raw_score: -1.42, p_val: "4.2e-9" },
      { tissue: "Colon - Transverse", raw_score: -2.15, p_val: "1.1e-12" },
      { tissue: "Whole Blood", raw_score: 0.14, p_val: "0.45" },
    ],
    literature_citations: [
      { pmid: "38192041", title: "Structural and functional consequences of oncogenic KRAS G12D mutations in pancreatic carcinoma." },
      { doi: "10.1038/s41586-024-07100-x", title: "Deep learning variant effect prediction across non-coding regulatory elements." },
    ],
  };

  const handleAnalyze = () => {
    setIsAnalyzing(true);
    setTimeout(() => {
      setIsAnalyzing(false);
    }, 400);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            <Dna className="w-6 h-6 text-cyan-400" />
            Genomic Variant & Mutation Interpreter
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            AlphaGenome API, ClinVar pathogenicity, dbSNP mapping, Ensembl VEP, and GTEx tissue eQTL telemetry
          </p>
        </div>
      </div>

      {/* Variant Query Header */}
      <Card variant="glass" className="space-y-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            Variant Identifier or Genomic Coordinates
          </CardTitle>
          <CardDescription>Format: chr:pos:ref&gt;alt (e.g. chr12:25245350:C&gt;T) or rsID (e.g. rs121913529)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <Input
              placeholder="e.g. chr12:25245350:C>T or rs121913529"
              value={variantInput}
              onChange={(e) => setVariantInput(e.target.value)}
              leftIcon={<Search className="w-4 h-4" />}
              className="flex-1 font-mono text-sm"
            />
            <Button variant="primary" isLoading={isAnalyzing} onClick={handleAnalyze} leftIcon={<Activity className="w-4 h-4" />}>
              Analyze Variant Effect
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Analysis Results Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card variant="glass" className="p-4 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Target Gene & Consequence</span>
          <h4 className="text-base font-extrabold text-slate-100">{mockVariantResult.gene_symbol}</h4>
          <p className="text-xs text-indigo-400 font-semibold">{mockVariantResult.consequence}</p>
        </Card>

        <Card variant="glass" className="p-4 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase">ClinVar Classification</span>
          <div className="flex items-center gap-1.5 pt-1">
            <Badge variant="danger" className="gap-1">
              <AlertTriangle className="w-3 h-3 text-rose-400" />
              Pathogenic
            </Badge>
          </div>
          <p className="text-[11px] text-slate-400 font-mono mt-1">dbSNP: {mockVariantResult.rsid}</p>
        </Card>

        <Card variant="glass" className="p-4 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase">gnomAD Allele Frequency</span>
          <h4 className="text-base font-extrabold text-emerald-400">{mockVariantResult.gnomad_af.split(" ")[0]}</h4>
          <p className="text-[11px] text-slate-400 font-mono">Population: Rare Mutation</p>
        </Card>

        <Card variant="glass" className="p-4 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase">AlphaGenome Disruption</span>
          <h4 className="text-base font-extrabold text-cyan-400">{(mockVariantResult.alphagenome_score * 100).toFixed(1)}%</h4>
          <p className="text-[11px] text-slate-400 font-mono">High Functional Effect</p>
        </Card>
      </div>

      {/* Deep-Dive Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("variant")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "variant" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <Dna className="w-4 h-4" />
          Annotation & Evidence
        </button>
        <button
          onClick={() => setActiveTab("expression")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === "expression" ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
          }`}
        >
          <Activity className="w-4 h-4" />
          GTEx Tissue eQTL Telemetry
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === "variant" && (
        <Card variant="glass">
          <CardHeader>
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Functional Evidence & Literature Provenance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-xs text-slate-300">
            {mockVariantResult.literature_citations.map((cit, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-slate-100">{cit.title}</h4>
                  <p className="text-[11px] text-slate-400 font-mono mt-0.5">{cit.pmid ? `PMID: ${cit.pmid}` : `DOI: ${cit.doi}`}</p>
                </div>
                <Badge variant="brand" className="gap-1">
                  <ExternalLink className="w-3 h-3" />
                  Cite
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {activeTab === "expression" && (
        <Card variant="glass">
          <CardHeader>
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400" />
              GTEx Tissue Expression Quantitative Trait Loci (eQTL)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Tissue Site</th>
                    <th className="px-4 py-3">Effect Size (NES)</th>
                    <th className="px-4 py-3">p-value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-200">
                  {mockVariantResult.eqtl_tissues.map((t, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/40">
                      <td className="px-4 py-3 font-bold text-slate-100">{t.tissue}</td>
                      <td className="px-4 py-3 text-rose-400">{t.raw_score}</td>
                      <td className="px-4 py-3 text-emerald-400">{t.p_val}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
