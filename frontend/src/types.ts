export type Project = {
  raw_markdown: string;
  topic: string;
  goal: string;
  description: string;
  input_data: string;
  expected_output: string;
  expert_solution: string;
  autotest: string;
};

export type ProjectStatus = 'in_progress' | 'completed' | 'not_started';

export type GenerateRequest = {
  comments: string[];
  presets?: string | null;
  config_path?: string | null;
  overrides?: string[] | null;
};

export type ExecutionResult = {
  stdout: string;
  stderr: string;
  exit_code: number;
  timed_out: boolean;
};

export type FeedbackResponse = {
  feedback: string;
  execution_result?: ExecutionResult | null;
};
