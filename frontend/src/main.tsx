import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "@/App";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/toaster";
import { ToastContextProvider } from "@/hooks/use-toast";
import "@/lib/i18n";
import { queryClient } from "@/lib/query-client";
import "@/styles/globals.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ToastContextProvider>
          <App />
          <Toaster />
        </ToastContextProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>,
);
