import { Download, QrCode as QrCodeIcon, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { EmptyState, LoadingState } from "@/components/ui/states";
import { buildQrUrl, buildQrUrlForLink, useUploadQrLogo, type QrOptions } from "@/hooks/use-qr";
import { useLinks } from "@/hooks/use-links";
import { useToast } from "@/hooks/use-toast";

const DEFAULT_OPTIONS: QrOptions = {
  size: 300,
  fgColor: "000000",
  bgColor: "FFFFFF",
  errorCorrection: "M",
  format: "png",
};

export function QrCodesPage() {
  const { t } = useTranslation();
  const { data: links, isLoading } = useLinks({ pageSize: 100 });
  const { toast } = useToast();
  const uploadLogo = useUploadQrLogo();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [linkId, setLinkId] = useState<string>("");
  const [customUrl, setCustomUrl] = useState("");
  const [options, setOptions] = useState<QrOptions>(DEFAULT_OPTIONS);

  const source = linkId ? links?.items.find((l) => l.id === linkId) : undefined;
  const previewUrl = linkId
    ? buildQrUrlForLink(linkId, options)
    : customUrl
      ? buildQrUrl(customUrl, options)
      : null;

  const handleLogoUpload = async (file: File) => {
    try {
      const result = await uploadLogo.mutateAsync(file);
      setOptions((prev) => ({ ...prev, logoId: result.logo_id }));
      toast({ title: t("qr.logoUploaded") });
    } catch {
      toast({ title: t("qr.logoUploadFailed"), variant: "destructive" });
    }
  };

  if (isLoading) return <LoadingState />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{t("qr.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("qr.subtitle")}</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr,340px]">
        <Card>
          <CardHeader>
            <CardTitle>{t("qr.sourceTitle")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label>{t("qr.fromLink")}</Label>
              <Select
                value={linkId || "none"}
                onValueChange={(v) => {
                  setLinkId(v === "none" ? "" : v);
                  if (v !== "none") setCustomUrl("");
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t("qr.chooseLink")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">{t("qr.noneCustomUrl")}</SelectItem>
                  {links?.items.map((link) => (
                    <SelectItem key={link.id} value={link.id}>
                      /{link.short_code}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {!linkId && (
              <div className="space-y-1.5">
                <Label htmlFor="custom-url">{t("qr.orCustomUrl")}</Label>
                <Input
                  id="custom-url"
                  placeholder={t("qr.customUrlPlaceholder")}
                  value={customUrl}
                  onChange={(e) => setCustomUrl(e.target.value)}
                />
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="size">{t("qr.size")}</Label>
                <Input
                  id="size"
                  type="number"
                  min={64}
                  max={2000}
                  value={options.size}
                  onChange={(e) => setOptions((prev) => ({ ...prev, size: Number(e.target.value) || prev.size }))}
                />
              </div>
              <div className="space-y-1.5">
                <Label>{t("qr.errorCorrection")}</Label>
                <Select
                  value={options.errorCorrection}
                  onValueChange={(v) => setOptions((prev) => ({ ...prev, errorCorrection: v as QrOptions["errorCorrection"] }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="L">{t("qr.errorCorrectionLow")}</SelectItem>
                    <SelectItem value="M">{t("qr.errorCorrectionMedium")}</SelectItem>
                    <SelectItem value="Q">{t("qr.errorCorrectionQuartile")}</SelectItem>
                    <SelectItem value="H">{t("qr.errorCorrectionHigh")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="fg-color">{t("qr.fgColor")}</Label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    className="h-9 w-9 shrink-0 rounded-md border border-input"
                    value={`#${options.fgColor}`}
                    onChange={(e) => setOptions((prev) => ({ ...prev, fgColor: e.target.value.slice(1) }))}
                  />
                  <Input
                    id="fg-color"
                    value={options.fgColor}
                    onChange={(e) => setOptions((prev) => ({ ...prev, fgColor: e.target.value.replace("#", "") }))}
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="bg-color">{t("qr.bgColor")}</Label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    className="h-9 w-9 shrink-0 rounded-md border border-input"
                    value={`#${options.bgColor}`}
                    onChange={(e) => setOptions((prev) => ({ ...prev, bgColor: e.target.value.slice(1) }))}
                  />
                  <Input
                    id="bg-color"
                    value={options.bgColor}
                    onChange={(e) => setOptions((prev) => ({ ...prev, bgColor: e.target.value.replace("#", "") }))}
                  />
                </div>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label>{t("qr.logoLabel")}</Label>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void handleLogoUpload(file);
                }}
              />
              <div className="flex items-center gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} disabled={uploadLogo.isPending}>
                  <Upload className="h-4 w-4" />
                  {uploadLogo.isPending ? t("common.uploading") : t("qr.uploadLogo")}
                </Button>
                {options.logoId && (
                  <Button type="button" variant="ghost" size="sm" onClick={() => setOptions((prev) => ({ ...prev, logoId: undefined }))}>
                    {t("qr.remove")}
                  </Button>
                )}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label>{t("qr.format")}</Label>
              <Select value={options.format} onValueChange={(v) => setOptions((prev) => ({ ...prev, format: v as QrOptions["format"] }))}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="png">PNG</SelectItem>
                  <SelectItem value="svg">SVG</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("qr.previewTitle")}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-4">
            {previewUrl ? (
              <>
                <div className="flex items-center justify-center rounded-lg border border-border bg-white p-4">
                  <img key={previewUrl} src={previewUrl} alt="QR code preview" className="h-48 w-48" />
                </div>
                {source && <p className="text-center text-xs text-muted-foreground">{source.short_url}</p>}
                <Button asChild className="w-full">
                  <a href={previewUrl} download={`qr-code.${options.format}`}>
                    <Download className="h-4 w-4" />
                    {t("qr.download", { format: options.format.toUpperCase() })}
                  </a>
                </Button>
              </>
            ) : (
              <EmptyState icon={QrCodeIcon} title={t("qr.emptyPreviewTitle")} description={t("qr.emptyPreviewDescription")} />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
