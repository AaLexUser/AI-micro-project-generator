import "../styles/globals.css";
import type { ReactNode } from "react";
import { Toaster } from "sonner";
import { NewsletterSignup } from "../components/marketing/NewsletterSignup";

export const metadata = {
  title: "AI Micro-Project Generator",
  description: "Generate learning micro-projects from code review issues",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground">
        <Toaster position="top-right" richColors />
        {/* Layered backgrounds */}
        <div className="pointer-events-none fixed inset-0 -z-10 bg-grid" />
        <div className="pointer-events-none fixed inset-0 -z-10 radial-spotlight" />
        <div className="pointer-events-none aurora -z-10" />
        <div className="container py-6 md:py-8">
          <header className="mb-10 rounded-2xl border bg-background/70 px-4 py-4 backdrop-blur-sm ring-gradient">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <a href="/" className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-blue-500 via-indigo-500 to-cyan-400 shadow-lg" />
                <div>
                  <div className="text-lg font-semibold tracking-tight md:text-xl gradient-text">AIPG</div>
                  <div className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">Micro-Project Generator</div>
                </div>
              </a>
              <div className="flex items-center justify-between gap-2 md:gap-4">
                <nav className="flex items-center gap-1 text-sm text-muted-foreground">
                  <a className="rounded-md px-3 py-2 hover:bg-accent hover:text-foreground" href="/">Chat</a>
                  <a className="rounded-md px-3 py-2 hover:bg-accent hover:text-foreground" href="/projects">Projects</a>
                  <a
                    href="https://github.com"
                    target="_blank"
                    className="relative hidden overflow-hidden rounded-md border px-3 py-2 text-xs uppercase tracking-wide text-muted-foreground/80 hover:text-foreground md:block"
                  >
                    <span className="shine absolute inset-0" />
                    <span className="relative">GitHub</span>
                  </a>
                </nav>
                <a
                  href="/projects"
                  className="relative inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-primary-foreground shadow-sm transition-all hover:opacity-95"
                >
                  <span className="absolute inset-0 rounded-md opacity-0 transition-opacity hover:opacity-100 shine" />
                  <span className="relative text-sm font-medium">Launch App</span>
                </a>
              </div>
            </div>
          </header>

          <main className="relative">{children}</main>

          <footer className="mt-14 rounded-2xl border bg-background/70 px-4 py-6 backdrop-blur-sm">
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              <div className="space-y-2">
                <div className="text-sm text-muted-foreground">© {new Date().getFullYear()} AIPG</div>
                <div className="text-xs text-muted-foreground">Built for world‑class learning experiences</div>
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium">Stay in the loop</div>
                <NewsletterSignup />
              </div>
              <div className="flex items-end justify-start gap-4 md:justify-end">
                <a className="text-xs text-muted-foreground hover:text-foreground" href="/">Terms</a>
                <a className="text-xs text-muted-foreground hover:text-foreground" href="/">Privacy</a>
                <a className="text-xs text-muted-foreground hover:text-foreground" href="/">Contact</a>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}


