export type SubmissionResult = {
  id: number;
  student_id: string;
  original_filename: string;
  status: string;
  score: number | null;
  feedback_text: string | null;
  preview_path: string | null;
  result_json: {
    comparison?: {
      component_scores?: Record<string, number>;
      errors?: string[];
    };
  } | null;
};

export type Batch = {
  id: number;
  reference_id: number;
  drawing_type: string;
  total_files: number;
  processed_files: number;
  status: string;
  summary_json: Record<string, string | number> | null;
  submissions: SubmissionResult[];
};

const API_BASE = "/api";

export async function uploadReference(formData: FormData) {
  const response = await fetch(`${API_BASE}/upload-reference`, { method: "POST", body: formData });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function uploadStudents(formData: FormData): Promise<Batch> {
  const response = await fetch(`${API_BASE}/upload-students`, { method: "POST", body: formData });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function processBatch(batchId: number) {
  const response = await fetch(`${API_BASE}/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ batch_id: batchId })
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function getResults(): Promise<{ batches: Batch[] }> {
  const response = await fetch(`${API_BASE}/results`);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

