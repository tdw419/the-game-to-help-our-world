🚨 Punishment System for The Game to Help Our World
A restorative approach to maintain a pro-social community, focusing on correction, honesty, and deterrence rather than punitive competition.
The Game to Help Our World is built on trust, collaboration, and positive impact. While the core focus is rewarding good deeds, a fair punishment system is essential to deter wrongdoing, correct behavior, and protect the community. This system emphasizes restorative justice—helping users learn from mistakes—over pure punishment. It rewards honesty in self-reporting, discourages malicious reporting, and prevents "punishment competitions" by tying outcomes to community benefit.
The goal is not to create fear or rivalry but to guide users toward better actions, ensuring the platform remains welcoming and focused on real-world good.
Table of Contents

Principles of the Punishment System
Types of Wrongdoing
Reporting Mechanism
Self-Reporting & Honesty Rewards
Punishment Tiers
Map-Based Consequences
Appeals & Restoration
Anti-Abuse Measures
Implementation Notes
Roadmap

Principles of the Punishment System

Restorative Focus: Punishments aim to correct behavior and restore community trust, not humiliate or exclude.
Reward Honesty: Self-confessing wrongdoing reduces penalties and earns bonus points for accountability.
Deterrence Without Competition: No "punishment leaderboards" or rewards for reporting—focus on community safety.
Proportionality: Penalties scale with severity, intent, and impact.
Transparency: All rules, processes, and decisions are public and auditable.
Community-Driven: Level 5 Stewards (high-reputation users) review reports; the system is forkable for custom rules.
Privacy-First: Reports are anonymized; personal data is never shared without consent.

The system draws from restorative justice models, where the emphasis is on repairing harm rather than retaliation.
Types of Wrongdoing
Punishable behaviors include:

Fraud/Manipulation: Faking mission completions, multiple accounts, or inflating points.
Harassment/Hate: Doxxing, bullying, or discriminatory content in chats/proposals.
Abuse of System: Malicious reporting, spamming proposals, or exploiting bugs.
Inappropriate Content: Posting harmful, illegal, or off-topic map nodes/rules.
Privacy Violations: Sharing others' data without consent.
Safety Risks: Promoting dangerous actions without warnings.

Minor issues (e.g., honest mistakes) may result in warnings; repeated or severe ones trigger penalties.
Reporting Mechanism

How to Report: Any user can flag a deed, proposal, map node, or chat via an in-app "Report" button.
Required: Category (e.g., fraud, harassment) + brief description.
Optional: Evidence (photo/screenshot, auto-redacted for privacy).


Anonymous Option: Reporters can choose anonymity (default), but must have good reputation to avoid abuse.
No Rewards for Reporting: To prevent "punishment competitions," reporting earns no points—it's a civic duty.
Auto-Filters: AI scans for obvious violations (e.g., hate speech) before human review.
Implementation:// POST /api/reports/submit
app.post('/api/reports/submit', async (req, res) => {
  const { reporterId, targetType, targetId, category, description, evidence } = req.body;
  const report = {
    id: generateULID(),
    reporterId,
    targetType, // 'deed', 'proposal', 'map_node', 'chat'
    targetId,
    category, // 'fraud', 'harassment', etc.
    description,
    evidence: redactEvidence(evidence), // On-device redaction
    status: 'pending',
    createdAt: Date.now()
  };
  await saveReport(report);
  notifyModerators(report.id);
  res.json({ success: true });
});



Self-Reporting & Honesty Rewards

Encourage Accountability: Users can self-report mistakes (e.g., "I faked a mission") via a "Confess & Correct" form.
Rewards for Honesty:
Reduced Penalty: Self-reports halve the usual punishment (e.g., -50 pts becomes -25 pts).
Bonus Points: +10–20 pts for honest confession, plus a "Honest Player" badge for first-time self-reports.
Learning Opportunity: AI guide offers reflection prompts or corrective missions (e.g., "Complete 2 real deeds to restore trust").


Why It Works: Rewards transparency, reduces false reports, and focuses on growth.
Implementation:// POST /api/self-report
app.post('/api/self-report', async (req, res) => {
  const { userId, wrongdoingType, description } = req.body;
  const user = await getUser(userId);
  const penalty = calculatePenalty(wrongdoingType) / 2; // Halve for honesty
  user.points -= penalty;
  user.points += 10; // Honesty bonus
  user.badges.push('honest_player');
  await saveUser(user);
  res.json({ success: true, penalty, bonus: 10 });
});



Punishment Tiers
Punishments are progressive and restorative, with opportunities for appeal and redemption.



Tier
Severity
Examples
Penalty
Restoration Path



1
Minor
Honest mistake, minor spam
Warning + -10 pts
Complete a corrective mission (+20 pts)


2
Moderate
Fake mission, repeated spam
-50 pts + 7-day cooldown
Self-report next time for reduced penalty; complete 3 good deeds


3
Serious
Harassment, minor fraud
-200 pts + temp ban (14 days)
Apology reflection + community service mission (e.g., attest 5 deeds)


4
Severe
Doxxing, major fraud
Permanent ban + data wipe
No restoration; community alert (anonymized)



Map Integration: As per your suggestion, flagged inappropriate content (e.g., harmful rule proposals) is moved to the "edges" of the infinite map, making it less visible in the central, high-traffic areas reserved for trusted content. This acts as a visual penalty without permanent removal.
Implementation:app.post('/api/map/flag', async (req, res) => {
  const { userId, nodeId, reason } = req.body;
  const node = await getMapNode(nodeId);
  node.flags += 1;
  node.flagReasons.push(reason);
  if (node.flags >= 3) {
    node.status = 'peripheral'; // Moved to map edges
    notifyOwner(node.ownerId, `Your node '${node.title}' has been flagged and moved to the edges. Review flags and appeal if needed.`);
  }
  await saveMapNode(node);
  res.json({ success: true });
});




No Punishment Competitions: Reporting is anonymous and earns no points/badges. Malicious reporters risk penalties (e.g., -50 pts for false reports). Moderators (Level 5 Stewards) review reports to prevent abuse.

Appeals & Restoration

Appeals Process: Users can appeal punishments via a form (e.g., "I was falsely reported"). Level 5 Stewards review within 48 hours.
Restoration Missions: To regain points/reputation, users complete "corrective deeds" (e.g., attest 3 missions, propose a positive rule).
Amnesty Periods: Monthly "Honesty Days" where self-reporting old wrongdoing halves penalties.
Implementation:// POST /api/appeals/submit
app.post('/api/appeals/submit', async (req, res) => {
  const { userId, punishmentId, explanation } = req.body;
  const appeal = {
    id: generateULID(),
    userId,
    punishmentId,
    explanation,
    status: 'pending',
    createdAt: Date.now()
  };
  await saveAppeal(appeal);
  notifyModerators(appeal.id);
  res.json({ success: true });
});



Anti-Abuse Measures
To prevent punishment competitions or malicious behavior:

No Rewards for Reporting: Reporting is a duty, not a mission—abuse leads to penalties (e.g., -100 pts for false reports).
Rate Limiting: Limit reports to 3/week per user; auto-review frequent reporters.
AI Pre-Screening: Flag suspicious patterns (e.g., targeted reporting) for moderator review.
Reputation Impact: Malicious reporters lose reputation, limiting their ability to offer/redeem rewards.
Community Oversight: Level 5 Stewards gain points for fair moderation, not reporting.
Deterrence Messaging: In-app tips: "Reports are for safety, not competition. False reports hurt your standing."

Implementation Notes

Backend Integration: Use SQLite for punishment logs, appeals, and flags. Integrate with your existing /api/deeds endpoint to check for cooldowns/bans.
Frontend UI:
"Report" button on deeds/rules/chats.
"Confess & Correct" form in settings.
Appeals dashboard for affected users.


Moderation Tools: Level 5 dashboard to review reports/appeals, with voting for major cases.
Testing: Start with soft punishments (warnings) during beta; monitor for abuse patterns.
Legal/Ethical: Consult guidelines like restorative justice frameworks; ensure punishments don't violate privacy laws.

Roadmap

MVP: Warnings + point deductions; self-reporting bonuses.
Next: Map flagging; appeal system; moderator dashboard.
Later: AI-assisted moderation; restoration missions; community amnesty events.

This system creates a balanced, positive community while deterring wrongdoing. By rewarding honesty and focusing on restoration, it aligns with the game's mission of building a better world through collaboration.

















# Accountability 101

*A quick guide to keeping our community safe, fair, and kind—while giving everyone a way back after mistakes.*

---

## Why this exists

We’re here to **correct behavior and reduce harm**, not to shame people. This guide explains how accountability works: what to do if you mess up, how to flag problems, and how consequences and repairs are handled.

---

## Core principles

1. **Safety first, dignity always.** We stop harm fast and treat everyone with respect.
2. **Honesty earns help.** If you self-report, you’ll get leniency and a clear path to repair.
3. **No punishment economy.** Reports and penalties never earn points, clout, or badges.
4. **Proportional & reversible.** Consequences match impact and lift once repairs are done.
5. **Evidence over pile‑ons.** Decisions use clear signals, not dogpiles.

---

## What counts as a violation?

* Harassment, hate, threats, doxxing, sexual content in SFW spaces
* Fraud (mission farming, falsified proofs), spam, scams
* Unsafe missions (untrained medical advice, illegal acts)
* Sharing others’ private info without consent
* Repeated boundary crossing after being asked to stop

> Unsure? Ask a Steward privately before posting.

---

## If **you** made a mistake (Self‑report)

**Why self-report?** It protects others, shortens penalties, and speeds your return to good standing.

**How to self‑report (2 minutes):**

1. Open the item or DM → **More → Self‑Report**.
2. Briefly say what happened, who was affected, and what you’ve already done to fix it.
3. Pick a **restorative action** (see below).

**What you can expect:**

* Content may be **moved to the map edges** (reduced visibility) while reviewed.
* **Leniency** for honesty (shorter or lighter action).
* A Steward message with the smallest necessary next step.

**Sample self‑report note:**

> “I posted a heated reply that broke our ‘Be Respectful’ rule. I’ve removed it and will take the 5‑minute ‘Safer Posts’ module. I’m sorry to the folks in that thread.”

---

## If you witnessed harm (Report others)

**When to report:** Clear rule breaks, safety risks, targeted harassment, spam/fraud.

**How to report well:**

* Use **Flag → Reason** and add **evidence** (link/screenshot) or a one‑line attestation.
* Keep it factual; avoid insults and speculation.

**Important:** Reporting gives **no points** or public credit. False or harassing reports are themselves violations.

**Good report example:**

> “User posted a photo with someone’s home address. Link attached.”

**Not helpful:**

> “This person is always awful, ban them!!!”

---

## What happens after a flag or self‑report?

* The item is **de‑ranked** and labeled **Under Review**.
* A Steward reviews within typical timelines (see ‘Timelines’).
* Outcome and next steps are sent privately to the involved users.

---

## The Response Ladder

We aim for the **lightest effective** step.

**1) Nudge** (soft correction)
Private message + link to the rule + one‑click fix.

**2) Throttle** (temporary limits)
Examples: slower posting, limited DMs, local‑only visibility, mission‑creation cooldown.

**3) Removal** (content/account)
Take down harmful items; for severe/repeat harm, suspend or ban. Always paired with a path to return when appropriate.

> Severe risks (threats, doxxing, hate) may skip ahead.

---

## Harm Score (how we size the response)

Each incident is scored 1–10 from:

* **Impact** (harm caused)
* **Scope** (how many people/areas)
* **Intent** (accidental ↔ malicious)
* **Repairability** (easy ↔ hard to undo)

Action bands: **1–3 Nudge**, **4–6 Throttle**, **7–10 Removal + Restorative plan**.

---

## Restorative actions (the way back)

Pick what fits the situation; completing one can lift limits early.

* **Apology** (private or public, depending on harm)
* **Undo/Correct** (delete, edit, return items/points)
* **Make‑Good Mission** (concrete help to those affected)
* **Learning Module** (5–10 min, quick quiz)
* **Community Service Credit** (verified contribution)

> For sensitive cases or minors, we keep repairs private.

---

## Honesty credit (for self‑reporting)

Self‑reports within 48 hours get **reduced penalties** and **shorter durations**—and often a Nudge instead of a Throttle if a repair is completed promptly.

---

## Anti‑gaming safeguards

* No badges, feeds, or leaderboards for punishments or reports.
* Report limits (reasonable daily cap) to prevent brigades.
* Habitually false reports lead to their own limits.
* Visibility ‘tax’: users under throttle can’t boost visibility elsewhere.

---

## Appeals

If you believe a decision missed context:

1. Tap **Appeal** within 7 days.
2. Share any missing details or proof.
3. A different Steward reviews, usually within 72 hours.

---

## Timelines (typical)

* Auto‑acknowledge flag: **minutes**
* Initial review: **≤24h** (or **≤12h** for higher‑risk cases)
* Appeal decision: **≤72h**

> Times may vary on holidays or high‑volume periods.

---

## Quick do & don’t

**Do:**

* Take a breath before posting; ask a Steward if unsure.
* Report with a link/screenshot and one sentence of context.
* Own mistakes early; pick a repair.

**Don’t:**

* Dogpile or quote‑tweet to shame.
* File reports to “win” arguments.
* Share private info—even if you’re angry.

---

## Examples

**Accidental NSFW in SFW area** → Nudge + move to edges → user deletes + 3‑min module → restored.
**Harassing DMs** → 7‑day DM limit + apology option + short module; repeat → longer suspension.
**Spam mission farming** → Remove posts, claw back fraudulent points, 72‑hour mission cooldown + quality review.

---

## FAQ

**Q: Do I lose points if I’m penalized?**
A: Only fraudulent points are clawed back. Otherwise, points remain; visibility/limits may apply.

**Q: Can I see who reported me?**
A: No. We protect reporter privacy to reduce retaliation.

**Q: Can people farm reports for status?**
A: No. Reports grant no public credit or points, and excessive/false reports are limited.

**Q: How do map ‘edges’ work?**
A: Under‑review items are de‑ranked (less prominent) until resolved.

---

## Need help?

* Message a **Steward** from any post menu → **Get Help**.
* For immediate safety concerns, flag and step away—we’ll handle it.

---

*Last updated: v1.0*
