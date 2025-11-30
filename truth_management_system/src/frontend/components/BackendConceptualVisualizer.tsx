import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Database, Lock, GitBranch, Shield, CheckCircle, Code } from 'lucide-react';

interface SchemaColumn {
  name: string;
  type: string;
  constraints: string;
}

const truthLedgerSchema: SchemaColumn[] = [
  { name: 'id', type: 'UUID', constraints: 'Primary Key' },
  { name: 'statement', type: 'TEXT', constraints: 'NOT NULL' },
  { name: 'context', type: 'JSONB', constraints: '' },
  { name: 'content_hash', type: 'VARCHAR(64)', constraints: 'UNIQUE, NOT NULL (SHA-256)' },
  { name: 'previous_hash', type: 'VARCHAR(64)', constraints: 'NOT NULL (Chain integrity)' },
  { name: 'confidence_level', type: 'VARCHAR(20)', constraints: 'NOT NULL (PROPOSED, ACCEPTED, etc.)' },
  { name: 'proposed_by', type: 'UUID', constraints: 'Foreign Key to users' },
  { name: 'timestamp', type: 'TIMESTAMPTZ', constraints: 'NOT NULL' },
  { name: 'version', type: 'INTEGER', constraints: 'DEFAULT 1 (Optimistic locking)' },
  { name: 'relationships', type: 'JSONB', constraints: 'Graph relationships' },
  { name: 'created_at', type: 'TIMESTAMPTZ', constraints: 'DEFAULT NOW()' },
  { name: 'updated_at', type: 'TIMESTAMPTZ', constraints: 'DEFAULT NOW()' },
];

const truthRelationshipsSchema: SchemaColumn[] = [
  { name: 'parent_truth_id', type: 'UUID', constraints: 'Foreign Key' },
  { name: 'child_truth_id', type: 'UUID', constraints: 'Foreign Key' },
  { name: 'relationship_type', type: 'VARCHAR(50)', constraints: 'SUPPORTS, CONTRADICTS, etc.' },
  { name: 'strength', type: 'DECIMAL(3,2)', constraints: '0.00 to 1.00' },
];

const cryptographicPatterns: string[] = [
  'Immutable Append-Only Ledger: Once written, truth entries cannot be updated',
  'Hash Chain Validation: Periodic background job verifies entire chain integrity',
  'Content Hash Pre-image: Store original content to allow re-computation',
  'Digital Signatures: Optional enhancement for non-repudiation',
];

const apiMiddlewareChain: string[] = [
  'JWT Validation',
  'Role-Based Authorization',
  'Rate Limiting',
  'Audit Logging',
];

const permissionMatrix: string[] = [
  'PROPOSE_TRUTH: Authenticated users',
  'CHALLENGE_TRUTH: Users with challenge credits',
  'ELEVATE_CONFIDENCE: Trusted validators',
  'READ_TRUTH: Public (with some filters)',
];

export default function BackendConceptualVisualizer() {
  return (
    <Card className="p-6 bg-white dark:bg-gray-800 shadow-lg rounded-lg">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-2xl font-bold text-gray-900 dark:text-gray-50">
          <Code className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          Truth Service Backend Architecture Guide
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-10">
        {/* Database Schema Visualization */}
        <div>
          <h3 className="flex items-center gap-2 text-xl font-semibold mb-4 text-gray-800 dark:text-gray-100">
            <Database className="h-5 w-5 text-green-600 dark:text-green-400" /> Database Schema Design
          </h3>
          <p className="text-muted-foreground mb-6">
            Detailed schema for core truth data and relationships, forming the foundation of immutable record-keeping.
          </p>

          <div className="space-y-8">
            <h4 className="text-lg font-medium flex items-center gap-2 text-gray-700 dark:text-gray-200">
              <Badge variant="secondary" className="bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-200 border-blue-200 dark:border-blue-700">
                <span className="font-mono">truth_ledger</span> Table
              </Badge>
            </h4>
            <Table className="bg-gray-50 dark:bg-gray-900 rounded-md">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[150px] text-gray-600 dark:text-gray-300">Column</TableHead>
                  <TableHead className="w-[100px] text-gray-600 dark:text-gray-300">Type</TableHead>
                  <TableHead className="text-gray-600 dark:text-gray-300">Constraints/Description</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {truthLedgerSchema.map((col, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono font-medium text-gray-900 dark:text-gray-50">{col.name}</TableCell>
                    <TableCell className="font-mono text-gray-700 dark:text-gray-200">{col.type}</TableCell>
                    <TableCell className="text-gray-600 dark:text-gray-300">{col.constraints}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            <Separator className="my-8 bg-gray-200 dark:bg-gray-700" />

            <h4 className="text-lg font-medium flex items-center gap-2 text-gray-700 dark:text-gray-200">
              <Badge variant="secondary" className="bg-purple-50 dark:bg-purple-950 text-purple-700 dark:text-purple-200 border-purple-200 dark:border-purple-700">
                <span className="font-mono">truth_relationships</span> Table
              </Badge>
            </h4>
            <Table className="bg-gray-50 dark:bg-gray-900 rounded-md">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[150px] text-gray-600 dark:text-gray-300">Column</TableHead>
                  <TableHead className="w-[100px] text-gray-600 dark:text-gray-300">Type</TableHead>
                  <TableHead className="text-gray-600 dark:text-gray-300">Constraints/Description</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {truthRelationshipsSchema.map((col, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono font-medium text-gray-900 dark:text-gray-50">{col.name}</TableCell>
                    <TableCell className="font-mono text-gray-700 dark:text-gray-200">{col.type}</TableCell>
                    <TableCell className="text-gray-600 dark:text-gray-300">{col.constraints}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>

        <Separator className="bg-gray-300 dark:bg-gray-600" />

        {/* Hash Chain Concept Demonstration */}
        <div>
          <h3 className="text-xl font-semibold flex items-center gap-2 text-xl font-semibold mb-4 text-gray-800 dark:text-gray-100">
            <GitBranch className="h-5 w-5 text-purple-600 dark:text-purple-400" /> Hash Chain Concept
          </h3>
          <p className="text-muted-foreground mb-6">
            Illustrating cryptographic integrity with <code className="font-mono text-blue-600 dark:text-blue-400">content_hash</code> and <code className="font-mono text-blue-600 dark:text-blue-400">previous_hash</code> for an immutable ledger.
          </p>
          <div className="relative p-8 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-900 dark:to-gray-800 rounded-xl shadow-inner border border-blue-100 dark:border-gray-700 overflow-hidden">
            <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 flex items-center justify-center pointer-events-none">
              <div className="w-1 h-full bg-gradient-to-b from-transparent via-blue-400 to-transparent animate-pulse opacity-70"></div>
            </div>
            <div className="space-y-6 text-center relative z-10">
              <div className="p-4 bg-white dark:bg-gray-700 rounded-lg shadow-md border border-gray-100 dark:border-gray-600">
                <Badge variant="default" className="text-lg px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold mb-2">TRUTH_ENTRY_N-1</Badge>
                <p className="text-sm text-gray-700 dark:text-gray-300 font-mono">Content Hash: <span className="font-bold text-gray-900 dark:text-gray-50">`HASH_A`</span></p>
              </div>

              <div className="flex items-center justify-center text-green-500">
                <CheckCircle className="h-8 w-8" />
                <span className="ml-2 text-lg font-medium text-gray-700 dark:text-gray-300">Links To</span>
              </div>

              <div className="p-4 bg-white dark:bg-gray-700 rounded-lg shadow-md border border-gray-100 dark:border-gray-600">
                <Badge variant="default" className="text-lg px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold mb-2">TRUTH_ENTRY_N</Badge>
                <p className="text-sm text-gray-700 dark:text-gray-300 font-mono">Content Hash: <span className="font-bold text-gray-900 dark:text-gray-50">`HASH_B`</span></p>
                <p className="text-sm text-gray-700 dark:text-gray-300 font-mono">Previous Hash: <span className="font-bold text-gray-900 dark:text-gray-50">`HASH_A`</span></p>
              </div>
              <p className="text-md text-gray-700 dark:text-gray-300 mt-4 italic">
                This mechanism ensures an immutable, verifiable chain, preventing tampering.
              </p>
            </div>
          </div>
        </div>

        <Separator className="bg-gray-300 dark:bg-gray-600" />

        {/* Security Patterns Highlight */}
        <div>
          <h3 className="text-xl font-semibold flex items-center gap-2 text-xl font-semibold mb-4 text-gray-800 dark:text-gray-100">
            <Shield className="h-5 w-5 text-red-600 dark:text-red-400" /> Cryptographic Integrity Patterns
          </h3>
          <ul className="list-disc pl-6 space-y-3 text-muted-foreground text-lg">
            {cryptographicPatterns.map((pattern, index) => (
              <li key={index} className="text-gray-700 dark:text-gray-300">{pattern}</li>
            ))}
          </ul>

          <Separator className="my-8 bg-gray-200 dark:bg-gray-700" />

          <h3 className="text-xl font-semibold flex items-center gap-2 text-xl font-semibold mb-4 text-gray-800 dark:text-gray-100">
            <Lock className="h-5 w-5 text-yellow-600 dark:text-yellow-400" /> API Security Implementation
          </h3>
          <p className="text-muted-foreground mb-6">
            Key middleware and access control for secure and robust API interactions.
          </p>

          <div className="space-y-6">
            <h4 className="text-lg font-medium text-gray-700 dark:text-gray-200">Middleware Chain:</h4>
            <div className="flex flex-wrap items-center gap-3">
              {apiMiddlewareChain.map((item, index) => (
                <React.Fragment key={index}>
                  <Badge variant="outline" className="px-4 py-2 text-sm bg-indigo-50 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-200 border-indigo-200 dark:border-indigo-700 font-medium">
                    {item}
                  </Badge>
                  {index < apiMiddlewareChain.length - 1 && (
                    <span className="text-gray-400 dark:text-gray-500 text-xl font-bold">→</span>
                  )}
                </React.Fragment>
              ))}
            </div>

            <Separator className="my-6 bg-gray-200 dark:bg-gray-700" />

            <h4 className="text-lg font-medium text-gray-700 dark:text-gray-200">Permission Matrix:</h4>
            <ul className="list-disc pl-6 space-y-3 text-muted-foreground text-lg">
              {permissionMatrix.map((permission, index) => (
                <li key={index} className="text-gray-700 dark:text-gray-300">{permission}</li>
              ))}
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}