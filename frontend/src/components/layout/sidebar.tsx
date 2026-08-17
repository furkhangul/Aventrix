import {
  BarChart3,
  Bell,
  FolderKanban,
  Key,
  LayoutDashboard,
  Link2,
  type LucideIcon,
  Settings,
  Shield,
  Smartphone,
  Webhook,
  Wrench,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";
import { Logo } from "@/components/logo";
import { cn } from "@/lib/utils";

export interface NavItem {
  labelKey: string;
  to?: string;
  icon: LucideIcon;
  comingSoon?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { labelKey: "nav.dashboard", to: "/", icon: LayoutDashboard },
  { labelKey: "nav.campaigns", to: "/projects", icon: FolderKanban },
  { labelKey: "nav.links", to: "/links", icon: Link2 },
  { labelKey: "nav.analytics", to: "/analytics", icon: BarChart3 },
  { labelKey: "nav.urlTools", to: "/url-tools", icon: Wrench },
  { labelKey: "nav.security", to: "/security", icon: Shield },
  { labelKey: "nav.api", to: "/api-keys", icon: Key },
  { labelKey: "nav.webhooks", to: "/webhooks", icon: Webhook },
  { labelKey: "nav.notifications", to: "/notifications", icon: Bell },
  { labelKey: "nav.devices", to: "/devices", icon: Smartphone },
];

export function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const { t } = useTranslation();
  return (
    <nav className="flex-1 space-y-1 overflow-y-auto p-3">
      {NAV_ITEMS.map((item) =>
        item.comingSoon ? (
          <div
            key={item.labelKey}
            className="flex cursor-not-allowed items-center justify-between gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground/50"
          >
            <span className="flex items-center gap-3">
              <item.icon className="h-4 w-4" />
              {t(item.labelKey)}
            </span>
            <span className="rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-medium">{t("nav.soon")}</span>
          </div>
        ) : (
          <NavLink
            key={item.labelKey}
            to={item.to!}
            end={item.to === "/"}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-foreground/80 hover:bg-accent hover:text-accent-foreground",
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {t(item.labelKey)}
          </NavLink>
        ),
      )}
    </nav>
  );
}

function SettingsLink({ onNavigate }: { onNavigate?: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="border-t border-border p-3">
      <NavLink
        to="/settings"
        onClick={onNavigate}
        className={({ isActive }) =>
          cn(
            "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
            isActive ? "bg-primary/10 text-primary" : "text-foreground/80 hover:bg-accent hover:text-accent-foreground",
          )
        }
      >
        <Settings className="h-4 w-4" />
        {t("nav.settings")}
      </NavLink>
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-card/50 lg:flex">
      <div className="flex h-16 items-center border-b border-border px-5">
        <Logo />
      </div>
      <NavList />
      <SettingsLink />
    </aside>
  );
}

export function MobileSidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center border-b border-border px-5">
        <Logo />
      </div>
      <NavList onNavigate={onNavigate} />
      <SettingsLink onNavigate={onNavigate} />
    </div>
  );
}
