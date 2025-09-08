"use client";
import { useEffect, useState } from "react";
import { Button } from "../../components/ui/button";

type MicroProject = {
  id: string;
  title: string;
  task_description: string | null;
  task_goal: string | null;
  expert_solution: string | null;
  issue: string;
  createdAt: string;
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<MicroProject[]>([]);

  useEffect(() => {
    const saved: MicroProject[] = JSON.parse(localStorage.getItem("projects") || "[]");
    setProjects(saved);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <h2 className="text-xl font-semibold tracking-tight">Generated Projects</h2>
        <a href="/" className="text-xs text-muted-foreground hover:text-foreground">Generate another</a>
      </div>
      {projects.length === 0 && (
        <div className="rounded-2xl border bg-background/70 p-6 text-muted-foreground backdrop-blur-sm">No projects yet. Generate one from the chat.</div>
      )}
      <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((p) => (
          <li key={p.id} className="glass ring-gradient rounded-2xl p-4">
            <h3 className="mb-2 line-clamp-2 text-base font-medium">{p.title}</h3>
            <p className="line-clamp-3 text-sm text-muted-foreground">{p.task_description ?? "No description"}</p>
            <div className="mt-3 flex items-center justify-between text-[11px] text-muted-foreground">
              <span>{new Date(p.createdAt).toLocaleString()}</span>
              <Button size="sm" href={`/projects/${p.id}`}>
                Open
              </Button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}


