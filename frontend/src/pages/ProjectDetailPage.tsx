import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Play, Loader2, CheckCircle, FileText, Target, Database, Eye, Terminal, AlertCircle, Clock, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { MarkdownRenderer } from '../components/MarkdownRenderer';
import { SuccessCelebration } from '../components/SuccessCelebration';
import { CodeEditor } from '../components/CodeEditor';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import type { Project, ExecutionResult, ProjectStatus } from '../types';

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

export function ProjectDetailPage() {
  const params = useParams<{ idx: string }>();
  const navigate = useNavigate();
  const [projects, setProjects] = usePersistentState<Project[]>('aipg:projects', []);
  const idx = useMemo(() => Number(params.idx ?? '-1'), [params.idx]);
  const project = projects[idx];

  const [code, setCode] = usePersistentState<string>(`aipg:code:${idx}`, '');
  const [codeLanguage, setCodeLanguage] = usePersistentState<string>(`aipg:codeLanguage:${idx}`, 'javascript');
  const [feedback, setFeedback] = usePersistentState<string>(`aipg:feedback:${idx}`, '');
  const [executionResult, setExecutionResult] = usePersistentState<ExecutionResult | null>(`aipg:execution:${idx}`, null);
  const [projectStatus, setProjectStatus] = useState<ProjectStatus>(() => api.getProjectStatus(idx));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [showSuccessCelebration, setShowSuccessCelebration] = useState(false);

  useEffect(() => {
    if (!project) {
      navigate('/');
    }
  }, [project, navigate]);

  async function handleSubmit() {
    if (!project) return;
    try {
      setLoading(true);
      setError(null);
      const res = await api.getFeedback({ project, user_solution: code });
      setFeedback(res.feedback);
      setExecutionResult(res.execution_result || null);

      // Update project status based on execution result
      if (res.execution_result?.exit_code === 0) {
        const newStatus: ProjectStatus = 'completed';
        setProjectStatus(newStatus);
        api.setProjectStatus(idx, newStatus);
        setShowSuccessCelebration(true);
      } else if (code.trim()) {
        const newStatus: ProjectStatus = 'in_progress';
        setProjectStatus(newStatus);
        api.setProjectStatus(idx, newStatus);
      }
    } catch (e: any) {
      setError(e?.message ?? 'Failed to get feedback');
    } finally {
      setLoading(false);
    }
  }

  function handleDeleteProject() {
    if (idx >= 0 && idx < projects.length) {
      api.deleteProject(idx);
      // Force a re-read from localStorage by updating the state
      const updatedProjects = JSON.parse(localStorage.getItem('aipg:projects') || '[]');
      setProjects(updatedProjects);
      setDeleteDialogOpen(false);
      navigate('/');
    }
  }

  if (!project) return null;

  return (
    <>
      <SuccessCelebration
        isVisible={showSuccessCelebration}
        onAnimationComplete={() => setShowSuccessCelebration(false)}
      />
      <div className="mx-auto max-w-6xl px-6 py-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" asChild>
          <Link to="/" className="flex items-center gap-2 text-primary">
            <ArrowLeft className="w-4 h-4" />
            Back to Projects
          </Link>
        </Button>
        <div className="flex items-center gap-3">
          <Badge variant="outline">
            Project #{idx + 1}
          </Badge>
          {projectStatus === 'completed' && (
            <Badge className="bg-green-100 text-green-800 border-green-200 flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              Completed
            </Badge>
          )}
          {projectStatus === 'in_progress' && (
            <Badge variant="secondary" className="flex items-center gap-1">
              <Play className="w-3 h-3" />
              In Progress
            </Badge>
          )}
          <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="destructive" size="sm" className="flex items-center gap-2">
                <Trash2 className="w-4 h-4" />
                Delete
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Delete Project</DialogTitle>
                <DialogDescription>
                  Are you sure you want to delete this project? This action cannot be undone.
                  All your code, feedback, and execution results for this project will be permanently removed.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
                  Cancel
                </Button>
                <Button variant="destructive" onClick={handleDeleteProject}>
                  Delete Project
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Project Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-3 flex-1">
              <Badge variant="secondary" className="w-fit">
                <Target className="w-4 h-4 mr-2" />
                {project.topic}
              </Badge>
              <CardTitle className="text-3xl leading-tight">
                {project.goal}
              </CardTitle>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-start gap-3">
                <div className="p-2 bg-primary rounded-lg">
                  <FileText className="w-5 h-5 text-primary-foreground" />
                </div>
                Project Description
              </CardTitle>
            </CardHeader>
            <CardContent>
              <MarkdownRenderer content={project.description} />
            </CardContent>
          </Card>

        {/* Input/Output Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="w-5 h-5 text-muted-foreground" />
                Input Data
              </CardTitle>
            </CardHeader>
            <CardContent>
              <MarkdownRenderer content={project.input_data} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5 text-muted-foreground" />
                Expected Output
              </CardTitle>
            </CardHeader>
            <CardContent>
              <MarkdownRenderer content={project.expected_output} />
            </CardContent>
          </Card>
          </div>
        </CardContent>
      </Card>

      {/* Solution Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Play className="w-5 h-5 text-green-600" />
            </div>
            Your Solution
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <CodeEditor
            value={code}
            onChange={setCode}
            language={codeLanguage}
            onLanguageChange={setCodeLanguage}
            className="h-80"
            placeholder="Write your solution here...

// Example:
function solve(input) {
    // Your code here
    return result;
}"
          />

          <Separator />

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <Button
              onClick={handleSubmit}
              disabled={loading || !code.trim()}
              className="flex items-center gap-3"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Getting Feedback...
                </>
              ) : (
                <>
                  <CheckCircle className="w-5 h-5" />
                  Submit for Feedback
                </>
              )}
            </Button>

            {error && (
              <Card className="border-red-200 bg-red-50">
                <CardContent className="py-3">
                  <p className="text-sm text-red-700">{error}</p>
                </CardContent>
              </Card>
            )}

            {!error && !code.trim() && (
              <div className="text-sm text-muted-foreground">
                💡 Write your solution above to get AI feedback
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Execution Results Section */}
      {executionResult && (
        <Card className={executionResult.exit_code === 0 ? "border-green-200 bg-gradient-to-r from-green-50 to-emerald-50" : ""}>
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${executionResult.exit_code === 0 ? "bg-green-100" : "bg-purple-100"}`}>
                <Terminal className={`w-5 h-5 ${executionResult.exit_code === 0 ? "text-green-600" : "text-purple-600"}`} />
              </div>
              Execution Results
              <div className="flex items-center gap-2 ml-auto">
                <Badge
                  variant={executionResult.exit_code === 0 ? "default" : "destructive"}
                  className={`flex items-center gap-1 ${executionResult.exit_code === 0 ? "bg-green-100 text-green-800 border-green-200" : ""}`}
                >
                  {executionResult.exit_code === 0 ? (
                    <CheckCircle className="w-3 h-3" />
                  ) : (
                    <AlertCircle className="w-3 h-3" />
                  )}
                  Exit Code: {executionResult.exit_code}
                </Badge>
                {executionResult.timed_out && (
                  <Badge variant="outline" className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Timed Out
                  </Badge>
                )}
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {executionResult.exit_code === 0 && (
              <Card className="border-green-200 bg-gradient-to-r from-green-50 to-emerald-50">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3 text-green-800">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                    <div>
                      <h4 className="font-semibold">🎉 Success! Your solution is working perfectly!</h4>
                      <p className="text-sm text-green-700">All tests passed and your code executed without errors.</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            {executionResult.stdout && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-green-700">Standard Output</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="text-sm bg-green-50 p-4 rounded-lg overflow-x-auto border border-green-200">
                    <code>{executionResult.stdout}</code>
                  </pre>
                </CardContent>
              </Card>
            )}
            {executionResult.stderr && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-red-700">Standard Error</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="text-sm bg-red-50 p-4 rounded-lg overflow-x-auto border border-red-200">
                    <code>{executionResult.stderr}</code>
                  </pre>
                </CardContent>
              </Card>
            )}
            {!executionResult.stdout && !executionResult.stderr && (
              <div className="text-center py-4 text-muted-foreground">
                No output captured
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Feedback Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <CheckCircle className="w-5 h-5 text-blue-600" />
            </div>
            AI Feedback
          </CardTitle>
        </CardHeader>
        <CardContent>
          {feedback ? (
            <Card className="bg-gradient-to-r from-blue-50 to-indigo-50/50 border-blue-200/50">
              <CardContent className="pt-6">
                <MarkdownRenderer content={feedback} />
              </CardContent>
            </Card>
          ) : (
            <div className="text-center py-12 space-y-4">
              <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mx-auto">
                <CheckCircle className="w-8 h-8 text-muted-foreground" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-medium">No feedback yet</h3>
                <p className="text-muted-foreground">Submit your solution above to receive detailed AI feedback and suggestions.</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      </div>
    </>
  );
}
