import { Download, Link2 as LinkIcon, Percent, Users, Zap } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DateRangeSelect } from "@/components/date-range-select";
import { StatCard } from "@/components/stat-card";
import { TopListCard } from "@/components/top-list-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { useAnalyticsOverview, buildAnalyticsExportUrl } from "@/hooks/use-analytics";
import { useCampaigns } from "@/hooks/use-campaigns";
import { useLinks } from "@/hooks/use-links";
import { formatNumber } from "@/lib/utils";
import type { DateRangePreset } from "@/lib/types";

export function AnalyticsPage() {
  const { t } = useTranslation();
  const [range, setRange] = useState<DateRangePreset>("30d");
  const [linkId, setLinkId] = useState<string | undefined>();
  const [campaignId, setCampaignId] = useState<string | undefined>();

  const { data: links } = useLinks({ pageSize: 100 });
  const { data: campaigns } = useCampaigns({ pageSize: 100 });
  const { data, isLoading, isError, refetch } = useAnalyticsOverview({ range, linkId, campaignId });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{t("analytics.title")}</h1>
          <p className="text-sm text-muted-foreground">{t("analytics.subtitle")}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Select value={linkId ?? "all"} onValueChange={(v) => setLinkId(v === "all" ? undefined : v)}>
            <SelectTrigger className="w-44">
              <SelectValue placeholder={t("analytics.allLinks")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("analytics.allLinks")}</SelectItem>
              {links?.items.map((link) => (
                <SelectItem key={link.id} value={link.id}>
                  /{link.short_code}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={campaignId ?? "all"} onValueChange={(v) => setCampaignId(v === "all" ? undefined : v)}>
            <SelectTrigger className="w-44">
              <SelectValue placeholder={t("analytics.allCampaigns")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("analytics.allCampaigns")}</SelectItem>
              {campaigns?.items.map((campaign) => (
                <SelectItem key={campaign.id} value={campaign.id}>
                  {campaign.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <DateRangeSelect value={range} onChange={setRange} />
          <Button variant="outline" size="sm" asChild>
            <a href={buildAnalyticsExportUrl({ range, linkId, campaignId, format: "csv" })} target="_blank" rel="noreferrer">
              <Download className="h-4 w-4" />
              {t("analytics.exportCsv")}
            </a>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <a href={buildAnalyticsExportUrl({ range, linkId, campaignId, format: "json" })} target="_blank" rel="noreferrer">
              <Download className="h-4 w-4" />
              {t("analytics.exportJson")}
            </a>
          </Button>
        </div>
      </div>

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard label={t("analytics.totalVisits")} icon={Zap} value={formatNumber(data?.total_visits ?? 0)} />
            <StatCard label={t("analytics.uniqueVisitors")} icon={Users} value={formatNumber(data?.unique_visitors ?? 0)} />
            <StatCard
              label={t("analytics.uniquenessRate")}
              icon={Percent}
              value={`${data?.conversion_rate ?? 0}%`}
              hint={t("analytics.uniquenessHint")}
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>{t("analytics.visitsOverTime")}</CardTitle>
            </CardHeader>
            <CardContent className="h-72 pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data?.timeseries} margin={{ left: -20, right: 8, top: 8 }}>
                  <defs>
                    <linearGradient id="analytics-gradient" x1="0" y1="0" x2="0" y2="1">
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
                  <Area type="monotone" dataKey="count" stroke="hsl(var(--primary))" fill="url(#analytics-gradient)" strokeWidth={2} name={t("analytics.totalVisits")} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
            <TopListCard title={t("analytics.topCountries")} items={data?.top_countries} isLoading={false} />
            <TopListCard title={t("analytics.topDevices")} items={data?.top_devices} isLoading={false} />
            <TopListCard title={t("analytics.topBrowsers")} items={data?.top_browsers} isLoading={false} />
            <TopListCard title={t("analytics.topOs")} items={data?.top_os} isLoading={false} />
            <TopListCard title={t("analytics.topReferrers")} items={data?.top_referrers} isLoading={false} />
          </div>

          {(links?.items.length ?? 0) === 0 && (
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <LinkIcon className="h-3.5 w-3.5" /> {t("analytics.createLinkHint")}
            </p>
          )}
        </>
      )}
    </div>
  );
}
