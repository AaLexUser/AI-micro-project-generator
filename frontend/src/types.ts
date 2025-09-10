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

export type GenerateRequest = {
  comments: string[];
  presets?: string | null;
  config_path?: string | null;
  overrides?: string[] | null;
};

export type FeedbackResponse = {
  feedback: string;
};
