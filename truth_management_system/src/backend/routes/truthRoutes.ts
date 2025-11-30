import { Router } from 'express';
import { truthService } from '../services/truthService';
import { ProposeTruthRequestDTO, ChallengeTruthRequestDTO, ResolveTruthRequestDTO, AddRelationshipRequestDTO } from '../interfaces/truth-dtos';
import { protect } from '../middleware/authMiddleware'; // Import protect middleware

const router = Router();

// GET all truths (publicly accessible)
router.get('/', async (req, res) => {
  try {
    const truths = await truthService.getTruths();
    res.status(200).json(truths);
  } catch (error: any) {
    res.status(500).json({ message: error.message });
  }
});

// GET truth by ID (publicly accessible)
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const truth = await truthService.getTruthById(id);
    if (truth) {
      res.status(200).json(truth);
    } else {
      res.status(404).send('Truth not found.');
    }
  } catch (error: any) {
    res.status(500).json({ message: error.message });
  }
});

// POST propose a new truth (requires authentication)
router.post('/', protect, async (req, res) => {
  try {
    const truthData: ProposeTruthRequestDTO = req.body;
    if (!truthData.content) {
      return res.status(400).send('Content is required to propose a truth.');
    }
    // Access user ID from authenticated request
    const proposedBy = req.user!.id; 
    const newTruth = await truthService.proposeTruth(truthData, proposedBy);
    res.status(201).json(newTruth);
  } catch (error: any) {
    res.status(500).json({ message: error.message });
  }
});

// POST challenge a truth (requires authentication - placeholder for now)
router.post('/:id/challenge', protect, async (req, res) => {
  try {
    const { id } = req.params;
    const challengeData: ChallengeTruthRequestDTO = req.body;
    if (!challengeData.reason) { // challengerId will come from req.user
      return res.status(400).send('Reason is required to challenge a truth.');
    }
    const challengerId = req.user!.id; // Use authenticated user ID
    const updatedTruth = await truthService.challengeTruth(id, { ...challengeData, challengerId });
    res.status(200).json(updatedTruth);
  } catch (error: any) {
    res.status(400).json({ message: error.message });
  }
});

// POST resolve a truth (requires authentication - placeholder for now)
router.post('/:id/resolve', protect, async (req, res) => {
  try {
    const { id } = req.params;
    const resolutionData: ResolveTruthRequestDTO = req.body;
    if (!resolutionData.resolutionType || !resolutionData.resolutionNotes) { // resolverId will come from req.user
      return res.status(400).send('Resolution type and notes are required to resolve a truth.');
    }
    const resolverId = req.user!.id; // Use authenticated user ID
    const updatedTruth = await truthService.resolveTruth(id, { ...resolutionData, resolverId });
    res.status(200).json(updatedTruth);
  } catch (error: any) {
    res.status(400).json({ message: error.message });
  }
});

// POST add a relationship to a truth (requires authentication)
router.post('/:id/relationships', protect, async (req, res) => {
  try {
    const { id } = req.params; // This is sourceTruthId
    const relationshipData: AddRelationshipRequestDTO = req.body;
    if (!relationshipData.targetTruthId || !relationshipData.relationshipType) {
      return res.status(400).send('Target Truth ID and relationship type are required to add a relationship.');
    }
    const updatedTruth = await truthService.addRelationship(id, relationshipData);
    res.status(200).json(updatedTruth);
  } catch (error: any) {
    res.status(400).json({ message: error.message });
  }
});

// GET verify truth integrity (publicly accessible)
router.get('/:id/verify-integrity', async (req, res) => {
  try {
    const { id } = req.params;
    const isIntegrityValid = await truthService.verifyTruthIntegrity(id);
    if (isIntegrityValid) {
      res.status(200).json({ message: `Integrity of truth ID ${id} is valid.`, valid: true });
    } else {
      res.status(400).json({ message: `Integrity of truth ID ${id} is invalid.`, valid: false });
    }
  } catch (error: any) {
    res.status(500).json({ message: error.message });
  }
});

export default router;