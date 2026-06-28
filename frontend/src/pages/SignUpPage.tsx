import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthLayout } from "@/components/AuthLayout";
import { Input } from "@/components/Input";
import { Button } from "@/components/Button";
import { useAuth, ApiError } from "@/context/AuthContext";

export function SignUpPage() {
  const { signUp } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
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
      await signUp(email, password, fullName);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Create your account" subtitle="Turn your resume into a portfolio site in minutes.">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          label="Full name"
          type="text"
          autoComplete="name"
          required
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Input
          label="Password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          hint="At least 8 characters, with a letter and a number."
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="text-sm text-danger">{error}</p>}
        <Button type="submit" isLoading={isSubmitting} className="mt-1 w-full">
          {isSubmitting ? "Creating account..." : "Create account"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-ink-500">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-accent-600 hover:text-accent-700">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
