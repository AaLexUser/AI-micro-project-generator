"use client";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "../../../components/ui/button";
import { Textarea } from "../../../components/ui/textarea";
import { toast } from "sonner";

type MicroProject = {
  id: string;
  title: string;
  task_description: string | null;
  task_goal: string | null;
  expert_solution: string | null;
  issue: string;
  createdAt: string;
};

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const [project, setProject] = useState<MicroProject | null>(null);
  const [userSolution, setUserSolution] = useState("");
  const [showExpert, setShowExpert] = useState(false);

  useEffect(() => {
    const saved: MicroProject[] = JSON.parse(localStorage.getItem("projects") || "[]");
    const found = saved.find((p) => p.id === params.id);
    setProject(found ?? null);
  }, [params.id]);

  const canReveal = useMemo(() => userSolution.trim().length > 0, [userSolution]);

  if (!project) {
    return (
      <div className="rounded-2xl border bg-background/70 p-6 text-muted-foreground backdrop-blur-sm">
        Project not found. Go back to <a className="text-primary underline" href="/projects">Projects</a>.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="glass ring-gradient rounded-2xl p-6">
        <h2 className="mb-1 text-xl font-semibold">{project.title}</h2>
        <p className="text-sm text-muted-foreground">Created {new Date(project.createdAt).toLocaleString()}</p>
        <div className="mt-4 grid grid-cols-1 gap-6 md:grid-cols-2">
          <section>
            <h3 className="mb-2 text-lg font-medium">Description</h3>
            <p className="whitespace-pre-wrap text-foreground">{project.task_description ?? "No description"}</p>
          </section>
          <section>
            <h3 className="mb-2 text-lg font-medium">Goal</h3>
            <p className="whitespace-pre-wrap text-foreground">{project.task_goal ?? "No goal provided"}</p>
          </section>
        </div>
      </div>

      <div className="rounded-2xl border bg-background/70 p-6 backdrop-blur-sm">
        <h3 className="mb-3 text-lg font-medium">Your Solution</h3>
        <Textarea
          value={userSolution}
          onChange={(e) => setUserSolution(e.target.value)}
          className="h-60 w-full resize-y font-mono text-sm"
          placeholder="Paste your solution here"
        />
        <div className="mt-3">
          <Button
            onClick={() => { setShowExpert(true); toast.success("Solution submitted"); }}
            disabled={!canReveal}
          >
            Submit Solution
          </Button>
        </div>
      </div>

      {showExpert && (
        <div className="rounded-2xl border bg-background/70 p-6 backdrop-blur-sm">
          <h3 className="mb-3 text-lg font-medium">Expert Solution</h3>
          <pre className="whitespace-pre-wrap rounded-md bg-muted p-4 text-sm">{project.expert_solution ?? "No expert solution available"}</pre>
        </div>
      )}
    </div>
  );
}


