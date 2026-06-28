import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthLayout } from "@/components/AuthLayout";
import { Input } from "@/components/Input";
import { Button } from "@/components/Button";
import { useAuth, ApiError } from "@/context/AuthContext";

export function LoginPage() {
  const { logIn } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (isSubmitting) return;
    setError(null);
    setIsSubmitting(true);
    try {
      await logIn(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Welcome back" subtitle="Log in to continue building your portfolio.">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <div>
          <Input
            label="Password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Link
            to="/forgot-password"
            className="mt-1.5 inline-block text-xs font-medium text-accent-600 hover:text-accent-700"
          >
            Forgot password?
          </Link>
        </div>
        {error && <p className="text-sm text-danger">{error}</p>}
        <Button type="submit" isLoading={isSubmitting} className="mt-1 w-full">
          {isSubmitting ? "Logging in..." : "Log in"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-ink-500">
        Don&apos;t have an account?{" "}
        <Link to="/signup" className="font-medium text-accent-600 hover:text-accent-700">
          Sign up
        </Link>
      </p>
    </AuthLayout>
  );
}
