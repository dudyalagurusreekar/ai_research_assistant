import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from "axios";

export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  correlation_id?: string;
  error?: {
    code: string;
    details: string;
  };
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

class ApiClient {
  private instance: AxiosInstance;
  private isRefreshing = false;
  private failedQueue: Array<{ resolve: (token: string) => void; reject: (err: any) => void }> = [];

  constructor() {
    this.instance = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request Interceptor: Inject JWT Access Token
    this.instance.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (typeof window !== "undefined") {
          const token = localStorage.getItem("ara_access_token");
          if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response Interceptor: Handle Refresh Token Queue & Errors
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => response.data,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            })
              .then((token) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                return this.instance(originalRequest);
              })
              .catch((err) => Promise.reject(err));
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const refreshToken = typeof window !== "undefined" ? localStorage.getItem("ara_refresh_token") : null;
            if (!refreshToken) {
              throw new Error("No refresh token available");
            }

            const refreshResponse = await axios.post(`${API_BASE_URL}/auth/refresh`, {
              refresh_token: refreshToken,
            });

            const newAccessToken = refreshResponse.data?.data?.access_token;
            if (newAccessToken && typeof window !== "undefined") {
              localStorage.setItem("ara_access_token", newAccessToken);
              this.instance.defaults.headers.common.Authorization = `Bearer ${newAccessToken}`;
              this.processQueue(null, newAccessToken);

              originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
              return this.instance(originalRequest);
            }
          } catch (refreshErr) {
            this.processQueue(refreshErr, null);
            if (typeof window !== "undefined") {
              localStorage.removeItem("ara_access_token");
              localStorage.removeItem("ara_refresh_token");
              window.location.href = "/login";
            }
            return Promise.reject(refreshErr);
          } finally {
            this.isRefreshing = false;
          }
        }

        const status = error.response?.status;
        const detailMsg = typeof error.response?.data?.detail === "string" ? error.response?.data?.detail : null;
        const rawMessage =
          error.response?.data?.error?.message ||
          detailMsg ||
          error.response?.data?.message ||
          error.message ||
          "An unexpected error occurred";

        const errorMessage = status && status === 404
          ? `Resource Not Found (404): ${error.config?.url || "Endpoint"}`
          : rawMessage;

        const customError: any = new Error(errorMessage);
        if (error.response) {
          customError.response = error.response;
          customError.status = status;
        }
        return Promise.reject(customError);
      }
    );
  }

  private processQueue(error: any, token: string | null = null): void {
    this.failedQueue.forEach((prom) => {
      if (error) {
        prom.reject(error);
      } else {
        prom.resolve(token!);
      }
    });
    this.failedQueue = [];
  }

  public get<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.instance.get(url, config);
  }

  public post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.instance.post(url, data, config);
  }

  public put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.instance.put(url, data, config);
  }

  public delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.instance.delete(url, config);
  }

  public patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.instance.patch(url, data, config);
  }
}

export const apiClient = new ApiClient();
