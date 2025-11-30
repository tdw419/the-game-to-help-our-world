// src/services/MultiLLMTruthDiscovery.ts
import { truthApiClient } from '@/api/TruthApiClient';
import { BackendTruthLedgerEntryDTO, ProposeTruthRequestDTO } from '@/backend-interfaces/truth-dtos';
import { lmStudioService } from './LMStudioService';

export interface LLMConfidenceSignal {
  model: string;
  confidence: number;
  reasoning: string;
  evidence: string[];
  uncertainty_areas: string[];
  extraction_timestamp: string;
}

export interface MultiLLMTruthAssessment {
  truthId?: string;
  content: string;
  confidence_signals: LLMConfidenceSignal[];
  aggregated_confidence: number;
  consensus_level: 'high' | 'medium' | 'low' | 'conflicting';
  suggested_relationships: string[];
  validation_recommendations: string[];
}

export interface SystematicInterrogationResult {
  topic: string;
  discovered_truths: MultiLLMTruthAssessment[];
  knowledge_gaps: string[];
  confidence_distribution: {
    high_confidence: number;
    medium_confidence: number;
    low_confidence: number;
    conflicting: number;
  };
  extraction_metadata: {
    interrogation_depth: number;
    follow_up_questions: string[];
    boundary_proximity: number;
  };
}

class MultiLLMTruthDiscovery {
  private availableModels = [
    'qwen/qwen2.5-coder-14b',
    'lm-studio-default',
    'confidence-analyzer'
  ];

  async systematicTopicInterrogation(topic: string, depth: number = 3): Promise<SystematicInterrogationResult> {
    const interrogationPlan = this.createInterrogationPlan(topic, depth);
    const discoveredTruths: MultiLLMTruthAssessment[] = [];
    const knowledgeGaps: string[] = [];
    
    for (const question of interrogationPlan.questions) {
      try {
        const assessment = await this.assessTruthWithMultipleModels(question);
        discoveredTruths.push(assessment);
        
        // Identify knowledge gaps from uncertainty signals
        assessment.confidence_signals.forEach(signal => {
          signal.uncertainty_areas.forEach(area => {
            if (!knowledgeGaps.includes(area)) {
              knowledgeGaps.push(area);
            }
          });
        });
      } catch (error) {
        console.error(`Failed to assess question: ${question}`, error);
      }
    }
    
    return {
      topic,
      discovered_truths: discoveredTruths,
      knowledge_gaps: knowledgeGaps,
      confidence_distribution: this.calculateConfidenceDistribution(discoveredTruths),
      extraction_metadata: {
        interrogation_depth: depth,
        follow_up_questions: interrogationPlan.followUps,
        boundary_proximity: this.calculateBoundaryProximity(discoveredTruths)
      }
    };
  }

  async assessTruthWithMultipleModels(content: string): Promise<MultiLLMTruthAssessment> {
    const confidenceSignals: LLMConfidenceSignal[] = [];
    
    // Assess truth with multiple models in parallel
    const assessmentPromises = this.availableModels.map(model => 
      this.getModelConfidenceSignal(model, content)
    );
    
    const results = await Promise.allSettled(assessmentPromises);
    
    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        confidenceSignals.push(result.value);
      } else {
        console.error(`Model ${this.availableModels[index]} assessment failed:`, result.reason);
      }
    });
    
    return {
      content,
      confidence_signals: confidenceSignals,
      aggregated_confidence: this.aggregateConfidence(confidenceSignals),
      consensus_level: this.determineConsensusLevel(confidenceSignals),
      suggested_relationships: this.extractSuggestedRelationships(confidenceSignals),
      validation_recommendations: this.generateValidationRecommendations(confidenceSignals)
    };
  }

  private async getModelConfidenceSignal(model: string, content: string): Promise<LLMConfidenceSignal> {
    // Use LM Studio service for confidence analysis
    const analysis = await lmStudioService.analyzeTruth({
      id: `temp-${Date.now()}`,
      content,
      confidence: 0.5, // Initial placeholder
      status: 'proposed',
      timestamp: new Date().toISOString(),
      relationships: [],
      contentHash: '',
      previousHash: ''
    } as BackendTruthLedgerEntryDTO);

    return {
      model,
      confidence: analysis.analysis.confidence,
      reasoning: analysis.analysis.reasoning,
      evidence: analysis.analysis.supporting_evidence || [],
      uncertainty_areas: analysis.analysis.contradictions || [],
      extraction_timestamp: new Date().toISOString()
    };
  }

  private createInterrogationPlan(topic: string, depth: number): {
    questions: string[];
    followUps: string[];
  } {
    const baseQuestions = [
      `What are the fundamental truths about ${topic}? Provide confidence levels.`,
      `What specific facts about ${topic} are you highly confident about?`,
      `Where are the knowledge boundaries for ${topic}? Show uncertainty.`,
      `What evidence supports your understanding of ${topic}?`,
      `What are common misconceptions about ${topic} and why are they wrong?`
    ];

    const followUps = [
      `How does ${topic} relate to adjacent knowledge domains?`,
      `What recent developments have affected understanding of ${topic}?`,
      `What would change your confidence about ${topic}?`,
      `How does ${topic} connect to fundamental principles?`
    ];

    return {
      questions: baseQuestions.slice(0, depth),
      followUps: depth > 1 ? followUps.slice(0, depth - 1) : []
    };
  }

  private aggregateConfidence(signals: LLMConfidenceSignal[]): number {
    if (signals.length === 0) return 0.5;
    
    const weights = this.calculateModelWeights(signals);
    const weightedSum = signals.reduce((sum, signal, index) => {
      return sum + (signal.confidence * weights[index]);
    }, 0);
    
    return weightedSum / weights.reduce((a, b) => a + b, 0);
  }

  private calculateModelWeights(signals: LLMConfidenceSignal[]): number[] {
    // Weight models based on reasoning quality and evidence provided
    return signals.map(signal => {
      let weight = 1.0;
      
      // Higher weight for signals with detailed reasoning
      if (signal.reasoning.length > 200) weight *= 1.2;
      
      // Higher weight for signals with supporting evidence
      if (signal.evidence.length > 0) weight *= 1.1;
      
      // Lower weight for signals with many uncertainty areas
      if (signal.uncertainty_areas.length > 2) weight *= 0.8;
      
      return weight;
    });
  }

  private determineConsensusLevel(signals: LLMConfidenceSignal[]): 'high' | 'medium' | 'low' | 'conflicting' {
    if (signals.length === 0) return 'low';
    
    const confidences = signals.map(s => s.confidence);
    const avgConfidence = confidences.reduce((a, b) => a + b, 0) / confidences.length;
    const variance = confidences.reduce((sum, conf) => sum + Math.pow(conf - avgConfidence, 2), 0) / confidences.length;
    
    if (variance < 0.05 && avgConfidence > 0.8) return 'high';
    if (variance < 0.1 && avgConfidence > 0.6) return 'medium';
    if (variance > 0.2) return 'conflicting';
    return 'low';
  }

  private extractSuggestedRelationships(signals: LLMConfidenceSignal[]): string[] {
    const relationships = new Set<string>();
    
    signals.forEach(signal => {
      // Extract relationship suggestions from reasoning
      const relationshipPatterns = [
        /related to ([^.,]+)/gi,
        /connected with ([^.,]+)/gi,
        /similar to ([^.,]+)/gi,
        /contrasts with ([^.,]+)/gi
      ];
      
      relationshipPatterns.forEach(pattern => {
        let match;
        while ((match = pattern.exec(signal.reasoning)) !== null) {
          relationships.add(match[1].trim());
        }
      });
    });
    
    return Array.from(relationships);
  }

  private generateValidationRecommendations(signals: LLMConfidenceSignal[]): string[] {
    const recommendations: string[] = [];
    
    if (this.determineConsensusLevel(signals) === 'conflicting') {
      recommendations.push('Multiple models show conflicting confidence levels. Requires human verification.');
    }
    
    const lowConfidenceSignals = signals.filter(s => s.confidence < 0.5);
    if (lowConfidenceSignals.length > 0) {
      recommendations.push('Some models show low confidence. Consider additional evidence gathering.');
    }
    
    const highUncertaintySignals = signals.filter(s => s.uncertainty_areas.length > 1);
    if (highUncertaintySignals.length > 0) {
      recommendations.push('Multiple uncertainty areas identified. Focus interrogation on these topics.');
    }
    
    return recommendations;
  }

  private calculateConfidenceDistribution(assessments: MultiLLMTruthAssessment[]): {
    high_confidence: number;
    medium_confidence: number;
    low_confidence: number;
    conflicting: number;
  } {
    const distribution = {
      high_confidence: 0,
      medium_confidence: 0,
      low_confidence: 0,
      conflicting: 0
    };
    
    assessments.forEach(assessment => {
      switch (assessment.consensus_level) {
        case 'high':
          distribution.high_confidence++;
          break;
        case 'medium':
          distribution.medium_confidence++;
          break;
        case 'low':
          distribution.low_confidence++;
          break;
        case 'conflicting':
          distribution.conflicting++;
          break;
      }
    });
    
    return distribution;
  }

  private calculateBoundaryProximity(assessments: MultiLLMTruthAssessment[]): number {
    if (assessments.length === 0) return 1.0;
    
    const uncertaintyCount = assessments.reduce((count, assessment) => {
      return count + assessment.confidence_signals.reduce((sigCount, signal) => {
        return sigCount + signal.uncertainty_areas.length;
      }, 0);
    }, 0);
    
    const totalSignals = assessments.reduce((count, assessment) => {
      return count + assessment.confidence_signals.length;
    }, 0);
    
    // Normalize to 0-1 scale (higher = closer to knowledge boundary)
    return Math.min(1.0, uncertaintyCount / (totalSignals * 2));
  }

  async proposeDiscoveredTruths(discoveryResult: SystematicInterrogationResult): Promise<ProposeTruthRequestDTO[]> {
    const truthProposals: ProposeTruthRequestDTO[] = [];
    
    for (const assessment of discoveryResult.discovered_truths) {
      if (assessment.aggregated_confidence > 0.7 && assessment.consensus_level !== 'conflicting') {
        truthProposals.push({
          content: assessment.content,
          initialConfidence: assessment.aggregated_confidence, // Use aggregated confidence
          reasoning: `Discovered through multi-LLM interrogation on topic "${discoveryResult.topic}". Aggregated confidence: ${(assessment.aggregated_confidence * 100).toFixed(1)}%. Consensus: ${assessment.consensus_level}.`,
          relationships: assessment.suggested_relationships.map(rel => ({
            targetTruthContent: rel, // Use targetTruthContent as we don't have IDs yet
            relationshipType: 'references'
          }))
        });
      }
    }
    
    return truthProposals;
  }

  private mapRelationshipToTruthId(relationship: string): string {
    // This would need to query existing truths to find matches
    // For now, return a placeholder
    return `relationship-${relationship.toLowerCase().replace(/\s+/g, '-')}`;
  }
}

export const multiLLMTruthDiscovery = new MultiLLMTruthDiscovery();
