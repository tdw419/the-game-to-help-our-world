// src/backend/services/truthService.ts
import { 
  BackendTruthLedgerEntryDTO, 
  ProposeTruthRequestDTO, 
  ChallengeTruthRequestDTO, 
  ResolveTruthRequestDTO, 
  AddRelationshipRequestDTO,
  BackendTruthRelationshipDTO
} from '../interfaces/truth-dtos';
import { generateContentHash } from '../utils/hash-util';
import { v4 as uuidv4 } from 'uuid';

// In-memory store for demonstration purposes
const truthLedger: BackendTruthLedgerEntryDTO[] = [];

export const truthService = {
  getTruths: async (): Promise<BackendTruthLedgerEntryDTO[]> => {
    return truthLedger;
  },

  getTruthById: async (id: string): Promise<BackendTruthLedgerEntryDTO | null> => {
    return truthLedger.find(truth => truth.id === id) || null;
  },

  // Modified to accept proposedBy
  proposeTruth: async (truthData: ProposeTruthRequestDTO, proposedBy: string): Promise<BackendTruthLedgerEntryDTO> => {
    const contentHash = generateContentHash(truthData.content);
    const previousHash = truthLedger.length > 0 ? truthLedger[truthLedger.length - 1].contentHash : '0'.repeat(64); // Genesis block hash

    const newTruth: BackendTruthLedgerEntryDTO = {
      id: uuidv4(),
      timestamp: new Date().toISOString(),
      content: truthData.content,
      status: 'proposed',
      confidence: 0.5, // Initial confidence
      notes: undefined,
      contentHash: contentHash,
      previousHash: previousHash,
      proposedBy: proposedBy, // Assign authenticated user ID
      relationships: truthData.initialRelationships ? truthData.initialRelationships.map(rel => ({...rel, confidence: rel.confidence || 0.7})) : [], // Assign default confidence for initial relationships
    };

    truthLedger.push(newTruth);
    return newTruth;
  },

  challengeTruth: async (truthId: string, challengeData: ChallengeTruthRequestDTO): Promise<BackendTruthLedgerEntryDTO> => {
    const truthIndex = truthLedger.findIndex(truth => truth.id === truthId);
    if (truthIndex === -1) {
      throw new Error(`Truth with ID ${truthId} not found.`);
    }

    const truth = truthLedger[truthIndex];

    if (truth.confidence === 1.0) { // Assuming 1.0 confidence means immutable
      throw new Error(`Truth with ID ${truthId} is immutable and cannot be challenged.`);
    }
    
    const updatedTruth: BackendTruthLedgerEntryDTO = {
      ...truth,
      status: 'challenged',
      confidence: Math.max(0.1, truth.confidence - 0.2), // Reduce confidence
      challengedBy: challengeData.challengerId, // This should probably be req.user.id in a protected route
      challengeReason: challengeData.reason,
      challengeTimestamp: new Date().toISOString(),
    };

    truthLedger[truthIndex] = updatedTruth;
    return updatedTruth;
  },

  resolveTruth: async (truthId: string, resolutionData: ResolveTruthRequestDTO): Promise<BackendTruthLedgerEntryDTO> => {
    const truthIndex = truthLedger.findIndex(truth => truth.id === truthId);
    if (truthIndex === -1) {
      throw new Error(`Truth with ID ${truthId} not found.`);
    }

    const truth = truthLedger[truthIndex];

    if (truth.status !== 'challenged') {
      throw new Error(`Truth with ID ${truthId} is not in 'challenged' status and cannot be resolved.`);
    }

    const newStatus = resolutionData.resolutionType === 're-accepted' ? 'accepted' : 'rejected';
    const newConfidence = resolutionData.resolutionType === 're-accepted' ? 0.8 : 0.2; // Adjust confidence based on resolution

    const updatedTruth: BackendTruthLedgerEntryDTO = {
      ...truth,
      status: newStatus,
      confidence: newConfidence,
      resolvedBy: resolutionData.resolverId, // This should probably be req.user.id in a protected route
      resolutionType: resolutionData.resolutionType,
      resolutionNotes: resolutionData.resolutionNotes,
      resolutionTimestamp: new Date().toISOString(),
      // Clear challenge-related fields
      challengedBy: undefined,
      challengeReason: undefined,
      challengeTimestamp: undefined,
    };

    truthLedger[truthIndex] = updatedTruth;
    return updatedTruth;
  },

  addRelationship: async (sourceTruthId: string, relationshipData: AddRelationshipRequestDTO): Promise<BackendTruthLedgerEntryDTO> => {
    const sourceTruthIndex = truthLedger.findIndex(truth => truth.id === sourceTruthId);
    if (sourceTruthIndex === -1) {
      throw new Error(`Source truth with ID ${sourceTruthId} not found.`);
    }

    const targetTruthExists = truthLedger.some(truth => truth.id === relationshipData.targetTruthId);
    if (!targetTruthExists) {
      throw new Error(`Target truth with ID ${relationshipData.targetTruthId} not found.`);
    }

    const sourceTruth = truthLedger[sourceTruthIndex];

    const newRelationship: BackendTruthRelationshipDTO = {
      ...relationshipData,
      confidence: relationshipData.confidence || 0.7 // Default confidence if not provided
    };

    const updatedTruth: BackendTruthLedgerEntryDTO = {
      ...sourceTruth,
      relationships: [...sourceTruth.relationships, newRelationship],
    };

    truthLedger[sourceTruthIndex] = updatedTruth;
    return updatedTruth;
  },

  verifyTruthIntegrity: async (truthId: string): Promise<boolean> => {
    const truthIndex = truthLedger.findIndex(truth => truth.id === truthId);
    if (truthIndex === -1) {
      return false; // Truth not found
    }

    const truth = truthLedger[truthIndex];

    // 1. Re-compute content hash and compare
    const recomputedHash = generateContentHash(truth.content);
    if (recomputedHash !== truth.contentHash) {
      console.warn(`Content hash mismatch for truth ID ${truthId}. Stored: ${truth.contentHash}, Recomputed: ${recomputedHash}`);
      return false;
    }

    // 2. Verify previousHash link in the chain (if not genesis block)
    if (truth.previousHash !== '0'.repeat(64)) {
      const previousTruth = truthLedger.find(t => t.contentHash === truth.previousHash);
      if (!previousTruth) {
        console.warn(`Previous truth not found for truth ID ${truthId}. Previous hash: ${truth.previousHash}`);
        return false; // Broken chain link
      }
    }

    return true; // Integrity verified
  }
};