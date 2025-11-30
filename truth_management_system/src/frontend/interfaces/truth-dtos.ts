// src/frontend/interfaces/truth-dtos.ts
// Re-defining DTOs for frontend clarity, assuming these would be in a shared lib or copied
export interface BackendTruthRelationshipDTO {
  targetTruthId: string;
  relationshipType: 'supersedes' | 'contradicts' | 'supports' | 'references';
  confidence: number;
  notes?: string;
}

export interface BackendTruthLedgerEntryDTO {
  id: string;
  timestamp: string;
  content: string;
  status: 'proposed' | 'accepted' | 'rejected' | 'superseded' | 'challenged' | 're-accepted';
  confidence: number;
  notes?: string;
  contentHash: string;
  previousHash: string;
  challengedBy?: string;
  challengeReason?: string;
  challengeTimestamp?: string;
  resolvedBy?: string;
  resolutionType?: 're-accepted' | 'rejected';
  resolutionNotes?: string;
  resolutionTimestamp?: string;
  relationships: BackendTruthRelationshipDTO[];
}

export interface ProposeTruthRequestDTO {
  content: string;
  initialRelationships?: Omit<BackendTruthRelationshipDTO, 'confidence'>[];
}

export interface ChallengeTruthRequestDTO {
  challengerId: string;
  reason: string;
}

export interface ResolveTruthRequestDTO {
  resolverId: string;
  resolutionType: 're-accepted' | 'rejected';
  resolutionNotes: string;
}

export interface AddRelationshipRequestDTO {
  targetTruthId: string;
  relationshipType: BackendTruthRelationshipDTO['relationshipType'];
  confidence: number;
  notes?: string;
}

// Frontend specific types, if needed, can be derived or extended from Backend DTOs
export type TruthLedgerEntry = BackendTruthLedgerEntryDTO; // For simplicity in frontend, directly use Backend DTO
