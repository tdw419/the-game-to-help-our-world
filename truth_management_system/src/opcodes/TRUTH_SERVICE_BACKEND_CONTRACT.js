{
  new_opcode_definition: {
    "name": "TRUTH_SERVICE_BACKEND_CONTRACT",
    "description": "Defines the abstract contract for the backend Truth Service, including data transfer objects (DTOs) and method signatures for all API operations. This serves as the authoritative specification for backend implementation to ensure compatibility with the frontend's TruthApiClient.",
    "context_type": "backend_api_contract",
    "dependencies": ["src/backend-interfaces/truth-dtos.ts", "src/backend-interfaces/truth-service.ts"],
    "spec_version": "1.0.0",
    "data_model_reference": {
      "BackendTruthLedgerEntryDTO": "src/backend-interfaces/truth-dtos.ts",
      "ProposeTruthRequestDTO": "src/backend-interfaces/truth-dtos.ts",
      "ChallengeTruthRequestDTO": "src/backend-interfaces/truth-dtos.ts",
      "ResolveTruthRequestDTO": "src/backend-interfaces/truth-dtos.ts",
      "AddRelationshipRequestDTO": "src/backend-interfaces/truth-dtos.ts"
    },
    "api_methods": {
      "getTruths": {
        "endpoint": "GET /api/truths?query={query}",
        "request": "query?: string",
        "response": "Promise<BackendTruthLedgerEntryDTO[]>"
      },
      "getTruthById": {
        "endpoint": "GET /api/truths/{id}",
        "request": "id: string",
        "response": "Promise<BackendTruthLedgerEntryDTO | null>"
      },
      "proposeTruth": {
        "endpoint": "POST /api/truths",
        "request": "ProposeTruthRequestDTO",
        "response": "Promise<BackendTruthLedgerEntryDTO>"
      },
      "challengeTruth": {
        "endpoint": "POST /api/truths/{id}/challenge",
        "request": "ChallengeTruthRequestDTO",
        "response": "Promise<BackendTruthLedgerEntryDTO>"
      },
      "resolveTruth": {
        "endpoint": "POST /api/truths/{id}/resolve",
        "request": "ResolveTruthRequestDTO",
        "response": "Promise<BackendTruthLedgerEntryDTO>"
      },
      "addRelationship": {
        "endpoint": "POST /api/truths/{id}/relationships",
        "request": "AddRelationshipRequestDTO",
        "response": "Promise<BackendTruthLedgerEntryDTO>"
      },
      "verifyTruthIntegrity": {
        "endpoint": "GET /api/truths/{id}/verify-integrity",
        "request": "id: string",
        "response": "Promise<boolean>"
      }
    }
  }
}