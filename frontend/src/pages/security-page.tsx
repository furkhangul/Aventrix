import { Shield, ShieldAlert, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { isApiError } from "@/hooks/use-auth";
import { useRunSecurityScan, useSecurityScans } from "@/hooks/use-security-center";
import { formatDateTime } from "@/lib/utils";
import type { SecurityScan } from "@/lib/types";

function scoreVariant(score: number): "success" | "warning" | "destructive" {
  if (score >= 80) return "success";
  if (score >= 50) return "warning";
  return "destructive";
}

function ScoreGauge({ score }: { score: number }) {
  const { t } = useTranslation();
  const Icon = score >= 80 ? ShieldCheck : score >= 50 ? Shield : ShieldAlert;
  return (
    <div className="flex items-center gap-4">
      <div className={`flex h-20 w-20 items-center justify-center rounded-full border-4 text-2xl font-semibold ${
        score >= 80 ? "border-success text-success" : score >= 50 ? "border-warning text-warning-foreground" : "border-destructive text-destructive"
      }`}>
        {score}
      </div>
      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
        <Icon className="h-4 w-4" />
        {t("security.scoreLabel")}
      </div>
    </div>
  );
}

function ScanResult({ scan }: { scan: SecurityScan }) {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base font-semibold text-foreground">{scan.domain}</CardTitle>
        <Badge variant={scoreVariant(scan.score)}>{scan.score}/100</Badge>
      </CardHeader>
      <CardContent className="space-y-5">
        <ScoreGauge score={scan.score} />

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="rounded-md border border-border p-3">
            <p className="mb-2 text-sm font-medium">{t("security.sslTitle")}</p>
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
          </div>

          <div className="rounded-md border border-border p-3">
            <p className="mb-2 text-sm font-medium">{t("security.headersTitle")}</p>
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
          </div>

          <div className="rounded-md border border-border p-3">
            <p className="mb-2 text-sm font-medium">{t("security.dnsTitle")}</p>
            {scan.dns_records ? (
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
          </div>

          <div className="rounded-md border border-border p-3">
            <p className="mb-2 text-sm font-medium">{t("security.whoisTitle")}</p>
            {scan.whois_info ? (
              <ul className="space-y-1 text-xs text-muted-foreground">
                <li>{t("security.whoisRegistrar", { registrar: scan.whois_info.registrar ?? t("common.unknown") })}</li>
                <li>{t("security.whoisCreated", { date: scan.whois_info.creation_date ? formatDateTime(scan.whois_info.creation_date) : t("common.unknown") })}</li>
                <li>{t("security.whoisExpires", { date: scan.whois_info.expiration_date ? formatDateTime(scan.whois_info.expiration_date) : t("common.unknown") })}</li>
              </ul>
            ) : (
              <p className="text-xs text-muted-foreground">{t("security.whoisUnavailable")}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-md border border-border p-3">
          <p className="text-sm font-medium">{t("security.reputationLabel")}</p>
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

        <p className="text-xs text-muted-foreground">{t("security.scannedAt", { date: formatDateTime(scan.created_at) })}</p>
      </CardContent>
    </Card>
  );
}

export function SecurityPage() {
  const { t } = useTranslation();
  const [domain, setDomain] = useState("");
  const runScan = useRunSecurityScan();
  const { data: history, isLoading, isError, refetch } = useSecurityScans();

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
          if (domain) runScan.mutate(domain);
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
      {runScan.data && <ScanResult scan={runScan.data} />}

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
              <div key={scan.id} className="flex items-center justify-between rounded-md border border-border p-3">
                <div>
                  <p className="text-sm font-medium">{scan.domain}</p>
                  <p className="text-xs text-muted-foreground">{formatDateTime(scan.created_at)}</p>
                </div>
                <Badge variant={scoreVariant(scan.score)}>{scan.score}/100</Badge>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
