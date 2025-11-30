import { v4 as uuidv4 } from 'uuid';
import {
  BackendTruthLedgerEntryDTO,
  BackendTruthRelationshipDTO,
  ProposeTruthRequestDTO,
  ChallengeTruthRequestDTO,
  ResolveTruthRequestDTO,
  AddRelationshipRequestDTO
} from '../backend-interfaces/truth-dtos'; // Import DTOs from new backend-interfaces path

const API_BASE_URL = '/api/truths'; // Hypothetical backend API endpoint

// The frontend's TruthLedgerEntry is essentially the BackendTruthLedgerEntryDTO
// when coming from the API, so we can reuse that type here.
export type TruthLedgerEntry = BackendTruthLedgerEntryDTO;
export type TruthRelationship = BackendTruthRelationshipDTO;

// This class acts as the client for a backend Truth API.
// It explicitly implements the expected contract defined in the TRUTH_SERVICE_BACKEND_CONTRACT Opcode.
class TruthApiClient {
  private _truths: TruthLedgerEntry[] = []; // In-memory cache for mock responses
  private latestHash: string = 'genesis'; // To simulate blockchain-like linking

  constructor() {
    this.initializeMockData();
  }

  // --- Helper for Mocking: Simulate backend cryptographic hashing ---
  private async computeHash(content: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(content + 'salt' + new Date().getTime());
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  // --- INTERNAL MOCKING HELPERS (Simulate backend logic locally) ---
  // These simulate the backend logic for manipulating the _truths array and generating IDs/hashes.
  private async _proposeTruthLocally(truthData: ProposeTruthRequestDTO): Promise<TruthLedgerEntry> {
    const contentHash = await this.computeHash(truthData.content);
    const isHighConfidence = truthData.content.toLowerCase().includes('true') || truthData.content.includes('1.0');

    const newEntry: TruthLedgerEntry = {
      id: uuidv4(),
      timestamp: new Date().toISOString(),
      content: truthData.content,
      status: isHighConfidence ? 'accepted' : 'proposed',
      confidence: isHighConfidence ? 1.0 : 0.75,
      notes: isHighConfidence ? "Automatically accepted as high-confidence truth." : "Awaiting verification.",
      contentHash: contentHash,
      previousHash: this.latestHash,
      relationships: truthData.initialRelationships?.map(rel => ({...rel, confidence: 0.8})) || [], // Add dummy confidence for mock
      // Ensure all fields from BackendTruthLedgerEntryDTO are present or undefined
      challengedBy: undefined,
      challengeReason: undefined,
      challengeTimestamp: undefined,
      resolvedBy: undefined,
      resolutionType: undefined,
      resolutionNotes: undefined,
      resolutionTimestamp: undefined,
    };
    this.latestHash = contentHash;
    this._truths.unshift(newEntry);
    return newEntry;
  }

  private async _challengeTruthLocally(truthId: string, challengeData: ChallengeTruthRequestDTO): Promise<TruthLedgerEntry> {
    const truthIndex = this._truths.findIndex(t => t.id === truthId);
    if (truthIndex === -1) throw new Error('Truth not found.');

    const truthToChallenge = { ...this._truths[truthIndex] };
    if (truthToChallenge.confidence === 1.0) {
      throw new Error("Immutable truths (confidence 1.0) cannot be directly challenged. They require a superseding truth with stronger evidence.");
    }
    if (truthToChallenge.status === 'challenged') {
      throw new Error('Truth is already under challenge.');
    }

    truthToChallenge.status = 'challenged';
    truthToChallenge.confidence = 0.5;
    truthToChallenge.challengedBy = challengeData.challengerId;
    truthToChallenge.challengeReason = challengeData.reason;
    truthToChallenge.challengeTimestamp = new Date().toISOString();
    // Clear any previous resolution data if being re-challenged
    truthToChallenge.resolvedBy = undefined;
    truthToChallenge.resolutionType = undefined;
    truthToChallenge.resolutionNotes = undefined;
    truthToChallenge.resolutionTimestamp = undefined;

    this._truths[truthIndex] = truthToChallenge;
    return truthToChallenge;
  }

  private async _resolveTruthLocally(truthId: string, resolutionData: ResolveTruthRequestDTO): Promise<TruthLedgerEntry> {
    const truthIndex = this._truths.findIndex(t => t.id === truthId);
    if (truthIndex === -1) throw new Error('Truth not found.');
    if (this._truths[truthIndex].status !== 'challenged') {
      throw new Error('Only challenged truths can be resolved.');
    }

    const truthToResolve = { ...this._truths[truthIndex] };
    truthToResolve.resolvedBy = resolutionData.resolverId;
    truthToResolve.resolutionType = resolutionData.resolutionType;
    truthToResolve.resolutionNotes = resolutionData.resolutionNotes;
    truthToResolve.resolutionTimestamp = new Date().toISOString();

    if (resolutionData.resolutionType === 're-accepted') {
      truthToResolve.status = 're-accepted';
      truthToResolve.confidence = 0.9;
    } else { // rejected
      truthToResolve.status = 'rejected';
      truthToResolve.confidence = 0.0;
    }

    // Clear challenge info
    truthToResolve.challengedBy = undefined;
    truthToResolve.challengeReason = undefined;
    truthToResolve.challengeTimestamp = undefined;

    this._truths[truthIndex] = truthToResolve;
    return truthToResolve;
  }

  private async _addRelationshipLocally(sourceTruthId: string, relationshipData: AddRelationshipRequestDTO): Promise<TruthLedgerEntry> {
    const sourceIndex = this._truths.findIndex(t => t.id === sourceTruthId);
    const targetTruth = this._truths.find(t => t.id === relationshipData.targetTruthId);

    if (sourceIndex === -1 || !targetTruth) {
      throw new Error('Source or target truth not found.');
    }

    const sourceTruth = { ...this._truths[sourceIndex] };
    const relationship: BackendTruthRelationshipDTO = {
      targetTruthId: relationshipData.targetTruthId,
      relationshipType: relationshipData.relationshipType,
      confidence: relationshipData.confidence,
      notes: relationshipData.notes
    };

    const existingIndex = sourceTruth.relationships.findIndex(
      r => r.targetTruthId === relationship.targetTruthId && r.relationshipType === relationship.relationshipType
    );

    if (existingIndex >= 0) {
      sourceTruth.relationships[existingIndex] = relationship;
    } else {
      sourceTruth.relationships.push(relationship);
    }

    this._truths[sourceIndex] = sourceTruth;
    return sourceTruth;
  }

  // Initializes some mock data for demonstration purposes,
  // simulating data that would come from a backend.
  private async initializeMockData() {
    if (this._truths.length === 0) {
      const coreAxiomsContent = `typescript {
  system_core_axioms: {
    "truth_immutability_principle": true, // Rating: 1.00
    "evidence_based_reasoning_required": true, // Rating: 1.00
    "calibration_scale_universal": true, // Rating: 1.00
  }
}`;
      const protocolValidationContent = `typescript {
  protocol_validation: {
    "immediate_effectiveness": 0.94,
    "clarity_improvement_over_unstructured": 0.88,
    "calibration_accuracy": 0.85,
  }
}`;
      const testHypothesisContent = `typescript {
  test_hypothesis: {
    "analog_os_stable_on_arm": 0.72,
    "gpu_shader_generation_efficient": 0.65,
  }
}`;

      const axiomEntry = await this._proposeTruthLocally({ content: coreAxiomsContent });
      const validationEntry = await this._proposeTruthLocally({ content: protocolValidationContent });
      await this._proposeTruthLocally({
        content: testHypothesisContent,
        initialRelationships: [
          { targetTruthId: validationEntry.id, relationshipType: 'supports', confidence: 0.8, notes: "Early testing supports protocol effectiveness" }
        ]
      });

      const currentValidationEntry = this._truths.find(t => t.id === validationEntry.id);
      if (currentValidationEntry) {
        await this._challengeTruthLocally(
          currentValidationEntry.id,
          { challengerId: "AI_Agent_Beta", reason: "New experimental data suggests lower clarity than initially assessed." }
        );
      }
    }
  }


  // --- PUBLIC API CLIENT METHODS (Simulated as per TRUTH_SERVICE_BACKEND_CONTRACT) ---

  // Corresponds to GET /api/truths?query={query}
  async getTruths(query?: string): Promise<TruthLedgerEntry[]> {
    await new Promise(resolve => setTimeout(resolve, 300));
    // --- REAL API CALL WOULD GO HERE ---
    // try {
    //   const response = await fetch(`${API_BASE_URL}?query=${query || ''}`, {
    //     headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
    //   });
    //   if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    //   const data: BackendTruthLedgerEntryDTO[] = await response.json();
    //   this._truths = data; // Update local cache with fresh data
    //   return data;
    // } catch (error) {
    //   console.error('Failed to fetch truths from API:', error);
    //   throw error;
    // }
    // --- END REAL API CALL ---
    let filteredTruths = [...this._truths];
    if (query) {
      const lowerCaseQuery = query.toLowerCase();
      filteredTruths = filteredTruths.filter(truth =>
        truth.content.toLowerCase().includes(lowerCaseQuery) ||
        truth.notes?.toLowerCase().includes(lowerCaseQuery) ||
        truth.status.toLowerCase().includes(lowerCaseQuery) ||
        truth.id.toLowerCase().includes(lowerCaseQuery) ||
        truth.contentHash.toLowerCase().includes(lowerCaseQuery) ||
        truth.challengeReason?.toLowerCase().includes(lowerCaseQuery) ||
        truth.resolutionNotes?.toLowerCase().includes(lowerCaseQuery)
      );
    }
    return filteredTruths;
  }

  // Corresponds to GET /api/truths/{id}
  async getTruthById(id: string): Promise<TruthLedgerEntry | null> {
    await new Promise(resolve => setTimeout(resolve, 300));
    // --- REAL API CALL WOULD GO HERE ---
    // try {
    //   const response = await fetch(`${API_BASE_URL}/${id}`, {
    //     headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
    //   });
    //   if (response.status === 404) return null;
    //   if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    //   return await response.json() as BackendTruthLedgerEntryDTO;
    // } catch (error) {
    //   console.error(`Failed to fetch truth ${id} from API:`, error);
    //   throw error;
    // }
    // --- END REAL API CALL ---
    return this._truths.find(t => t.id === id) || null;
  }

  // Corresponds to POST /api/truths
  async proposeTruth(truthData: ProposeTruthRequestDTO): Promise<TruthLedgerEntry> {
    await new Promise(resolve => setTimeout(resolve, 500));
    // --- REAL API CALL WOULD GO HERE ---
    // try {
    //   const response = await fetch(API_BASE_URL, {
    //     method: 'POST',
    //     headers: {
    //       'Content-Type': 'application/json',
    //       'Authorization': 'Bearer YOUR_TOKEN'
    //     },
    //     body: JSON.stringify(truthData)
    //   });
    //   if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    //   const newTruth: BackendTruthLedgerEntryDTO = await response.json();
    //   this._truths.unshift(newTruth);
    //   this.latestHash = newTruth.contentHash;
    //   return newTruth;
    // } catch (error) {
    //   console.error('Failed to propose truth to API:', error);
    //   throw error;
    // }
    // --- END REAL API CALL ---
    return this._proposeTruthLocally(truthData);
  }

  // Corresponds to POST /api/truths/{id}/challenge
  async challengeTruth(truthId: string, challengeData: ChallengeTruthRequestDTO): Promise<TruthLedgerEntry> {
    await new Promise(resolve => setTimeout(resolve, 500));
    // --- REAL API CALL WOULD GO HERE ---
    // try {
    //   const response = await fetch(`${API_BASE_URL}/${truthId}/challenge`, {
    //     method: 'POST',
    //     headers: {
    //       'Content-Type': 'application/json',
    //       'Authorization': 'Bearer YOUR_TOKEN'
    //     },
    //     body: JSON.stringify(challengeData)
    //   });
    //   if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    //   const updatedTruth: BackendTruthLedgerEntryDTO = await response.json();
    //   const index = this._truths.findIndex(t => t.id === truthId);
    //   if (index !== -1) this._truths[index] = updatedTruth;
    //   return updatedTruth;
    // } catch (error) {
    //   console.error(`Failed to challenge truth ${truthId} via API:`, error);
    //   throw error;
    // }
    // --- END REAL API CALL ---
    return this._challengeTruthLocally(truthId, challengeData);
  }

  // Corresponds to POST /api/truths/{id}/resolve
  async resolveTruth(truthId: string, resolutionData: ResolveTruthRequestDTO): Promise<TruthLedgerEntry> {
    await new Promise(resolve => setTimeout(resolve, 500));
    // --- REAL API CALL WOULD GO HERE ---
    // try {
    //   const response = await fetch(`${API_BASE_URL}/${truthId}/resolve`, {
    //     method: 'POST',
    //     headers: {
    //       'Content-Type': 'application/json',
    //       'Authorization': 'Bearer YOUR_TOKEN'
    //     },
    //     body: JSON.stringify(resolutionData)
    //   });
    //   if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    //   const updatedTruth: BackendTruthLedgerEntryDTO = await response.json();
    //   const index = this._truths.findIndex(t => t.id === truthId);
    //   if (index !== -1) this._truths[index] = updatedTruth;
    //   return updatedTruth;
    // } catch (error) {
    //   console.error(`Failed to resolve truth ${truthId} via API:`, error);
    //   throw error;
    // }
    // --- END REAL API CALL ---
    return this._resolveTruthLocally(truthId, resolutionData);
  }

  // Corresponds to POST /api/truths/{id}/relationships
  async addRelationship(sourceTruthId: string, relationshipData: AddRelationshipRequestDTO): Promise<TruthLedgerEntry> {
    await new Promise(resolve => setTimeout(resolve, 300));
    // --- REAL API CALL WOULD GO HERE ---
    // try {
    //   const response = await fetch(`${API_BASE_URL}/${sourceTruthId}/relationships`, {
    //     method: 'POST',
    //     headers: {
    //       'Content-Type': 'application/json',
    //       'Authorization': 'Bearer YOUR_TOKEN'
    //     },
    //     body: JSON.stringify(relationshipData)
    //   });
    //   if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    //   const updatedTruth: BackendTruthLedgerEntryDTO = await response.json();
    //   const index = this._truths.findIndex(t => t.id === sourceTruthId);
    //   if (index !== -1) this._truths[index] = updatedTruth;
    //   return updatedTruth;
    // } catch (error) {
    //   console.error(`Failed to add relationship for truth ${sourceTruthId} via API:`, error);
    //   throw error;
    // }
    // --- END REAL API CALL ---
    return this._addRelationshipLocally(sourceTruthId, relationshipData);
  }


  // Corresponds to GET /api/truths/{id}/verify-integrity
  async verifyTruthIntegrity(truthId: string): Promise<boolean> {
    await new Promise(resolve => setTimeout(resolve, 200));
    // --- REAL API CALL WOULD GO HERE ---
    // try {
    //   const response = await fetch(`${API_BASE_URL}/${truthId}/verify-integrity`, {
    //     headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
    //   });
    //   if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    //   const result: { isValid: boolean } = await response.json();
    //   return result.isValid;
    // } catch (error) {
    //   console.error(`Failed to verify truth integrity for ${truthId} via API:`, error);
    //   throw error;
    // }
    // --- END REAL API CALL ---
    const truth = this._truths.find(t => t.id === truthId);
    if (!truth) return false;
    const computedHash = await this.computeHash(truth.content);
    return computedHash.substring(0, 20) === truth.contentHash.substring(0, 20);
  }
}

export const truthApiClient = new TruthApiClient();
