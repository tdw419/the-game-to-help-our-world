# The Game to Help Our World

**Turn real-world good deeds into points, unlock new abilities, and help design the game itself.**

> *Pick up litter = 1 point. Help a neighbor = 3 points. Organize a cleanup = 10 points.*  
> **But here's the twist: You get to decide what the rules should be.**

A mobile-first, open-source, and hijackable game where players earn points for good deeds, propose new rules through conversation, and collectively build an "infinite map" of positive actions. The player whose rule set is most adopted becomes the MVP.

## What is this?

The Game to Help Our World is a **collaborative protocol** where players:

- **Do good deeds** and earn points through verification
- **Chat with others** to develop and refine game rules  
- **Progress through levels** from Beginner to Steward
- **Shape the future** of how positive actions are rewarded
- **Fork and customize** the entire system for their community

This isn't just a game—it's a **crowdsourced experiment** in building better incentive systems for positive change.

## Core Loop

1. **Learn**: Chat with the AI guide to understand how points work and pick your first mission
2. **Do**: Complete a good deed (solo or with others)
3. **Verify**: Honor system + optional photo or peer attestation  
4. **Propose**: Suggest new rules ("Action X = Y points, verified by Z")
5. **Adopt**: Community tries your rules; most adopted become standard
6. **Improve**: Optional data donation helps train smarter AI guides

## Level Progression

| Level | Name | Unlock | Activity |
|-------|------|---------|----------|
| **1** | **Beginner** | AI Tutorial | Learn rules, earn first 20 points |
| **2** | **Player** | Mentor Chat | Match with experienced players, discuss rules |
| **3** | **Trusted** | Mission Mode | Video chat globally, propose rules, submit map coordinates |
| **4** | **Developer** | GitHub Access | Submit code/rule proposals, shape development |
| **5** | **Steward** | Governance | Vote on proposals, guide game evolution |

## Key Features

### The Infinite Map
Players explore the "borders" of positive action by:
- Submitting coordinates for real-world good deeds
- Proposing verification methods for new actions
- Voting on community rule proposals
- **Goal**: Become MVP by having your "map" most widely adopted

### Hijackable by Design
- **Open source** under Apache 2.0 license
- **Export your data** - take conversations and contributions anywhere
- **Fork-friendly** - detailed setup instructions for your own instance
- **API-first** - integrate with other tools and platforms

### Privacy-First
- **Local storage** by default - conversations stay on your device
- **Opt-in sharing** - choose what helps improve the game
- **Transparent benefits** - see exactly how your data helps others
- **One-click export/delete** - you own your contributions

## Quick Start

### Option 1: Play Now (Zero Install)
Visit our hosted instance and start immediately:
```
https://play.gametohelp.world
```
Add to your phone's home screen for app-like experience.

### Option 2: Self-Hosted
Run your own instance with full control:

```bash
# Clone the repository
git clone https://github.com/your-org/game-to-help-our-world.git
cd game-to-help-our-world

# Install and run
npm install
npm start
```

Visit `http://localhost:3000` to begin.

### Option 3: Docker (Recommended for Communities)
```bash
docker run -p 3000:3000 -v game_data:/app/data \
  ghcr.io/your-org/game-to-help-our-world:latest
```

## Technical Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Mobile PWA    │◄──►│   Node.js API    │◄──►│   SQLite DB     │
│ (Local Storage) │    │   (WebSocket)    │    │ (Rules/Points)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  WebRTC P2P     │    │  AnythingLLM     │    │  Rule Proposals │
│  (Video Chat)   │    │  (AI Guide)      │    │  (Community)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Current Stack:**
- **Frontend**: Progressive Web App (HTML/CSS/JavaScript)
- **Backend**: Node.js + Express + WebSockets  
- **Database**: SQLite with Better-SQLite3
- **Real-time**: WebRTC for peer-to-peer communication
- **AI**: Rule-based system evolving to AnythingLLM integration
- **Storage**: IndexedDB for local conversation history

## Data & Privacy

### What We Collect (With Your Consent)
- **Chat conversations** - help improve AI responses
- **Rule proposals** - expand the game's possibilities  
- **Map submissions** - define new areas for good deeds
- **Usage patterns** - optimize the experience

### How We Use It
- **Train the AI** to give better guidance to new players
- **Develop better rules** based on community discussions
- **Build the infinite map** of possible positive actions
- **Research impact** of gamified social good

### Your Control
- **View everything** you've contributed via your dashboard
- **Export all data** in portable JSONL format
- **Delete your contributions** if you change your mind
- **Fork the project** and take your data with you

### Benefits for Contributing
- **Points**: 10 per unique session, +5 for rule adoption
- **Badges**: Data Pioneer, Map Mentor, Rule Creator
- **Influence**: Voting weight for governance decisions
- **Recognition**: Public acknowledgment for valuable contributions

## Contributing

### As a Player
- **Play the game** - your conversations become valuable training data
- **Propose rules** - suggest new actions and verification methods  
- **Share ideas** - help expand the infinite map
- **Mentor newcomers** - guide others through the progression

### As a Developer
- **Fork the repo** - create your own version for different causes
- **Submit PRs** - improve the core platform
- **Run community instances** - host for specific groups
- **Build integrations** - connect to other positive-impact tools

### Development Setup
```bash
git clone https://github.com/your-org/game-to-help-our-world
cd game-to-help-our-world
npm install

# Create local database
node scripts/init-db.js

# Start development server  
npm run dev
```

## Roadmap

### Phase 1: Foundation (Current)
- ✅ Rule-based AI tutorial system
- ✅ Level progression and points
- ✅ Local conversation storage
- 🔄 Mobile-friendly PWA

### Phase 2: Community Intelligence
- 🔄 AnythingLLM integration for smarter responses
- 📅 Advanced rule proposal and voting system
- 📅 Map visualization and exploration
- 📅 Enhanced gamification and rewards

### Phase 3: Decentralized Network  
- 📅 Peer-to-peer communication via WebRTC
- 📅 Federated instances sharing data
- 📅 Mobile native apps
- 📅 Blockchain integration (optional)

### Phase 4: The Infinite Game
- 📅 Self-governing community protocols
- 📅 Cross-platform ecosystem integration
- 📅 Real-world impact measurement  
- 📅 Global deployment and scaling

## Community

- **Discord**: Join our community discussions
- **GitHub**: Technical discussions and feature requests  
- **Weekly Town Halls**: Community governance meetings
- **Office Hours**: Get help contributing to the project

## FAQ

### How do you prevent cheating?
Trust-based system with optional verification through photos and peer attestation. The community self-moderates through the leveling system and reputation.

### Who owns the game rules?
The community does. Higher-level players vote on proposals, but anyone can fork and try different approaches.

### What makes this different from other social impact apps?
1. **Community-driven rules** - players build the system together
2. **Complete transparency** - open source with exportable data
3. **Progressive governance** - influence grows with contribution  
4. **Conversation-first** - discussion drives gameplay
5. **Infinite scalability** - no central authority controls growth

### Can I really "hijack" this?
Yes! Export your data, fork the code, modify the rules, and launch your own version. We encourage it - that's how good ideas spread.

## License & Forking

Apache License 2.0 - use it, modify it, commercialize it, just keep the mission alive.

See [FORKING.md](docs/FORKING.md) for detailed instructions on creating your own version.

## Get Involved

Ready to help build the future of positive action?

1. **🎮 Play the game** - start earning points for good deeds
2. **💬 Join conversations** - help develop better rules
3. **💻 Contribute code** - improve the platform
4. **🍴 Fork and customize** - create your own version
5. **🌍 Spread the mission** - invite others to participate

---

**Remember**: This game belongs to everyone who helps build it. The best ideas win through adoption, not authority. The map is infinite because we keep expanding it together.

*Pick up litter. Help a neighbor. Change the world.*
