export interface User {
  id: number;
  email: string;
  full_name?: string;
  role: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  project_type: string;
  default_model: string;
  owner_id: number;
  created_at: string;
  updated_at: string;
  num_datasets: number;
  num_experiments: number;
  num_traces: number;
}

export interface DatasetCase {
  id: number;
  dataset_id: number;
  input_text: string;
  expected_output?: string;
  context?: string;
  metadata_json?: Record<string, any>;
  created_at: string;
}

export interface Dataset {
  id: number;
  project_id: number;
  name: string;
  description?: string;
  version: number;
  num_cases: number;
  file_format: string;
  created_at: string;
  updated_at: string;
}

export interface PromptVersion {
  id: number;
  prompt_id: number;
  version_number: number;
  template_text: string;
  system_instruction?: string;
  variables: string[];
  model_parameters?: Record<string, any>;
  change_summary?: string;
  created_at: string;
}

export interface Prompt {
  id: number;
  project_id: number;
  name: string;
  description?: string;
  current_version: number;
  created_at: string;
  updated_at: string;
  latest_version?: PromptVersion;
}

export interface EvaluationResult {
  id: number;
  test_case_run_id: number;
  metric_name: string;
  score: number;
  passed: boolean;
  reasoning?: string;
  supported_claims?: string[];
  unsupported_claims?: string[];
  evidence?: string;
  latency_ms: number;
  is_human_reviewed: boolean;
  human_override_score?: number;
  human_notes?: string;
  created_at: string;
}

export interface TestCaseRun {
  id: number;
  experiment_run_id: number;
  dataset_case_id?: number;
  input_text: string;
  expected_output?: string;
  context?: string;
  generated_output?: string;
  status: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_estimate: number;
  error_message?: string;
  retry_count: number;
  evaluations: EvaluationResult[];
  created_at: string;
}

export interface ExperimentRun {
  id: number;
  experiment_id: number;
  model_name: string;
  provider_name: string;
  status: string;
  summary_metrics?: {
    avg_correctness?: number;
    avg_faithfulness?: number;
    avg_context_precision?: number;
    avg_context_recall?: number;
    avg_relevance?: number;
    avg_hallucination_score?: number;
    avg_latency_ms?: number;
    total_tokens?: number;
    total_cost?: number;
    success_count?: number;
    fail_count?: number;
  };
  started_at?: string;
  completed_at?: string;
  created_at: string;
  test_case_runs?: TestCaseRun[];
}

export interface Experiment {
  id: number;
  project_id: number;
  name: string;
  description?: string;
  status: string;
  dataset_id?: number;
  prompt_version_id?: number;
  config_json?: {
    models: string[];
    evaluators: string[];
    temperature?: number;
    max_tokens?: number;
    system_instruction?: string;
  };
  total_cases: number;
  processed_cases: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  runs: ExperimentRun[];
}

export interface TraceSpan {
  id: number;
  trace_id: number;
  parent_span_id?: number;
  span_name: string;
  span_type: string;
  start_time: string;
  end_time?: string;
  latency_ms: number;
  input_data?: string;
  output_data?: string;
  status: string;
  error_message?: string;
  attributes_json?: Record<string, any>;
}

export interface Trace {
  id: number;
  project_id: number;
  experiment_id?: number;
  test_case_run_id?: number;
  trace_name: string;
  status: string;
  start_time: string;
  end_time?: string;
  latency_ms: number;
  total_tokens: number;
  total_cost: number;
  metadata_json?: Record<string, any>;
  created_at: string;
  spans: TraceSpan[];
}

export interface DashboardMetrics {
  total_evaluations: number;
  total_test_cases: number;
  avg_correctness: number;
  avg_faithfulness: number;
  avg_latency_ms: number;
  total_tokens: number;
  total_cost: number;
  failed_executions: number;
  success_rate: number;
  score_over_time: Array<{
    timestamp: string;
    date_label: string;
    correctness: number;
    faithfulness: number;
    cost: number;
    latency: number;
    tokens: number;
  }>;
  model_performance: Array<{
    model_name: string;
    correctness: number;
    faithfulness: number;
    latency_ms: number;
    cost: number;
    total_evals: number;
  }>;
  latency_distribution: Array<{
    range_label: string;
    count: number;
  }>;
  token_consumption_over_time: Array<{
    date: string;
    tokens: number;
    experiment: string;
  }>;
  cost_over_time: Array<{
    date: string;
    cost: number;
    experiment: string;
  }>;
  success_vs_failure: {
    success: number;
    failed: number;
  };
  is_empty: boolean;
}

export interface ModelComparisonData {
  experiment_id: number;
  experiment_name: string;
  dataset_name: string;
  models: string[];
  radar_data: Array<Record<string, any>>;
  model_summaries: Array<{
    model_name: string;
    provider_name: string;
    avg_correctness: number;
    avg_faithfulness: number;
    avg_context_precision: number;
    avg_context_recall: number;
    avg_relevance: number;
    avg_hallucination_score: number;
    avg_latency_ms: number;
    total_tokens: number;
    total_cost: number;
    success_rate: number;
    total_runs: number;
    win_rate: number;
  }>;
  side_by_side_cases: Array<{
    case_id: number;
    input: string;
    expected?: string;
    models: Record<string, {
      output?: string;
      latency_ms: number;
      tokens: number;
      cost: number;
      correctness: number;
      status: string;
    }>;
  }>;
}
