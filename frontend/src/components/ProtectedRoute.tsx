import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export function ProtectedRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-ink-300 border-t-accent-600" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
