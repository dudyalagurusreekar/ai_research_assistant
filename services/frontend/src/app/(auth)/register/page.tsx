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

const registerSchema = z.object({
  full_name: z.string().min(2, "Full name is required"),
  email: z.string().email("Please enter a valid enterprise email address"),
  password: z.string().min(8, "Password must be at least 8 characters long"),
  role: z.string().default("Researcher"),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      role: "Researcher",
    },
  });

  const onSubmit = async (values: RegisterFormValues) => {
    setIsLoading(true);
    setErrorMsg(null);

    try {
      await apiRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify(values),
      });

      // Auto login after successful registration
      const loginRes = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: values.email, password: values.password }),
      });

      const token = loginRes.access_token || loginRes.token;
      const userProfile = {
        id: loginRes.user_id || "usr_new",
        email: values.email,
        full_name: values.full_name,
        role: values.role,
        tenant_id: loginRes.tenant_id || "tenant_default_enterprise",
        is_active: true,
      };

      setAuth(userProfile, token, loginRes.refresh_token);
      router.push("/dashboard");
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Registration failed. Please check your network connection.");
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
          <CardTitle className="text-2xl font-bold tracking-tight">Create ARA Account</CardTitle>
          <CardDescription className="text-xs text-muted-foreground">
            Join your organization&apos;s AI Research Assistant platform
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
              <label className="text-xs font-semibold text-foreground">Full Name</label>
              <Input
                type="text"
                placeholder="Dr. Eleanor Vance"
                {...register("full_name")}
                error={errors.full_name?.message}
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Work Email Address</label>
              <Input
                type="email"
                placeholder="eleanor@research-lab.org"
                {...register("email")}
                error={errors.email?.message}
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Password</label>
              <Input
                type="password"
                placeholder="••••••••"
                {...register("password")}
                error={errors.password?.message}
              />
            </div>

            <Button type="submit" className="w-full" isLoading={isLoading}>
              Register Enterprise Account
            </Button>
          </form>
        </CardContent>

        <CardFooter className="flex flex-col gap-3 border-t border-border/40 text-center pt-4">
          <p className="text-xs text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
