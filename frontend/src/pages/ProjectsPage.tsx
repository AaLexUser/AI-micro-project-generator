import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, X, Loader2, Lightbulb, ArrowRight, Sparkles, Trash2, CheckCircle, Play } from 'lucide-react';
import { api } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import type { Project, ProjectStatus } from '../types';

function usePersistentState<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(() => {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : initial;
  });
  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value));
  }, [key, value]);
  return [value, setValue] as const;
}

export function ProjectsPage() {
  const [comments, setComments] = usePersistentState<string[]>(
    'aipg:comments',
    []
  );
  const [commentInput, setCommentInput] = useState('');
  const [projects, setProjects] = usePersistentState<Project[]>(
    'aipg:projects',
    []
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState<number | null>(null);

  const canSubmit = useMemo(
    () => comments.length > 0 && !loading,
    [comments.length, loading]
  );

  async function handleGenerate() {
    try {
      setLoading(true);
      setError(null);
      const result = await api.generateProjects({ comments });
      setProjects(result);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to generate projects');
    } finally {
      setLoading(false);
    }
  }

  function addComment() {
    const trimmed = commentInput.trim();
    if (!trimmed) return;
    setComments([...comments, trimmed]);
    setCommentInput('');
  }

  function handleKeyPress(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      addComment();
    }
  }

  function removeComment(idx: number) {
    setComments(comments.filter((_, i) => i !== idx));
  }


  function handleDeleteProject(projectIndex: number) {
    if (projectIndex >= 0 && projectIndex < projects.length) {
      api.deleteProject(projectIndex);
      // Force a re-read from localStorage by updating the state
      const updatedProjects = JSON.parse(localStorage.getItem('aipg:projects') || '[]');
      setProjects(updatedProjects);
      setDeleteDialogOpen(null);
    }
  }

  function getProjectStatus(projectIndex: number): ProjectStatus {
    return api.getProjectStatus(projectIndex);
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-12 space-y-12">
      {/* Hero Section */}
      <section className="text-center space-y-6">
        <div className="space-y-3">
          <h1 className="text-4xl font-bold text-gray-900">
            Generate <span className="bg-gradient-to-r from-primary to-primary/80 bg-clip-text text-transparent">AI-Powered</span> Learning Projects
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Share your learning goals, interests, and constraints to get personalized micro-projects designed just for you.
          </p>
        </div>
      </section>

      {/* Input Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Lightbulb className="w-5 h-5 text-primary" />
            </div>
            Share Your Ideas
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3">
            <Textarea
              value={commentInput}
              onChange={(e) => setCommentInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Share your learning goals, preferred topics, skill level, time constraints, or specific interests... (Press Enter to add)"
              className="h-20 flex-1 resize-none"
              rows={3}
            />
            <Button
              onClick={addComment}
              disabled={!commentInput.trim()}
              className="h-fit flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add
            </Button>
          </div>

          {comments.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-muted-foreground">Your Requirements ({comments.length})</h3>
              <div className="space-y-2">
                {comments.map((c, idx) => (
                  <Card
                    key={idx}
                    className="group bg-gradient-to-r from-primary/5 to-primary/10 border-primary/20"
                  >
                    <CardContent className="flex items-start gap-3 p-4">
                      <div className="flex-1">
                        <p className="leading-relaxed">{c}</p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeComment(idx)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 h-auto text-red-600 hover:text-red-700 hover:bg-red-100"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          <Separator />

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <Button
              onClick={handleGenerate}
              disabled={!canSubmit}
              className="flex items-center gap-3"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Generating Projects...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Generate Projects
                </>
              )}
            </Button>

            {error && (
              <Card className="border-red-200 bg-red-50">
                <CardContent className="py-2">
                  <p className="text-sm text-red-700">{error}</p>
                </CardContent>
              </Card>
            )}

            {!error && comments.length === 0 && (
              <div className="text-sm text-muted-foreground">
                💡 Add at least one requirement to generate projects
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Projects Section */}
      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold text-gray-900">Generated Projects</h2>
          {projects.length > 0 && (
            <div className="text-sm text-gray-500">
              {projects.length} project{projects.length !== 1 ? 's' : ''} available
            </div>
          )}
        </div>

        {projects.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center space-y-4">
              <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mx-auto">
                <Sparkles className="w-8 h-8 text-muted-foreground" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-medium">No projects yet</h3>
                <p className="text-muted-foreground">Add your requirements above and generate personalized learning projects.</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {projects.map((p, idx) => {
              const status = getProjectStatus(idx);
              const isCompleted = status === 'completed';
              const isInProgress = status === 'in_progress';

              return (
                <Card
                  key={idx}
                  className={`group hover:shadow-lg transform hover:scale-[1.02] transition-all duration-200 animate-slide-up ${
                    isCompleted
                      ? 'border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 shadow-green-100 animate-success-glow'
                      : isInProgress
                        ? 'border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 shadow-blue-100'
                        : ''
                  }`}
                  style={{ animationDelay: `${idx * 100}ms` }}
                >
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex flex-col gap-2">
                      <Badge variant="secondary" className="text-xs w-fit">
                        {p.topic}
                      </Badge>
                      {isCompleted && (
                        <Badge className="bg-green-100 text-green-800 border-green-200 flex items-center gap-1 w-fit">
                          <CheckCircle className="w-3 h-3" />
                          Completed
                        </Badge>
                      )}
                      {isInProgress && (
                        <Badge variant="secondary" className="flex items-center gap-1 w-fit">
                          <Play className="w-3 h-3" />
                          In Progress
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Dialog open={deleteDialogOpen === idx} onOpenChange={(open) => setDeleteDialogOpen(open ? idx : null)}>
                        <DialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="opacity-0 group-hover:opacity-100 transition-opacity p-1 h-auto text-red-600 hover:text-red-700 hover:bg-red-100"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Delete Project</DialogTitle>
                            <DialogDescription>
                              Are you sure you want to delete "{p.goal}"? This action cannot be undone.
                              All your code, feedback, and execution results for this project will be permanently removed.
                            </DialogDescription>
                          </DialogHeader>
                          <DialogFooter>
                            <Button variant="outline" onClick={() => setDeleteDialogOpen(null)}>
                              Cancel
                            </Button>
                            <Button variant="destructive" onClick={() => handleDeleteProject(idx)}>
                              Delete Project
                            </Button>
                          </DialogFooter>
                        </DialogContent>
                      </Dialog>
                      <Link to={`/project/${idx}`} className="block">
                        <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                      </Link>
                    </div>
                  </div>

                  <Link to={`/project/${idx}`} className="block">
                    <div className="space-y-2">
                      <h3 className="text-lg font-semibold line-clamp-2 group-hover:text-primary transition-colors">
                        {p.goal}
                      </h3>
                      <p className="text-muted-foreground text-sm line-clamp-3 leading-relaxed">
                        {p.description}
                      </p>
                      {isCompleted && (
                        <div className="flex items-center gap-2 text-green-600 text-sm font-medium">
                          <CheckCircle className="w-4 h-4" />
                          <span>🎉 Successfully completed!</span>
                        </div>
                      )}
                    </div>

                    <Separator />

                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>Click to view details</span>
                      <span className="group-hover:text-primary transition-colors">→</span>
                    </div>
                  </Link>
                </CardContent>
              </Card>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
