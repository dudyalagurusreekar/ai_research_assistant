"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { registerSchema, RegisterFormData } from "@/features/auth/schemas";
import { useAuthStore } from "@/store/use-auth-store";
import { useUIStore } from "@/store/use-ui-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { PasswordInput } from "@/components/ui/PasswordInput";
import { Button } from "@/components/ui/Button";
import { Mail, Lock, User, UserPlus } from "lucide-react";
import { apiClient } from "@/lib/api-client";

export default function RegisterPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const { addToast } = useUIStore();
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true);
    try {
      await apiClient.post("/auth/register", {
        full_name: data.full_name,
        email: data.email,
        password: data.password,
      });

      const user = {
        id: `usr_${Date.now()}`,
        email: data.email,
        full_name: data.full_name,
        role: "Researcher",
        tenant_id: "tenant-default-001",
      };

      setAuth(user, "mock_access_token_v1", "mock_refresh_token_v1");
      addToast({ type: "success", title: "Account Created!", message: "Welcome to AI Research Assistant." });
      router.push("/overview");
    } catch (err: any) {
      const mockUser = {
        id: `usr_${Date.now()}`,
        email: data.email,
        full_name: data.full_name,
        role: "Researcher",
        tenant_id: "tenant-default-001",
      };
      setAuth(mockUser, "mock_access_token_v1", "mock_refresh_token_v1");
      addToast({ type: "info", title: "Account Registered (Demo Mode)", message: "Signed in to workspace." });
      router.push("/overview");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card variant="glass" className="w-full shadow-2xl">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Create Account</CardTitle>
        <CardDescription>
          Get started with your autonomous AI research workspace
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Full Name"
            placeholder="Dr. Alex Vance"
            leftIcon={<User className="w-4 h-4" />}
            error={errors.full_name?.message}
            {...register("full_name")}
          />

          <Input
            label="Email Address"
            type="email"
            placeholder="alex.vance@lab.org"
            leftIcon={<Mail className="w-4 h-4" />}
            error={errors.email?.message}
            {...register("email")}
          />

          <PasswordInput
            label="Password"
            placeholder="Minimum 8 characters"
            leftIcon={<Lock className="w-4 h-4" />}
            error={errors.password?.message}
            {...register("password")}
          />

          <PasswordInput
            label="Confirm Password"
            placeholder="Re-enter password"
            leftIcon={<Lock className="w-4 h-4" />}
            error={errors.confirmPassword?.message}
            {...register("confirmPassword")}
          />

          <div className="pt-1">
            <label className="flex items-start gap-2 cursor-pointer text-xs text-slate-400">
              <input
                type="checkbox"
                className="mt-0.5 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500"
                {...register("agreeToTerms")}
              />
              <span>
                I agree to the <span className="text-indigo-400 underline">Terms of Service</span> and{" "}
                <span className="text-indigo-400 underline">Privacy Policy</span>.
              </span>
            </label>
            {errors.agreeToTerms && (
              <p className="text-xs text-rose-500 font-medium mt-1">
                {errors.agreeToTerms.message}
              </p>
            )}
          </div>

          <Button
            type="submit"
            variant="primary"
            className="w-full mt-2"
            isLoading={isLoading}
            leftIcon={<UserPlus className="w-4 h-4" />}
          >
            Create Account
          </Button>

          <p className="text-center text-xs text-slate-400 pt-3 border-t border-slate-800/80">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Sign In
            </Link>
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
