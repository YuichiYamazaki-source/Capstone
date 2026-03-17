# Embedding Space Analysis — Summary

Full analysis and visualizations: [`data/embedding-analysis/`](../../data/embedding-analysis/embedding-analysis.md)

## Key Findings

1,000 コースの dense embedding (text-embedding-3-small, 1536-dim) を t-SNE で可視化し、4 軸で色分け分析した結果：

| Color axis | Cluster? | Meaning |
|-----------|----------|---------|
| **Topic** | ✅ Clear | Embedding はトピック（科目分野）の意味的類似性を捉えている |
| **Skill** | △ Weak | データが sparse (2,195 ユニーク) で弱いクラスタのみ |
| **Level** | ❌ None | Beginner/Intermediate/Advanced は空間全体に混在 |
| **Organization** | ❌ None | 提供組織による分離なし |

## Design Validation

この分析により、現行の RAG 設計が embedding の特性と整合していることが確認できた：

- **Semantic search** → トピック類似度に専念（embedding が捉える軸）
- **BM25 keyword matching** → 特定スキル・ツール名の補完（embedding が弱い軸）
- **Payload filter** → Level, Organization, Rating（embedding が捉えない軸）

## Future Directions

Embedding クラスタリング (HDBSCAN / BERTopic) による自動トピック分類が有望。詳細は full analysis を参照。
