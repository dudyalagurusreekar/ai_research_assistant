"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { resetPasswordSchema, ResetPasswordFormData } from "@/features/auth/schemas";
import { useUIStore } from "@/store/use-ui-store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { PasswordInput } from "@/components/ui/PasswordInput";
import { Button } from "@/components/ui/Button";
import { Lock, KeyRound, CheckCircle2 } from "lucide-react";

export default function ResetPasswordPage() {
  const router = useRouter();
  const { addToast } = useUIStore();
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    setIsLoading(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 800));
      setIsSuccess(true);
      addToast({
        type: "success",
        title: "Password Updated",
        message: "Your password has been reset successfully.",
      });
    } catch (err: any) {
      addToast({ type: "error", title: "Reset Failed", message: "Invalid or expired token." });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card variant="glass" className="w-full shadow-2xl">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Set New Password</CardTitle>
        <CardDescription>
          Choose a secure password for your research assistant account
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isSuccess ? (
          <div className="text-center space-y-4 py-4">
            <div className="flex items-center justify-center w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-500 mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h4 className="text-base font-semibold text-slate-100">Password Reset Complete</h4>
            <p className="text-xs text-slate-400 max-w-xs mx-auto leading-relaxed">
              You can now sign in with your new password.
            </p>
            <div className="pt-2">
              <Button variant="primary" className="w-full" onClick={() => router.push("/login")}>
                Sign In Now
              </Button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <PasswordInput
              label="New Password"
              placeholder="Minimum 8 characters"
              leftIcon={<Lock className="w-4 h-4" />}
              error={errors.password?.message}
              {...register("password")}
            />

            <PasswordInput
              label="Confirm New Password"
              placeholder="Re-enter new password"
              leftIcon={<Lock className="w-4 h-4" />}
              error={errors.confirmPassword?.message}
              {...register("confirmPassword")}
            />

            <Button
              type="submit"
              variant="primary"
              className="w-full mt-2"
              isLoading={isLoading}
              leftIcon={<KeyRound className="w-4 h-4" />}
            >
              Update Password
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
