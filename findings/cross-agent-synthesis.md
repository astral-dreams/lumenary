# Cross-Agent Synthesis

Claude Code findings were imported from the user's message on 2026-05-25.

## Agreements

- The system should be recursive and persistent.
- The local filesystem should be a primary knowledge surface.
- The agent should maintain its own exploration state and use prior findings to decide next directions.
- Convergence across independent traditions is an important signal.
- Self-critique is required before treating a synthesis as valuable.

## Differences

- Claude Code prefers a Claude API orchestrator as the main thinking engine.
- Codex prefers a provider-neutral engine where OpenAI, Claude, local Hermes, and later LangGraph can be swapped in by role.
- Claude Code initially avoids databases; Codex keeps Markdown as source of truth but leaves room for DuckDB/Qdrant indexes once the corpus grows.

## Combined Direction

Build a custom Python loop first. Store everything important in Markdown and JSONL. Keep Codex, Claude, and future model findings separately attributed. Treat original observations and publishable syntheses as the core product.
