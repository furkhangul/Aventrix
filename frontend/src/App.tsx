import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/app-shell";
import { GuestRoute, ProtectedRoute } from "@/components/protected-route";
import { LoadingState } from "@/components/ui/states";
import { ConsentGatePage } from "@/pages/consent-gate-page";
import { ForgotPasswordPage } from "@/pages/forgot-password-page";
import { LinkNotFoundPage } from "@/pages/link-not-found-page";
import { LoginPage } from "@/pages/login-page";
import { NotFoundPage } from "@/pages/not-found-page";
import { RegisterPage } from "@/pages/register-page";
import { ResetPasswordPage } from "@/pages/reset-password-page";
import { VerifyEmailPage } from "@/pages/verify-email-page";

// Code-split the authenticated app (charts, tables, forms) away from the
// small, always-needed public/auth pages above, so the first paint for a
// visitor clicking a tracking link — or logging in — stays light.
const DashboardPage = lazy(() => import("@/pages/dashboard-page").then((m) => ({ default: m.DashboardPage })));
const CampaignsPage = lazy(() => import("@/pages/campaigns-page").then((m) => ({ default: m.CampaignsPage })));
const CampaignDetailPage = lazy(() =>
  import("@/pages/campaign-detail-page").then((m) => ({ default: m.CampaignDetailPage })),
);
const LinksPage = lazy(() => import("@/pages/links-page").then((m) => ({ default: m.LinksPage })));
const SettingsPage = lazy(() => import("@/pages/settings-page").then((m) => ({ default: m.SettingsPage })));
const AnalyticsPage = lazy(() => import("@/pages/analytics-page").then((m) => ({ default: m.AnalyticsPage })));
const UrlToolsPage = lazy(() => import("@/pages/url-tools-page").then((m) => ({ default: m.UrlToolsPage })));
const SecurityPage = lazy(() => import("@/pages/security-page").then((m) => ({ default: m.SecurityPage })));
const ApiPage = lazy(() => import("@/pages/api-page").then((m) => ({ default: m.ApiPage })));
const WebhooksPage = lazy(() => import("@/pages/webhooks-page").then((m) => ({ default: m.WebhooksPage })));
const NotificationsPage = lazy(() =>
  import("@/pages/notifications-page").then((m) => ({ default: m.NotificationsPage })),
);
const DevicesPage = lazy(() => import("@/pages/devices-page").then((m) => ({ default: m.DevicesPage })));
const DeviceControlPage = lazy(() =>
  import("@/pages/device-control-page").then((m) => ({ default: m.DeviceControlPage })),
);

function PageFallback() {
  return (
    <div className="flex h-full min-h-[50vh] items-center justify-center">
      <LoadingState />
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<GuestRoute />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
        </Route>

        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/t/:code/gate" element={<ConsentGatePage />} />
        <Route path="/t/not-found" element={<LinkNotFoundPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route
              path="/"
              element={
                <Suspense fallback={<PageFallback />}>
                  <DashboardPage />
                </Suspense>
              }
            />
            <Route
              path="/projects"
              element={
                <Suspense fallback={<PageFallback />}>
                  <CampaignsPage />
                </Suspense>
              }
            />
            <Route
              path="/projects/:id"
              element={
                <Suspense fallback={<PageFallback />}>
                  <CampaignDetailPage />
                </Suspense>
              }
            />
            <Route
              path="/links"
              element={
                <Suspense fallback={<PageFallback />}>
                  <LinksPage />
                </Suspense>
              }
            />
            <Route
              path="/settings"
              element={
                <Suspense fallback={<PageFallback />}>
                  <SettingsPage />
                </Suspense>
              }
            />
            <Route
              path="/analytics"
              element={
                <Suspense fallback={<PageFallback />}>
                  <AnalyticsPage />
                </Suspense>
              }
            />
            <Route path="/qr-codes" element={<Navigate to="/url-tools" replace />} />
            <Route
              path="/url-tools"
              element={
                <Suspense fallback={<PageFallback />}>
                  <UrlToolsPage />
                </Suspense>
              }
            />
            <Route
              path="/security"
              element={
                <Suspense fallback={<PageFallback />}>
                  <SecurityPage />
                </Suspense>
              }
            />
            <Route
              path="/api-keys"
              element={
                <Suspense fallback={<PageFallback />}>
                  <ApiPage />
                </Suspense>
              }
            />
            <Route
              path="/webhooks"
              element={
                <Suspense fallback={<PageFallback />}>
                  <WebhooksPage />
                </Suspense>
              }
            />
            <Route
              path="/notifications"
              element={
                <Suspense fallback={<PageFallback />}>
                  <NotificationsPage />
                </Suspense>
              }
            />
            <Route
              path="/devices"
              element={
                <Suspense fallback={<PageFallback />}>
                  <DevicesPage />
                </Suspense>
              }
            />
            <Route
              path="/devices/:deviceId/control"
              element={
                <Suspense fallback={<PageFallback />}>
                  <DeviceControlPage />
                </Suspense>
              }
            />
          </Route>
        </Route>

        <Route path="/404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
