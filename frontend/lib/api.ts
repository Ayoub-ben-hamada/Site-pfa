const RAW_API_URL = process.env.NEXT_PUBLIC_API_URL
const API_BASE = RAW_API_URL?.replace(/\/$/, "") || "http://localhost:8000"

if (typeof window !== "undefined" && !RAW_API_URL) {
  // Helpful dev-time warning when env var is not configured
  // (optional fallback to localhost to keep local dev working)
  // eslint-disable-next-line no-console
  console.warn(
    "NEXT_PUBLIC_API_URL is not set — defaulting frontend API base to http://localhost:8000"
  )
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("cni_token") : null

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    cache: "no-store",
    headers,
  })

  if (!response.ok) {
    if (response.status === 401 && typeof window !== "undefined" && endpoint !== "/login") {
      localStorage.removeItem("cni_token")
      localStorage.removeItem("cni_user")
      window.location.assign("/login")
    }

    const error = await response.json().catch(() => ({ detail: "Erreur serveur" }))
    throw new Error(error.detail || `Erreur ${response.status}`)
  }

  return response.json()
}

export interface PredictionFieldOption {
  label: string
  value: string
}

export interface PredictionField {
  name: string
  label: string
  type: "number" | "select" | "text" | "checkbox-group"
  placeholder?: string
  options?: Array<string | PredictionFieldOption>
  min?: number
  max?: number
  step?: number
}

export interface PredictionModelMeta {
  model_name: string
  display_name: string
  description: string
  model_type: "classification" | "regression"
  required_features: string[]
  input_fields: PredictionField[]
  example_values: Record<string, any>
}

export interface PredictionResponse {
  model_name: string
  display_name: string
  model_type: "classification" | "regression"
  prediction: number
  probability?: number | null
  confidence?: number | null
  message: string
  model_backend: string
  used_features: string[]
  input_summary: Record<string, any>
}

// Auth
export const authApi = {
  login: (email: string, password: string) =>
    apiRequest<{ access_token: string; user: any }>("/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  
  me: () => apiRequest<any>("/me"),
}

// Client APIs
export const clientApi = {
  getProducts: () => apiRequest<any[]>("/products"),
  updateProduct: (productId: number) =>
    apiRequest<any>(`/products/${productId}/update`, { method: "POST" }),
  getNotifications: () => apiRequest<any[]>("/notifications"),
  getInstallations: () => apiRequest<any[]>("/client/installations"),
}

// Admin APIs
export const adminApi = {
  getUsers: () => apiRequest<any[]>("/admin/users"),
  createUser: (data: any) =>
    apiRequest<any>("/admin/users", { method: "POST", body: JSON.stringify(data) }),
  updateUser: (userId: number, data: any) =>
    apiRequest<any>(`/admin/users/${userId}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteUser: (userId: number) =>
    apiRequest<any>(`/admin/users/${userId}`, { method: "DELETE" }),
  
  getProducts: () => apiRequest<any[]>("/admin/products"),
  createProduct: (data: any) =>
    apiRequest<any>("/admin/products", { method: "POST", body: JSON.stringify(data) }),
  updateProduct: (productId: number, data: any) =>
    apiRequest<any>(`/admin/products/${productId}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteProduct: (productId: number) =>
    apiRequest<any>(`/admin/products/${productId}`, { method: "DELETE" }),

  getPermissions: (userId: number, productId: number) =>
    apiRequest<any>(`/admin/permissions?user_id=${userId}&product_id=${productId}`),

  updatePermissions: (data: any) =>
    apiRequest<any>("/admin/permissions", { method: "PUT", body: JSON.stringify(data) }),
}

// Dashboard APIs
export const dashboardApi = {
  getKpis: () => apiRequest<any>("/dashboard/kpis"),
  getTargetAnalysis: (variable: string) => apiRequest<any>(`/dashboard/target/${variable}`),
  getPredictions: () => apiRequest<any>("/dashboard/predictions"),
  getRiskAnalysis: () => apiRequest<any>("/dashboard/risk-analysis"),
  getDecisionSupport: (limit: number = 100) => apiRequest<any>(`/dashboard/decision-support?limit=${limit}`),
  getInstallations: () => apiRequest<any[]>("/dashboard/installations"),
}

export const mlPredictionsApi = {
  listModels: () => apiRequest<PredictionModelMeta[]>("/ml-predictions/models"),
  predict: (modelName: string, features: Record<string, any>) =>
    apiRequest<PredictionResponse>("/ml-predictions/predict", {
      method: "POST",
      body: JSON.stringify({ model_name: modelName, features }),
    }),
  health: () => apiRequest<{ status: string; service: string }>("/ml-predictions/health"),
}
