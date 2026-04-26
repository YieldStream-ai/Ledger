import axios from "axios";
import type { ParseConfig, ParseResponse, ReviewItem, TemplateDetail } from "./types";

const API_BASE = import.meta.env.VITE_API_URL || "";

const api = axios.create({ baseURL: API_BASE });

export async function parseUpload(
  file: File,
  config: ParseConfig,
  onProgress?: (pct: number) => void
): Promise<ParseResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (config.documentTypeHint) {
    formData.append("document_type_hint", config.documentTypeHint);
  }
  formData.append("include_enrichment", String(config.includeEnrichment));
  formData.append("cross_check_balances", String(config.crossCheckBalances));
  if (config.businessName) {
    formData.append("business_name", config.businessName);
  }
  if (config.industry) {
    formData.append("industry", config.industry);
  }

  const res = await api.post<ParseResponse>("/parse/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (e.total) {
        onProgress?.(Math.round((e.loaded * 100) / e.total));
      }
    },
  });
  return res.data;
}

export async function getReviewQueue(): Promise<ReviewItem[]> {
  const res = await api.get<ReviewItem[]>("/review/queue");
  return res.data;
}

export async function clearReviewQueue(): Promise<void> {
  await api.delete("/review/queue");
}

export async function removeReviewItem(id: string): Promise<void> {
  await api.delete(`/review/queue/${id}`);
}

export async function getBankTemplates(): Promise<TemplateDetail[]> {
  const res = await api.get<TemplateDetail[]>("/templates/bank");
  return res.data;
}

export async function healthCheck(): Promise<boolean> {
  try {
    await api.get("/health");
    return true;
  } catch {
    return false;
  }
}
