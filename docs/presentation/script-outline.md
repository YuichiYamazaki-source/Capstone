# 発表原稿アウトライン

発表 15分 + Q&A 5分 = 合計 20分
位置づけ: PoC complete + PoB partial

---

## セクション 1: オープニング — Why & ポジショニング (2-3分)

### 1-1. 市場機会 (30秒)

- スライド: Market Opportunity
- ポイント: E-Learning市場 $200B (2020) -> $843B (2030)
- 成長要因: AI統合 (41% YoY)、リモートワークによるリスキリング需要、コスト優位性
- 繋ぎ: 「しかし、学習体験そのものはまだ追いついていない」

> 原稿:
>Hello, everyone.
>I'll do a presentation about College Course Finder. 
> E-Learningの市場規模は2020年に2000億ドルでしたが、2030年には8400億ドルまで成長する見込みです。
> AI活用やリモートワークの拡大がその背景にあります。
> しかし、市場が伸びている一方で、学習者の体験そのものにはまだ課題が残っています。

### 1-2. 課題 — 4つのPain Point (45秒)

- スライド: The Problem
- 具体例を交えた4つの課題:
  1. Intent Mismatch — 学生は「MLを学びたい」と言うが、検索にはコース名やコード番号が必要
  2. Prerequisite Confusion — 上級コースに必要な前提知識が見えないことがおおい
  3. Path Discovery — 入門から上級への学習パスを手動で組み立てるのは時間がかかる
  4. Fragmented Info — 情報がカタログ、履修ガイド、学科資料に散在
- 繋ぎ: 「この4つを解決するために、AIを使ったシステムを構築しました」

> 原稿:
>
> 具体的にどんな課題があるかというと、例えば学生が「機械学習を学びたい」と思ったとき、ビギナーはChatGPTなどと壁打ちをしながら、複数のResourcesを見て検索をします。知識がない中で自分にどのSkillが不足していてどんな知識が必要かを考えながら学習プランを考察し、講義を選択するのはビギナーにとってはハードルが高いです。一方で上級者にとっては、既に知っている内容について講義を聞く時間は無駄になってしまいます。
> このこれらの課題を解決するために、AIを活用したコース発見システムを構築しました。

### 1-3. ポジショニング — PoC + PoB 宣言 (45秒)

- スライドなし（口頭のみ、またはObjectiveスライド上で補足）
- 宣言: 「本PJの位置づけは PoC complete + PoB partial です」
- フルPoBでない理由:
  1. 講義データに欠損が多く、講義内容の詳細な取得が困難
  2. Ground Truth問題 — 「正解」を誰が定義するのか？
  3. 実ユーザーデータがない（サンプルサイズ1）
- 戦略: 計測する仕組みを先に作る（LangFuse + DeepEval）→ 実ユーザーで改善ループを回す
- 繋ぎ: 「では実際に動かしてお見せします」

> 原稿:
>
> ここで前提として、document_pdf(requirements)の自分の解釈を補足します。
> 本プロジェクトの位置づけは「PoC完了、PoB一部実施」です。
> フルPoBに至っていない理由は3つあります。
> 1つ目は、講義データの欠損です。コース説明文が数行しかないうえ、スキルDescriptionが欠如しているデータも多いです。そのため、スキルとの精密なマッチングが困難です。
> 2つ目は、Ground Truthの問題です。「このクエリに対してどのコースが正解か」を誰が定義するのか。開発者である自分でさえ、説明文が短すぎて自信を持って正解とは言えないため、データセットを用意するのが紺なんです。
> 3つ目は、実ユーザーデータがないことです。一人で開発しているため、サンプルサイズは1です。
> そこで戦略として、まず計測の仕組みを先に作りました。LangFuseでオンラインのトレーシング、DeepEvalで評価のハーネスを構築し、実ユーザーが使ったとき・使った後にすぐ改善ループを回せる状態にしています。私は、このPoC実施後にデモをする機会が必要だと思っています。
> では、実際にシステムを動かしてお見せします。

---

## セクション 2: デモ (5-6分)

### 2-1. ユーザー登録 & オンボーディング (1分)

- 画面: Register -> Onboarding
- 操作: アカウント作成、スキル・興味分野・学習目的を入力
- 説明: プロフィール情報がAgent側に渡り、パーソナライズの基盤になる

> 原稿:
>
> デモでは「機械学習を学びたいビジネスパーソン」をペルソナとして進めます。
> まずユーザー登録をします。名前とメールアドレスを入れてアカウントを作成します。
> 次にオンボーディングで、自分のスキル・興味分野・学習目的を入力します。ここにもLLM導入の余地があると思いますが、今回はデータから抽出したskillsを検索して入力することになります。存在しないものについても、登録は可能です。
> ここで入力した情報が、このあとのAgentによるパーソナライズの基盤になります。登録が終わると、自分のプロファイルに情報が蓄積されます。

### 2-2. チャット — 自然言語でのコース発見 (1.5分)

- 画面: Chat (Exploreページ)
- クエリ例: "I want to learn machine learning for finance"
- 操作: Learning Advisorが意図を解釈し、パーソナライズされた結果を返す
- 補足: 裏ではHybrid Search (BM25 + Dense + RRF) が動いている
- 繋ぎ: 「チャットは対話的な探索用です。より深い分析には個別のAgentがあります」

> 原稿:
>
> 次にチャット画面です。自然言語で質問を入力すると、Learning Advisorがユーザーの意図を解釈して、関連するコースを返してくれます。
> 例えば「I want to learn machine learning for finance」と入れてみます。
> このように、プロフィール情報も加味した上でコースが推薦されます。
> チャットは対話的な探索向けの機能です。より深い分析には、個別のAgentがあります。

### 2-3. Analyze — 個別Agent実行 (1.5分)

- 画面: Analysisページ
- 操作: Skill Gap、Career、Learning Pathの各Agentを独立して実行
- 見せるもの: Agent毎の構造化された出力（チャットテキストではなく整形済み）
- 繋ぎ: 「では、裏側で何が起きているか見てみましょう」

> 原稿:
>
> こちらがAnalysisページです。ここでは自分のSkillと理想のスキル間のGap分析、CareerのPersonalな情報を加味した理想像の提案、Learning Pathの提案機能を個別に実行できます。
> ではSkill Gap Agentを動かしてみます。プロフィールの情報と、Web検索で取得した市場データをもとに、今の自分に足りないスキルを分析してくれます。
> Career AgentやLearning Path Agentも同様に、それぞれ構造化された出力を返します。チャットのような自由テキストではなく、整理された形式で結果が出るのが特徴です。
> なお、画面上の他の機能はモックアップの段階ですが、今後の実装の検討余地はあると考えています。
> では、裏側で何が起きているかを見てみましょう。

### 2-4. LangFuse — トレーシング & コスト可視化 (1分)

- 画面: LangFuseダッシュボード
- 見せるもの: Trace — どのAgentがどのToolを呼び、トークン数・コスト・レイテンシはいくらか
- 強調: すべてのLLM呼び出しが自動的に計測されている

> 原稿:
>
> LangFuseのダッシュボードを開きます。先ほどのリクエストのTraceがここに記録されています。
> このTraceを展開すると、どのAgentがどのToolを呼んだか、各ステップのトークン数・コスト・レイテンシが全て見えます。
> ポイントは、これを手動で仕込んだのではなく、OpenAI Agents SDKとLangFuseの統合により、すべてのLLM呼び出しが自動的に計測されている点です。今の精度はいいものではないかもしれませんが、改善にとってとてもいいことだと思います。
> [Metrics(LLM-as-a-Judge)とPrompt Versioningは画面を使って説明]

### 2-5. LangFuse — LLM-as-a-Judge & Promptバージョン管理 (1分)

- 画面: LangFuse（評価タブ / Prompt管理）
- 見せるもの: DeepEvalスコア (Relevancy, Faithfulness等) がTraceに紐づいている
- 見せるもの: Promptのバージョン管理 — Prompt変更の影響をTraceで追跡可能
- 繋ぎ: 「ユーザー向けと運用向けの両面をお見せしました。次にアーキテクチャを説明します」

> 原稿:
>
> 次に評価とPrompt管理です。DeepEvalというフレームワークでLLM-as-a-Judgeの評価を行っており、RelevancyやFaithfulnessといったスコアがTraceに紐づいて確認できます。
> また、LangFuseのPrompt管理機能を使って、Promptのバージョンを管理しています。Promptを変更した際に、どのバージョンでどういう結果が出たかをTraceから追跡できます。
> ここまでがユーザー向けと運用向けの両面です。次に、アーキテクチャの説明に移ります。
> [※ 実際の画面に合わせて修正予定]

---

## セクション 3: アーキテクチャ (5-6分)

### 3-1. Agent設計 — 設計判断 (1.5分)

- スライド: Agent Overview (要件 -> 実装のマッピング)
- 4つのLLM + 5つの共有Tool (OpenAI Agents SDK)
- 重要な設計判断: 要件上のCourse Retrieval AgentをAgentではなくToolとして実装
  - 理由: コース検索は「推論」ではなく「検索実行」→ LLMを挟む必要がない
- ハンドオフ: Learning Advisor -> Skill Gap / Career / Learning Path
- Agent毎のTool割り当て (LA/SGA/CA/LPD)
- Web Searchツール: Skill GapとCareerのAgentがリアルタイム市場データを取得

> 原稿:
>
> まずAgent設計の全体像です。本システムは4つのLLMと5つの共有ToolをOpenAI Agents SDKで構成しています。
> ユーザーのクエリはまずLearning Advisorが受け取ります。Learning Advisorはクエリの意図を判断し、必要に応じてSkill Gap、Career、Learning Pathの各専門Agentにハンドオフします。
> 1つ重要な設計判断として、要件上はCourse Retrieval Agentという5つ目のAgentがありましたが、これはAgentではなくToolとして実装しました。理由は、コース検索は「推論」ではなく「検索の実行」だからです。LLMを挟む必要がないので、Toolにした方がコストもレイテンシも下がります。
> また、Skill GapとCareerのAgentにはWeb Searchツールを割り当てており、リアルタイムの市場データを取得できるようにしています。
> このAgent構成の中で特に品質を左右するのが、コース検索を担うRAGの部分です。ここを詳しく説明します。


### 3-2. RAG — Indexingパイプライン (1分)

- スライド: RAG Indexing Pipeline
- フロー: CSV (6,645件) -> MongoDB -> OpenAI embedding (1,536次元) + BM25 sparse -> Qdrant
- 設計判断: チャンキングなし — コース説明文が短いので1コース = 1ドキュメント
- Dense入力: title + description
- BM25入力: title + description + skills

> 原稿:
>
> RAGのIndexingパイプラインです。元データはCourseraの6,645件のコースCSVです。まずこれをMongoDBに格納し、そこからQdrantに2種類のベクトルを生成して格納します。
>
> この「2種類のベクトル」が重要なので説明します。
>
> 1つ目がDense Vector、いわゆるEmbeddingです。OpenAIのtext-embedding-3-smallを使い、1,536次元のベクトルを生成します。
> Dense Vectorの思想は「意味の近さ」です。テキストを高次元の数値ベクトルに変換し、意味的に似たものがベクトル空間上で近くなります。例えば「機械学習」と「ディープラーニング」は文字列としては異なりますが、Embeddingでは近い位置に配置されます。
> 入力にはコースのtitleとdescriptionを使っています。つまり「このコースが何についてのコースか」という意味的な情報を捉えます。ただし、前述のとおりdescriptionの情報が少なくあまり広い特徴量は解釈できていないと思っています。
>
> 2つ目がBM25 Sparse Vectorです。これは伝統的なキーワード検索の考え方をベクトル化したものです。
> BM25の思想は「単語の重要度」です。あるドキュメントの中で、その単語がどれくらい頻繁に出現し、かつコーパス全体ではどれくらい珍しいかを数値化します。よくある単語は重みが低く、特徴的な単語は重みが高くなります。
> Sparseと呼ばれるのは、全語彙のうち実際に出現する単語だけが非ゼロの値を持つため、ベクトルのほとんどがゼロだからです。
> BM25の入力にはtitle、description、skillsを使っています。skillsを含めているのは、「Python」「TensorFlow」のような具体的なスキル名はEmbeddingでは捉えきれないことがあるためです。
>
> なお、チャンキングは行っていません。一般的なRAGではドキュメントを分割しますが、コース説明文は数行しかないため、1コース＝1ドキュメントで十分だと考えました。

### 3-3. RAG — Queryパイプライン & Hybrid Search (1.5分)

- スライド: RAG Query Pipeline
- フロー: クエリ -> Embedding -> Dense Search (weight 1.5) + BM25 Search (weight 1.2) -> RRF統合
- Payload Filter: level, min_rating, organization（両方の検索に適用）
- フォールバック連鎖: Hybrid -> BM25のみ -> MongoDB $text search -> エラーメッセージ
- Qdrantを選んだ理由: ネイティブHybrid Search、Payload Filter、Docker対応

> 原稿:
>
> 次に、検索時のQueryパイプラインです。ユーザーのクエリが来ると、Indexingと同じロジックで処理されます。
> クエリをOpenAI Embeddingで1,536次元のDense Vectorに変換し、同時にBM25でSparse Vectorも生成します。
>
> Indexingで作った2種類のベクトルに対して、それぞれ検索をかけます。
> Dense Searchは「意味的に近いコース」を探します。重みは1.5です。
> BM25 Searchは「キーワードが一致するコース」を探します。重みは1.2です。
> この2つの結果をRRF（Reciprocal Rank Fusion）で統合します。RRFは各検索結果の順位を使ってマージする手法で、スコアのスケールが異なる2つの検索結果を公平に統合できます。
>
> さらに、Payload Filterとしてlevel、min_rating、organizationでフィルタリングをかけています。これはDense SearchにもBM25 Searchにも両方適用されます。
>
> フォールバックも設計しています。Hybrid Searchが失敗した場合はBM25のみ、それもダメならMongoDBのテキスト検索、最終的にはエラーメッセージを返します。
>
> QdrantをベクトルDBに選んだ理由は、このHybrid Searchをネイティブでサポートしていること、Payload Filterが使えること、そしてDockerで簡単に動くことです。


### 3-4. データ分析 — なぜHybrid Searchか (時間があれば) (1分)

- スライド: Design Decision — Data Analysis -> Hybrid Search Design
- Embeddingが捉えるもの: トピック・分野（t-SNEで明確なクラスタ）
- Embeddingが捉えないもの: level, organization, skills, rating
- したがって: Dense Vectorで「何のコースか」+ BM25でスキル名 + Payload Filterでメタデータ
- データに基づいた設計であり、恣意的ではない

> 原稿:
>
> ここで、なぜHybrid Searchという設計にしたのか、データ分析の結果からお話しします。
> 1,000件のコースをEmbeddingしてt-SNEで可視化した結果、Embeddingが捉えられるものと捉えられないものが明確になりました。
>
> Embeddingが捉えられるのはトピック・分野です。t-SNEの可視化でデータサイエンス、ビジネス、プログラミングなど明確なクラスタが形成されました。
> 一方、Embeddingが捉えられないのは、difficulty level、organization、skills、ratingです。これらはベクトル空間上で全く分離しませんでした。skillをEmbedding空間に入れてみてもよかったのですが、講義自体を見る時間はなかったので、title + descriptionでどこまでできるかを見てみたかったからです。
>
> この分析結果から設計方針が決まりました。
> 「何のコースか」はDense Vectorのセマンティック検索で。「PythonやTensorFlow」のような具体的なスキル名はBM25のキーワード検索で。level、organization、ratingはPayload Filterで。
> つまり、Hybrid Searchは恣意的な選択ではなく、データ分析に基づいた設計判断です。

---

## セクション 4: クロージング — Strong Point & Next (1-2分)

### 4-1. このCapstoneのStrong Point (30秒)

- 専用スライドなし（口頭でまとめ）
- 3つのStrong Point:
  1. エンドツーエンドで動くPoC: Hybrid Search + Multi-Agent + Frontend
  2. 計測ファースト: LangFuseトレーシング + DeepEval評価フレームワーク
  3. スコープの規律: PoC/PoB/Prdの境界を定義し、「やらなかったこととその理由」をドキュメント化

> 原稿:
>
> 最後に、このCapstoneのStrong Pointを3つ挙げます。
> 1つ目は、エンドツーエンドで動くPoCであること。Hybrid Search、Multi-Agent、Frontendまで一気通貫で動作します。
> 2つ目は、計測ファーストの設計です。LangFuseによるトレーシングとDeepEvalによる評価フレームワークを先に作り、改善ループを回せる基盤を整えたことで、PoBへの取り残しを対応しやすくなります。
> 3つ目は、スコープの規律です。PoC・PoB・Prdの境界を定義し、「やらなかったこと」と「その理由」をドキュメントとして残しています。

### 4-2. 課題と学び (30秒)

- 最大の課題: Ground Truthの構築
  - 現在の38ケースはDBクエリから生成したもので、人間が検証した正解データではない
  - コース説明文が短すぎて、自信を持って「正解」とラベル付けできない
- 学び: 機能拡張より先にObservabilityと評価基盤を構築すべき

> 原稿:
>
> 最大の課題はGround Truthの構築です。現在38ケースのテストデータがありますが、これはDBクエリから機械的に生成したもので、人間が検証した正解データではありません。
> コース説明文が短すぎて、開発者自身でも「これが正解」と自信を持って言えないのが現状です。
> ここから得た学びは、機能を増やす前にObservabilityと評価基盤を先に作るべきだということです。計測できなければ改善もできません。

### 4-3. Next Action — PoB & Prd ロードマップ (30秒)

- PoB:
  - KPI定義 (エンゲージメント、推薦受容率)
  - ROI試算 (APIコスト vs. 提供価値)
  - 実ユーザーフィードバックからGround Truth構築
  - コスト最適化のためのModel Routing
- Prd:
  - Azureゼロトラスト環境へのデプロイ
  - 学習分析ダッシュボード
  - 協調フィルタリングのためのA2A通信
- 締めの一言: 「PoCで技術の実現可能性は証明しました。次のステップはビジネス価値の証明です。」

> 原稿:
>
> Next Actionです。PoBフェーズではKPIの定義、ROI試算、そして実ユーザーのフィードバックからGround Truthを構築します。また、コスト最適化のためにModel Routingも導入したいと考えています。
> Prdフェーズでは、Azureのゼロトラスト環境へのデプロイ、学習分析ダッシュボード、A2A通信による協調フィルタリングなどを視野に入れています。
> PoCで技術の実現可能性は証明しました。次のステップは、ビジネス価値の証明です。
> 以上で発表を終わります。ご質問があればお願いします。

---

## 付録: Q&A想定問答

| 質問 | 回答のポイント |
|------|--------------|
| なぜMongoDB + Qdrantの2つ？ | MongoDBはCRUD/認証/テキストフォールバック用、Qdrantはネイティブhybrid search用。関心の分離。 |
| なぜチャンキングしない？ | コース説明文は数文しかない。1コース = 1ドキュメントで十分。 |
| なぜRerankerを無効化した？ | Cross-encoderで評価済み — コース説明文が短く類似しすぎていて品質向上が見られなかった。データに基づく判断。 |
| OpenAI障害時の対応は？ | Circuit Breaker (3回失敗 -> 30秒open)、ローカルMiniLM-L6-v2 (384次元)へフォールバック、次にBM25のみ、最後にMongoDB $text。 |
| 1クエリあたりのコストは？ | LangFuseで追跡。(ダッシュボードの実数値を見せる) |
| なぜLangChainではなくOpenAI Agents SDK？ | 軽量、抽象化のオーバーヘッドが少ない、ハンドオフロジックを直接制御できる。 |
| Ground Truthはどう作った？ | DBクエリで期待コースを抽出 + 手動でルーティングラベルを付与。38ケース。限界は認識済み — 人間による検証が必要。 |
| IR metricsが1K→6.6Kで大幅に下がった理由は？ | 2つの問題が重なっている。第1に方式の問題：Precision@K/Recall@KがGTタイトルとの文字列完全一致で判定しているため、GTにない関連コースが全て「不正解」扱い（Precision@5: 0.61→0.16）。DeepEvalのContextualPrecision/Recall（LLM-as-Judge）を使うべきだった。第2にGTそのものの正当性：GTはDBクエリから機械的に生成しており「ユーザーにとって本当に良い推薦か」の人間の判断が入っていない。LLM-as-Judgeに変えれば数値はより正確になるが、GTの根拠が薄い以上、いい数値が出てもUXとの相関は保証されない。本当の検証には実ユーザーの評価が必要。 |
| なぜDeepEvalのContextualPrecision/Recallを使わなかった？ | 使うべきだった。ただし問題は半分しか解決しない。文字列一致→LLM-as-Judgeで数値の正確性は上がるが、GT自体が人間の「これが良い推薦」という判断に基づいていないため、メトリクスの改善がUX改善と相関する保証がない。完全な解決は：(1) LLM-as-Judgeで計測精度を上げる + (2) 実ユーザーのフィードバックからGTを構築し、メトリクスとUXを紐づける。両方PoB課題。 |
| RRF重み [BM25=1.2, Dense=1.5] の根拠は？ | Denseに高めの重みを付けたのは、セマンティック検索の方がユーザーの意図を捉えやすいため。BM25はスキル名など具体語のカバーが役割。経験的初期値であり体系的チューニングはしていない。Grid SearchはPoB課題。 |
| DeepEvalのthreshold 0.5は低くない？ | PoC段階では壊滅的に悪い応答を検出するベースライン。GTが不完全な現状で高い閾値を設定すると偽陰性（良い応答が不合格）が増える。実ユーザーデータでGT改善後に段階的に引き上げる。 |
| PoCなのになぜマイクロサービス？ | 評価チェックリストに「Microservices Representation」が明記。加えてAI ServiceとCourse Serviceは依存ライブラリが大きく異なり（AI: openai-agents, DeepEval / Course: Motor, pymongo）、コンテナ分離の方がビルドが速い。 |
| Prompt Injectionの7つのregexで十分？ | Regexは第1防衛線（"ignore previous instructions"等の典型パターン検出）。Topic relevanceチェック（150+キーワード + LLMフォールバック）が第2防衛線。PoB/Prdでは専用分類モデル（Rebuff, Lakera Guard）を検討。 |
| ローカルMiniLMにフォールバックした時の品質は？ | 次元が1/4（1536→384）なので品質は劣化する。フォールバックの目的は完全停止の防止であり品質維持ではない。フォールバック連鎖（Hybrid→BM25のみ→MongoDB $text）は品質と可用性のトレードオフ。 |
| OpenAI一本でベンダーロックインは？ | PoCではエコシステム一貫性を優先。ロックインリスクは認識済み。HuggingFaceのEmbeddingフォールバックは実装済み。PoBのModel Routingでマルチベンダー対応を計画。 |
| OpenAI Agents SDKのhandoffはどう動く？ | `handoff()`は現在のAgentの実行を終了し、会話コンテキストを別Agentに渡す。Runner（実行ループ）が次のAgentのプロンプトとToolセットに切り替える。HTTP通信ではなくプロセス内の関数呼び出し。 |
