"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { useUIStore } from "@/store/use-ui-store";
import { useAuthStore } from "@/store/use-auth-store";
import {
  Microscope,
  Cpu,
  Database,
  Building2,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Dna,
  Brain,
  FlaskConical,
} from "lucide-react";

export default function OnboardingPage() {
  const router = useRouter();
  const { addToast } = useUIStore();
  const { user } = useAuthStore();
  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Form Selections
  const [domain, setDomain] = useState("Biomedical & Genomics");
  const [llmProvider, setLlmProvider] = useState("Gemini 2.5 Pro");
  const [workspaceName, setWorkspaceName] = useState("My Deep Research Lab");

  const domains = [
    { title: "Biomedical & Genomics", desc: "CRISPR, AlphaFold, PubMed literature synthesis", icon: <Dna className="w-5 h-5 text-indigo-400" /> },
    { title: "Machine Learning & AI", desc: "arXiv preprints, benchmark suites, PyTorch evaluation", icon: <Brain className="w-5 h-5 text-cyan-400" /> },
    { title: "Cheminformatics", desc: "PubChem, ChEMBL, molecular target docking analysis", icon: <FlaskConical className="w-5 h-5 text-emerald-400" /> },
    { title: "General Research", desc: "Web browser automation, document RAG, data analytics", icon: <Microscope className="w-5 h-5 text-amber-400" /> },
  ];

  const llms = [
    { title: "Gemini 2.5 Pro", desc: "High reasoning capacity with 1M+ context window (Default)", badge: "Recommended" },
    { title: "Ollama Local (Offline)", desc: "100% air-gapped local model execution on private host", badge: "Privacy" },
    { title: "Claude 3.5 Sonnet", desc: "High code and mathematical reasoning accuracy", badge: "Cloud" },
    { title: "OpenAI GPT-4o", desc: "Multi-modal vision and structured analytical processing", badge: "Cloud" },
  ];

  const handleNext = () => {
    if (step < 3) {
      setStep((step + 1) as 1 | 2 | 3);
    } else {
      addToast({
        type: "success",
        title: "Onboarding Complete!",
        message: "Your AI research workspace has been initialized.",
      });
      router.push("/overview");
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center p-4 sm:p-6 bg-slate-950 text-slate-100 relative overflow-hidden font-sans">
      {/* Background Glow */}
      <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />

      {/* Progress Indicator */}
      <div className="w-full max-w-xl mb-6 flex items-center justify-between text-xs font-semibold text-slate-400">
        <div className="flex items-center gap-2">
          <span className={`w-7 h-7 rounded-full flex items-center justify-center font-bold ${step >= 1 ? "bg-indigo-600 text-white" : "bg-slate-800"}`}>1</span>
          <span className={step === 1 ? "text-indigo-400" : ""}>Research Specialization</span>
        </div>
        <div className="w-12 h-0.5 bg-slate-800" />
        <div className="flex items-center gap-2">
          <span className={`w-7 h-7 rounded-full flex items-center justify-center font-bold ${step >= 2 ? "bg-indigo-600 text-white" : "bg-slate-800"}`}>2</span>
          <span className={step === 2 ? "text-indigo-400" : ""}>AI Engine Setup</span>
        </div>
        <div className="w-12 h-0.5 bg-slate-800" />
        <div className="flex items-center gap-2">
          <span className={`w-7 h-7 rounded-full flex items-center justify-center font-bold ${step >= 3 ? "bg-indigo-600 text-white" : "bg-slate-800"}`}>3</span>
          <span className={step === 3 ? "text-indigo-400" : ""}>Workspace Name</span>
        </div>
      </div>

      {/* Step Wizard Container */}
      <Card variant="glass" className="w-full max-w-xl shadow-2xl">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl flex items-center justify-center gap-2">
            <Sparkles className="w-6 h-6 text-indigo-400" />
            {step === 1 && "Select Primary Research Specialization"}
            {step === 2 && "Choose Preferred AI Model Provider"}
            {step === 3 && "Name Your Research Workspace"}
          </CardTitle>
          <CardDescription>
            {step === 1 && "Configure default domain knowledge integrations for spaCy & NetworkX"}
            {step === 2 && "Select default LLM routing provider for autonomous planner agents"}
            {step === 3 && "Set your primary project name for document RAG & graph snapshots"}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-5">
          {/* Step 1: Research Domain */}
          {step === 1 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {domains.map((item) => (
                <div
                  key={item.title}
                  onClick={() => setDomain(item.title)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    domain === item.title
                      ? "bg-indigo-600/20 border-indigo-500 shadow-glow-indigo"
                      : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center gap-2.5 mb-1.5">
                    {item.icon}
                    <h4 className="text-sm font-bold text-slate-100">{item.title}</h4>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
                </div>
              ))}
            </div>
          )}

          {/* Step 2: AI Engine Provider */}
          {step === 2 && (
            <div className="space-y-3">
              {llms.map((item) => (
                <div
                  key={item.title}
                  onClick={() => setLlmProvider(item.title)}
                  className={`flex items-center justify-between p-4 rounded-xl border cursor-pointer transition-all ${
                    llmProvider === item.title
                      ? "bg-indigo-600/20 border-indigo-500 shadow-glow-indigo"
                      : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold text-slate-100">{item.title}</h4>
                      <Badge variant="brand">{item.badge}</Badge>
                    </div>
                    <p className="text-xs text-slate-400">{item.desc}</p>
                  </div>
                  {llmProvider === item.title && (
                    <CheckCircle2 className="w-5 h-5 text-indigo-400 shrink-0" />
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Step 3: Workspace Setup */}
          {step === 3 && (
            <div className="space-y-4">
              <Input
                label="Workspace Display Name"
                value={workspaceName}
                onChange={(e) => setWorkspaceName(e.target.value)}
                placeholder="e.g. CRISPR Genomic Target Synthesis Lab"
                leftIcon={<Building2 className="w-4 h-4" />}
              />

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                <span className="text-xs font-bold text-slate-400 block uppercase tracking-wider">
                  Summary Configuration
                </span>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">User Account</span>
                  <span className="text-slate-100 font-semibold">{user?.email || "admin@ara-research.org"}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Domain Focus</span>
                  <span className="text-indigo-400 font-semibold">{domain}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Primary Model</span>
                  <span className="text-cyan-400 font-semibold">{llmProvider}</span>
                </div>
              </div>
            </div>
          )}

          {/* Wizard Controls */}
          <div className="flex items-center justify-between pt-4 border-t border-slate-800">
            {step > 1 ? (
              <Button variant="outline" onClick={() => setStep((step - 1) as 1 | 2 | 3)} leftIcon={<ArrowLeft className="w-4 h-4" />}>
                Back
              </Button>
            ) : (
              <div />
            )}

            <Button
              variant="primary"
              onClick={handleNext}
              rightIcon={step === 3 ? <CheckCircle2 className="w-4 h-4" /> : <ArrowRight className="w-4 h-4" />}
            >
              {step === 3 ? "Complete Setup" : "Next Step"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
