"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { toast } from "sonner";
import { MessageBubble } from "../components/chat/MessageBubble";
import { CheckCircle2, Sparkles, Layers, Rocket, LineChart, Shield } from "lucide-react";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type MicroProject = {
  id: string;
  title: string;
  task_description: string | null;
  task_goal: string | null;
  expert_solution: string | null;
  issue: string;
  createdAt: string;
};

export default function Page() {
  const [code, setCode] = useState("");
  const [comment, setComment] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [selectedIssue, setSelectedIssue] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const issues = useMemo(() =>
    messages
      .filter((m) => m.role === "assistant")
      .map((m) => m.content)
      .slice(-5),
  [messages]);

  const listRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function addUserMessage(text: string) {
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content: text }]);
  }
  function addAssistantMessage(text: string) {
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "assistant", content: text }]);
  }

  async function onSend() {
    if (!comment.trim()) return;
    const display = code.trim() ? `Issue: ${comment}\n\nCode:\n${code}` : comment;
    addUserMessage(display);
    // For now, echo back as a detected issue entry
    addAssistantMessage(comment.trim());
    setComment("");
    try {
      const health = await fetch("/api/health").then((r) => r.json()).catch(() => ({ status: "down" }));
      if (health?.status !== "ok") toast.warning("Backend is not reachable. Generation may fail.");
    } catch {}
  }

  async function onGenerate() {
    const issueToUse = selectedIssue || comment.trim();
    if (!issueToUse) {
      toast.message("Please select or enter an issue first");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ issue: issueToUse }),
      });
      if (!res.ok) {
        const err = await res.text();
        throw new Error(err || "Failed to generate");
      }
      const data = await res.json();
      const project: MicroProject = {
        id: crypto.randomUUID(),
        title: data.task_description?.slice(0, 60) || "Micro Project",
        task_description: data.task_description ?? null,
        task_goal: data.task_goal ?? null,
        expert_solution: data.expert_solution ?? null,
        issue: selectedIssue,
        createdAt: new Date().toISOString(),
      };
      const saved = JSON.parse(localStorage.getItem("projects") || "[]");
      saved.unshift(project);
      localStorage.setItem("projects", JSON.stringify(saved));
      addAssistantMessage(`Generated project: ${project.title}`);
      toast.success("Project generated");
      window.location.href = `/projects/${project.id}`;
    } catch (e: any) {
      const message = e?.message || "Generation failed";
      addAssistantMessage(`Error: ${message}`);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-14 md:space-y-16">
      {/* Hero */}
      <section className="relative text-center">
        <div className="mx-auto max-w-4xl">
          <div className="inline-flex items-center gap-2 rounded-full border bg-background/60 px-3 py-1 text-xs text-muted-foreground backdrop-blur">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-blue-500" />
            Trusted by teams leveling up through real code
          </div>
          <h1 className="display-1 mt-4 font-bold tracking-tight">
            Turning code reviews into <span className="gradient-text">elite micro‑projects</span>
          </h1>
          <p className="display-2 mx-auto mt-3 max-w-3xl text-muted-foreground">
            Paste feedback. Get a guided challenge with objectives and an expert solution. Move like a modern fintech unicorn.
          </p>
          <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button className="relative">
              <span className="absolute inset-0 rounded-md opacity-0 transition-opacity hover:opacity-100 shine" />
              <span className="relative">Start generating</span>
            </Button>
            <a href="/projects" className="rounded-md border px-4 py-2 text-sm hover:bg-accent">View projects</a>
          </div>
        </div>
        <div className="pointer-events-none absolute inset-x-0 -bottom-6 h-24 dot-grid opacity-20" />
      </section>

      {/* Trust bar */}
      <section className="mx-auto -mt-4 max-w-5xl rounded-2xl border bg-background/60 p-4 backdrop-blur-sm ring-gradient">
        <div className="grid grid-cols-2 items-center gap-6 sm:grid-cols-3 md:grid-cols-6">
          {[
            "Aurum Capital",
            "Nebula Labs",
            "Vertex AI",
            "Helios Bank",
            "Orion Cloud",
            "QuantumEdge",
          ].map((name) => (
            <div key={name} className="logo-sheen text-center text-xs font-medium text-muted-foreground">
              {name}
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {[
            { icon: <Sparkles className="h-5 w-5 text-blue-400" />, title: "Generate instantly", desc: "From review to challenge with one click." },
            { icon: <Layers className="h-5 w-5 text-cyan-400" />, title: "Structured tasks", desc: "Clear objectives with expert solution reveal." },
            { icon: <Shield className="h-5 w-5 text-indigo-400" />, title: "Best‑practice UX", desc: "Polished flows inspired by top‑tier apps." },
            { icon: <Rocket className="h-5 w-5 text-blue-400" />, title: "Career momentum", desc: "Grow rapidly with focused practice." },
            { icon: <LineChart className="h-5 w-5 text-cyan-400" />, title: "Measurable progress", desc: "Log projects and track learning." },
            { icon: <CheckCircle2 className="h-5 w-5 text-indigo-400" />, title: "Production ready", desc: "Fast, reliable experience." },
          ].map((f, idx) => (
            <div key={idx} className="glass ring-gradient rounded-2xl p-5">
              <div className="mb-2 inline-flex items-center gap-2 rounded-md border bg-background/70 px-2 py-1 text-xs text-muted-foreground">
                {f.icon}
                <span>Feature</span>
              </div>
              <div className="text-base font-medium">{f.title}</div>
              <div className="mt-1 text-sm text-muted-foreground">{f.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Steps */}
      <section className="mx-auto max-w-5xl">
        <h3 className="mb-4 text-center text-lg font-semibold tracking-tight">How it works</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {[
            { step: "1", title: "Paste context", desc: "Add code and the review comment." },
            { step: "2", title: "Generate challenge", desc: "We craft tasks and a goal." },
            { step: "3", title: "Solve & reveal", desc: "Submit your solution, then compare." },
          ].map((s) => (
            <div key={s.step} className="rounded-2xl border bg-background/70 p-5 backdrop-blur-sm">
              <div className="mb-2 text-xs text-muted-foreground">Step {s.step}</div>
              <div className="text-base font-medium">{s.title}</div>
              <div className="mt-1 text-sm text-muted-foreground">{s.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Workspace */}
      <section className="grid grid-cols-1 items-start gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <div className="glass ring-gradient rounded-2xl p-5">
            <h3 className="mb-3 text-lg font-medium">Workspace</h3>
            <div>
              <h4 className="mb-2 text-sm font-medium text-muted-foreground">Code (optional)</h4>
              <Textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="h-44 w-full resize-y font-mono text-sm"
                placeholder="Paste your code to give context..."
              />
            </div>
            <div className="mt-4">
              <h4 className="mb-2 text-sm font-medium text-muted-foreground">Review comment / Issue</h4>
              <Textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                className="h-28 w-full resize-y"
                placeholder="Describe the issue or paste a review comment..."
              />
            </div>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <Button onClick={onSend} className="relative">
                <span className="absolute inset-0 rounded-md opacity-0 transition-opacity hover:opacity-100 shine" />
                <span className="relative">Add to chat</span>
              </Button>
              <div className="flex items-center gap-2">
                <select
                  value={selectedIssue}
                  onChange={(e) => setSelectedIssue(e.target.value)}
                  className="rounded-md border bg-background/80 px-2 py-2 backdrop-blur-sm"
                >
                  <option value="">Select issue...</option>
                  {issues.map((i, idx) => (
                    <option key={idx} value={i}>
                      {i.length > 80 ? i.slice(0, 80) + "…" : i}
                    </option>
                  ))}
                </select>
                <Button onClick={onGenerate} disabled={!selectedIssue || loading}>
                  {loading ? "Generating..." : "Generate Project"}
                </Button>
              </div>
            </div>
          </div>

          <div ref={listRef} className="mt-6 max-h-[52vh] overflow-auto rounded-2xl border bg-background/70 p-4 backdrop-blur-sm">
            <h3 className="mb-3 text-lg font-medium">Chat</h3>
            <div className="space-y-3">
              {messages.map((m) => (
                <MessageBubble key={m.id} role={m.role} content={m.content} />
              ))}
              {messages.length === 0 && (
                <div className="text-sm text-gray-500">No messages yet. Add a comment and optionally code, then click "Add to chat".</div>
              )}
            </div>
          </div>
        </div>

        <aside className="lg:col-span-2">
          <div className="rounded-2xl border bg-background/70 p-4 backdrop-blur-sm">
            <h3 className="mb-3 text-lg font-medium">Recent Issues</h3>
            <ul className="space-y-2">
              {issues.map((i, idx) => (
                <li key={idx}>
                  <button
                    className={clsx(
                      "w-full rounded-md border px-3 py-2 text-left transition-colors hover:bg-accent",
                      selectedIssue === i && "border-primary"
                    )}
                    onClick={() => setSelectedIssue(i)}
                  >
                    {i.length > 100 ? i.slice(0, 100) + "…" : i}
                  </button>
                </li>
              ))}
              {issues.length === 0 && (
                <li className="text-sm text-gray-500">Generated from assistant messages. Add to chat first.</li>
              )}
            </ul>
          </div>
          <div className="mt-6 rounded-2xl border bg-background/70 p-4 backdrop-blur-sm">
            <a href="/projects" className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-primary-foreground hover:opacity-90">View Projects</a>
          </div>
        </aside>
      </section>
    </div>
  );
}


