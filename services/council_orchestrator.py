"""
BouleAI — Council Orchestrator
================================

Implements the **Scatter → Gather** phase of the BouleAI architecture:

  Scatter  — fan-out the user prompt to all N council models concurrently.
  Gather   — collect every response (success or graceful failure) once all
             coroutines complete, never waiting on stragglers sequentially.

Architecture rules enforced here:
  ✅ Rule 1 — Fully async; zero blocking calls.
  ✅ Rule 2 — Resilience delegated to OpenRouterClient (backoff/retry).
  ✅ Rule 3 — asyncio.gather(return_exceptions=True) guarantees that one
              dead model never cancels the other three.
  ✅ Rule 3 — Any residual exception that escapes the client is caught here
              and converted to the same fallback string format.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Sequence

from services.openrouter_client import OpenRouterClient

logger = logging.getLogger("boule_ai.orchestrator")

# ---------------------------------------------------------------------------
# Separator used in the aggregated output string
# ---------------------------------------------------------------------------
_SECTION_DIVIDER = "=" * 72


# ---------------------------------------------------------------------------
# Result dataclass — richer than a plain string; easy to extend later
# ---------------------------------------------------------------------------
@dataclass
class CouncilMemberResult:
    """Holds the outcome for a single council model."""

    model: str
    response: str
    succeeded: bool  # False when the fallback string had to be used

    @property
    def short_name(self) -> str:
        """Human-friendly label, e.g. 'mistral-7b-instruct' from the full ID."""
        # OpenRouter IDs look like "provider/model-name:variant"
        # We strip the provider prefix and variant suffix for readability.
        name = self.model.split("/")[-1]    # drop "provider/"
        name = name.split(":")[0]           # drop ":free" / ":nitro" etc.
        return name


@dataclass
class CouncilSession:
    """Complete output of one scatter-gather round."""

    prompt: str
    members: list[CouncilMemberResult] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Aggregated string — this is what gets handed to the Chairman model  #
    # ------------------------------------------------------------------ #
    def to_aggregated_string(self) -> str:
        """
        Format all council member responses into a single labelled block.

        Example output
        --------------
        ════════════════...
        [Council Member 1/4] mistral-7b-instruct
        ════════════════...
        <response text or fallback marker>

        ════════════════...
        [Council Member 2/4] gemma-7b-it
        ...
        """
        total = len(self.members)
        sections: list[str] = []

        for idx, member in enumerate(self.members, start=1):
            header = (
                f"{_SECTION_DIVIDER}\n"
                f"[Council Member {idx}/{total}] {member.short_name}\n"
                f"Model ID: {member.model}\n"
                f"Status: {'✅ Success' if member.succeeded else '❌ Failed (fallback)'}\n"
                f"{_SECTION_DIVIDER}"
            )
            sections.append(f"{header}\n{member.response.strip()}")

        return "\n\n".join(sections)

    @property
    def success_count(self) -> int:
        return sum(1 for m in self.members if m.succeeded)

    @property
    def failure_count(self) -> int:
        return len(self.members) - self.success_count


# ---------------------------------------------------------------------------
# Fallback sentinel — mirrors the format from openrouter_client.py
# ---------------------------------------------------------------------------
_FALLBACK_MARKER = "[{model} encountered an unexpected orchestration error]"


def _is_fallback(text: str) -> bool:
    """Detect whether a response string is a failure placeholder."""
    # BUG FIX — operator precedence: `and` binds tighter than `or`, so the
    # original expression:
    #   text.startswith("[") and "failed" in lower  OR  "error" in lower and text.startswith("[")
    # evaluated the right-hand `or` branch incorrectly: any genuine council
    # answer containing the word 'error' (e.g. "error handling best practices")
    # would be classified as a failure. Fix: explicit parentheses per clause.
    lower = text.lower()
    return text.startswith("[") and ("failed" in lower or "error" in lower)


# ---------------------------------------------------------------------------
# Core orchestration function
# ---------------------------------------------------------------------------
async def query_council(
    prompt: str,
    model_list: Sequence[str],
    client: OpenRouterClient | None = None,
    *,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> CouncilSession:
    """
    Scatter the user ``prompt`` to every model in ``model_list`` concurrently,
    then gather all responses into a :class:`CouncilSession`.

    Parameters
    ----------
    prompt:
        The raw user question / task to send to each council member.
    model_list:
        Sequence of OpenRouter model ID strings, e.g.::

            [
                "mistralai/mistral-7b-instruct:free",
                "google/gemma-7b-it:free",
                "meta-llama/llama-3-8b-instruct:free",
                "openchat/openchat-7b:free",
            ]

    client:
        An existing :class:`OpenRouterClient` instance to reuse (recommended
        for connection-pool efficiency).  If ``None``, a fresh client is
        created and closed automatically after the gather completes.
    temperature:
        Sampling temperature forwarded to every model.
    max_tokens:
        Token cap forwarded to every model.

    Returns
    -------
    CouncilSession
        Contains per-model results and a pre-formatted aggregated string
        ready to be passed to the Chairman model.

    Notes
    -----
    * ``asyncio.gather(return_exceptions=True)`` is the critical safety net:
      even if a coroutine raises an exception that somehow escaped the client's
      own try/except, it is captured here as an ``Exception`` object rather
      than propagating and cancelling the sibling tasks.
    * The :class:`OpenRouterClient` itself already converts all errors to a
      fallback string, so seeing a raw ``Exception`` here should be rare —
      but we handle it anyway for defence-in-depth.
    """
    if not model_list:
        raise ValueError("model_list must contain at least one model ID.")

    # ------------------------------------------------------------------ #
    # Build the message payload — same prompt for every council member    #
    # ------------------------------------------------------------------ #
    messages: list[dict[str, str]] = [
        {"role": "user", "content": prompt},
    ]

    # ------------------------------------------------------------------ #
    # Manage client lifetime                                               #
    # ------------------------------------------------------------------ #
    _own_client = client is None
    if _own_client:
        client = OpenRouterClient()
        logger.debug("query_council: created a transient OpenRouterClient.")

    try:
        # ---------------------------------------------------------------- #
        # SCATTER — fire all coroutines at once                             #
        # ---------------------------------------------------------------- #
        logger.info(
            "🚀 Scattering prompt to %d council models concurrently…",
            len(model_list),
        )

        coroutines = [
            client.chat(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            for model in model_list
        ]

        # return_exceptions=True  ← the KEY flag:
        #   • Successful tasks  → their return value (a str)
        #   • Failed tasks      → the Exception object itself, NOT re-raised
        #   This means all N tasks always run to completion regardless of
        #   what any sibling does.
        raw_results: list[str | BaseException] = await asyncio.gather(
            *coroutines,
            return_exceptions=True,
        )

        # ---------------------------------------------------------------- #
        # GATHER — interpret every result                                  #
        # ---------------------------------------------------------------- #
        session = CouncilSession(prompt=prompt)

        for model, result in zip(model_list, raw_results):
            if isinstance(result, BaseException):
                # Should be extremely rare — the client already handles this —
                # but we convert it to a fallback string rather than letting
                # it surface as an unhandled exception.
                fallback_text = _FALLBACK_MARKER.format(model=model)
                logger.error(
                    "✗ [%s] unexpected exception escaped the client layer: %s — %s",
                    model,
                    type(result).__name__,
                    result,
                )
                session.members.append(
                    CouncilMemberResult(
                        model=model,
                        response=fallback_text,
                        succeeded=False,
                    )
                )
            else:
                # result is a str — either a genuine answer or the client's
                # own fallback marker (e.g. "[model failed to respond…]").
                succeeded = not _is_fallback(result)
                session.members.append(
                    CouncilMemberResult(
                        model=model,
                        response=result,
                        succeeded=succeeded,
                    )
                )

        logger.info(
            "✅ Council gather complete — %d/%d models succeeded.",
            session.success_count,
            len(model_list),
        )
        return session

    finally:
        if _own_client:
            await client.close()
            logger.debug("query_council: transient OpenRouterClient closed.")


# ---------------------------------------------------------------------------
# Chairman Model — System Prompt
# ---------------------------------------------------------------------------
# DESIGN INTENT
# The system prompt is deliberately restrictive.  The Chairman's sole job is
# to SYNTHESIZE, not to participate as a 5th council voice.  Every clause
# below serves that constraint:
#
#  • "You are a Chairman, NOT a participant" — role identity
#  • "Do NOT add your own opinion" — explicit prohibition (Verification ✅)
#  • "Do NOT invent information" — prevents hallucination fill-in
#  • Numbered output format — keeps the response machine-parseable
# ---------------------------------------------------------------------------
CHAIRMAN_SYSTEM_PROMPT: str = """
You are the Chairman of the BouleAI Advisory Council.
Your SOLE function is to SYNTHESIZE and ARBITRATE the answers already provided
by the council members below.  You are NOT a participant in the debate.

STRICT RULES — violating any of these is a critical failure:

1. DO NOT add your own opinion, conjecture, or personal perspective.
   You are a referee, not a 5th council member.
2. DO NOT invent, assume, or hallucinate any information that was not
   explicitly stated by at least one council member.
3. If council members AGREE, state the consensus directly and concisely.
4. If council members CONTRADICT each other, identify the contradiction,
   weigh the evidence each side provided, and declare the most
   well-supported position. Briefly explain which evidence was stronger.
5. If a council member FAILED to respond (their answer contains a failure
   marker like "[Model X failed to respond…]"), note this and exclude their
   non-answer from your synthesis without penalising the overall result.
6. Structure your final answer in this exact format:

   ## Consensus Verdict
   <Your synthesized, definitive answer here.>

   ## Key Points of Agreement
   <Bullet list of what the council agreed on.>

   ## Contradictions Resolved (if any)
   <Explain any contradictions and how you resolved them.  Omit this
    section if there were no meaningful contradictions.>

   ## Council Participation
   <State how many models responded successfully vs. failed.>

Your output is the final word.  Do not hedge with phrases like
"I think", "in my opinion", or "you might want to".
""".strip()


# ---------------------------------------------------------------------------
# Chairman synthesis function
# ---------------------------------------------------------------------------
async def synthesize_consensus(
    original_prompt: str,
    aggregated_council_responses: str,
    chairman_model: str,
    client: OpenRouterClient | None = None,
    *,
    temperature: float = 0.3,   # lower temp → more deterministic synthesis
    max_tokens: int = 2048,
) -> str:
    """
    Pass the original prompt + all council responses to the Chairman model
    for final synthesis.

    Parameters
    ----------
    original_prompt:
        The exact question the user originally asked — given to the Chairman
        so it can keep the synthesis focused on the user's actual query.
    aggregated_council_responses:
        The pre-formatted string from :meth:`CouncilSession.to_aggregated_string`.
    chairman_model:
        OpenRouter model ID for the Chairman (e.g.
        ``"mistralai/mixtral-8x7b-instruct:free"``).
    client:
        Shared :class:`OpenRouterClient` instance.  If ``None``, a transient
        one is created and closed automatically.
    temperature:
        Kept low (default 0.3) to favour deterministic arbitration over
        creative variation.
    max_tokens:
        Token budget for the Chairman's final verdict.

    Returns
    -------
    str
        The Chairman's synthesized verdict, or a fallback string if the
        Chairman model itself fails after retries.
    """
    # The Chairman receives:
    #   [system]  → strict synthesis rules (no 5th opinion, etc.)
    #   [user]    → the original question + all council answers
    user_payload = (
        f"## Original User Question\n{original_prompt}\n\n"
        f"## Council Responses\n{aggregated_council_responses}"
    )

    messages: list[dict[str, str]] = [
        {"role": "system", "content": CHAIRMAN_SYSTEM_PROMPT},
        {"role": "user",   "content": user_payload},
    ]

    logger.info("🎓 Sending council responses to Chairman model [%s]…", chairman_model)

    _own_client = client is None
    if _own_client:
        client = OpenRouterClient()

    try:
        verdict = await client.chat(
            model=chairman_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:  # noqa: BLE001
        # BUG FIX — the original had no except clause (only finally), so any
        # exception that escaped client.chat() — e.g. a ValueError from an
        # unexpected JSON structure — would propagate unhandled out of this
        # function. Since client.chat() already handles errors internally,
        # this path is rare, but we must catch it for defence-in-depth.
        logger.exception(
            "✗ Chairman model [%s] raised unexpectedly: %s", chairman_model, exc
        )
        verdict = (
            f"[Chairman model {chairman_model} failed to synthesize: "
            f"{type(exc).__name__}]"
        )
    finally:
        if _own_client:
            await client.close()

    logger.info("\u2705 Chairman synthesis complete.")
    return verdict
