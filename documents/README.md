# ChatterFix Documentation Index

**AI Team: START HERE for all project information**

This folder contains all project documentation. Before making any changes, review the relevant documents below.

---

## Quick Reference

| Document | Purpose |
|----------|---------|
| [CODE_ARCHITECTURE_REVIEW.md](./CODE_ARCHITECTURE_REVIEW.md) | Complete codebase review with A- grade (90/100) |
| [REVIEW_ACTION_ITEMS.md](./REVIEW_ACTION_ITEMS.md) | Priority tasks from code review |
| [CHATTERFIX_COMPLETE_DOCUMENTATION.md](./CHATTERFIX_COMPLETE_DOCUMENTATION.md) | Full system documentation |
| [production-launch-checklist.md](./production-launch-checklist.md) | Pre-deployment checklist |

---

## Documentation Categories

### Architecture & Code Review
- **CODE_ARCHITECTURE_REVIEW.md** - Comprehensive code review (A- grade)
- **REVIEW_ACTION_ITEMS.md** - Prioritized action items from review
- **REVIEW_EXECUTIVE_SUMMARY.md** - High-level summary for stakeholders
- **DEPENDENCY_ANALYSIS_REPORT.md** - Dependency audit and security

### AI Team & Intelligence
- **AI_TEAM_COLLABORATION_GUIDE.md** - How the AI team works together
- **AI_TEAM_COORDINATION.md** - Coordination protocols
- **AI_TEAM_PROTOCOLS.md** - Detailed team protocols
- **AI_TEAM_WORKFLOW.md** - Workflow documentation
- **AUTONOMOUS_AI_SYSTEM_DOCUMENTATION.md** - Autonomous AI capabilities
- **AUTONOMOUS_AI_SYSTEM_SUMMARY.md** - AI system summary
- **AUTONOMOUS_DEMO.md** - Demo mode documentation

### Deployment & Operations
- **DEPLOYMENT.md** - Deployment procedures
- **DEPLOYMENT-OPTIMIZATION.md** - Performance optimizations
- **production-launch-checklist.md** - Pre-launch checklist
- **cloud-scheduler-setup.md** - Cloud Scheduler configuration
- **MONITORING.md** - Monitoring and alerting setup

### Security
- **FIREBASE_SECURITY_AUDIT.md** - Firebase security review
- **FIRESTORE_SECURITY_REPORT.md** - Firestore rules audit

### Features & Modules
- **CHATTERFIX_COMPLETE_DOCUMENTATION.md** - Complete feature documentation
- **IOT_ADVANCED_MODULE.md** - IoT module documentation
- **LINESMART_INTELLIGENCE_README.md** - LineSmart training integration
- **pm-automation-schema.md** - PM Automation database schema
- **VOICE_AI_ROADMAP.md** - Voice/AI feature roadmap

### Development
- **UI_STYLE_GUIDE.md** - Frontend styling guidelines
- **COMPREHENSIVE_IMPLEMENTATION_PLAN.md** - Implementation planning
- **MIGRATION_GUIDE.md** - Migration procedures
- **COMPONENT_SHOWCASE.html** - UI component examples

---

## Priority Reading Order (New AI Team Members)

1. **CLAUDE.md** (root) - Core instructions and learned lessons
2. **CODE_ARCHITECTURE_REVIEW.md** - Understand current state
3. **REVIEW_ACTION_ITEMS.md** - Know what needs work
4. **CHATTERFIX_COMPLETE_DOCUMENTATION.md** - Full system understanding
5. **AI_TEAM_PROTOCOLS.md** - How we work

---

## Key Lessons Learned

See `/CLAUDE.md` for the complete list of lessons, but critical ones include:

1. **Cookie Auth for HTML pages** - Use `get_current_user_from_cookie()`, not OAuth2
2. **Fetch credentials** - Always use `credentials: 'include'` for auth endpoints
3. **SECRET_KEY** - Must be set, no fallbacks in any environment
4. **Security Headers** - All responses include HSTS, CSP, X-Frame-Options
5. **Firebase Config** - All fields required in web/mobile

---

## Document Maintenance

- Update documents when features change
- Add new lessons to CLAUDE.md
- Keep action items current in REVIEW_ACTION_ITEMS.md
- Tag completed items in CODE_ARCHITECTURE_REVIEW.md

---

*Last Updated: December 2024*
