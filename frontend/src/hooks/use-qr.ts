import { useMutation } from "@tanstack/react-query";
import { apiUpload } from "@/lib/api";

export interface QrOptions {
  size: number;
  fgColor: string;
  bgColor: string;
  errorCorrection: "L" | "M" | "Q" | "H";
  format: "png" | "svg";
  logoId?: string;
}

function buildQuery(data: string, options: QrOptions): string {
  const search = new URLSearchParams({
    data,
    size: String(options.size),
    fg_color: options.fgColor,
    bg_color: options.bgColor,
    error_correction: options.errorCorrection,
    format: options.format,
  });
  if (options.logoId) search.set("logo_id", options.logoId);
  return search.toString();
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export function buildQrUrl(data: string, options: QrOptions): string {
  return `${API_BASE}/api/v1/qr/generate?${buildQuery(data, options)}`;
}

export function buildQrUrlForLink(linkId: string, options: QrOptions): string {
  const search = new URLSearchParams({
    size: String(options.size),
    fg_color: options.fgColor,
    bg_color: options.bgColor,
    error_correction: options.errorCorrection,
    format: options.format,
  });
  if (options.logoId) search.set("logo_id", options.logoId);
  return `${API_BASE}/api/v1/qr/links/${linkId}?${search.toString()}`;
}

export function useUploadQrLogo() {
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return apiUpload<{ logo_id: string; url: string }>("/api/v1/qr/logo", formData);
    },
  });
}
