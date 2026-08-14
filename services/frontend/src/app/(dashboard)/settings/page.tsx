"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/stores/authStore";
import { Settings, Key, Cpu, Shield, Save } from "lucide-react";
import { useState } from "react";

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-4xl">
        <div className="border-b border-border/50 pb-4">
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Settings className="h-5 w-5 text-primary" /> Platform Settings & User Profile
          </h1>
          <p className="text-xs text-muted-foreground">
            Manage your account credentials, API tokens, and LLM provider routing preferences.
          </p>
        </div>

        {saved && (
          <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-400 font-semibold">
            Settings updated successfully.
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-6">
          {/* User Profile Card */}
          <Card className="glass-panel">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Shield className="h-4 w-4 text-primary" /> Profile Credentials
              </CardTitle>
              <CardDescription className="text-xs">Your enterprise identity and RBAC role</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Full Name</label>
                  <Input defaultValue={user?.full_name || "Enterprise User"} />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Email Address</label>
                  <Input defaultValue={user?.email || "user@ara-research.org"} disabled />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Role</label>
                <Input defaultValue={user?.role || "Admin"} disabled />
              </div>
            </CardContent>
          </Card>

          {/* API Keys Card */}
          <Card className="glass-panel">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Key className="h-4 w-4 text-amber-400" /> Model Provider Keys
              </CardTitle>
              <CardDescription className="text-xs">Configured LLM provider credentials for multi-provider routing</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Google Gemini API Key</label>
                <Input type="password" defaultValue="••••••••••••••••••••••••••••••••" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">OpenAI API Key</label>
                <Input type="password" defaultValue="••••••••••••••••••••••••••••••••" />
              </div>
            </CardContent>
          </Card>

          <Button type="submit" className="gap-2">
            <Save className="h-4 w-4" /> Save Preferences
          </Button>
        </form>
      </div>
    </DashboardLayout>
  );
}
