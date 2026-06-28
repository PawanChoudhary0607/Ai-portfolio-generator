import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { AuthLayout } from "@/components/AuthLayout";
import { Input } from "@/components/Input";
import { Button } from "@/components/Button";
import { ApiError } from "@/context/AuthContext";
import { authApi } from "@/api/client";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await authApi.forgotPassword(email);
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <AuthLayout title="Check your email" subtitle="">
        <p className="text-sm text-ink-700">
          If an account exists for <span className="font-medium text-ink-900">{email}</span>, we&apos;ve sent a link
          to reset your password.
        </p>
        <Link to="/login" className="mt-6 inline-block text-sm font-medium text-accent-600 hover:text-accent-700">
          Back to log in
        </Link>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Reset your password" subtitle="We'll send a reset link to your email.">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        {error && <p className="text-sm text-danger">{error}</p>}
        <Button type="submit" isLoading={isSubmitting} className="mt-1 w-full">
          Send reset link
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-ink-500">
        <Link to="/login" className="font-medium text-accent-600 hover:text-accent-700">
          Back to log in
        </Link>
      </p>
    </AuthLayout>
  );
}
