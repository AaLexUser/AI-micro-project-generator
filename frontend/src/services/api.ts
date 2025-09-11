import type { FeedbackResponse, GenerateRequest, Project, ProjectStatus } from '../types';

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
  // Local storage operations for project management
  getProjectStatus(projectIndex: number): ProjectStatus {
    const status = localStorage.getItem(`aipg:status:${projectIndex}`);
    return (status as ProjectStatus) || 'not_started';
  },

  setProjectStatus(projectIndex: number, status: ProjectStatus): void {
    localStorage.setItem(`aipg:status:${projectIndex}`, status);
  },

  deleteProject(projectIndex: number): void {
    const projects = JSON.parse(localStorage.getItem('aipg:projects') || '[]');

    if (projectIndex >= 0 && projectIndex < projects.length) {
      // Clean up related localStorage entries for the deleted project
      localStorage.removeItem(`aipg:code:${projectIndex}`);
      localStorage.removeItem(`aipg:feedback:${projectIndex}`);
      localStorage.removeItem(`aipg:execution:${projectIndex}`);
      localStorage.removeItem(`aipg:status:${projectIndex}`);

      // Shift remaining entries to maintain consistency
      for (let i = projectIndex + 1; i < projects.length; i++) {
        const code = localStorage.getItem(`aipg:code:${i}`);
        const feedback = localStorage.getItem(`aipg:feedback:${i}`);
        const execution = localStorage.getItem(`aipg:execution:${i}`);
        const status = localStorage.getItem(`aipg:status:${i}`);

        if (code !== null) {
          localStorage.setItem(`aipg:code:${i - 1}`, code);
          localStorage.removeItem(`aipg:code:${i}`);
        }
        if (feedback !== null) {
          localStorage.setItem(`aipg:feedback:${i - 1}`, feedback);
          localStorage.removeItem(`aipg:feedback:${i}`);
        }
        if (execution !== null) {
          localStorage.setItem(`aipg:execution:${i - 1}`, execution);
          localStorage.removeItem(`aipg:execution:${i}`);
        }
        if (status !== null) {
          localStorage.setItem(`aipg:status:${i - 1}`, status);
          localStorage.removeItem(`aipg:status:${i}`);
        }
      }

      // Remove the project from the array
      projects.splice(projectIndex, 1);
      localStorage.setItem('aipg:projects', JSON.stringify(projects));
    }
  },
};
