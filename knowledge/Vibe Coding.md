# Vibe Coding — Strategy & Lessons

**Tags**: #type/knowledge #domain/vibe-coding

AI-assisted development (Claude Code) での学び・戦略・パターンを蓄積する。

---

## Strategy（戦略）

### Skills as Reusable Knowledge
- `~/.claude/skills/` にSKILL.mdを置くとClaude Codeが自動参照する
- プロジェクト横断で使える共通パターンの蓄積先
- 現在のskills: `docker-compose`, `llm-ops`

### Discuss → Approve → Implement
- 説明 → 承認 → 実装の順で進める
- Claude Codeに勝手に実装させない

### Cost Awareness
- LLM/API呼び出し前にコスト見積もりを出す
- 承認を得てから実行

---

## Patterns（パターン集）

### Docker Compose
- Dev: volume mount (HMR), Prod: COPY (self-contained)
- Port expose はgatewayのみ、内部はDocker network
- Per-service Dockerfile で軽量ビルド
- → 詳細: `~/.claude/skills/docker-compose/SKILL.md`

### LLM Ops
- Observability (tracing) / Monitoring (metrics) / Evaluation (offline) の責務分離
- DeepEval: `--limit 2-3` で先にエラー確認、コスト見積もり後に本実行
- LangFuse v4: decorators廃止、`observe` + `get_client` を使用
- Guardrails: rule-based > LLM-based (latency/cost)
- → 詳細: `~/.claude/skills/llm-ops/SKILL.md`

---

## Lessons（学び）

<!-- Format:
### YYYY-MM-DD: Title
**Context**: What happened
**Lesson**: What to do/avoid next time
-->

### 2026-03-13: Obsidian API patch with emoji headings
**Context**: Obsidian Local REST API の patch_content で絵文字入り見出しを target に指定するとマッチしない
**Lesson**: 絵文字付き見出しへの patch は避け、append_content を使うか、見出しから絵文字を除外する
