import { Navigate, Outlet, useLocation } from "react-router-dom";
import { LoadingState } from "@/components/ui/states";
import { useIsAuthenticated } from "@/hooks/use-auth";

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useIsAuthenticated();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingState label="Loading your workspace…" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}

export function GuestRoute() {
  const { isAuthenticated, isLoading } = useIsAuthenticated();

  if (isLoading) return null;
  if (isAuthenticated) return <Navigate to="/" replace />;

  return <Outlet />;
}
