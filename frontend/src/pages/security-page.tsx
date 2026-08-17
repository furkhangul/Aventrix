import { Download, Shield, ShieldAlert, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { isApiError } from "@/hooks/use-auth";
import { useRunSecurityScan, useSecurityScan, useSecurityScans } from "@/hooks/use-security-center";
import { generateSecurityReportPdf } from "@/lib/security-pdf";
import { formatDateTime } from "@/lib/utils";
import type { FindingSeverity, SecurityScan } from "@/lib/types";

function scoreVariant(score: number): "success" | "warning" | "destructive" {
  if (score >= 80) return "success";
  if (score >= 50) return "warning";
  return "destructive";
}

function severityVariant(severity: FindingSeverity): "destructive" | "warning" | "default" | "outline" {
  if (severity === "high") return "destructive";
  if (severity === "medium") return "warning";
  if (severity === "low") return "default";
  return "outline";
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <li className="flex items-start justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium text-foreground">{value}</span>
    </li>
  );
}

function Panel({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-border p-4">
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <p className="text-sm font-medium">{title}</p>
        {hint && <p className="text-[11px] text-muted-foreground">{hint}</p>}
      </div>
      {children}
    </div>
  );
}

function ScoreGauge({ score }: { score: number }) {
  const { t } = useTranslation();
  const Icon = score >= 80 ? ShieldCheck : score >= 50 ? Shield : ShieldAlert;
  return (
    <div className="flex items-center gap-4">
      <div
        className={`flex h-20 w-20 items-center justify-center rounded-full border-4 text-2xl font-semibold ${
          score >= 80 ? "border-success text-success" : score >= 50 ? "border-warning text-warning-foreground" : "border-destructive text-destructive"
        }`}
      >
        {score}
      </div>
      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
        <Icon className="h-4 w-4" />
        {t("security.scoreLabel")}
      </div>
    </div>
  );
}

function FindingsList({ scan }: { scan: SecurityScan }) {
  const { t } = useTranslation();
  const findings = scan.findings ?? [];
  if (findings.length === 0) {
    return <p className="text-xs text-muted-foreground">{t("security.findings.no_issues_found")}</p>;
  }
  return (
    <ul className="space-y-2">
      {findings.map((finding, index) => (
        <li key={`${finding.code}-${index}`} className="flex items-start gap-2 text-sm">
          <Badge variant={severityVariant(finding.severity)} className="mt-0.5 shrink-0">
            {t(`security.findingSeverity.${finding.severity}`)}
          </Badge>
          <span className="text-foreground">
            {t(`security.findingCodes.${finding.code}`, finding.params as Record<string, unknown>)}
          </span>
        </li>
      ))}
    </ul>
  );
}

function ScanResult({ scan }: { scan: SecurityScan }) {
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="text-base font-semibold text-foreground">{scan.domain}</CardTitle>
        <div className="flex items-center gap-2">
          <Badge variant={scoreVariant(scan.score)}>{scan.score}/100</Badge>
          <Button type="button" variant="outline" size="sm" onClick={() => generateSecurityReportPdf(scan, t)}>
            <Download className="mr-1.5 h-3.5 w-3.5" />
            {t("security.downloadPdf")}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <ScoreGauge score={scan.score} />

        <Panel title={t("security.findingsTitle")}>
          <FindingsList scan={scan} />
        </Panel>

        <Tabs defaultValue="dns">
          <TabsList className="flex-wrap">
            <TabsTrigger value="dns">{t("security.dnsTitle")}</TabsTrigger>
            <TabsTrigger value="tls-headers">{t("security.sslTitle")}</TabsTrigger>
            <TabsTrigger value="cookies-tech">{t("security.cookiesTitle")}</TabsTrigger>
            <TabsTrigger value="robots">{t("security.robotsTitle")}</TabsTrigger>
            <TabsTrigger value="whois">{t("security.whoisTitle")}</TabsTrigger>
          </TabsList>

          <TabsContent value="dns" className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Panel title={t("security.dnsTitle")}>
              {scan.dns_records && Object.values(scan.dns_records).some((v) => v.length > 0) ? (
                <ul className="space-y-1 text-xs text-muted-foreground">
                  {Object.entries(scan.dns_records)
                    .filter(([, values]) => values.length > 0)
                    .map(([type, values]) => (
                      <li key={type}>
                        <span className="font-medium text-foreground">{type}:</span> {values.join(", ")}
                      </li>
                    ))}
                </ul>
              ) : (
                <p className="text-xs text-muted-foreground">{t("security.noDnsRecords")}</p>
              )}
            </Panel>

            <Panel title={t("security.ipInfoTitle")}>
              {scan.ip_info ? (
                <ul className="space-y-1 text-xs">
                  <InfoRow label={t("security.ipAddress")} value={scan.ip_info.ip_address} />
                  <InfoRow label={t("security.ipAsn")} value={scan.ip_info.asn ?? t("common.unknown")} />
                  <InfoRow label={t("security.ipOrg")} value={scan.ip_info.organization ?? scan.ip_info.isp ?? t("common.unknown")} />
                  <InfoRow
                    label={t("security.ipLocation")}
                    value={[scan.ip_info.city, scan.ip_info.country].filter(Boolean).join(", ") || t("common.unknown")}
                  />
                </ul>
              ) : (
                <p className="text-xs text-muted-foreground">{t("security.ipInfoUnavailable")}</p>
              )}
            </Panel>

            <Panel
              title={t("security.subdomainsTitle")}
              hint={scan.subdomains && scan.subdomains.length > 0 ? t("security.subdomainsCount", { count: scan.subdomains.length }) : undefined}
            >
              {scan.subdomains && scan.subdomains.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {scan.subdomains.map((sub) => (
                    <Badge key={sub} variant="outline" className="font-normal">
                      {sub}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">{t("security.noSubdomainsFound")}</p>
              )}
            </Panel>

            <Panel title={t("security.dnsPropagationTitle")}>
              {scan.dns_propagation ? (
                <>
                  <Badge variant={scan.dns_propagation.consistent ? "success" : "warning"} className="mb-2">
                    {scan.dns_propagation.consistent ? t("security.dnsPropagationConsistent") : t("security.dnsPropagationInconsistent")}
                  </Badge>
                  <ul className="space-y-1 text-xs text-muted-foreground">
                    {Object.entries(scan.dns_propagation.resolvers).map(([resolver, ips]) => (
                      <li key={resolver}>
                        <span className="font-medium text-foreground">{resolver}:</span> {ips.length > 0 ? ips.join(", ") : t("common.unknown")}
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <p className="text-xs text-muted-foreground">{t("security.dnsPropagationUnavailable")}</p>
              )}
            </Panel>
          </TabsContent>

          <TabsContent value="tls-headers" className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Panel title={t("security.sslTitle")}>
              {scan.ssl_info?.valid ? (
                <ul className="space-y-1 text-xs text-muted-foreground">
                  <li>{t("security.sslIssuer", { issuer: scan.ssl_info.issuer ?? t("common.unknown") })}</li>
                  <li>{t("security.sslProtocol", { protocol: scan.ssl_info.protocol ?? t("common.unknown") })}</li>
                  <li>
                    {t("security.sslExpires", { date: scan.ssl_info.expires_at ? formatDateTime(scan.ssl_info.expires_at) : t("common.unknown") })}{" "}
                    {scan.ssl_info.days_remaining != null && `(${scan.ssl_info.days_remaining}d)`}
                  </li>
                </ul>
              ) : (
                <p className="text-xs text-muted-foreground">{t("security.noValidCert")}</p>
              )}
            </Panel>

            <Panel title={t("security.headersTitle")}>
              {scan.headers_info?.reachable ? (
                <ul className="space-y-1 text-xs">
                  {Object.entries(scan.headers_info.headers).map(([header, value]) => (
                    <li key={header} className="flex items-center justify-between gap-2">
                      <span className="text-muted-foreground">{header}</span>
                      <Badge variant={value ? "success" : "outline"}>{value ? t("security.headerPresent") : t("security.headerMissing")}</Badge>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-muted-foreground">{scan.headers_info?.error ?? t("security.notReachable")}</p>
              )}
            </Panel>
          </TabsContent>

          <TabsContent value="cookies-tech" className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Panel title={t("security.cookiesTitle")}>
              {scan.cookie_info && scan.cookie_info.length > 0 ? (
                <ul className="space-y-2 text-xs">
                  {scan.cookie_info.map((cookie) => (
                    <li key={cookie.name} className="space-y-1">
                      <p className="font-medium text-foreground">{cookie.name}</p>
                      <div className="flex flex-wrap gap-1">
                        <Badge variant={cookie.secure ? "success" : "outline"}>Secure</Badge>
                        <Badge variant={cookie.http_only ? "success" : "outline"}>HttpOnly</Badge>
                        <Badge variant={cookie.same_site ? "success" : "outline"}>SameSite{cookie.same_site ? `=${cookie.same_site}` : ""}</Badge>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-muted-foreground">{t("security.noCookiesFound")}</p>
              )}
            </Panel>

            <Panel title={t("security.techTitle")}>
              {scan.tech_info && scan.tech_info.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {scan.tech_info.map((tech) => (
                    <Badge key={`${tech.category}-${tech.technology}`} variant="secondary" className="font-normal">
                      {tech.technology}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">{t("security.noTechDetected")}</p>
              )}
            </Panel>
          </TabsContent>

          <TabsContent value="robots">
            <Panel title={t("security.robotsTitle")}>
              {scan.robots_info ? (
                <ul className="space-y-1 text-xs text-muted-foreground">
                  <InfoRow label={t("security.robotsFound")} value={scan.robots_info.robots_found ? t("common.yes") : t("common.no")} />
                  <InfoRow label={t("security.sitemapFound")} value={scan.robots_info.sitemap_found ? t("common.yes") : t("common.no")} />
                  {scan.robots_info.sitemap_url_count != null && (
                    <InfoRow label={t("security.sitemapUrlCount")} value={String(scan.robots_info.sitemap_url_count)} />
                  )}
                  {scan.robots_info.disallow_rules.length > 0 && (
                    <li className="pt-2">
                      <p className="mb-1 font-medium text-foreground">{t("security.disallowRulesTitle")}</p>
                      <p className="break-all">{scan.robots_info.disallow_rules.join(", ")}</p>
                    </li>
                  )}
                </ul>
              ) : (
                <p className="text-xs text-muted-foreground">{t("common.unknown")}</p>
              )}
            </Panel>
          </TabsContent>

          <TabsContent value="whois" className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Panel title={t("security.whoisTitle")}>
              {scan.whois_info ? (
                <ul className="space-y-1 text-xs text-muted-foreground">
                  <li>{t("security.whoisRegistrar", { registrar: scan.whois_info.registrar ?? t("common.unknown") })}</li>
                  <li>{t("security.whoisCreated", { date: scan.whois_info.creation_date ? formatDateTime(scan.whois_info.creation_date) : t("common.unknown") })}</li>
                  <li>{t("security.whoisExpires", { date: scan.whois_info.expiration_date ? formatDateTime(scan.whois_info.expiration_date) : t("common.unknown") })}</li>
                </ul>
              ) : (
                <p className="text-xs text-muted-foreground">{t("security.whoisUnavailable")}</p>
              )}
            </Panel>

            <Panel title={t("security.reputationLabel")}>
              <div className="flex items-center gap-2">
                <Badge
                  variant={
                    scan.reputation_info?.verdict === "clean"
                      ? "success"
                      : scan.reputation_info?.verdict === "malicious"
                        ? "destructive"
                        : "warning"
                  }
                >
                  {scan.reputation_info?.verdict ?? t("common.unknown")}
                </Badge>
                <span className="text-xs text-muted-foreground">{t("security.reputationVia", { provider: scan.reputation_info?.provider ?? "n/a" })}</span>
              </div>
            </Panel>
          </TabsContent>
        </Tabs>

        <p className="text-xs text-muted-foreground">{t("security.scannedAt", { date: formatDateTime(scan.created_at) })}</p>
      </CardContent>
    </Card>
  );
}

export function SecurityPage() {
  const { t } = useTranslation();
  const [domain, setDomain] = useState("");
  const [historyScanId, setHistoryScanId] = useState<string | null>(null);
  const runScan = useRunSecurityScan();
  const historyScan = useSecurityScan(historyScanId ?? undefined);
  const { data: history, isLoading, isError, refetch } = useSecurityScans();

  const activeScan = historyScanId ? historyScan.data : runScan.data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{t("security.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("security.subtitle")}</p>
      </div>

      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (!domain) return;
          setHistoryScanId(null);
          runScan.mutate(domain);
        }}
      >
        <Input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder={t("security.domainPlaceholder")} className="max-w-sm" />
        <Button type="submit" disabled={runScan.isPending || !domain}>
          {runScan.isPending ? t("security.scanning") : t("security.scan")}
        </Button>
      </form>

      {runScan.isPending && <LoadingState label={t("security.scanningHint")} />}
      {runScan.isError && (
        <ErrorState message={isApiError(runScan.error) ? runScan.error.message : t("security.couldNotScan")} />
      )}
      {activeScan && <ScanResult scan={activeScan} />}

      <div>
        <h2 className="mb-3 text-sm font-semibold text-muted-foreground">{t("security.historyTitle")}</h2>
        {isLoading ? (
          <LoadingState />
        ) : isError ? (
          <ErrorState onRetry={() => refetch()} />
        ) : !history || history.items.length === 0 ? (
          <EmptyState icon={Shield} title={t("security.noScansYet")} description={t("security.noScansDescription")} />
        ) : (
          <div className="space-y-2">
            {history.items.map((scan) => (
              <button
                key={scan.id}
                type="button"
                onClick={() => setHistoryScanId(scan.id)}
                className={`flex w-full items-center justify-between rounded-md border p-3 text-left transition-colors hover:bg-muted/50 ${
                  historyScanId === scan.id ? "border-primary" : "border-border"
                }`}
              >
                <div>
                  <p className="text-sm font-medium">{scan.domain}</p>
                  <p className="text-xs text-muted-foreground">{formatDateTime(scan.created_at)}</p>
                </div>
                <Badge variant={scoreVariant(scan.score)}>{scan.score}/100</Badge>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
