"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { useAuthStore } from "@/stores/authStore";
import { apiRequest, ApiError } from "@/lib/api-client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Sparkles, Shield, AlertCircle } from "lucide-react";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid enterprise email address"),
  password: z.string().min(8, "Password must be at least 8 characters long"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "admin@ara-research.org",
      password: "AdminPassword123!",
    },
  });

  const onSubmit = async (values: LoginFormValues) => {
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const res = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify(values),
      });

      const token = res.access_token || res.token;
      const userProfile = {
        id: res.user_id || "usr_admin",
        email: values.email,
        full_name: res.full_name || "Enterprise Researcher",
        role: res.role || "Admin",
        tenant_id: res.tenant_id || "tenant_default_enterprise",
        is_active: true,
      };

      setAuth(userProfile, token, res.refresh_token);
      router.push("/dashboard");
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Failed to authenticate with enterprise server.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-background p-4 relative overflow-hidden">
      {/* Background Glow Overlay */}
      <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-primary/20 blur-3xl" />
      <div className="absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-sky-500/20 blur-3xl" />

      <Card className="w-full max-w-md glass-panel relative z-10 border-border/80 shadow-2xl">
        <CardHeader className="space-y-2 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/30">
            <Sparkles className="h-6 w-6" />
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight">ARA Enterprise Login</CardTitle>
          <CardDescription className="text-xs text-muted-foreground">
            Sign in to access your autonomous research workspace
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {errorMsg && (
              <div className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-xs text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Email Address</label>
              <Input
                type="email"
                placeholder="name@enterprise.org"
                {...register("email")}
                error={errors.email?.message}
              />
            </div>

            <div className="space-y-1">
              <div className="flex justify-between items-center">
                <label className="text-xs font-semibold text-foreground">Password</label>
                <a href="#" className="text-[11px] text-primary hover:underline">Forgot password?</a>
              </div>
              <Input
                type="password"
                placeholder="••••••••"
                {...register("password")}
                error={errors.password?.message}
              />
            </div>

            <Button type="submit" className="w-full" isLoading={isLoading}>
              Sign In to Platform
            </Button>
          </form>
        </CardContent>

        <CardFooter className="flex flex-col gap-3 border-t border-border/40 text-center pt-4">
          <p className="text-xs text-muted-foreground">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="font-semibold text-primary hover:underline">
              Request access
            </Link>
          </p>
          <div className="flex items-center justify-center gap-1.5 text-[11px] text-muted-foreground">
            <Shield className="h-3.5 w-3.5 text-emerald-400" /> SOC2 Type II Certified Security
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
