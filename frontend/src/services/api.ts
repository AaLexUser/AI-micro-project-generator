import type { FeedbackResponse, GenerateRequest, Project } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

async function http<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });
  if (!res.ok) {
    let detail: string | undefined;
    try {
      const data = await res.json();
      detail = (data as any)?.detail;
    } catch {}
    throw new Error(detail || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  async generateProjects(payload: GenerateRequest): Promise<Project[]> {
    return http<Project[]>('/projects', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  async getFeedback(payload: { project: Project; user_solution: string }): Promise<FeedbackResponse> {
    return http<FeedbackResponse>('/feedback', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};


