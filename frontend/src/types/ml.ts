export interface ModelStatus {
  loaded: boolean;
  weights_found: boolean;
  mode: string | null;
  files: string[];
  missing_files: string[];
}

export interface MLStatus {
  enabled: boolean;
  device: string;
  models_dir: string;
  models_dir_exists: boolean;
  missing_dependencies: string[];
  blastocyst: ModelStatus;
  timelapse: ModelStatus;
}

interface PredictionBase {
  model_version: string;
  task: string;
  status: "ok" | "no_recommendation";
  warnings: string[];
  disclaimer: string;
}

export interface BlastocystPrediction extends PredictionBase {
  expansion_class: number;
  probabilities: { exp: number[]; icm: number[] | null; te: number[] | null };
  icm: "A" | "B" | "C" | null;
  te: "A" | "B" | "C" | null;
  gardner: string;
  confidence: number;
}

export interface TimelapsePrediction extends PredictionBase {
  model: string;
  n_frames: number;
  video_hours: number;
  events_hours: Record<string, number>;
  morphokinetics: Record<string, number | null>;
  last_stage: string;
  flags: string[];
  stage_confidence: number;
  blastocyst_rank_research: number | null;
  blastocyst_rank_meaning: string;
  blastocyst_probability_research: number | null;
}

export type PredictionResult =
  | { kind: "blastocyst"; data: BlastocystPrediction }
  | { kind: "timelapse"; data: TimelapsePrediction };
