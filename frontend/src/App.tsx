import { Navigate, Route, Routes } from "react-router-dom";
import { useEffect } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AppShell } from "@/components/AppShell";
import { LandingPage } from "@/pages/LandingPage";
import { SignUpPage } from "@/pages/SignUpPage";
import { LoginPage } from "@/pages/LoginPage";
import { ForgotPasswordPage } from "@/pages/ForgotPasswordPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { UploadPage } from "@/pages/UploadPage";
import { ResultsPage } from "@/pages/ResultsPage";
import { ThemeGalleryPage } from "@/pages/ThemeGalleryPage";
import { SupportPage } from "@/pages/SupportPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { applyAppearance, getStoredAccent, getStoredTheme } from "@/lib/theme";

export default function App() {
  useEffect(() => {
    const sync = () => applyAppearance(getStoredTheme(), getStoredAccent());
    sync();
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    media.addEventListener("change", sync);
    window.addEventListener("storage", sync);
    return () => {
      media.removeEventListener("change", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/signup" element={<SignUpPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/portfolios/:id" element={<ResultsPage />} />
          <Route path="/themes" element={<ThemeGalleryPage />} />
          <Route path="/support" element={<SupportPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
