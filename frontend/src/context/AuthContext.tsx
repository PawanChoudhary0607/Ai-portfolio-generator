import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import type { User } from "@shared/types";
import { ApiError, authApi, setToken } from "@/api/client";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  signUp: (email: string, password: string, fullName: string) => Promise<void>;
  logIn: (email: string, password: string) => Promise<void>;
  logOut: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setIsLoading(false);
      return;
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => {
        // Stored token is invalid/expired — clear it rather than looping
        // on a request that will keep failing.
        setToken(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const signUp = useCallback(async (email: string, password: string, fullName: string) => {
    const result = await authApi.signUp(email, password, fullName);
    setToken(result.access_token);
    setUser(result.user);
  }, []);

  const logIn = useCallback(async (email: string, password: string) => {
    const result = await authApi.logIn(email, password);
    setToken(result.access_token);
    setUser(result.user);
  }, []);

  const logOut = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, signUp, logIn, logOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}

export { ApiError };
