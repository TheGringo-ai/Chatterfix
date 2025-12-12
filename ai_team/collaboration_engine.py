"""
Advanced Collaboration Engine for AI Team
Implements sophisticated collaboration patterns including devil's advocate mode,
consensus building, specialized teams, and cross-agent learning
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class CollaborationMode(Enum):
    """Different collaboration modes"""
    PARALLEL = "parallel"  # All agents work simultaneously
    SEQUENTIAL = "sequential"  # Agents work in sequence
    DEVILS_ADVOCATE = "devils_advocate"  # One agent challenges others
    CONSENSUS_BUILDING = "consensus_building"  # Focus on agreement
    SPECIALIZED_TEAMS = "specialized_teams"  # Domain-specific teams
    PEER_REVIEW = "peer_review"  # Agents review each other's work
    BRAINSTORMING = "brainstorming"  # Creative ideation mode
    CRITICAL_ANALYSIS = "critical_analysis"  # Deep analysis mode


class AgentRole(Enum):
    """Specialized roles for collaboration"""
    LEAD = "lead"
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    CHALLENGER = "challenger"  # Devil's advocate
    SYNTHESIZER = "synthesizer"
    VALIDATOR = "validator"
    INNOVATOR = "innovator"


@dataclass
class CollaborationContext:
    """Context for collaboration session"""
    mode: CollaborationMode
    domain: str
    complexity_level: str
    time_constraints: Optional[int] = None
    quality_requirements: float = 0.7
    creativity_emphasis: float = 0.5
    consensus_threshold: float = 0.8
    allow_disagreement: bool = True


@dataclass
class AgentContribution:
    """An agent's contribution to collaboration"""
    agent_name: str
    role: AgentRole
    content: str
    confidence: float
    timestamp: datetime
    response_time: float
    quality_score: float = 0.0
    innovation_score: float = 0.0
    agreement_level: float = 0.0  # Agreement with other agents


@dataclass
class CollaborationRound:
    """A round of collaboration"""
    round_number: int
    prompt: str
    contributions: List[AgentContribution]
    consensus_level: float
    quality_metrics: Dict[str, float]
    insights_generated: List[str]
    conflicts_identified: List[str]


@dataclass
class CollaborationResult:
    """Final result of collaboration session"""
    session_id: str
    mode: CollaborationMode
    rounds: List[CollaborationRound]
    final_output: str
    consensus_achieved: bool
    quality_score: float
    innovation_score: float
    total_time: float
    agent_performances: Dict[str, Dict[str, float]]
    lessons_learned: List[str]
    improvement_suggestions: List[str]


class ConsensusEngine:
    """Engine for building consensus among agents"""

    def __init__(self):
        self.agreement_threshold = 0.8
        self.max_iterations = 5

    async def build_consensus(self, contributions: List[AgentContribution],
                            target_consensus: float = 0.8) -> Tuple[str, float, List[str]]:
        """Build consensus from agent contributions"""
        try:
            # Analyze agreement levels
            consensus_analysis = await self._analyze_consensus(contributions)
            
            if consensus_analysis["consensus_level"] >= target_consensus:
                # Strong consensus - synthesize directly
                synthesis = await self._synthesize_consensus(contributions, consensus_analysis)
                return synthesis, consensus_analysis["consensus_level"], []
            
            else:
                # Need to work toward consensus
                conflicts = consensus_analysis["conflicts"]
                resolution_strategies = await self._generate_resolution_strategies(conflicts, contributions)
                
                # Create compromise solution
                compromise = await self._create_compromise_solution(contributions, resolution_strategies)
                new_consensus_level = await self._estimate_consensus_level(compromise, contributions)
                
                return compromise, new_consensus_level, resolution_strategies
                
        except Exception as e:
            logger.error(f"Error building consensus: {e}")
            # Fallback to simple synthesis
            return await self._simple_synthesis(contributions), 0.5, []

    async def _analyze_consensus(self, contributions: List[AgentContribution]) -> Dict[str, Any]:
        """Analyze consensus level among contributions"""
        if len(contributions) < 2:
            return {"consensus_level": 1.0, "conflicts": [], "agreements": []}
        
        # Simple consensus analysis based on content similarity
        agreements = []
        conflicts = []
        total_similarity = 0.0
        comparisons = 0
        
        for i in range(len(contributions)):
            for j in range(i + 1, len(contributions)):
                similarity = await self._calculate_content_similarity(
                    contributions[i].content, contributions[j].content
                )
                total_similarity += similarity
                comparisons += 1
                
                if similarity > 0.7:
                    agreements.append({
                        "agents": [contributions[i].agent_name, contributions[j].agent_name],
                        "similarity": similarity,
                        "topic": self._extract_common_topic(contributions[i].content, contributions[j].content)
                    })
                elif similarity < 0.3:
                    conflicts.append({
                        "agents": [contributions[i].agent_name, contributions[j].agent_name],
                        "similarity": similarity,
                        "disagreement": self._identify_disagreement(contributions[i].content, contributions[j].content)
                    })
        
        consensus_level = total_similarity / max(comparisons, 1)
        
        return {
            "consensus_level": consensus_level,
            "conflicts": conflicts,
            "agreements": agreements,
            "average_similarity": consensus_level
        }

    async def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two pieces of content"""
        # Simple word-based similarity (can be enhanced with embeddings)
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return 0.0
        
        jaccard_similarity = len(intersection) / len(union)
        
        # Boost similarity for key agreement phrases
        agreement_phrases = [
            "i agree", "exactly", "correct", "yes", "same approach", "similar idea"
        ]
        disagreement_phrases = [
            "i disagree", "however", "but", "on the contrary", "different approach"
        ]
        
        content1_lower = content1.lower()
        content2_lower = content2.lower()
        
        agreement_boost = sum(
            0.1 for phrase in agreement_phrases 
            if phrase in content1_lower and phrase in content2_lower
        )
        
        disagreement_penalty = sum(
            0.1 for phrase in disagreement_phrases 
            if phrase in content1_lower or phrase in content2_lower
        )
        
        final_similarity = min(1.0, max(0.0, jaccard_similarity + agreement_boost - disagreement_penalty))
        return final_similarity

    def _extract_common_topic(self, content1: str, content2: str) -> str:
        """Extract common topic from two contents"""
        # Simple approach - find common important words
        import re
        
        # Extract key terms (longer words, technical terms)
        pattern = r'\b[A-Za-z]{4,}\b'
        words1 = set(re.findall(pattern, content1.lower()))
        words2 = set(re.findall(pattern, content2.lower()))
        
        common_words = words1 & words2
        
        # Filter out common stop words
        stop_words = {'this', 'that', 'with', 'from', 'they', 'have', 'been', 'will', 'would', 'could', 'should'}
        common_words = common_words - stop_words
        
        return ", ".join(sorted(list(common_words))[:3])  # Top 3 common topics

    def _identify_disagreement(self, content1: str, content2: str) -> str:
        """Identify the source of disagreement between two contents"""
        # Look for contradictory statements
        contradiction_patterns = [
            (r'\b(yes|true|correct|right)\b', r'\b(no|false|incorrect|wrong)\b'),
            (r'\b(good|better|best)\b', r'\b(bad|worse|worst)\b'),
            (r'\b(should|must|need)\b', r'\b(should not|must not|don\'t need)\b'),
        ]
        
        content1_lower = content1.lower()
        content2_lower = content2.lower()
        
        for positive_pattern, negative_pattern in contradiction_patterns:
            if (re.search(positive_pattern, content1_lower) and re.search(negative_pattern, content2_lower)) or \
               (re.search(negative_pattern, content1_lower) and re.search(positive_pattern, content2_lower)):
                return "Contradictory evaluations detected"
        
        # Look for different approaches
        if "approach" in content1_lower and "approach" in content2_lower:
            return "Different approaches suggested"
        
        return "Unclear disagreement source"

    async def _synthesize_consensus(self, contributions: List[AgentContribution], 
                                  consensus_analysis: Dict) -> str:
        """Synthesize a consensus solution from contributions"""
        agreements = consensus_analysis.get("agreements", [])
        
        # Extract key points from agreements
        key_points = []
        for agreement in agreements:
            key_points.append(agreement.get("topic", ""))
        
        # Combine all contributions with emphasis on agreed points
        synthesis_parts = []
        synthesis_parts.append("CONSENSUS SOLUTION:")
        
        # Add agreed-upon points
        if key_points:
            unique_points = list(set(filter(None, key_points)))
            if unique_points:
                synthesis_parts.append(f"Key agreed points: {', '.join(unique_points)}")
        
        # Add synthesized content from all agents
        all_content = " ".join(contrib.content for contrib in contributions)
        synthesis_parts.append(f"\nIntegrated approach: {all_content[:500]}...")
        
        return "\n".join(synthesis_parts)

    async def _generate_resolution_strategies(self, conflicts: List[Dict], 
                                            contributions: List[AgentContribution]) -> List[str]:
        """Generate strategies to resolve conflicts"""
        strategies = []
        
        if not conflicts:
            return ["No conflicts to resolve"]
        
        for conflict in conflicts:
            disagreement = conflict.get("disagreement", "Unknown disagreement")
            agents = conflict.get("agents", [])
            
            if "Contradictory evaluations" in disagreement:
                strategies.append(f"Seek middle ground between {' and '.join(agents)} evaluations")
            elif "Different approaches" in disagreement:
                strategies.append(f"Combine approaches from {' and '.join(agents)}")
            else:
                strategies.append(f"Further discussion needed between {' and '.join(agents)}")
        
        return strategies

    async def _create_compromise_solution(self, contributions: List[AgentContribution], 
                                        strategies: List[str]) -> str:
        """Create a compromise solution"""
        compromise_parts = []
        compromise_parts.append("COMPROMISE SOLUTION:")
        compromise_parts.append("(Balancing different perspectives)")
        
        # Include elements from all contributions
        for contrib in contributions:
            # Take first meaningful sentence
            sentences = contrib.content.split('. ')
            if sentences:
                compromise_parts.append(f"- From {contrib.agent_name}: {sentences[0]}")
        
        # Add resolution strategies
        if strategies:
            compromise_parts.append("\nResolution approach:")
            for strategy in strategies:
                compromise_parts.append(f"- {strategy}")
        
        return "\n".join(compromise_parts)

    async def _estimate_consensus_level(self, compromise: str, contributions: List[AgentContribution]) -> float:
        """Estimate consensus level for compromise solution"""
        # Simple estimation based on content inclusion
        compromise_words = set(compromise.lower().split())
        
        total_overlap = 0.0
        for contrib in contributions:
            contrib_words = set(contrib.content.lower().split())
            overlap = len(compromise_words & contrib_words) / max(len(contrib_words), 1)
            total_overlap += overlap
        
        return total_overlap / len(contributions)

    async def _simple_synthesis(self, contributions: List[AgentContribution]) -> str:
        """Simple fallback synthesis"""
        if not contributions:
            return "No contributions to synthesize"
        
        # Just concatenate all contributions
        synthesis = "SYNTHESIZED RESPONSE:\n"
        for i, contrib in enumerate(contributions):
            synthesis += f"\n{i+1}. {contrib.agent_name}: {contrib.content[:200]}...\n"
        
        return synthesis


class DevilsAdvocateEngine:
    """Engine for running devil's advocate mode"""

    def __init__(self):
        self.challenge_strategies = [
            "What are the potential flaws in this approach?",
            "What assumptions are we making that might be wrong?",
            "How could this solution fail in edge cases?",
            "What are the downsides or risks we haven't considered?",
            "Is there a completely different approach we should consider?",
            "What would critics of this solution say?",
            "How does this handle scalability/performance concerns?",
            "What security vulnerabilities might exist?"
        ]

    async def generate_challenges(self, original_contributions: List[AgentContribution],
                                main_solution: str) -> List[str]:
        """Generate challenges for devil's advocate mode"""
        try:
            challenges = []
            
            # Identify key claims in the solution
            key_claims = await self._extract_key_claims(main_solution)
            
            # Generate specific challenges
            for claim in key_claims:
                challenge = await self._generate_challenge_for_claim(claim)
                if challenge:
                    challenges.append(challenge)
            
            # Add general strategic challenges
            challenges.extend(self.challenge_strategies[:3])
            
            return challenges
            
        except Exception as e:
            logger.error(f"Error generating challenges: {e}")
            return self.challenge_strategies[:3]

    async def _extract_key_claims(self, solution: str) -> List[str]:
        """Extract key claims from solution for targeted challenges"""
        # Simple extraction - look for confident statements
        import re
        
        sentences = solution.split('. ')
        key_claims = []
        
        confidence_indicators = ['should', 'will', 'must', 'best', 'always', 'never', 'only']
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in confidence_indicators):
                key_claims.append(sentence)
        
        return key_claims[:3]  # Top 3 claims

    async def _generate_challenge_for_claim(self, claim: str) -> Optional[str]:
        """Generate a specific challenge for a claim"""
        claim_lower = claim.lower()
        
        if 'best' in claim_lower or 'optimal' in claim_lower:
            return f"Challenge: How do we know this is truly the best solution? What alternatives were considered? Claim: '{claim}'"
        
        elif 'always' in claim_lower or 'never' in claim_lower:
            return f"Challenge: Are there edge cases where this wouldn't hold true? Claim: '{claim}'"
        
        elif 'should' in claim_lower or 'must' in claim_lower:
            return f"Challenge: What are the trade-offs of this requirement? Could there be valid exceptions? Claim: '{claim}'"
        
        else:
            return f"Challenge: What evidence supports this assertion? Claim: '{claim}'"


class SpecializedTeamOrganizer:
    """Organizes agents into specialized teams based on domain and task type"""

    def __init__(self):
        self.team_configurations = {
            "coding_team": {
                "lead": "chatgpt-coder",
                "specialists": ["grok-coder", "claude-analyst"],
                "domain": "software_development",
                "capabilities": ["coding", "debugging", "architecture"]
            },
            "analysis_team": {
                "lead": "claude-analyst",
                "specialists": ["grok-reasoner", "gemini-creative"],
                "domain": "analysis_research",
                "capabilities": ["analysis", "reasoning", "research"]
            },
            "creative_team": {
                "lead": "gemini-creative",
                "specialists": ["claude-analyst", "chatgpt-coder"],
                "domain": "creative_design",
                "capabilities": ["creativity", "design", "innovation"]
            },
            "architecture_team": {
                "lead": "claude-analyst",
                "specialists": ["chatgpt-coder", "grok-reasoner"],
                "domain": "system_architecture",
                "capabilities": ["architecture", "planning", "system-design"]
            }
        }

    async def organize_team(self, task_type: str, available_agents: List[str],
                          domain: str = "general") -> Dict[str, List[str]]:
        """Organize agents into specialized team"""
        try:
            # Determine best team configuration
            team_config = await self._select_team_config(task_type, domain)
            
            # Assign roles
            team_organization = {
                "lead": [],
                "specialists": [],
                "reviewers": []
            }
            
            # Assign lead
            preferred_lead = team_config.get("lead")
            if preferred_lead and preferred_lead in available_agents:
                team_organization["lead"].append(preferred_lead)
                remaining_agents = [a for a in available_agents if a != preferred_lead]
            else:
                # Pick first available as lead
                team_organization["lead"].append(available_agents[0])
                remaining_agents = available_agents[1:]
            
            # Assign specialists
            preferred_specialists = team_config.get("specialists", [])
            for specialist in preferred_specialists:
                if specialist in remaining_agents:
                    team_organization["specialists"].append(specialist)
                    remaining_agents.remove(specialist)
            
            # Remaining agents become reviewers
            team_organization["reviewers"] = remaining_agents
            
            logger.info(f"🎯 Organized {task_type} team: Lead={team_organization['lead']}, "
                       f"Specialists={team_organization['specialists']}, "
                       f"Reviewers={team_organization['reviewers']}")
            
            return team_organization
            
        except Exception as e:
            logger.error(f"Error organizing team: {e}")
            # Fallback to simple organization
            return {
                "lead": available_agents[:1],
                "specialists": available_agents[1:3],
                "reviewers": available_agents[3:]
            }

    async def _select_team_config(self, task_type: str, domain: str) -> Dict:
        """Select best team configuration for task"""
        # Match task type to team configuration
        if "cod" in task_type.lower() or "implement" in task_type.lower():
            return self.team_configurations["coding_team"]
        
        elif "analy" in task_type.lower() or "research" in task_type.lower():
            return self.team_configurations["analysis_team"]
        
        elif "creativ" in task_type.lower() or "design" in task_type.lower():
            return self.team_configurations["creative_team"]
        
        elif "architect" in task_type.lower() or "system" in task_type.lower():
            return self.team_configurations["architecture_team"]
        
        else:
            # Default to analysis team
            return self.team_configurations["analysis_team"]


class AdvancedCollaborationEngine:
    """Main collaboration engine coordinating all collaboration modes"""

    def __init__(self):
        self.consensus_engine = ConsensusEngine()
        self.devils_advocate = DevilsAdvocateEngine()
        self.team_organizer = SpecializedTeamOrganizer()
        self.collaboration_history = []

    async def execute_collaboration(self, prompt: str, context: str, available_agents: List[str],
                                  collaboration_context: CollaborationContext) -> CollaborationResult:
        """Execute advanced collaboration session"""
        try:
            session_id = f"collab_{int(time.time())}"
            start_time = time.time()
            
            logger.info(f"🤝 Starting {collaboration_context.mode.value} collaboration: {session_id}")
            
            # Organize team based on mode
            if collaboration_context.mode == CollaborationMode.SPECIALIZED_TEAMS:
                team_organization = await self.team_organizer.organize_team(
                    prompt, available_agents, collaboration_context.domain
                )
            else:
                team_organization = {"lead": available_agents[:1], "specialists": available_agents[1:]}
            
            # Execute collaboration rounds
            rounds = []
            current_prompt = prompt
            
            if collaboration_context.mode == CollaborationMode.DEVILS_ADVOCATE:
                rounds = await self._execute_devils_advocate_mode(
                    current_prompt, context, available_agents, collaboration_context
                )
            
            elif collaboration_context.mode == CollaborationMode.CONSENSUS_BUILDING:
                rounds = await self._execute_consensus_building(
                    current_prompt, context, available_agents, collaboration_context
                )
            
            elif collaboration_context.mode == CollaborationMode.PEER_REVIEW:
                rounds = await self._execute_peer_review(
                    current_prompt, context, available_agents, collaboration_context
                )
            
            elif collaboration_context.mode == CollaborationMode.BRAINSTORMING:
                rounds = await self._execute_brainstorming(
                    current_prompt, context, available_agents, collaboration_context
                )
            
            else:
                # Default parallel mode
                rounds = await self._execute_parallel_mode(
                    current_prompt, context, available_agents, collaboration_context
                )
            
            # Generate final output
            final_output = await self._synthesize_final_output(rounds, collaboration_context)
            
            # Calculate metrics
            total_time = time.time() - start_time
            quality_score = self._calculate_quality_score(rounds)
            innovation_score = self._calculate_innovation_score(rounds)
            consensus_achieved = self._check_consensus_achievement(rounds, collaboration_context)
            
            # Generate insights and lessons
            lessons_learned = await self._extract_lessons_learned(rounds)
            improvement_suggestions = await self._generate_improvement_suggestions(rounds)
            
            # Calculate agent performances
            agent_performances = self._calculate_agent_performances(rounds)
            
            result = CollaborationResult(
                session_id=session_id,
                mode=collaboration_context.mode,
                rounds=rounds,
                final_output=final_output,
                consensus_achieved=consensus_achieved,
                quality_score=quality_score,
                innovation_score=innovation_score,
                total_time=total_time,
                agent_performances=agent_performances,
                lessons_learned=lessons_learned,
                improvement_suggestions=improvement_suggestions
            )
            
            # Store in history
            self.collaboration_history.append(result)
            
            logger.info(f"✅ Collaboration completed: {session_id} "
                       f"(Quality: {quality_score:.2f}, Innovation: {innovation_score:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in collaboration execution: {e}")
            # Return minimal result
            return CollaborationResult(
                session_id=session_id,
                mode=collaboration_context.mode,
                rounds=[],
                final_output=f"Collaboration failed: {str(e)}",
                consensus_achieved=False,
                quality_score=0.0,
                innovation_score=0.0,
                total_time=time.time() - start_time,
                agent_performances={},
                lessons_learned=[],
                improvement_suggestions=[]
            )

    async def _execute_devils_advocate_mode(self, prompt: str, context: str, 
                                          available_agents: List[str],
                                          collab_context: CollaborationContext) -> List[CollaborationRound]:
        """Execute devil's advocate collaboration mode"""
        rounds = []
        
        # Round 1: Initial solutions
        initial_contributions = await self._gather_initial_contributions(
            prompt, context, available_agents
        )
        
        # Synthesize initial solution
        initial_solution = await self.consensus_engine._simple_synthesis(initial_contributions)
        
        rounds.append(CollaborationRound(
            round_number=1,
            prompt=prompt,
            contributions=initial_contributions,
            consensus_level=0.5,
            quality_metrics={"initial": 0.7},
            insights_generated=["Initial solution generated"],
            conflicts_identified=[]
        ))
        
        # Round 2: Devil's advocate challenges
        challenges = await self.devils_advocate.generate_challenges(
            initial_contributions, initial_solution
        )
        
        # Get challenger response
        if available_agents:
            challenger_agent = available_agents[0]  # Use first agent as challenger
            challenge_prompt = f"Original solution: {initial_solution}\n\nChallenges to address:\n" + \
                             "\n".join(f"- {challenge}" for challenge in challenges)
            
            challenge_contribution = AgentContribution(
                agent_name=f"{challenger_agent}_challenger",
                role=AgentRole.CHALLENGER,
                content=f"Challenges identified: {'. '.join(challenges[:3])}",
                confidence=0.8,
                timestamp=datetime.now(timezone.utc),
                response_time=2.0
            )
            
            rounds.append(CollaborationRound(
                round_number=2,
                prompt=challenge_prompt,
                contributions=[challenge_contribution],
                consensus_level=0.3,  # Low due to challenges
                quality_metrics={"challenge": 0.8},
                insights_generated=challenges,
                conflicts_identified=challenges
            ))
        
        return rounds

    async def _execute_consensus_building(self, prompt: str, context: str,
                                        available_agents: List[str],
                                        collab_context: CollaborationContext) -> List[CollaborationRound]:
        """Execute consensus building collaboration mode"""
        rounds = []
        max_rounds = 3
        
        for round_num in range(1, max_rounds + 1):
            # Gather contributions
            contributions = await self._gather_initial_contributions(prompt, context, available_agents)
            
            # Build consensus
            consensus_result, consensus_level, resolution_strategies = await self.consensus_engine.build_consensus(
                contributions, collab_context.consensus_threshold
            )
            
            rounds.append(CollaborationRound(
                round_number=round_num,
                prompt=prompt,
                contributions=contributions,
                consensus_level=consensus_level,
                quality_metrics={"consensus": consensus_level},
                insights_generated=[consensus_result],
                conflicts_identified=resolution_strategies
            ))
            
            # If consensus achieved, stop
            if consensus_level >= collab_context.consensus_threshold:
                break
            
            # Update prompt for next round
            prompt = f"Previous round consensus: {consensus_result}\nResolution needed for: {', '.join(resolution_strategies)}"
        
        return rounds

    async def _execute_peer_review(self, prompt: str, context: str,
                                 available_agents: List[str],
                                 collab_context: CollaborationContext) -> List[CollaborationRound]:
        """Execute peer review collaboration mode"""
        rounds = []
        
        # Round 1: Initial solutions
        initial_contributions = await self._gather_initial_contributions(prompt, context, available_agents)
        
        rounds.append(CollaborationRound(
            round_number=1,
            prompt=prompt,
            contributions=initial_contributions,
            consensus_level=0.6,
            quality_metrics={"initial": 0.7},
            insights_generated=["Initial solutions generated"],
            conflicts_identified=[]
        ))
        
        # Round 2: Peer reviews
        review_contributions = []
        for i, contribution in enumerate(initial_contributions):
            # Each agent reviews another agent's work
            reviewer_idx = (i + 1) % len(initial_contributions)
            if reviewer_idx < len(available_agents):
                reviewer = available_agents[reviewer_idx]
                
                review_contribution = AgentContribution(
                    agent_name=f"{reviewer}_reviewer",
                    role=AgentRole.REVIEWER,
                    content=f"Review of {contribution.agent_name}: Good approach, suggest improving clarity",
                    confidence=0.7,
                    timestamp=datetime.now(timezone.utc),
                    response_time=1.5
                )
                review_contributions.append(review_contribution)
        
        if review_contributions:
            rounds.append(CollaborationRound(
                round_number=2,
                prompt="Peer review round",
                contributions=review_contributions,
                consensus_level=0.8,
                quality_metrics={"review": 0.8},
                insights_generated=["Peer reviews completed"],
                conflicts_identified=[]
            ))
        
        return rounds

    async def _execute_brainstorming(self, prompt: str, context: str,
                                   available_agents: List[str],
                                   collab_context: CollaborationContext) -> List[CollaborationRound]:
        """Execute brainstorming collaboration mode"""
        rounds = []
        
        # Modify prompt for creative brainstorming
        brainstorm_prompt = f"Brainstorm creative solutions for: {prompt}. Think outside the box and suggest innovative approaches."
        
        contributions = await self._gather_initial_contributions(brainstorm_prompt, context, available_agents)
        
        rounds.append(CollaborationRound(
            round_number=1,
            prompt=brainstorm_prompt,
            contributions=contributions,
            consensus_level=0.4,  # Low consensus expected in brainstorming
            quality_metrics={"creativity": 0.8},
            insights_generated=[f"Creative idea from {c.agent_name}" for c in contributions],
            conflicts_identified=[]
        ))
        
        return rounds

    async def _execute_parallel_mode(self, prompt: str, context: str,
                                   available_agents: List[str],
                                   collab_context: CollaborationContext) -> List[CollaborationRound]:
        """Execute parallel collaboration mode"""
        contributions = await self._gather_initial_contributions(prompt, context, available_agents)
        
        rounds = [CollaborationRound(
            round_number=1,
            prompt=prompt,
            contributions=contributions,
            consensus_level=0.6,
            quality_metrics={"parallel": 0.7},
            insights_generated=["Parallel processing completed"],
            conflicts_identified=[]
        )]
        
        return rounds

    async def _gather_initial_contributions(self, prompt: str, context: str,
                                          available_agents: List[str]) -> List[AgentContribution]:
        """Gather initial contributions from available agents"""
        contributions = []
        
        # Simulate agent responses (in real implementation, would call actual agents)
        for agent_name in available_agents:
            contribution = AgentContribution(
                agent_name=agent_name,
                role=AgentRole.CONTRIBUTOR,
                content=f"[{agent_name}] Response to: {prompt[:50]}... (simulated response)",
                confidence=0.7 + (hash(agent_name) % 30) / 100,  # Vary confidence
                timestamp=datetime.now(timezone.utc),
                response_time=1.0 + (hash(agent_name) % 20) / 10  # Vary response time
            )
            contributions.append(contribution)
        
        return contributions

    async def _synthesize_final_output(self, rounds: List[CollaborationRound],
                                     collab_context: CollaborationContext) -> str:
        """Synthesize final output from all rounds"""
        if not rounds:
            return "No collaboration rounds completed"
        
        synthesis_parts = []
        synthesis_parts.append(f"COLLABORATIVE SOLUTION ({collab_context.mode.value} mode)")
        synthesis_parts.append("=" * 50)
        
        for round in rounds:
            synthesis_parts.append(f"\nRound {round.round_number}:")
            synthesis_parts.append(f"Consensus Level: {round.consensus_level:.2f}")
            
            if round.insights_generated:
                synthesis_parts.append("Key Insights:")
                for insight in round.insights_generated[:3]:
                    synthesis_parts.append(f"- {insight}")
        
        # Add final recommendation
        last_round = rounds[-1]
        if last_round.contributions:
            best_contribution = max(last_round.contributions, key=lambda x: x.confidence)
            synthesis_parts.append(f"\nRecommended Approach: {best_contribution.content[:200]}...")
        
        return "\n".join(synthesis_parts)

    def _calculate_quality_score(self, rounds: List[CollaborationRound]) -> float:
        """Calculate overall quality score from rounds"""
        if not rounds:
            return 0.0
        
        total_quality = 0.0
        total_contributions = 0
        
        for round in rounds:
            for contribution in round.contributions:
                total_quality += contribution.quality_score
                total_contributions += 1
        
        return total_quality / max(total_contributions, 1)

    def _calculate_innovation_score(self, rounds: List[CollaborationRound]) -> float:
        """Calculate innovation score from rounds"""
        if not rounds:
            return 0.0
        
        innovation_indicators = 0
        total_insights = 0
        
        for round in rounds:
            total_insights += len(round.insights_generated)
            
            # Count innovation indicators
            for insight in round.insights_generated:
                if any(word in insight.lower() for word in ['innovative', 'creative', 'novel', 'unique']):
                    innovation_indicators += 1
        
        return min(1.0, innovation_indicators / max(total_insights, 1))

    def _check_consensus_achievement(self, rounds: List[CollaborationRound],
                                   collab_context: CollaborationContext) -> bool:
        """Check if consensus was achieved"""
        if not rounds:
            return False
        
        final_round = rounds[-1]
        return final_round.consensus_level >= collab_context.consensus_threshold

    async def _extract_lessons_learned(self, rounds: List[CollaborationRound]) -> List[str]:
        """Extract lessons learned from collaboration"""
        lessons = []
        
        if not rounds:
            return ["No rounds to learn from"]
        
        # Analyze consensus progression
        consensus_levels = [round.consensus_level for round in rounds]
        if len(consensus_levels) > 1:
            if consensus_levels[-1] > consensus_levels[0]:
                lessons.append("Consensus building was effective")
            else:
                lessons.append("Consensus building needs improvement")
        
        # Analyze agent participation
        all_agents = set()
        for round in rounds:
            all_agents.update(contrib.agent_name for contrib in round.contributions)
        
        lessons.append(f"Collaboration involved {len(all_agents)} unique agent perspectives")
        
        # Analyze conflicts
        total_conflicts = sum(len(round.conflicts_identified) for round in rounds)
        if total_conflicts > 0:
            lessons.append(f"Identified and worked through {total_conflicts} conflicts")
        
        return lessons

    async def _generate_improvement_suggestions(self, rounds: List[CollaborationRound]) -> List[str]:
        """Generate suggestions for improving collaboration"""
        suggestions = []
        
        if not rounds:
            return ["Complete at least one collaboration round"]
        
        # Analyze quality scores
        avg_quality = self._calculate_quality_score(rounds)
        if avg_quality < 0.6:
            suggestions.append("Focus on improving response quality")
        
        # Analyze consensus levels
        final_consensus = rounds[-1].consensus_level if rounds else 0
        if final_consensus < 0.7:
            suggestions.append("Work on building stronger consensus")
        
        # Analyze participation
        agent_participation = {}
        for round in rounds:
            for contrib in round.contributions:
                agent_participation[contrib.agent_name] = agent_participation.get(contrib.agent_name, 0) + 1
        
        if agent_participation:
            min_participation = min(agent_participation.values())
            max_participation = max(agent_participation.values())
            if max_participation > min_participation * 2:
                suggestions.append("Balance participation across all agents")
        
        if not suggestions:
            suggestions.append("Collaboration is working well")
        
        return suggestions

    def _calculate_agent_performances(self, rounds: List[CollaborationRound]) -> Dict[str, Dict[str, float]]:
        """Calculate individual agent performance metrics"""
        performances = {}
        
        for round in rounds:
            for contrib in round.contributions:
                agent_name = contrib.agent_name
                
                if agent_name not in performances:
                    performances[agent_name] = {
                        "contributions": 0,
                        "avg_confidence": 0.0,
                        "avg_response_time": 0.0,
                        "total_quality": 0.0
                    }
                
                perf = performances[agent_name]
                perf["contributions"] += 1
                perf["avg_confidence"] = (perf["avg_confidence"] + contrib.confidence) / perf["contributions"]
                perf["avg_response_time"] = (perf["avg_response_time"] + contrib.response_time) / perf["contributions"]
                perf["total_quality"] += contrib.quality_score
        
        return performances

    def get_collaboration_analytics(self) -> Dict[str, Any]:
        """Get analytics about collaboration patterns"""
        if not self.collaboration_history:
            return {"message": "No collaboration history available"}
        
        # Analyze collaboration patterns
        mode_usage = {}
        quality_trends = []
        consensus_trends = []
        
        for result in self.collaboration_history:
            # Mode usage
            mode = result.mode.value
            mode_usage[mode] = mode_usage.get(mode, 0) + 1
            
            # Trends
            quality_trends.append(result.quality_score)
            consensus_trends.append(result.consensus_achieved)
        
        # Calculate averages
        avg_quality = sum(quality_trends) / len(quality_trends)
        consensus_rate = sum(consensus_trends) / len(consensus_trends)
        
        return {
            "total_collaborations": len(self.collaboration_history),
            "mode_usage": mode_usage,
            "average_quality": avg_quality,
            "consensus_achievement_rate": consensus_rate,
            "quality_trend": quality_trends[-5:],  # Last 5
            "most_effective_mode": max(mode_usage.items(), key=lambda x: x[1])[0] if mode_usage else None,
            "recommendations": self._generate_analytics_recommendations(avg_quality, consensus_rate)
        }

    def _generate_analytics_recommendations(self, avg_quality: float, consensus_rate: float) -> List[str]:
        """Generate recommendations based on analytics"""
        recommendations = []
        
        if avg_quality < 0.6:
            recommendations.append("Focus on improving collaboration quality")
        
        if consensus_rate < 0.7:
            recommendations.append("Improve consensus building techniques")
        
        if len(self.collaboration_history) < 10:
            recommendations.append("Gather more collaboration data for better insights")
        
        if not recommendations:
            recommendations.append("Collaboration performance is strong")
        
        return recommendations


# Global collaboration engine instance
_collaboration_engine = None

def get_collaboration_engine() -> AdvancedCollaborationEngine:
    """Get the global collaboration engine instance"""
    global _collaboration_engine
    if _collaboration_engine is None:
        _collaboration_engine = AdvancedCollaborationEngine()
    return _collaboration_engine