// src/lib/types.ts

/**
 * Defines the structure of an Opcode entity based on the backend API response.
 */
export interface Opcode {
  id: string;
  name: string;
  prompt_template: string;
  avg_execution_time?: number; // Optional, as it can be null
  category: "data_processing" | "decision" | "code" | "system" | "simulation" | "architecture" | "custom";
  confidence_threshold?: number; // Optional
  execution_count?: number; // Optional
  input_schema?: { [key: string]: any }; // JSON object, can be complex
  output_schema?: { [key: string]: any }; // JSON object, can be complex
  simulation_enabled?: boolean; // Optional
  success_rate?: number; // Optional
  temperature?: number; // Optional
  // Additional fields from the database response
  created_date?: string; // Stored as datetime in Python, typically serialized as string
  updated_date?: string;
  created_by_id?: string;
  created_by?: string;
  is_sample?: boolean;
}