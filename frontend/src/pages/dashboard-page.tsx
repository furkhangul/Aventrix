import { FolderKanban, Link2, Percent, Users, Zap } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DateRangeSelect } from "@/components/date-range-select";
import { StatCard } from "@/components/stat-card";
import { TopListCard } from "@/components/top-list-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboardSummary, useDashboardTimeseries, useDashboardTop } from "@/hooks/use-dashboard";
import { useMe } from "@/hooks/use-auth";
import { formatNumber } from "@/lib/utils";
import type { DateRangePreset } from "@/lib/types";

export function DashboardPage() {
  const { t } = useTranslation();
  const [range, setRange] = useState<DateRangePreset>("30d");
  const { data: me } = useMe();
  const { data: summary, isLoading: summaryLoading } = useDashboardSummary(range);
  const { data: timeseries, isLoading: timeseriesLoading } = useDashboardTimeseries(range);
  const { data: topCountries, isLoading: countriesLoading } = useDashboardTop("country", range);
  const { data: topDevices, isLoading: devicesLoading } = useDashboardTop("device", range);
  const { data: topBrowsers, isLoading: browsersLoading } = useDashboardTop("browser", range);
  const { data: topReferrers, isLoading: referrersLoading } = useDashboardTop("referrer", range);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            {me?.full_name ? t("dashboard.welcomeBackNamed", { name: me.full_name.split(" ")[0] }) : t("dashboard.welcomeBack")}
          </h1>
          <p className="text-sm text-muted-foreground">{t("dashboard.subtitle")}</p>
        </div>
        <DateRangeSelect value={range} onChange={setRange} />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <StatCard label={t("dashboard.totalLinks")} icon={Link2} value={summaryLoading ? "—" : formatNumber(summary?.total_links ?? 0)} />
        <StatCard label={t("dashboard.totalVisits")} icon={Zap} value={summaryLoading ? "—" : formatNumber(summary?.total_visits ?? 0)} />
        <StatCard label={t("dashboard.uniqueVisitors")} icon={Users} value={summaryLoading ? "—" : formatNumber(summary?.unique_visitors ?? 0)} />
        <StatCard label={t("dashboard.todaysVisits")} icon={Zap} value={summaryLoading ? "—" : formatNumber(summary?.today_visits ?? 0)} />
        <StatCard label={t("dashboard.activeCampaigns")} icon={FolderKanban} value={summaryLoading ? "—" : formatNumber(summary?.active_campaigns ?? 0)} />
        <StatCard
          label={t("dashboard.uniquenessRate")}
          icon={Percent}
          value={summaryLoading ? "—" : `${summary?.conversion_rate ?? 0}%`}
          hint={t("dashboard.uniquenessHint")}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("dashboard.visitsOverTime")}</CardTitle>
        </CardHeader>
        <CardContent className="h-72 pt-2">
          {timeseriesLoading ? (
            <div className="h-full w-full animate-pulse rounded-md bg-muted" />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeseries} margin={{ left: -20, right: 8, top: 8 }}>
                <defs>
                  <linearGradient id="visits-gradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
                <XAxis
                  dataKey="date"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                  tickFormatter={(v: string) => new Date(v).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                />
                <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--popover))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: 8,
                    fontSize: 13,
                  }}
                  labelFormatter={(v: string) => new Date(v).toLocaleDateString()}
                />
                <Area type="monotone" dataKey="count" stroke="hsl(var(--primary))" fill="url(#visits-gradient)" strokeWidth={2} name={t("dashboard.totalVisits")} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <TopListCard title={t("dashboard.topCountries")} items={topCountries} isLoading={countriesLoading} />
        <TopListCard title={t("dashboard.topDevices")} items={topDevices} isLoading={devicesLoading} />
        <TopListCard title={t("dashboard.topBrowsers")} items={topBrowsers} isLoading={browsersLoading} />
        <TopListCard title={t("dashboard.topReferrers")} items={topReferrers} isLoading={referrersLoading} />
      </div>
    </div>
  );
}
