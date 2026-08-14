"use client";

import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { PasswordInput } from "@/components/ui/PasswordInput";
import { Badge } from "@/components/ui/Badge";
import {
  Settings,
  Save,
  Shield,
  KeyRound,
  Server,
  User,
  Lock,
  Activity,
  Cpu,
  Sparkles,
  Bell,
  HardDrive,
  Database,
  Globe,
  BarChart3,
  Sliders,
} from "lucide-react";
import { useAuthStore } from "@/store/use-auth-store";
import { useUIStore } from "@/store/use-ui-store";

export default function SettingsPage() {
  const { user, updateUser } = useAuthStore();
  const { addToast } = useUIStore();
  const [activeTab, setActiveTab] = useState<string>("profile");

  // Profile State
  const [fullName, setFullName] = useState(user?.full_name || "Administrator");
  const [email] = useState(user?.email || "admin@ara-research.org");

  // AI Model State
  const [defaultModel, setDefaultModel] = useState("gemini-2.5-pro");
  const [backupModel, setBackupModel] = useState("claude-3.5-sonnet");
  const [temperature, setTemperature] = useState(0.2);
  const [maxTokens, setMaxTokens] = useState(4096);

  // RAG Settings State
  const [chunkSize, setChunkSize] = useState(512);
  const [chunkOverlap, setChunkOverlap] = useState(64);
  const [topK, setTopK] = useState(5);

  const handleSave = () => {
    updateUser({ full_name: fullName });
    addToast({ type: "success", title: "Settings Saved", message: "Platform configuration updated successfully." });
  };

  const tabs = [
    { id: "profile", name: "User Profile", icon: <User className="w-4 h-4" /> },
    { id: "ai_models", name: "AI Models & Parameters", icon: <Cpu className="w-4 h-4" /> },
    { id: "prompts", name: "Prompt Library", icon: <Sparkles className="w-4 h-4" /> },
    { id: "workspace", name: "Workspace Preferences", icon: <Sliders className="w-4 h-4" /> },
    { id: "notifications", name: "Notifications", icon: <Bell className="w-4 h-4" /> },
    { id: "security", name: "Security Center", icon: <Lock className="w-4 h-4" /> },
    { id: "memory", name: "Memory Settings", icon: <HardDrive className="w-4 h-4" /> },
    { id: "rag", name: "RAG & Chunking", icon: <Database className="w-4 h-4" /> },
    { id: "browser", name: "Browser Automation", icon: <Globe className="w-4 h-4" /> },
    { id: "analytics", name: "Data Intelligence", icon: <BarChart3 className="w-4 h-4" /> },
  ];

  return (
    <div className="space-y-6 max-w-5xl animate-fade-in">
      <div>
        <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
          <Settings className="w-6 h-6 text-indigo-500" />
          Reports, Administration & Settings Control Center
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Centralized configuration for AI models, RAG chunking, security sessions, memory retention, and user preferences
        </p>
      </div>

      {/* Tabs Horizontal Scroll Bar */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2 overflow-x-auto">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-colors ${
              activeTab === t.id ? "bg-indigo-600 text-white shadow-glow-indigo" : "text-slate-400 hover:bg-slate-800"
            }`}
          >
            {t.icon}
            <span>{t.name}</span>
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === "profile" && (
        <Card variant="glass">
          <CardHeader>
            <CardTitle>User Profile Credentials</CardTitle>
            <CardDescription>Personal details and assigned security role</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input label="Full Name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
            <Input label="Email Address" value={email} disabled />

            <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <div>
                <span className="text-xs font-bold text-slate-100 block">RBAC Security Role</span>
                <span className="text-[11px] text-slate-400">System Administrator Permissions</span>
              </div>
              <Badge variant="brand">{user?.role || "Admin"}</Badge>
            </div>

            <div className="flex justify-end">
              <Button variant="primary" leftIcon={<Save className="w-4 h-4" />} onClick={handleSave}>
                Save Profile
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* AI Models Tab */}
      {activeTab === "ai_models" && (
        <Card variant="glass">
          <CardHeader>
            <CardTitle>AI Model & LLM Provider Configuration</CardTitle>
            <CardDescription>Configure primary model, backup failover, and decoding parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-300">Default Model Engine</label>
                <select
                  value={defaultModel}
                  onChange={(e) => setDefaultModel(e.target.value)}
                  className="w-full text-xs font-semibold p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100"
                >
                  <option value="gemini-2.5-pro">Gemini 2.5 Pro (Recommended)</option>
                  <option value="ollama-local">Ollama Local (Air-gapped)</option>
                  <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
                  <option value="gpt-4o">OpenAI GPT-4o</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-300">Backup Failover Model</label>
                <select
                  value={backupModel}
                  onChange={(e) => setBackupModel(e.target.value)}
                  className="w-full text-xs font-semibold p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100"
                >
                  <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
                  <option value="gpt-4o">OpenAI GPT-4o</option>
                </select>
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-bold text-slate-300">
                <span>Temperature</span>
                <span className="text-indigo-400 font-mono">{temperature}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full accent-indigo-500 bg-slate-800"
              />
            </div>

            <div className="flex justify-end">
              <Button variant="primary" leftIcon={<Save className="w-4 h-4" />} onClick={handleSave}>
                Save AI Configuration
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* RAG Settings Tab */}
      {activeTab === "rag" && (
        <Card variant="glass">
          <CardHeader>
            <CardTitle>Enterprise RAG & Chunking Parameters</CardTitle>
            <CardDescription>Vector embedding dimensions, chunk size, and hybrid search settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Input
                label="Chunk Size (Tokens)"
                type="number"
                value={chunkSize}
                onChange={(e) => setChunkSize(Number(e.target.value))}
              />
              <Input
                label="Chunk Overlap (Tokens)"
                type="number"
                value={chunkOverlap}
                onChange={(e) => setChunkOverlap(Number(e.target.value))}
              />
              <Input
                label="Top-K Retrieval Count"
                type="number"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
              />
            </div>

            <div className="flex justify-end">
              <Button variant="primary" leftIcon={<Save className="w-4 h-4" />} onClick={handleSave}>
                Save RAG Parameters
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Security Tab */}
      {activeTab === "security" && (
        <Card variant="glass">
          <CardHeader>
            <CardTitle>Security Center & Active Sessions</CardTitle>
            <CardDescription>Manage active JWT sessions, devices, and OAuth tokens</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-bold text-slate-100 block">Current Web Session (Active)</span>
                <span className="text-slate-400 text-[11px]">IP: 127.0.0.1 • Token Expiration: 24h</span>
              </div>
              <Badge variant="success">Active</Badge>
            </div>

            <div className="flex justify-end">
              <Button variant="danger" size="sm" onClick={() => addToast({ type: "info", title: "Sessions Revoked", message: "Logged out other devices." })}>
                Revoke All Other Sessions
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
