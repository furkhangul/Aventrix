import { Copy, Link2 } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { useAnalyzeUrl, useRedirectCheck } from "@/hooks/use-url-tools";
import { useToast } from "@/hooks/use-toast";
import { isApiError } from "@/hooks/use-auth";

function EncoderDecoderTab() {
  const { t } = useTranslation();
  const { toast } = useToast();
  const [input, setInput] = useState("");

  const encoded = useMemo(() => {
    try {
      return encodeURIComponent(input);
    } catch {
      return "";
    }
  }, [input]);
  const decoded = useMemo(() => {
    try {
      return decodeURIComponent(input);
    } catch {
      return t("urlTools.encoder.invalidInput");
    }
  }, [input, t]);

  const copy = (value: string) => {
    navigator.clipboard.writeText(value);
    toast({ title: t("common.copiedToClipboard") });
  };

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="encoder-input">{t("urlTools.encoder.inputLabel")}</Label>
        <Input id="encoder-input" value={input} onChange={(e) => setInput(e.target.value)} placeholder="https://example.com/path?q=hello world" />
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label>{t("urlTools.encoder.encoded")}</Label>
          <div className="flex items-start gap-2 rounded-md border border-border bg-muted/40 p-2.5">
            <code className="flex-1 break-all text-sm">{encoded || "—"}</code>
            <Button type="button" variant="ghost" size="icon" onClick={() => copy(encoded)}>
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div className="space-y-1.5">
          <Label>{t("urlTools.encoder.decoded")}</Label>
          <div className="flex items-start gap-2 rounded-md border border-border bg-muted/40 p-2.5">
            <code className="flex-1 break-all text-sm">{decoded || "—"}</code>
            <Button type="button" variant="ghost" size="icon" onClick={() => copy(decoded)}>
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function UtmBuilderTab() {
  const { t } = useTranslation();
  const { toast } = useToast();
  const [baseUrl, setBaseUrl] = useState("");
  const [source, setSource] = useState("");
  const [medium, setMedium] = useState("");
  const [campaign, setCampaign] = useState("");
  const [term, setTerm] = useState("");
  const [content, setContent] = useState("");

  const built = useMemo(() => {
    if (!baseUrl) return "";
    try {
      const url = new URL(baseUrl);
      if (source) url.searchParams.set("utm_source", source);
      if (medium) url.searchParams.set("utm_medium", medium);
      if (campaign) url.searchParams.set("utm_campaign", campaign);
      if (term) url.searchParams.set("utm_term", term);
      if (content) url.searchParams.set("utm_content", content);
      return url.toString();
    } catch {
      return "";
    }
  }, [baseUrl, source, medium, campaign, term, content]);

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="utm-base">{t("urlTools.utm.destinationUrl")}</Label>
        <Input id="utm-base" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} placeholder="https://example.com" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="utm-source">{t("urlTools.utm.source")}</Label>
          <Input id="utm-source" value={source} onChange={(e) => setSource(e.target.value)} placeholder="instagram" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="utm-medium">{t("urlTools.utm.medium")}</Label>
          <Input id="utm-medium" value={medium} onChange={(e) => setMedium(e.target.value)} placeholder="social" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="utm-campaign">{t("urlTools.utm.campaign")}</Label>
          <Input id="utm-campaign" value={campaign} onChange={(e) => setCampaign(e.target.value)} placeholder="summer2026" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="utm-term">{t("urlTools.utm.term")}</Label>
          <Input id="utm-term" value={term} onChange={(e) => setTerm(e.target.value)} />
        </div>
        <div className="col-span-2 space-y-1.5">
          <Label htmlFor="utm-content">{t("urlTools.utm.content")}</Label>
          <Input id="utm-content" value={content} onChange={(e) => setContent(e.target.value)} />
        </div>
      </div>
      {built && (
        <div className="space-y-1.5">
          <Label>{t("urlTools.utm.generatedUrl")}</Label>
          <div className="flex items-start gap-2 rounded-md border border-border bg-muted/40 p-2.5">
            <code className="flex-1 break-all text-sm">{built}</code>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => {
                navigator.clipboard.writeText(built);
                toast({ title: t("common.copiedToClipboard") });
              }}
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

function AnalyzerTab() {
  const { t } = useTranslation();
  const [url, setUrl] = useState("");
  const analyze = useAnalyzeUrl();

  return (
    <div className="space-y-4">
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (url) analyze.mutate(url);
        }}
      >
        <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder={t("urlTools.analyzer.urlPlaceholder")} className="flex-1" />
        <Button type="submit" disabled={analyze.isPending || !url}>
          {analyze.isPending ? t("urlTools.analyzer.analyzing") : t("urlTools.analyzer.analyze")}
        </Button>
      </form>

      {analyze.isPending && <LoadingState label={t("urlTools.analyzer.fetchingPage")} />}
      {analyze.isError && (
        <ErrorState message={isApiError(analyze.error) ? analyze.error.message : t("urlTools.analyzer.couldNotAnalyze")} />
      )}
      {analyze.data && (
        <Card>
          <CardContent className="space-y-3 p-5">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={analyze.data.status_code < 400 ? "success" : "destructive"}>{analyze.data.status_code}</Badge>
              <span className="text-sm text-muted-foreground">{analyze.data.elapsed_ms.toFixed(0)} ms</span>
              {analyze.data.redirect_count > 0 && (
                <Badge variant="outline">{t("urlTools.analyzer.redirects", { count: analyze.data.redirect_count })}</Badge>
              )}
            </div>
            <div>
              <p className="text-xs text-muted-foreground">{t("urlTools.analyzer.finalUrl")}</p>
              <p className="break-all text-sm">{analyze.data.final_url}</p>
            </div>
            {analyze.data.title && (
              <div>
                <p className="text-xs text-muted-foreground">{t("urlTools.analyzer.title")}</p>
                <p className="text-sm font-medium">{analyze.data.title}</p>
              </div>
            )}
            {analyze.data.description && (
              <div>
                <p className="text-xs text-muted-foreground">{t("urlTools.analyzer.description")}</p>
                <p className="text-sm">{analyze.data.description}</p>
              </div>
            )}
            <div>
              <p className="text-xs text-muted-foreground">{t("urlTools.analyzer.contentType")}</p>
              <p className="text-sm">{analyze.data.content_type ?? t("urlTools.analyzer.unknown")}</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function RedirectCheckerTab() {
  const { t } = useTranslation();
  const [url, setUrl] = useState("");
  const check = useRedirectCheck();

  return (
    <div className="space-y-4">
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (url) check.mutate(url);
        }}
      >
        <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com" className="flex-1" />
        <Button type="submit" disabled={check.isPending || !url}>
          {check.isPending ? t("urlTools.redirects.checking") : t("urlTools.redirects.checkChain")}
        </Button>
      </form>

      {check.isPending && <LoadingState label={t("urlTools.redirects.followingRedirects")} />}
      {check.isError && (
        <ErrorState message={isApiError(check.error) ? check.error.message : t("urlTools.redirects.couldNotCheck")} />
      )}
      {check.data && (
        <div className="space-y-2">
          {check.data.hops.map((hop, index) => (
            <div key={index} className="flex items-start gap-3 rounded-md border border-border p-3">
              <Badge variant={hop.status_code < 400 ? (hop.status_code >= 300 ? "warning" : "success") : "destructive"}>
                {hop.status_code}
              </Badge>
              <div className="min-w-0 flex-1">
                <p className="break-all text-sm">{hop.url}</p>
                {hop.location && (
                  <p className="mt-0.5 flex items-center gap-1 break-all text-xs text-muted-foreground">
                    <Link2 className="h-3 w-3 shrink-0" /> {hop.location}
                  </p>
                )}
              </div>
              <span className="shrink-0 text-xs text-muted-foreground">{hop.elapsed_ms.toFixed(0)} ms</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function UrlToolsPage() {
  const { t } = useTranslation();
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{t("urlTools.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("urlTools.subtitle")}</p>
      </div>

      <Tabs defaultValue="encoder">
        <TabsList>
          <TabsTrigger value="encoder">{t("urlTools.tabEncoder")}</TabsTrigger>
          <TabsTrigger value="utm">{t("urlTools.tabUtm")}</TabsTrigger>
          <TabsTrigger value="analyzer">{t("urlTools.tabAnalyzer")}</TabsTrigger>
          <TabsTrigger value="redirects">{t("urlTools.tabRedirects")}</TabsTrigger>
        </TabsList>
        <TabsContent value="encoder">
          <Card>
            <CardHeader>
              <CardTitle>{t("urlTools.encoder.title")}</CardTitle>
            </CardHeader>
            <CardContent>
              <EncoderDecoderTab />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="utm">
          <Card>
            <CardHeader>
              <CardTitle>{t("urlTools.utm.title")}</CardTitle>
            </CardHeader>
            <CardContent>
              <UtmBuilderTab />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="analyzer">
          <AnalyzerTab />
        </TabsContent>
        <TabsContent value="redirects">
          <RedirectCheckerTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
