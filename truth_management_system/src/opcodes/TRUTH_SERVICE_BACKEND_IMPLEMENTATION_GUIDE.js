{
  new_opcode_definition: {
    "name": "TRUTH_SERVICE_BACKEND_IMPLEMENTATION_GUIDE",
    "description": "Provides detailed architectural and implementation guidance for the backend Truth Service, covering database schema design, cryptographic integrity patterns, concurrency control strategies, and API security implementation. It aims to bridge TypeScript contracts with backend realities.",
    "context_type": "backend_implementation_guide",
    "dependencies": ["TRUTH_SERVICE_BACKEND_CONTRACT"],
    "spec_version": "1.0.0",
    "guide_content": {
      "database_schema_design": {
        "truth_ledger": {
          "id": "UUID (Primary Key)",
          "statement": "TEXT (NOT NULL)",
          "context": "JSONB",
          "content_hash": "VARCHAR(64) (UNIQUE, NOT NULL) // SHA-256",
          "previous_hash": "VARCHAR(64) (NOT NULL)         // Chain integrity",
          "confidence_level": "VARCHAR(20) (NOT NULL)      // PROPOSED, ACCEPTED, etc.",
          "proposed_by": "UUID (Foreign Key to users)",
          "timestamp": "TIMESTAMPTZ (NOT NULL)",
          "version": "INTEGER (DEFAULT 1)                  // Optimistic locking",
          "relationships": "JSONB                          // Graph relationships",
          "created_at": "TIMESTAMPTZ (DEFAULT NOW())",
          "updated_at": "TIMESTAMPTZ (DEFAULT NOW())"
        },
        "truth_relationships": {
          "parent_truth_id": "UUID (Foreign Key)",
          "child_truth_id": "UUID (Foreign Key)",
          "relationship_type": "VARCHAR(50)                // SUPPORTS, CONTRADICTS, etc.",
          "strength": "DECIMAL(3,2)                        // 0.00 to 1.00"
        }
      },
      "cryptographic_integrity_patterns": [
        "Immutable Append-Only Ledger: Once written, truth entries cannot be updated",
        "Hash Chain Validation: Periodic background job verifies entire chain integrity",
        "Content Hash Pre-image: Store original content to allow re-computation",
        "Digital Signatures: Optional enhancement for non-repudiation"
      ],
      "api_security_implementation": {
        "middleware_chain": [
          "JWT Validation",
          "Role-Based Authorization",
          "Rate Limiting",
          "Audit Logging"
        ],
        "permission_matrix": {
          "PROPOSE_TRUTH": "Authenticated users",
          "CHALLENGE_TRUTH": "Users with challenge credits",
          "ELEVATE_CONFIDENCE": "Trusted validators",
          "READ_TRUTH": "Public (with some filters)"
        }
      }
    }
  }
}