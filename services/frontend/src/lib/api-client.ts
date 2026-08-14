/**
 * Universal API Client for ARA v1.0 Backend API Integration.
 */

export interface ResponseEnvelope<T = any> {
  success: boolean;
  data: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  } | null;
  timestamp: string;
  correlation_id?: string;
}

export class ApiError extends Error {
  code: string;
  details?: any;
  status: number;

  constructor(message: string, code: string = "API_ERROR", status: number = 500, details?: any) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("ara_access_token") : null;
  const correlationId = typeof window !== "undefined" ? window.crypto.randomUUID() : "client-init";

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Correlation-ID": correlationId,
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith("http") ? endpoint : `${BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const isJson = response.headers.get("content-type")?.includes("application/json");
    const body = isJson ? await response.json() : null;

    if (!response.ok) {
      const errorMsg = body?.error?.message || body?.detail || response.statusText || "Request failed";
      const errorCode = body?.error?.code || `HTTP_${response.status}`;
      throw new ApiError(errorMsg, errorCode, response.status, body?.error?.details);
    }

    // Unwrap ResponseEnvelope if present
    if (body && typeof body === "object" && "success" in body && "data" in body) {
      const envelope = body as ResponseEnvelope<T>;
      if (!envelope.success) {
        throw new ApiError(
          envelope.error?.message || "Operation failed",
          envelope.error?.code || "UNHANDLED_ERROR",
          response.status,
          envelope.error?.details
        );
      }
      return envelope.data;
    }

    return body as T;
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(err.message || "Network connection error", "NETWORK_ERROR", 0);
  }
}
