// src/backend-interfaces/truth-service.ts

import {
  BackendTruthLedgerEntryDTO,
  ProposeTruthRequestDTO,
  ChallengeTruthRequestDTO,
  ResolveTruthRequestDTO,
  AddRelationshipRequestDTO
} from './truth-dtos';

/**
 * Defines the contract for the Backend Truth Service.
 * Any concrete backend implementation (e.g., in Python, Go, Node.js)
 * MUST adhere to this interface to be compatible with the frontend's TruthApiClient.
 */
export abstract class TruthServiceBackend {

  /**
   * Retrieves a list of truth ledger entries.
   *
   * @param query An optional search string to filter truths by content, status, etc.
   * @returns A promise that resolves to an array of truth ledger entries.
   */
  abstract getTruths(query?: string): Promise<BackendTruthLedgerEntryDTO[]>;

  /**
   * Retrieves a single truth ledger entry by its ID.
   *
   * @param id The unique identifier of the truth.
   * @returns A promise that resolves to the truth ledger entry, or null if not found.
   */
  abstract getTruthById(id: string): Promise<BackendTruthLedgerEntryDTO | null>;

  /**
   * Proposes a new truth to be added to the ledger.
   * The backend is responsible for validating content, computing hash,
   * setting initial status/confidence, and establishing the previousHash link.
   *
   * @param truthData The data for the new truth, primarily its content.
   * @returns A promise that resolves to the newly created truth ledger entry.
   */
  abstract proposeTruth(truthData: ProposeTruthRequestDTO): Promise<BackendTruthLedgerEntryDTO>;

  /**
   * Challenges an existing truth, marking it for review.
   * Only truths with confidence < 1.0 can typically be challenged directly.
   *
   * @param truthId The ID of the truth to challenge.
   * @param challengeData The details of the challenge (challenger ID, reason).
   * @returns A promise that resolves to the updated truth ledger entry.
   * @throws Error if the truth is immutable (confidence 1.0) or already challenged.
   */
  abstract challengeTruth(truthId: string, challengeData: ChallengeTruthRequestDTO): Promise<BackendTruthLedgerEntryDTO>;

  /**
   * Resolves a previously challenged truth.
   *
   * @param truthId The ID of the challenged truth.
   * @param resolutionData The details of the resolution (resolver ID, type, notes).
   * @returns A promise that resolves to the updated truth ledger entry.
   * @throws Error if the truth is not currently challenged.
   */
  abstract resolveTruth(truthId: string, resolutionData: ResolveTruthRequestDTO): Promise<BackendTruthLedgerEntryDTO>;

  /**
   * Adds a directional relationship from a source truth to a target truth.
   *
   * @param sourceTruthId The ID of the truth from which the relationship originates.
   * @param relationshipData The details of the relationship (target ID, type, confidence, notes).
   * @returns A promise that resolves to the updated source truth ledger entry.
   * @throws Error if source or target truth is not found.
   */
  abstract addRelationship(sourceTruthId: string, relationshipData: AddRelationshipRequestDTO): Promise<BackendTruthLedgerEntryDTO>;

  /**
   * Verifies the cryptographic integrity of a specific truth entry.
   * This might involve re-computing the hash or checking against a trusted source.
   *
   * @param truthId The ID of the truth to verify.
   * @returns A promise that resolves to true if integrity is valid, false otherwise.
   */
  abstract verifyTruthIntegrity(truthId: string): Promise<boolean>;

  /**
   * (Optional) Allows a truth with 1.0 confidence to be "superseded" by a new 1.0 truth.
   * This would involve creating a new truth, linking it, and updating the old truth's status.
   * This method would be complex and likely involve multiple steps.
   */
  // abstract supersedeTruth(oldTruthId: string, newTruthContent: string, supersederId: string): Promise<BackendTruthLedgerEntryDTO>;
}
