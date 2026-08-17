import { jsPDF } from "jspdf";
import type { TFunction } from "i18next";
import type { SecurityScan } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

const PAGE_WIDTH = 210;
const PAGE_HEIGHT = 297;
const MARGIN = 16;
const CONTENT_WIDTH = PAGE_WIDTH - MARGIN * 2;

const COLORS = {
  primary: [79, 70, 229] as const,
  text: [30, 30, 40] as const,
  muted: [110, 110, 125] as const,
  border: [225, 225, 232] as const,
  high: [220, 38, 38] as const,
  medium: [217, 119, 6] as const,
  low: [37, 99, 235] as const,
  info: [100, 116, 139] as const,
  success: [22, 163, 74] as const,
};

function severityColor(severity: string): readonly [number, number, number] {
  if (severity === "high") return COLORS.high;
  if (severity === "medium") return COLORS.medium;
  if (severity === "low") return COLORS.low;
  return COLORS.info;
}

function scoreColor(score: number): readonly [number, number, number] {
  if (score >= 80) return COLORS.success;
  if (score >= 50) return COLORS.medium;
  return COLORS.high;
}

class ReportWriter {
  doc = new jsPDF({ unit: "mm", format: "a4" });
  y = MARGIN;

  ensureSpace(height: number) {
    if (this.y + height > PAGE_HEIGHT - MARGIN) {
      this.doc.addPage();
      this.y = MARGIN;
    }
  }

  sectionTitle(title: string) {
    this.ensureSpace(12);
    this.y += 4;
    this.doc.setDrawColor(...COLORS.primary);
    this.doc.setLineWidth(0.6);
    this.doc.line(MARGIN, this.y, MARGIN + 8, this.y);
    this.doc.setFont("helvetica", "bold");
    this.doc.setFontSize(11);
    this.doc.setTextColor(...COLORS.text);
    this.doc.text(title, MARGIN + 11, this.y + 1.2);
    this.y += 6;
  }

  row(label: string, value: string) {
    this.ensureSpace(6);
    this.doc.setFont("helvetica", "normal");
    this.doc.setFontSize(9);
    this.doc.setTextColor(...COLORS.muted);
    this.doc.text(label, MARGIN, this.y);
    this.doc.setTextColor(...COLORS.text);
    const lines = this.doc.splitTextToSize(value || "-", CONTENT_WIDTH - 45);
    this.doc.text(lines, MARGIN + 45, this.y);
    this.y += 5 * Math.max(lines.length, 1);
  }

  paragraph(text: string) {
    this.ensureSpace(6);
    this.doc.setFont("helvetica", "normal");
    this.doc.setFontSize(9);
    this.doc.setTextColor(...COLORS.text);
    const lines = this.doc.splitTextToSize(text, CONTENT_WIDTH);
    this.doc.text(lines, MARGIN, this.y);
    this.y += 5 * lines.length;
  }

  emptyNote(text: string) {
    this.ensureSpace(5);
    this.doc.setFont("helvetica", "italic");
    this.doc.setFontSize(9);
    this.doc.setTextColor(...COLORS.muted);
    this.doc.text(text, MARGIN, this.y);
    this.y += 6;
  }

  badgeLine(color: readonly [number, number, number], label: string, text: string) {
    this.ensureSpace(6.5);
    this.doc.setFillColor(...color);
    this.doc.roundedRect(MARGIN, this.y - 3.4, 18, 4.6, 1, 1, "F");
    this.doc.setFont("helvetica", "bold");
    this.doc.setFontSize(7);
    this.doc.setTextColor(255, 255, 255);
    this.doc.text(label.toUpperCase(), MARGIN + 9, this.y - 0.3, { align: "center" });
    this.doc.setFont("helvetica", "normal");
    this.doc.setFontSize(9);
    this.doc.setTextColor(...COLORS.text);
    const lines = this.doc.splitTextToSize(text, CONTENT_WIDTH - 22);
    this.doc.text(lines, MARGIN + 22, this.y);
    this.y += 5 * Math.max(lines.length, 1) + 1;
  }

  divider() {
    this.ensureSpace(4);
    this.doc.setDrawColor(...COLORS.border);
    this.doc.setLineWidth(0.2);
    this.doc.line(MARGIN, this.y, PAGE_WIDTH - MARGIN, this.y);
    this.y += 5;
  }
}

function findingSeverityLabel(t: TFunction, severity: string): string {
  return t(`security.findingSeverity.${severity}`, severity);
}

function findingMessage(t: TFunction, finding: SecurityScan["findings"] extends (infer U)[] | null ? U : never): string {
  return t(`security.findingCodes.${finding.code}`, finding.params as Record<string, unknown>);
}

export function generateSecurityReportPdf(scan: SecurityScan, t: TFunction) {
  const w = new ReportWriter();
  const doc = w.doc;

  // --- Header banner ---
  doc.setFillColor(...COLORS.primary);
  doc.rect(0, 0, PAGE_WIDTH, 28, "F");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(15);
  doc.setTextColor(255, 255, 255);
  doc.text(t("security.pdf.title"), MARGIN, 13);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.text(scan.domain, MARGIN, 21);

  const [sr, sg, sb] = scoreColor(scan.score);
  doc.setFillColor(sr, sg, sb);
  doc.circle(PAGE_WIDTH - MARGIN - 10, 14, 9, "F");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.setTextColor(255, 255, 255);
  doc.text(String(scan.score), PAGE_WIDTH - MARGIN - 10, 16, { align: "center" });

  w.y = 36;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8.5);
  doc.setTextColor(...COLORS.muted);
  doc.text(t("security.pdf.generatedAt", { date: formatDateTime(new Date().toISOString()) }), MARGIN, w.y);
  doc.text(t("security.scannedAt", { date: formatDateTime(scan.created_at) }), PAGE_WIDTH - MARGIN, w.y, { align: "right" });
  w.y += 7;

  // --- Findings summary ---
  w.sectionTitle(t("security.findingsTitle"));
  if (!scan.findings || scan.findings.length === 0) {
    w.emptyNote(t("security.findings.no_issues_found"));
  } else {
    for (const finding of scan.findings) {
      w.badgeLine(severityColor(finding.severity), findingSeverityLabel(t, finding.severity), findingMessage(t, finding));
    }
  }
  w.divider();

  // --- DNS records ---
  w.sectionTitle(t("security.dnsTitle"));
  const dnsEntries = Object.entries(scan.dns_records ?? {}).filter(([, v]) => v.length > 0);
  if (dnsEntries.length === 0) {
    w.emptyNote(t("security.noDnsRecords"));
  } else {
    for (const [type, values] of dnsEntries) w.row(type, values.join(", "));
  }
  w.divider();

  // --- IP / ASN ---
  w.sectionTitle(t("security.ipInfoTitle"));
  if (scan.ip_info) {
    w.row(t("security.ipAddress"), scan.ip_info.ip_address);
    w.row(t("security.ipAsn"), scan.ip_info.asn ?? "-");
    w.row(t("security.ipOrg"), scan.ip_info.organization ?? scan.ip_info.isp ?? "-");
    w.row(t("security.ipLocation"), [scan.ip_info.city, scan.ip_info.country].filter(Boolean).join(", ") || "-");
  } else {
    w.emptyNote(t("security.ipInfoUnavailable"));
  }
  w.divider();

  // --- Subdomains ---
  w.sectionTitle(t("security.subdomainsTitle"));
  if (!scan.subdomains || scan.subdomains.length === 0) {
    w.emptyNote(t("security.noSubdomainsFound"));
  } else {
    w.paragraph(scan.subdomains.join(",  "));
  }
  w.divider();

  // --- DNS propagation ---
  w.sectionTitle(t("security.dnsPropagationTitle"));
  if (scan.dns_propagation) {
    w.row(
      t("security.dnsPropagationStatus"),
      scan.dns_propagation.consistent ? t("security.dnsPropagationConsistent") : t("security.dnsPropagationInconsistent"),
    );
    for (const [resolver, ips] of Object.entries(scan.dns_propagation.resolvers)) {
      w.row(resolver, ips.length > 0 ? ips.join(", ") : t("common.unknown"));
    }
  } else {
    w.emptyNote(t("security.dnsPropagationUnavailable"));
  }
  w.divider();

  // --- HTTP / security headers ---
  w.sectionTitle(t("security.headersTitle"));
  if (scan.headers_info?.reachable) {
    for (const [header, value] of Object.entries(scan.headers_info.headers)) {
      w.row(header, value ? t("security.headerPresent") : t("security.headerMissing"));
    }
  } else {
    w.emptyNote(scan.headers_info?.error ?? t("security.notReachable"));
  }
  w.divider();

  // --- TLS ---
  w.sectionTitle(t("security.sslTitle"));
  if (scan.ssl_info?.valid) {
    w.row(t("security.pdf.sslIssuer"), scan.ssl_info.issuer ?? t("common.unknown"));
    w.row(t("security.pdf.sslProtocol"), scan.ssl_info.protocol ?? t("common.unknown"));
    w.row(
      t("security.pdf.sslExpires"),
      `${scan.ssl_info.expires_at ? formatDateTime(scan.ssl_info.expires_at) : t("common.unknown")}${
        scan.ssl_info.days_remaining != null ? ` (${scan.ssl_info.days_remaining}d)` : ""
      }`,
    );
  } else {
    w.emptyNote(t("security.noValidCert"));
  }
  w.divider();

  // --- WHOIS ---
  w.sectionTitle(t("security.whoisTitle"));
  if (scan.whois_info) {
    w.row(t("security.pdf.whoisRegistrar"), scan.whois_info.registrar ?? t("common.unknown"));
    w.row(t("security.pdf.whoisCreated"), scan.whois_info.creation_date ? formatDateTime(scan.whois_info.creation_date) : t("common.unknown"));
    w.row(t("security.pdf.whoisExpires"), scan.whois_info.expiration_date ? formatDateTime(scan.whois_info.expiration_date) : t("common.unknown"));
  } else {
    w.emptyNote(t("security.whoisUnavailable"));
  }
  w.divider();

  // --- Cookies ---
  w.sectionTitle(t("security.cookiesTitle"));
  if (!scan.cookie_info || scan.cookie_info.length === 0) {
    w.emptyNote(t("security.noCookiesFound"));
  } else {
    for (const cookie of scan.cookie_info) {
      const flags = [
        cookie.secure ? "Secure" : null,
        cookie.http_only ? "HttpOnly" : null,
        cookie.same_site ? `SameSite=${cookie.same_site}` : null,
      ]
        .filter(Boolean)
        .join(", ");
      w.row(cookie.name, flags || t("security.cookieNoFlags"));
    }
  }
  w.divider();

  // --- Technology ---
  w.sectionTitle(t("security.techTitle"));
  if (!scan.tech_info || scan.tech_info.length === 0) {
    w.emptyNote(t("security.noTechDetected"));
  } else {
    w.paragraph(scan.tech_info.map((tech) => `${tech.technology} (${tech.category})`).join(",  "));
  }
  w.divider();

  // --- Robots / Sitemap ---
  w.sectionTitle(t("security.robotsTitle"));
  if (scan.robots_info) {
    w.row(t("security.robotsFound"), scan.robots_info.robots_found ? t("common.yes") : t("common.no"));
    w.row(t("security.sitemapFound"), scan.robots_info.sitemap_found ? t("common.yes") : t("common.no"));
    if (scan.robots_info.sitemap_url_count != null) w.row(t("security.sitemapUrlCount"), String(scan.robots_info.sitemap_url_count));
    if (scan.robots_info.disallow_rules.length > 0) w.paragraph(`Disallow: ${scan.robots_info.disallow_rules.join(",  ")}`);
  } else {
    w.emptyNote(t("common.unknown"));
  }

  // --- Reputation ---
  w.divider();
  w.sectionTitle(t("security.reputationLabel"));
  w.row(t("security.reputationLabel"), scan.reputation_info?.verdict ?? t("common.unknown"));

  // --- Footer / page numbers ---
  const pageCount = doc.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(7.5);
    doc.setTextColor(...COLORS.muted);
    doc.text("FurOfTheWeak Security Center", MARGIN, PAGE_HEIGHT - 8);
    doc.text(`${i} / ${pageCount}`, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 8, { align: "right" });
  }

  doc.save(`security-report-${scan.domain}-${scan.id.slice(0, 8)}.pdf`);
}
