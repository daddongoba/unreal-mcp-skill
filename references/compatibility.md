# Model Compatibility Fallback (read on install or when the skill feels "dumb")

This skill was tuned on a strong model with aggressive context-slimming (v3.3). If a weaker/different model uses it and quality drops, run this fallback — it restores the safety rails the slim version delegates to model competence.

## Capability baseline test (30 seconds, do once on a fresh session)

1. Ask it to call `list_toolsets` and report the count. (basic tool use)
2. Feed a deliberately-wrong param and check it reads the error's named missing-param and retries (G12 loop). (error-driven iteration)
3. Ask "can I edit AnimBP state machines?" — correct answer: refused at tool layer, alternatives exist. (respect for capability boundaries + no hallucination)

**If any test fails → run WEAK-MODE MODE below.**

## Weak-mode adjustments

1. **Verification Tiering OFF**: ignore Q-level exemptions — verify EVERY save (disk), EVERY profile write (readback), EVERY DSL write (readback). The tiering was calibrated for a model that doesn't hallucinate tool success. (v3.6 note: the normal-mode hard rail already mandates DSL readback for any non-verbatim write; weak-mode keeps the fuller set — disk-verify saves + profile readbacks too.)
2. **Pattern A/B back in context**: read `scripts/mcp_call.ps1` header fully; use the PowerShell fallback patterns verbatim rather than improvising HTTP.
3. **Requirement De-Risking expanded**: before ANY build, enumerate the six ambiguity triggers (referential target / fuzzy trigger / vague verb / frameless direction / ambiguous term / missing numbers) explicitly in the reply, then ask. Do not rely on "feeling" that the request is clear.
4. **Per-toolset describe first**: before calling ANY toolset's tool, `describe_toolset` once. Skip the G12 error-iterate shortcut.
5. **Templates verbatim**: when a template matches, copy it closer to verbatim (fewer adaptations per pass) — adaptations require judgment the weak model may lack; do one change at a time and re-verify.

## Why this file exists

v3.3 slimmed SKILL.md from 35KB to ~14KB by delegating "things a strong model does anyway" (asking when unclear, error-driven iteration, verification judgment) to model competence. That's a deliberate trade: cheaper activation for capable models, and this fallback restores the rails when competence isn't there. The knowledge was sunk to references/, never deleted — weak mode = read more, trust less.
