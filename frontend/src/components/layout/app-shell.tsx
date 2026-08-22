import { AnimatePresence, motion } from "framer-motion";
import { Outlet, useLocation } from "react-router-dom";
import { Navbar } from "@/components/layout/navbar";
import { Sidebar } from "@/components/layout/sidebar";

export function AppShell() {
  const location = useLocation();

  return (
    <div className="relative flex h-screen overflow-hidden bg-background">
      {/* Fixed brand wash behind the whole shell — cheap, and it stops the
          large empty areas of sparse pages reading as dead grey. */}
      <div aria-hidden className="pointer-events-none fixed inset-0 aurora opacity-70" />

      <Sidebar />
      <div className="relative flex min-w-0 flex-1 flex-col">
        <Navbar />
        <main className="flex-1 overflow-y-auto">
          <div className="container max-w-7xl py-6 sm:py-8">
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
                className="will-animate"
              >
                <Outlet />
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>
    </div>
  );
}
