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

export interface NavGroup {
  labelKey: string;
  items: NavItem[];
}

/**
 * Grouped rather than one flat list: eleven equally-weighted links read as
 * a wall, and the daily-driver pages (dashboard/campaigns/links) were
 * getting the same visual weight as the once-a-month ones.
 */
export const NAV_GROUPS: NavGroup[] = [
  {
    labelKey: "nav.groupWorkspace",
    items: [
      { labelKey: "nav.dashboard", to: "/", icon: LayoutDashboard },
      { labelKey: "nav.campaigns", to: "/projects", icon: FolderKanban },
      { labelKey: "nav.links", to: "/links", icon: Link2 },
      { labelKey: "nav.analytics", to: "/analytics", icon: BarChart3 },
    ],
  },
  {
    labelKey: "nav.groupToolkit",
    items: [
      { labelKey: "nav.urlTools", to: "/url-tools", icon: Wrench },
      { labelKey: "nav.security", to: "/security", icon: Shield },
      { labelKey: "nav.devices", to: "/devices", icon: Smartphone },
    ],
  },
  {
    labelKey: "nav.groupPlatform",
    items: [
      { labelKey: "nav.api", to: "/api-keys", icon: Key },
      { labelKey: "nav.webhooks", to: "/webhooks", icon: Webhook },
      { labelKey: "nav.notifications", to: "/notifications", icon: Bell },
    ],
  },
];

/** Flat view of the same items — kept for tests and anything that just needs the routes. */
export const NAV_ITEMS: NavItem[] = NAV_GROUPS.flatMap((group) => group.items);

const linkClasses = (isActive: boolean) =>
  cn(
    "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
    isActive
      ? "bg-primary/10 text-primary shadow-sm"
      : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
  );

/** The 3px brand bar that slides in on the active item's left edge. */
function ActiveRail({ isActive }: { isActive: boolean }) {
  return (
    <span
      aria-hidden
      className={cn(
        "absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-brand-gradient transition-all duration-200",
        isActive ? "opacity-100" : "scale-y-0 opacity-0",
      )}
    />
  );
}

export function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const { t } = useTranslation();
  return (
    <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4">
      {NAV_GROUPS.map((group) => (
        <div key={group.labelKey} className="space-y-1">
          <p className="px-3 pb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground/70">
            {t(group.labelKey)}
          </p>
          {group.items.map((item) =>
            item.comingSoon ? (
              <div
                key={item.labelKey}
                className="flex cursor-not-allowed items-center justify-between gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground/50"
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
                className={({ isActive }) => linkClasses(isActive)}
              >
                {({ isActive }) => (
                  <>
                    <ActiveRail isActive={isActive} />
                    <item.icon
                      className={cn(
                        "h-4 w-4 transition-transform duration-200",
                        !isActive && "group-hover:scale-110",
                      )}
                    />
                    {t(item.labelKey)}
                  </>
                )}
              </NavLink>
            ),
          )}
        </div>
      ))}
    </nav>
  );
}

function SettingsLink({ onNavigate }: { onNavigate?: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="border-t border-border/70 p-3">
      <NavLink to="/settings" onClick={onNavigate} className={({ isActive }) => linkClasses(isActive)}>
        {({ isActive }) => (
          <>
            <ActiveRail isActive={isActive} />
            <Settings className="h-4 w-4" />
            {t("nav.settings")}
          </>
        )}
      </NavLink>
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-border/70 bg-card/40 lg:flex">
      <div className="flex h-16 items-center px-5">
        <Logo size="sm" />
      </div>
      <NavList />
      <SettingsLink />
    </aside>
  );
}

export function MobileSidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center px-5">
        <Logo size="sm" />
      </div>
      <NavList onNavigate={onNavigate} />
      <SettingsLink onNavigate={onNavigate} />
    </div>
  );
}
