// src/frontend/services/TruthApiClient.ts
import { 
  BackendTruthLedgerEntryDTO, 
  ProposeTruthRequestDTO, 
  ChallengeTruthRequestDTO, 
  ResolveTruthRequestDTO,
  AddRelationshipRequestDTO
} from '../interfaces/truth-dtos';

const API_BASE_URL = 'http://localhost:3000/api/truths'; // Assumes backend runs on port 3000

// Helper function to get token
const getToken = (): string | null => {
  return localStorage.getItem('jwtToken');
};

const getHeaders = (): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

export const TruthApiClient = {
  getTruths: async (): Promise<BackendTruthLedgerEntryDTO[]> => {
    const response = await fetch(API_BASE_URL);
    if (!response.ok) {
      throw new Error(`Failed to fetch truths: ${response.statusText}`);
    }
    return response.json();
  },

  getTruthById: async (id: string): Promise<BackendTruthLedgerEntryDTO | null> => {
    const response = await fetch(`${API_BASE_URL}/${id}`);
    if (response.status === 404) {
      return null;
    }
    if (!response.ok) {
      throw new Error(`Failed to fetch truth by ID ${id}: ${response.statusText}`);
    }
    return response.json();
  },

  proposeTruth: async (truthData: ProposeTruthRequestDTO): Promise<BackendTruthLedgerEntryDTO> => {
    const response = await fetch(API_BASE_URL, {
      method: 'POST',
      headers: getHeaders(), // Use authenticated headers
      body: JSON.stringify(truthData),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Failed to propose truth: ${errorData.message || response.statusText}`);
    }
    return response.json();
  },

  challengeTruth: async (truthId: string, challengeData: ChallengeTruthRequestDTO): Promise<BackendTruthLedgerEntryDTO> => {
    const response = await fetch(`${API_BASE_URL}/${truthId}/challenge`, {
      method: 'POST',
      headers: getHeaders(), // Use authenticated headers
      body: JSON.stringify(challengeData),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Failed to challenge truth: ${errorData.message || response.statusText}`);
    }
    return response.json();
  },

  resolveTruth: async (truthId: string, resolutionData: ResolveTruthRequestDTO): Promise<BackendTruthLedgerEntryDTO> => {
    const response = await fetch(`${API_BASE_URL}/${truthId}/resolve`, {
      method: 'POST',
      headers: getHeaders(), // Use authenticated headers
      body: JSON.stringify(resolutionData),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Failed to resolve truth: ${errorData.message || response.statusText}`);
    }
    return response.json();
  },

  addRelationship: async (sourceTruthId: string, relationshipData: AddRelationshipRequestDTO): Promise<BackendTruthLedgerEntryDTO> => {
    const response = await fetch(`${API_BASE_URL}/${sourceTruthId}/relationships`, {
      method: 'POST',
      headers: getHeaders(), // Use authenticated headers
      body: JSON.stringify(relationshipData),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Failed to add relationship: ${errorData.message || response.statusText}`);
    }
    return response.json();
  },

  verifyTruthIntegrity: async (truthId: string): Promise<{ message: string; valid: boolean }> => {
    const response = await fetch(`${API_BASE_URL}/${truthId}/verify-integrity`);
    // Note: Backend returns 400 for invalid integrity, 200 for valid.
    if (response.status === 400) {
      const errorData = await response.json();
      return { message: errorData.message || 'Integrity check failed.', valid: false };
    }
    if (!response.ok) {
      throw new Error(`Failed to verify truth integrity: ${response.statusText}`);
    }
    return response.json();
  },
};