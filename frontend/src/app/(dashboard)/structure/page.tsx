"use client";

import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Boxes, Search, Sparkles, Cpu, ShieldCheck, Eye, Download, Activity, Layers } from "lucide-react";

export default function ProteinStructurePage() {
  const [uniprotInput, setUniprotInput] = useState("P01308");
  const [isSearching, setIsSearching] = useState(false);

  const mockStructureData = {
    uniprot_id: "P01308",
    protein_name: "Insulin (INS_HUMAN)",
    organism: "Homo sapiens (Human)",
    pdb_entries: ["1TRZ", "2INS", "3I40"],
    alphafold_plddt: 94.8,
    disorder_percentage: "5.2%",
    domains: [
      { name: "Insulin B chain", residues: "1 - 30", confidence: 0.98 },
      { name: "C-peptide", residues: "33 - 63", confidence: 0.82 },
      { name: "Insulin A chain", residues: "65 - 85", confidence: 0.97 },
    ],
  };

  const handleSearch = () => {
    setIsSearching(true);
    setTimeout(() => {
      setIsSearching(false);
    }, 400);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            <Boxes className="w-6 h-6 text-purple-400" />
            Protein 3D Structure & Biomolecular Viewer
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            AlphaFold 3 structural predictions, PDB 3D coordinates, pLDDT confidence scores, and domain boundaries
          </p>
        </div>
      </div>

      {/* Structure Query Input */}
      <Card variant="glass" className="space-y-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-400" />
            UniProt Accession ID or PDB Code
          </CardTitle>
          <CardDescription>Enter UniProt ID (e.g. P01308, P04637) or PDB coordinate ID (e.g. 1TUP)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <Input
              placeholder="e.g. P01308 or 1TRZ"
              value={uniprotInput}
              onChange={(e) => setUniprotInput(e.target.value)}
              leftIcon={<Search className="w-4 h-4" />}
              className="flex-1 font-mono text-sm"
            />
            <Button variant="primary" isLoading={isSearching} onClick={handleSearch} leftIcon={<Boxes className="w-4 h-4" />}>
              Fetch AlphaFold / PDB 3D Structure
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card variant="glass" className="p-4 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Protein Name</span>
          <h4 className="text-sm font-extrabold text-slate-100">{mockStructureData.protein_name}</h4>
          <p className="text-xs text-purple-400 font-mono">UniProt: {mockStructureData.uniprot_id}</p>
        </Card>

        <Card variant="glass" className="p-4 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase">AlphaFold pLDDT Score</span>
          <h4 className="text-base font-extrabold text-emerald-400">{mockStructureData.alphafold_plddt} / 100</h4>
          <Badge variant="success">Very High Confidence</Badge>
        </Card>

        <Card variant="glass" className="p-4 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Intrinsic Disorder</span>
          <h4 className="text-base font-extrabold text-cyan-400">{mockStructureData.disorder_percentage}</h4>
          <p className="text-[11px] text-slate-400 font-mono">Mostly Ordered Structure</p>
        </Card>

        <Card variant="glass" className="p-4 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Experimental PDB Entries</span>
          <div className="flex gap-1.5 pt-1">
            {mockStructureData.pdb_entries.map((pdb) => (
              <Badge key={pdb} variant="brand">{pdb}</Badge>
            ))}
          </div>
        </Card>
      </div>

      {/* 3D Structure Viewport Simulation */}
      <Card variant="glass" className="overflow-hidden">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <Eye className="w-4 h-4 text-purple-400" />
              AlphaFold 3D Molecular Coordinate Viewport ({mockStructureData.uniprot_id})
            </CardTitle>
            <CardDescription>Color scheme: pLDDT structural confidence score (Blue = &gt;90, Cyan = 70-90, Yellow = 50-70)</CardDescription>
          </div>
          <Button variant="outline" size="sm" leftIcon={<Download className="w-3.5 h-3.5" />}>
            Download .PDB Coordinates
          </Button>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="h-72 rounded-xl bg-slate-950 border border-slate-800 relative flex items-center justify-center p-6 overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(#6b21a8_1px,transparent_1px)] [background-size:16px_16px] opacity-25" />
            
            {/* Visual Biomolecular Structure Model Representation */}
            <div className="relative z-10 text-center space-y-3">
              <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-purple-600 via-indigo-500 to-cyan-400 opacity-80 blur-lg mx-auto animate-pulse" />
              <div className="relative z-20 space-y-1">
                <Badge variant="brand" className="px-3 py-1 font-mono text-xs shadow-glow-indigo">
                  AlphaFold 3 Multimer Coordinates Loaded
                </Badge>
                <p className="text-xs text-slate-400 font-mono pt-1">
                  Residues 1-85 • Atomic Precision • Active Binding Pocket
                </p>
              </div>
            </div>
          </div>

          {/* Domain Breakdown Table */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-200 uppercase font-mono">Structural Domain Boundaries</h4>
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Domain Name</th>
                    <th className="px-4 py-3">Residue Span</th>
                    <th className="px-4 py-3">pLDDT Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-200">
                  {mockStructureData.domains.map((dom, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/40">
                      <td className="px-4 py-3 font-bold text-slate-100">{dom.name}</td>
                      <td className="px-4 py-3 text-cyan-400">{dom.residues}</td>
                      <td className="px-4 py-3 text-emerald-400 font-bold">{(dom.confidence * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
