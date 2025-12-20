"""
AI Consensus Engine - Multi-Model Debate System
For complex tasks, multiple AI models collaborate through debate.

Flow:
1. Claude proposes a solution
2. Gemini critiques for bugs/security
3. Grok judges if critique is valid
4. Final synthesized answer

Part of the Self-Orchestrating AI Team.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ConsensusRole(Enum):
    PROPOSER = "proposer"       # Claude - Creates initial solution
    CRITIC = "critic"           # Gemini - Reviews for issues
    JUDGE = "judge"             # Grok - Decides on critique validity
    SYNTHESIZER = "synthesizer" # ChatGPT - Creates final answer


@dataclass
class ConsensusRound:
    """One round of the consensus debate."""
    role: ConsensusRole
    model: str
    input_prompt: str
    response: str
    confidence: float
    issues_found: List[str]
    time_taken: float


@dataclass
class ConsensusResult:
    """Final result of the consensus process."""
    final_answer: str
    consensus_reached: bool
    confidence: float
    rounds: List[ConsensusRound]
    models_used: List[str]
    total_time: float
    debate_summary: str


class AIConsensusEngine:
    """
    Multi-model debate and consensus system.

    For complex questions, we don't just ask one AI - we make them debate.
    This catches errors, security issues, and produces better solutions.
    """

    PROPOSER_PROMPT = """You are the Lead Architect AI. Your job is to propose solutions.

CODEBASE CONTEXT:
{codebase_context}

USER REQUEST:
{user_request}

Provide a clear, actionable solution. Include:
1. Approach summary
2. Files to modify
3. Code changes needed
4. Potential risks

Be specific and technical."""

    CRITIC_PROMPT = """You are the Code Reviewer AI. Your job is to find problems.

ORIGINAL REQUEST:
{user_request}

PROPOSED SOLUTION:
{proposed_solution}

Critically analyze this solution for:
1. Security vulnerabilities (OWASP Top 10)
2. Logic errors or bugs
3. Missing edge cases
4. Performance issues
5. Code quality problems

Be harsh but fair. List specific issues with line references if applicable.
If the solution is solid, say "NO ISSUES FOUND" and explain why it's good."""

    JUDGE_PROMPT = """You are the Technical Judge AI. Your job is to evaluate the debate.

ORIGINAL REQUEST:
{user_request}

PROPOSED SOLUTION:
{proposed_solution}

CRITIC'S REVIEW:
{critique}

Evaluate:
1. Are the critic's concerns valid? (Yes/Partially/No for each)
2. Which issues are critical vs nice-to-have?
3. What's the final verdict?

Provide a balanced judgment that considers both perspectives."""

    SYNTHESIZER_PROMPT = """You are the Solution Synthesizer AI. Create the final answer.

ORIGINAL REQUEST:
{user_request}

PROPOSED SOLUTION:
{proposed_solution}

CRITIQUE:
{critique}

JUDGMENT:
{judgment}

Create the FINAL answer that:
1. Incorporates valid critique points
2. Maintains the good parts of the proposal
3. Is ready for implementation
4. Includes any warnings or considerations

Format as a clear, actionable response."""

    def __init__(self):
        self._gemini = None
        self._openai = None
        self._anthropic = None

    async def _get_model_response(
        self,
        model_name: str,
        prompt: str,
        role: ConsensusRole
    ) -> tuple[str, float]:
        """Get response from a specific model."""
        import time
        start = time.time()

        try:
            if model_name == "gemini" and os.getenv("GEMINI_API_KEY"):
                response = await self._call_gemini(prompt)
            elif model_name == "openai" and os.getenv("OPENAI_API_KEY"):
                response = await self._call_openai(prompt)
            elif model_name == "claude" and os.getenv("ANTHROPIC_API_KEY"):
                response = await self._call_claude(prompt)
            else:
                # Fallback to whatever is available
                response = await self._call_any_available(prompt)

            elapsed = time.time() - start
            return response, elapsed

        except Exception as e:
            logger.error(f"Model {model_name} failed: {e}")
            elapsed = time.time() - start
            return f"[Error from {model_name}: {str(e)}]", elapsed

    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API."""
        try:
            from app.services.gemini_service import gemini_service
            response = await gemini_service.generate_response(prompt, context="")
            return response
        except Exception as e:
            raise Exception(f"Gemini error: {e}")

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI error: {e}")

    async def _call_claude(self, prompt: str) -> str:
        """Call Claude API."""
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Claude error: {e}")

    async def _call_any_available(self, prompt: str) -> str:
        """Try any available model."""
        if os.getenv("GEMINI_API_KEY"):
            return await self._call_gemini(prompt)
        elif os.getenv("OPENAI_API_KEY"):
            return await self._call_openai(prompt)
        elif os.getenv("ANTHROPIC_API_KEY"):
            return await self._call_claude(prompt)
        else:
            return "[No AI models configured. Add GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY to .env]"

    async def reach_consensus(
        self,
        user_request: str,
        codebase_context: str = "",
        min_models: int = 2
    ) -> ConsensusResult:
        """
        Run the full consensus process.

        Args:
            user_request: The user's question or task
            codebase_context: Relevant codebase information
            min_models: Minimum models required (2 for debate, 3+ for full consensus)
        """
        import time
        start_time = time.time()
        rounds: List[ConsensusRound] = []
        models_used = []

        logger.info(f"🧠 Starting consensus process for: {user_request[:50]}...")

        # Step 1: PROPOSER (Claude/Gemini) creates initial solution
        proposer_prompt = self.PROPOSER_PROMPT.format(
            codebase_context=codebase_context or "No specific context provided.",
            user_request=user_request
        )
        proposal, time1 = await self._get_model_response("gemini", proposer_prompt, ConsensusRole.PROPOSER)
        rounds.append(ConsensusRound(
            role=ConsensusRole.PROPOSER,
            model="gemini",
            input_prompt=proposer_prompt[:200] + "...",
            response=proposal,
            confidence=0.8,
            issues_found=[],
            time_taken=time1
        ))
        models_used.append("gemini")
        logger.info(f"  ✅ Proposal generated ({time1:.2f}s)")

        # Step 2: CRITIC (OpenAI) reviews for issues
        critic_prompt = self.CRITIC_PROMPT.format(
            user_request=user_request,
            proposed_solution=proposal
        )
        critique, time2 = await self._get_model_response("openai", critic_prompt, ConsensusRole.CRITIC)

        # Parse issues from critique
        issues = self._extract_issues(critique)
        rounds.append(ConsensusRound(
            role=ConsensusRole.CRITIC,
            model="openai",
            input_prompt=critic_prompt[:200] + "...",
            response=critique,
            confidence=0.85,
            issues_found=issues,
            time_taken=time2
        ))
        models_used.append("openai")
        logger.info(f"  ✅ Critique complete ({time2:.2f}s) - {len(issues)} issues found")

        # Step 3: JUDGE decides on critique validity (optional for 2-model)
        judgment = ""
        if min_models >= 3 and os.getenv("XAI_API_KEY"):
            judge_prompt = self.JUDGE_PROMPT.format(
                user_request=user_request,
                proposed_solution=proposal,
                critique=critique
            )
            judgment, time3 = await self._get_model_response("grok", judge_prompt, ConsensusRole.JUDGE)
            rounds.append(ConsensusRound(
                role=ConsensusRole.JUDGE,
                model="grok",
                input_prompt=judge_prompt[:200] + "...",
                response=judgment,
                confidence=0.9,
                issues_found=[],
                time_taken=time3
            ))
            models_used.append("grok")
            logger.info(f"  ✅ Judgment rendered ({time3:.2f}s)")

        # Step 4: SYNTHESIZER creates final answer
        synth_prompt = self.SYNTHESIZER_PROMPT.format(
            user_request=user_request,
            proposed_solution=proposal,
            critique=critique,
            judgment=judgment or "No separate judgment - using critique directly."
        )
        final_answer, time4 = await self._get_model_response("gemini", synth_prompt, ConsensusRole.SYNTHESIZER)
        rounds.append(ConsensusRound(
            role=ConsensusRole.SYNTHESIZER,
            model="gemini",
            input_prompt=synth_prompt[:200] + "...",
            response=final_answer,
            confidence=0.9,
            issues_found=[],
            time_taken=time4
        ))
        logger.info(f"  ✅ Final answer synthesized ({time4:.2f}s)")

        total_time = time.time() - start_time

        # Generate debate summary
        debate_summary = self._generate_debate_summary(rounds)

        return ConsensusResult(
            final_answer=final_answer,
            consensus_reached=True,
            confidence=0.85,
            rounds=rounds,
            models_used=list(set(models_used)),
            total_time=total_time,
            debate_summary=debate_summary
        )

    def _extract_issues(self, critique: str) -> List[str]:
        """Extract issue list from critique text."""
        issues = []
        lines = critique.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('- ', '* ', '1.', '2.', '3.', '4.', '5.')):
                if any(word in line.lower() for word in ['issue', 'bug', 'error', 'problem', 'vulnerability', 'risk']):
                    issues.append(line)
        return issues[:10]  # Cap at 10

    def _generate_debate_summary(self, rounds: List[ConsensusRound]) -> str:
        """Generate human-readable debate summary."""
        summary_parts = ["## AI Team Debate Summary\n"]

        for round in rounds:
            role_emoji = {
                ConsensusRole.PROPOSER: "💡",
                ConsensusRole.CRITIC: "🔍",
                ConsensusRole.JUDGE: "⚖️",
                ConsensusRole.SYNTHESIZER: "✨"
            }
            emoji = role_emoji.get(round.role, "🤖")
            summary_parts.append(f"{emoji} **{round.role.value.title()}** ({round.model}) - {round.time_taken:.2f}s")
            if round.issues_found:
                summary_parts.append(f"   Issues: {len(round.issues_found)}")

        return "\n".join(summary_parts)


# Singleton
_consensus_engine: Optional[AIConsensusEngine] = None


def get_consensus_engine() -> AIConsensusEngine:
    """Get or create the consensus engine."""
    global _consensus_engine
    if _consensus_engine is None:
        _consensus_engine = AIConsensusEngine()
    return _consensus_engine
