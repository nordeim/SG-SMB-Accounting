"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Lock, Mail } from "lucide-react";
import { cn } from "@/lib/utils";

export default function LoginPage() {
  const [error, setError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    // Simulate login - will be replaced with actual auth in Milestone 4
    setTimeout(() => {
      setIsSubmitting(false);
      router.push("/dashboard");
    }, 1000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-void p-4">
      <Card className="w-full max-w-md border-border bg-carbon rounded-sm">
        <CardHeader className="space-y-1 text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-10 h-10 bg-accent-primary flex items-center justify-center rounded-sm">
              <span className="font-mono font-bold text-void text-xl">L</span>
            </div>
            <CardTitle className="font-display text-2xl text-text-primary">
              LEDGER<span className="text-accent-primary">SG</span>
            </CardTitle>
          </div>
          <CardDescription className="text-text-secondary">
            Sign in to your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert
                variant="destructive"
                className="rounded-sm border-alert bg-alert/10"
              >
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <label
                className="text-sm font-medium text-text-secondary"
                htmlFor="email"
              >
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <Input
                  id="email"
                  type="email"
                  name="email"
                  required
                  className={cn(
                    "pl-10 rounded-sm border-border bg-surface",
                    "focus-visible:ring-accent-primary/50"
                  )}
                  placeholder="you@company.sg"
                  disabled={isSubmitting}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label
                className="text-sm font-medium text-text-secondary"
                htmlFor="password"
              >
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <Input
                  id="password"
                  type="password"
                  name="password"
                  required
                  minLength={8}
                  className={cn(
                    "pl-10 rounded-sm border-border bg-surface",
                    "focus-visible:ring-accent-primary/50"
                  )}
                  placeholder="••••••••"
                  disabled={isSubmitting}
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full rounded-sm bg-accent-primary text-void hover:bg-accent-primary-dim"
              disabled={isSubmitting}
              aria-busy={isSubmitting}
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-void/30 border-t-void rounded-full animate-spin" />
                  Signing in...
                </span>
              ) : (
                "Sign In"
              )}
            </Button>

            <div className="flex items-center justify-between text-sm">
              <Link
                href="#"
                className="text-accent-primary hover:text-accent-primary-dim underline-offset-4 hover:underline"
              >
                Forgot password?
              </Link>
              <Link
                href="#"
                className="text-accent-primary hover:text-accent-primary-dim underline-offset-4 hover:underline"
              >
                Create account
              </Link>
            </div>

            <p className="text-center text-xs text-text-muted pt-4">
              By signing in, you agree to our Terms of Service and Privacy Policy
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
