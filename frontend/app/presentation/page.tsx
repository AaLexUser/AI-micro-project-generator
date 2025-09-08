"use client";

import { MessageBubble } from "../../components/chat/MessageBubble";
import { Button } from "../../components/ui/button";
import { Textarea } from "../../components/ui/textarea";

export default function PresentationPage() {
  const sampleCode = `// Example component
function sum(a: number, b: number) {
  return a + b // missing semicolon + no input validation
}
`;

  const sampleComment = `Consider adding input validation and fixing lint issues.
Also, handle edge cases for non-numeric inputs.`;

  const sampleDescription = `Refactor the utility function to include input validation and
proper TypeScript types. Ensure linter passes.`;

  const sampleGoal = `Implement a robust sum function with type checks and tests.`;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <h2 className="text-xl font-semibold tracking-tight">Presentation: Workspace • Chat • Project</h2>
        <a href="/" className="text-xs text-muted-foreground hover:text-foreground">Back to Home</a>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Workspace Panel */}
        <section className="glass ring-gradient rounded-2xl p-5">
          <h3 className="mb-3 text-lg font-medium">Workspace</h3>
          <div>
            <h4 className="mb-2 text-sm font-medium text-muted-foreground">Code (preview)</h4>
            <Textarea
              value={sampleCode}
              readOnly
              className="h-44 w-full resize-none font-mono text-sm"
            />
          </div>
          <div className="mt-4">
            <h4 className="mb-2 text-sm font-medium text-muted-foreground">Review comment / Issue</h4>
            <Textarea
              value={sampleComment}
              readOnly
              className="h-28 w-full resize-none"
            />
          </div>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <Button disabled className="relative">
              <span className="absolute inset-0 rounded-md opacity-0 transition-opacity hover:opacity-100 shine" />
              <span className="relative">Add to chat</span>
            </Button>
            <Button disabled>Generate Project</Button>
          </div>
        </section>

        {/* Chat Panel */}
        <section className="rounded-2xl border bg-background/70 p-5 backdrop-blur-sm">
          <h3 className="mb-3 text-lg font-medium">Chat</h3>
          <div className="space-y-3">
            <MessageBubble role="user" content={"Issue: function lacks validation and semicolon.\n\nCode snippet provided above."} />
            <MessageBubble role="assistant" content={"Detected issue: Missing validation and lint problems. Suggest adding type checks and tests."} />
            <MessageBubble role="assistant" content={"Ready to generate a micro‑project with clear tasks and an expert solution."} />
          </div>
        </section>

        {/* Project Panel */}
        <section className="rounded-2xl border bg-background/70 p-5 backdrop-blur-sm">
          <h3 className="mb-2 text-lg font-medium">Project</h3>
          <p className="text-sm text-muted-foreground">Created {new Date().toLocaleString()}</p>
          <div className="mt-4 grid grid-cols-1 gap-4">
            <div>
              <h4 className="mb-1 text-sm font-medium text-muted-foreground">Description</h4>
              <p className="whitespace-pre-wrap text-sm">{sampleDescription}</p>
            </div>
            <div>
              <h4 className="mb-1 text-sm font-medium text-muted-foreground">Goal</h4>
              <p className="whitespace-pre-wrap text-sm">{sampleGoal}</p>
            </div>
          </div>

          <div className="mt-5">
            <h4 className="mb-2 text-sm font-medium">Your Solution (preview)</h4>
            <Textarea readOnly className="h-40 w-full resize-none font-mono text-sm" placeholder="Your solution would appear here in the real flow." />
            <div className="mt-3">
              <Button disabled>Submit Solution</Button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}





