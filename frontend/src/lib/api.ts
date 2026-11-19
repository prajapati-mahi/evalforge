const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

class ApiService {
  private getToken(): string | null {
    if (typeof window !== "undefined") {
      return localStorage.getItem("evalforge_token");
    }
    return null;
  }

  public setToken(token: string): void {
    if (typeof window !== "undefined") {
      localStorage.setItem("evalforge_token", token);
    }
  }

  public removeToken(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("evalforge_token");
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      Accept: "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // In demo mode or development, let requests proceed gracefully
      console.warn("Unauthenticated API request.");
    }

    if (!response.ok) {
      const errorText = await response.text();
      let errorJson;
      try {
        errorJson = JSON.parse(errorText);
      } catch {
        errorJson = { detail: errorText || response.statusText };
      }
      throw new Error(errorJson.detail || `Request failed with code ${response.status}`);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // Dashboard
  async getDashboardMetrics(projectId?: number, timeRange = "30d") {
    const p = projectId ? `&project_id=${projectId}` : "";
    return this.request<any>(`/dashboard/metrics?time_range=${timeRange}${p}`);
  }

  // Projects
  async getProjects() {
    return this.request<any[]>("/projects");
  }

  async createProject(data: { name: string; description?: string; project_type?: string; default_model?: string }) {
    return this.request<any>("/projects", { method: "POST", body: JSON.stringify(data) });
  }

  async deleteProject(id: number) {
    return this.request<any>(`/projects/${id}`, { method: "DELETE" });
  }

  // Datasets
  async getDatasets(projectId?: number) {
    const p = projectId ? `?project_id=${projectId}` : "";
    return this.request<any[]>(`/datasets${p}`);
  }

  async getDatasetCases(datasetId: number) {
    return this.request<any[]>(`/datasets/${datasetId}/cases`);
  }

  async addDatasetCase(datasetId: number, data: { input_text: string; expected_output?: string; context?: string }) {
    return this.request<any>(`/datasets/${datasetId}/cases`, { method: "POST", body: JSON.stringify(data) });
  }

  async deleteDatasetCase(caseId: number) {
    return this.request<any>(`/datasets/cases/${caseId}`, { method: "DELETE" });
  }

  async seedSampleDataset(projectId: number) {
    return this.request<any>(`/datasets/seed-sample?project_id=${projectId}`, { method: "POST" });
  }

  async validateDatasetUpload(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return this.request<any>("/datasets/validate-upload", { method: "POST", body: formData });
  }

  async uploadDataset(projectId: number, name: string, description: string, file: File) {
    const formData = new FormData();
    formData.append("project_id", projectId.toString());
    formData.append("name", name);
    formData.append("description", description);
    formData.append("file", file);
    return this.request<any>("/datasets/upload", { method: "POST", body: formData });
  }

  // Prompts
  async getPrompts(projectId: number) {
    return this.request<any[]>(`/prompts?project_id=${projectId}`);
  }

  async getPromptVersions(promptId: number) {
    return this.request<any[]>(`/prompts/${promptId}/versions`);
  }

  async createPrompt(data: { project_id: number; name: string; description?: string; initial_template: string; system_instruction?: string }) {
    return this.request<any>("/prompts", { method: "POST", body: JSON.stringify(data) });
  }

  async createPromptVersion(promptId: number, data: { template_text: string; system_instruction?: string; change_summary?: string }) {
    return this.request<any>(`/prompts/${promptId}/versions`, { method: "POST", body: JSON.stringify(data) });
  }

  async testPrompt(data: { template_text: string; system_instruction?: string; variables: Record<string, string>; model_name: string }) {
    return this.request<any>("/prompts/test", { method: "POST", body: JSON.stringify(data) });
  }

  // Experiments
  async getExperiments(projectId?: number) {
    const p = projectId ? `?project_id=${projectId}` : "";
    return this.request<any[]>(`/experiments${p}`);
  }

  async getExperiment(id: number) {
    return this.request<any>(`/experiments/${id}`);
  }

  async getExperimentResults(id: number) {
    return this.request<any>(`/experiments/${id}/results`);
  }

  async createExperiment(data: any) {
    return this.request<any>("/experiments", { method: "POST", body: JSON.stringify(data) });
  }

  async runExperiment(id: number) {
    return this.request<any>(`/experiments/${id}/run`, { method: "POST" });
  }

  async cancelExperiment(id: number) {
    return this.request<any>(`/experiments/${id}/cancel`, { method: "POST" });
  }

  // Comparisons
  async getModelComparison(experimentId: number, modelNames?: string[]) {
    return this.request<any>("/comparisons", {
      method: "POST",
      body: JSON.stringify({ experiment_id: experimentId, model_names: modelNames }),
    });
  }

  // Traces
  async getTraces(projectId?: number, status?: string, modelName?: string, search?: string) {
    const params = new URLSearchParams();
    if (projectId) params.append("project_id", projectId.toString());
    if (status) params.append("status", status);
    if (modelName) params.append("model_name", modelName);
    if (search) params.append("search", search);
    return this.request<any[]>(`/traces?${params.toString()}`);
  }

  async getTrace(id: number) {
    return this.request<any>(`/traces/${id}`);
  }

  // Single Evaluation Playground
  async runEvaluation(data: { metric_name: string; query: string; response: string; expected_output?: string; context?: string; judge_model?: string }) {
    return this.request<any>("/evaluations/run", { method: "POST", body: JSON.stringify(data) });
  }

  async reviewEvaluation(evaluationId: number, overrideScore: number, passed: boolean, notes?: string) {
    return this.request<any>(`/evaluations/${evaluationId}/review`, {
      method: "PUT",
      body: JSON.stringify({ override_score: overrideScore, passed, notes }),
    });
  }

  // Providers & Pricing
  async getProviders() {
    return this.request<any[]>("/providers");
  }

  async configureProvider(data: { provider_name: string; api_key: string }) {
    return this.request<any>("/providers/configure", { method: "POST", body: JSON.stringify(data) });
  }

  async testProvider(providerName: string) {
    return this.request<any>(`/providers/test/${providerName}`, { method: "POST" });
  }

  async getPricing() {
    return this.request<any[]>("/providers/pricing");
  }

  // Reports
  async generateReport(experimentId: number, format = "pdf") {
    return this.request<any>("/reports", {
      method: "POST",
      body: JSON.stringify({ experiment_id: experimentId, format }),
    });
  }

  // Auth
  async login(email: string, password: string) {
    const res = await this.request<any>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    if (res.access_token) {
      this.setToken(res.access_token);
    }
    return res;
  }

  async register(email: string, password: string, fullName?: string) {
    const res = await this.request<any>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    if (res.access_token) {
      this.setToken(res.access_token);
    }
    return res;
  }

  async getMe() {
    return this.request<any>("/auth/me");
  }
}

export const api = new ApiService();
