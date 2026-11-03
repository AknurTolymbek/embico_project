import { apiClient } from "./client";
import type {
  BlastocystPrediction,
  MLStatus,
  TimelapsePrediction,
} from "../types/ml";

// Let the browser set multipart/form-data with its generated boundary.
const uploadConfig = (signal: AbortSignal) => ({
  headers: { "Content-Type": undefined },
  signal,
  timeout: 10 * 60 * 1000,
});

export const mlApi = {
  status: async (): Promise<MLStatus> =>
    (await apiClient.get<MLStatus>("/api/v1/ml/status")).data,
  blastocyst: async (
    image: File,
    signal: AbortSignal,
  ): Promise<BlastocystPrediction> => {
    const form = new FormData();
    form.append("image", image);
    return (
      await apiClient.post<BlastocystPrediction>(
        "/api/v1/ml/blastocyst/predict",
        form,
        uploadConfig(signal),
      )
    ).data;
  },
  timelapse: async (
    input: {
      frames: File[];
      hours: number[];
      framesFm: File[];
      framesFp: File[];
    },
    signal: AbortSignal,
  ): Promise<TimelapsePrediction> => {
    const form = new FormData();
    input.frames.forEach((file) => form.append("frames", file));
    form.append("hours", JSON.stringify(input.hours));
    input.framesFm.forEach((file) => form.append("frames_fm", file));
    input.framesFp.forEach((file) => form.append("frames_fp", file));
    return (
      await apiClient.post<TimelapsePrediction>(
        "/api/v1/ml/timelapse/predict",
        form,
        uploadConfig(signal),
      )
    ).data;
  },
};
