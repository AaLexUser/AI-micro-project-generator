import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Play, Loader2, CheckCircle, FileText, Target, Database, Eye } from 'lucide-react';
import { api } from '../services/api';
import { MarkdownRenderer } from '../components/MarkdownRenderer';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import type { Project } from '../types';

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
  const [projects] = usePersistentState<Project[]>('aipg:projects', []);
  const idx = useMemo(() => Number(params.idx ?? '-1'), [params.idx]);
  const project = projects[idx];

  const [code, setCode] = usePersistentState<string>(`aipg:code:${idx}`, '');
  const [feedback, setFeedback] = usePersistentState<string>(`aipg:feedback:${idx}`, '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    } catch (e: any) {
      setError(e?.message ?? 'Failed to get feedback');
    } finally {
      setLoading(false);
    }
  }

  if (!project) return null;

  return (
    <div className="mx-auto max-w-6xl px-6 py-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" asChild>
          <Link to="/" className="flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Projects
          </Link>
        </Button>
        <Badge variant="outline">
          Project #{idx + 1}
        </Badge>
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
          <Textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="h-80 font-mono text-sm"
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
  );
}
