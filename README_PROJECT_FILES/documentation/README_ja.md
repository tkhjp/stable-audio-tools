# オーディオデータセット収集・処理パイプライン

## プロジェクト概要

このプロジェクトは、**大規模なオーディオデータセットの収集、処理、分析を行うための総合的なパイプライン**です。複数の日本語・英語音源から音声データを統合し、CLAP（Contrastive Language-Audio Pre-training）フレームワークを用いた音声-テキスト生成モデルのトレーニングと評価を目的としています。

### 主な機能

- 🎵 **複数ソースからの音声収集**: Freesound、OtoLogic、効果音ラボ（Taira Komori）からの自動ダウンロード
- 🌐 **日英翻訳**: 日本語メタデータの英語翻訳とAI生成説明文の作成
- 🔍 **セマンティック分析**: T5埋め込みを用いた類似プロンプトの検出
- 📊 **CLAPモデル評価**: 音声-テキスト類似度、Fréchet Distance、KLダイバージェンスの計算
- 🗂️ **データ整理**: 重複除去、リネーム、メタデータマッピングの自動化

---

## データソース統計

| プラットフォーム | ファイル数 | ステータス | 主な情報 |
|----------|-------|--------|----------|
| **Freesound** | 420,543 | マッピング完了 | 個別ファイル、豊富なメタデータ、各種CCライセンス |
| **効果音ラボ (Taira Komori)** | 5,466 | マッピング完了 | 直接MP3ダウンロード、カテゴリ分類済み |
| **OtoLogic** | 465 | ZIPマッピング完了 | CC BY 4.0、ZIPパッケージ、日本語メタデータ |
| **FreeAudio** | 複数ZIP | 処理・展開済み | 効果音ラボコレクション由来 |
| **CLAPデータセット** | 89,370+ | Train/Test/Val分割済み | AudioCaptions（YouTube由来） |
| **合計** | 426,474+ | 統合済み | 全ソース合計 |

### ストレージ概要
- **audio/** - 1.9 GB（連番リネーム済み最終音声）
- **freeaudio/** - 3.0 GB（ZIPコレクション）
- **clips_oversample/** - 152 MB（オーバーサンプリング済みクリップ）
- **oversample/** - 2.4 GB（オーバーサンプリング済みトレーニングデータ）

---

## プロジェクト構成

### 1. データ収集レイヤー

複数のプラットフォームから音声ファイルをスクレイピング・ダウンロードします。

**主要スクリプト:**

- **`otologic_downloader_complete.py`** (628行)
  - OtoLogicからCC BY 4.0ライセンスの音声をダウンロード
  - メタデータ自動抽出、日本語テキスト処理

- **`freeaudio_annotator.py`** (374行)
  - FreeAudio ZIPコレクションの処理
  - Webスクレイピングによる説明文取得
  - AIプロンプト自動生成

- **`test_tairakomori_scraping.py`** (98行)
  - 効果音ラボWebサイトのスクレイピングテスト

### 2. メタデータ・マッピングレイヤー

ファイル名とURLの包括的なマッピングを作成します。

**主要スクリプト:**

- **`generate_freesound_mapping.py`** (162行)
  - metadata.jsonlからFreesoundメタデータとURLを抽出

- **`generate_tairakomori_mapping.py`** (461行)
  - Webスクレイピング + ローカルマッピング生成

- **`generate_otologic_zip_mapping_accurate.py`** (342行)
  - 個別MP3ファイルと含有ZIPファイルのマッピング

- **`fix_otologic_mapping_accurate.py`** (309行)
  - OtoLogicマッピングを動作するZIP URLに修正

**出力CSVファイル（主要マッピング）:**

1. **`freesound_filename_url_mapping.csv`** (262 MB) - 420,543ファイル、メタデータ付き
2. **`tairakomori_filename_url_mapping.csv`** (1.1 MB) - 5,466ファイル、カテゴリ付き
3. **`otologic_mp3_to_zip_accurate.csv`** (161 KB) - 465件の検証済みZIPマッピング

### 3. データ処理・翻訳レイヤー

日本語メタデータを英語に変換し、説明文を生成します。

**主要スクリプト:**

- **`translate_japanese.py`** (267行)
  - OpenAI GPTを使用した日本語オノマトペ・名称のバッチ翻訳

- **`freeaudio_prompt_generator.py`** (378行)
  - ファイルパスとOpenAI APIから英語説明文を生成

- **`otologic_prompt_generator_final.py`** (550行)
  - OtoLogicメタデータ抽出、キーワード整形、プロンプト生成

**翻訳出力:**

- **`translated_onomatopoeia.csv`** - 日本語擬音語 → 英語等価表現
- **`translated_names.csv`** - 日本語名称 → 英語名称
- **`freeaudio_prompts.csv`** - FreeAudioコレクション用生成説明文
- **`otologic_prompts.jsonl`** - OtoLogic音声用JSONL形式プロンプト

### 4. ファイル整理・重複除去レイヤー

音声ファイルをクリーニング、整理し、トレーニングデータセットに統合します。

**主要スクリプト:**

- **`copy_files_and_generate_csv.py`** (202行)
  - ファイルコピーと連番マッピング作成

- **`remove_preview_and_renumber.py`** (307行)
  - プレビューファイル除去と連番振り直し

- **`remove_duplicates_and_renumber.py`** (342行)
  - 重複除去とクリーンマッピング作成

- **`rename_from_csv_fixed.py`** (297行)
  - CSVマッピングに基づくファイル名変更（改良版）

- **`extract_freeaudio_zips.py`** (94行)
  - ZIPファイルのフォルダ展開

**出力マッピング:**

- **`sequential_audio_mapping_final.csv`** (740 KB) - 最終クリーニング済みマッピング（重複除去・プレビュー除去完了）

### 5. 分析・評価レイヤー

音声特性の分析とモデルパフォーマンスの評価を行います。

**主要スクリプト:**

- **`analyze_freeaudio_durations.py`** (199行)
  - 音声時間分析とプロット生成

- **`analyze_long_audio_durations.py`** (217行)
  - 長時間音声ファイルの識別

- **`analyze_preview_durations.py`** (100行)
  - プレビューファイル時間分析

**出力:**

- **`freeaudio_duration_analysis.csv`** (128 KB) - 時間統計データ
- **`long_audio_files_over_5.0s.csv`** - 5秒超ファイルリスト

### 6. 類似度・セマンティック分析レイヤー

意味的に類似したプロンプトを検出し、テキスト-音声アライメントを評価します。

**主要スクリプト（T5評価）:**

- **`t5_eval/t5_similarity_finder.py`** (80+行)
  - T5埋め込みベースの類似度検索

- **`t5_eval/analyze_csv_similarity.py`**
  - 類似度分布の分析

- **`full_dataset_similarity.py`** (273行)
  - 全データセット類似度分析（再計算機能含む）

- **`get_very_high_ids.py`** (263行)
  - 高類似度プロンプトIDの抽出

**主要ファイル:**

- **`prompts_update.jsonl`** (425,294行) - 425Kプロンプト（ID付き）
- **`before_ft_with_similarities.csv`** - T5類似度スコア
- **`before_ft_with_very_high_ids.csv`** - 高類似度グルーピング

### 7. CLAPトレーニング・評価（clap/ディレクトリ）

音声-テキストモデルのトレーニングと評価を行います。

**主要ファイル:**

- **`cal_metrics_improved.py`** (43K行) - 包括的音声評価システム
  - CLAPスコア（テキスト-音声類似度）計算
  - Fréchet Distance（分布類似度）計算
  - KLダイバージェンス（クラス分布）計算

- **`combine_and_find_similar.py`** - train/test/valデータセット結合
- **`find_similar_captions.py`** - 意味的に類似したキャプション検索
- **`config_example.json`** - 設定テンプレート

**トレーニングデータ:**

- **`train.csv`** (6 MB) - 音声-テキストペアのトレーニングセット
- **`test.csv`** (388 KB) - テストセット
- **`val.csv`** (166 KB) - 検証セット
- **`combined_dataset.csv`** (7.3 MB) - 統合データセット（89K行）
- **`eval_prompts.csv`** (11 KB) - マッチしたキャプション付き評価プロンプト

**CSVカラム形式:**
```csv
audiocap_id,youtube_id,start_time,caption
89370,pgLXVFvo5GI,27,"a woman laughs and speaks while birds vocalize..."
```

### 8. ファインチューニング・メトリクス（ft/ディレクトリ）

モデルファインチューニングの進捗と評価メトリクスを追跡します。

**主要ファイル:**

- **`all_metrics.csv`** - 統合トレーニングメトリクス（全実行履歴）
- **`tf_analysis.ipynb`** - TensorFlowメトリクス分析用Jupyterノートブック

---

## ワークフロー

### フェーズ1: データ収集・マッピング

```
Webスクレイピング (otologic/tairakomori/freesound)
    ↓
メタデータ抽出・マッピング生成
    ↓
ファイル名→URL CSVファイル作成
    ↓
URL検証・ダウンロードテスト
```

### フェーズ2: メタデータ処理・翻訳

```
生メタデータ（日本語）
    ↓
ZIPメタデータファイル + Webスクレイピングから抽出
    ↓
日本語→英語翻訳（OpenAI GPT）
    ↓
AI説明文生成（OpenAI GPT-4o-mini）
    ↓
CSV・JSONL形式で保存
```

### フェーズ3: 音声整理

```
音声ファイル（混在ソース）
    ↓
統一ディレクトリへコピー/展開
    ↓
重複検出・除去
    ↓
プレビューファイル除去
    ↓
連番リネーム（sound_1.mp3, sound_2.mp3...）
    ↓
連番マッピングCSV生成
```

### フェーズ4: 分析・品質管理

```
音声時間分析
    ↓
長時間/短時間サンプル識別
    ↓
統計計算
    ↓
時間分析レポート生成
```

### フェーズ5: セマンティック分析

```
JSONLプロンプト読み込み（425K件）
    ↓
T5埋め込み生成
    ↓
コサイン類似度計算
    ↓
類似プロンプト識別
    ↓
類似度閾値レポート作成
```

### フェーズ6: モデルトレーニング（CLAP）

```
Train/Test/Val分割準備
    ↓
音声-キャプションペアマッチング
    ↓
類似キャプション検索（Sentence Transformers）
    ↓
eval_prompts.csv作成
    ↓
CLAPモデルトレーニング
    ↓
メトリクス計算:
    - CLAPスコア（テキスト-音声類似度）
    - Fréchet Distance（分布）
    - KLダイバージェンス（クラス分布）
```

---

## データ形式例

### 連番音声マッピング
```csv
sequential_number,sequential_filename,original_filename,source,duration_seconds
1,sound_1.mp3,トライアングル03-1(長).mp3,otologic_sounds_smart,16.52
2,sound_2.mp3,ビブラスラップ01-7(低　短　リバーブ).mp3,otologic_sounds_smart,5.04
```

### Freesoundマッピング
```csv
sound_id,filename,freesound_url,preview_hq_mp3,username,tags,category,duration_seconds
```

### OtoLogic ZIPマッピング
```csv
mp3_filename,sound_effect_title,category,zip_download_url,zip_filename
骨折01-3(リバーブ).mp3,Fracture,Sound Effects,https://otologic.jp/sounds/se/mp3-zip/Fracture02-mp3.zip,Fracture02-mp3.zip
```

### アノテーションデータ
```csv
original_path,english_filename,name,onomatopoeia,duration,file_name,prompt_english
otologic_sounds_smart/Instruments/...mp3,bright_triangle_sound.mp3,Chime,ding,5.0,sound_1.mp3,bright triangle sound...
```

### プロンプトJSONL（425,294件）
```json
{"id": 793855, "prompt": "snare hits cracks claps rimshots all original produced by CVLTIV8R"}
{"id": 793856, "prompt": "electronic drum machine kick bass deep sub wobble"}
```

---

## 技術スタック

### コアライブラリ

- **データ処理**: pandas, numpy, scipy
- **音声処理**: mutagen, librosa, soundfile, torchaudio
- **機械学習/埋め込み**: sentence-transformers, torch, transformers
- **Webスクレイピング**: requests, beautifulsoup4, lxml
- **AI/API**: OpenAI GPT (gpt-4o-mini, 言語モデル)
- **評価**: scikit-learn, einops, tqdm
- **ロギング**: Python loggingモジュール

### オプションコンポーネント

- **CLAPモデル**: laion_clap（音声-テキスト類似度用）
- **音声埋め込み**: openl3（Fréchet Distance用）
- **音声分類**: PaSST (hear21passt)
- **音声生成**: stable-audio-tools（拡散モデル）

---

## セットアップとインストール

### 基本要件

```bash
# Python 3.8以上推奨
python --version

# 基本的な依存関係のインストール
pip install pandas numpy scipy
pip install mutagen librosa soundfile
pip install requests beautifulsoup4 lxml
pip install sentence-transformers transformers
pip install openai tqdm
```

### プラットフォーム別要件

**OtoLogic用:**
```bash
pip install -r requirements_otologic.txt
```

**効果音ラボ（Taira Komori）用:**
```bash
pip install -r requirements_tairakomori.txt
```

**FreeAudio用:**
```bash
pip install -r requirements_freeaudio.txt
```

### 環境変数

OpenAI API使用時は環境変数を設定:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

---

## 使用方法

### 1. データ収集

**OtoLogicからのダウンロード:**
```bash
python otologic_downloader_complete.py
```

**効果音ラボマッピング生成:**
```bash
python generate_tairakomori_mapping.py
```

**Freesoundマッピング生成:**
```bash
python generate_freesound_mapping.py
```

### 2. メタデータ処理

**日本語翻訳:**
```bash
python translate_japanese.py
```

**OtoLogic用AIプロンプト生成:**
```bash
python otologic_prompt_generator_final.py
```

**FreeAudio用AIプロンプト生成:**
```bash
python freeaudio_prompt_generator.py
```

### 3. ファイル整理

**重複除去とリネーム:**
```bash
python remove_duplicates_and_renumber.py
```

**プレビュー除去:**
```bash
python remove_preview_and_renumber.py
```

**CSVベースのリネーム:**
```bash
python rename_from_csv_fixed.py
```

### 4. 分析

**時間分析:**
```bash
python analyze_freeaudio_durations.py
python analyze_long_audio_durations.py
```

**T5類似度分析:**
```bash
cd t5_eval
python t5_similarity_finder.py --input prompts_update.jsonl --threshold 0.9
```

### 5. CLAP評価

**メトリクス計算:**
```bash
cd clap
python cal_metrics_improved.py --config config_example.json
```

---

## プロジェクト統計

### コードメトリクス
- **Pythonコード総行数**: 10,078行（メインスクリプトのみ）
- **JSONL総レコード数**: 425,294プロンプト
- **CSV総ファイル数**: 40以上のデータ/マッピングファイル
- **Jupyterノートブック数**: 10（分析、アノテーション、オーバーサンプリング）

### データメトリクス
- **マッピング済み総音声ファイル数**: 426,474以上
- **総ストレージ（ローカル）**: 約11.3 GB
- **トレーニングデータセット**: 89,370音声-テキストペア（CLAP）
- **最大CSVファイル**: freesound_filename_url_mapping.csv (262 MB)

### 言語別カバレッジ
- **英語**: Freesound（420K）、CLAPアノテーション
- **日本語**: OtoLogic（465）、効果音ラボ（5.4K）、FreeAudioコレクション
- **バイリンガル**: 翻訳付きマッピング

---

## 主要な機能とユースケース

### ユースケース1: データパイプライン構築

1. マッピング生成スクリプトを実行してURLデータベース作成
2. 検証スクリプトでURL検証
3. アノテーション/スクレイピングでメタデータ強化
4. 日本語説明文を翻訳
5. AIプロンプト生成

### ユースケース2: 音声データセット準備

1. ソースから音声ファイルをコピー/展開
2. 重複とプレビューを除去
3. ファイルを連番でリネーム
4. 最終マッピングCSV生成
5. 時間分布分析

### ユースケース3: モデルトレーニング

1. train/test/valデータセット結合
2. 音声用の類似キャプション検索
3. 評価プロンプト作成
4. CLAPモデル読み込み
5. 類似度メトリクス計算
6. モデルパフォーマンス評価

### ユースケース4: 品質分析

1. T5でプロンプト類似度分析
2. 準重複プロンプト識別
3. 類似度閾値レポート生成
4. 高類似度グルーピング出力
5. データセットクリーンアップ支援

---

## 既存ドキュメント

プロジェクトには複数の詳細ドキュメントが含まれています：

1. **[README.md](README.md)** - T5類似度ファインダーのドキュメント
2. **[README_audio_mappings_complete.md](README_audio_mappings_complete.md)** - 完全マッピングシステムドキュメント
3. **[README_otologic.md](README_otologic.md)** - OtoLogicダウンローダードキュメント
4. **[README_freeaudio.md](README_freeaudio.md)** - FreeAudioアノテータードキュメント
5. **[README_tairakomori_mapping.md](README_tairakomori_mapping.md)** - 効果音ラボシステムドキュメント
6. **[clap/README_improvements.md](clap/README_improvements.md)** - CLAP評価改善ドキュメント

---

## ライセンス情報

### 音声ソースライセンス

- **OtoLogic**: CC BY 4.0 - 商用利用可、帰属表示必須
- **効果音ラボ（Taira Komori）**: サイトの利用規約に準拠
- **Freesound**: 個別ファイルごとに異なるCCライセンス（メタデータに記載）

### コードライセンス

このプロジェクトのコードは、各スクリプトに記載されたライセンスに従います。

---

## トラブルシューティング

### よくある問題

**1. OpenAI API エラー**
```python
# 環境変数が設定されているか確認
echo $OPENAI_API_KEY

# または.envファイルに設定
OPENAI_API_KEY=your-key-here
```

**2. 文字エンコーディングエラー（日本語処理時）**
```python
# ファイル読み込み時にエンコーディング指定
pd.read_csv('file.csv', encoding='utf-8')
```

**3. メモリ不足（大規模データセット処理時）**
```python
# チャンク処理を使用
for chunk in pd.read_csv('large_file.csv', chunksize=10000):
    process(chunk)
```

**4. ダウンロード失敗**
```bash
# ログファイルを確認
cat otologic_downloader.log
cat extract_freeaudio_zips.log
```

---

## ファイル管理と重複について

### 削除可能な旧バージョンファイル

プロジェクトの反復開発により、いくつかの重複ファイルが存在します。以下は安全に削除可能な旧バージョンです：

#### 🗑️ 削除推奨：Pythonスクリプト（旧バージョン）

| 削除可能 | 保持版 | 理由 |
|---------|--------|------|
| `fix_otologic_mapping.py` | `fix_otologic_mapping_accurate.py` | 実際のメタデータ使用版 |
| `generate_otologic_zip_mapping.py` | `generate_otologic_zip_mapping_accurate.py` | HTML解析の精度向上版 |
| `rename_from_csv.py` | `rename_from_csv_fixed.py` | ZIP構造サポート改善版 |
| `generate_english_otologic_mapping.py` | `generate_english_otologic_corrected.py` | HTML解析の正確性向上版 |

#### 🗑️ 削除推奨：CSVマッピングファイル（中間バージョン）

| 削除可能 | 保持版 | 削減容量 |
|---------|--------|----------|
| `english_otologic_mapping.csv` (4.2 MB) | `english_otologic_final.csv` | 最終完成版を保持 |
| `english_otologic_simple.csv` (1.4 MB) | `english_otologic_final.csv` | 最終完成版を保持 |
| `english_otologic_corrected.csv` (957 KB) | `english_otologic_final.csv` | 最終完成版を保持 |
| `english_otologic_complete.csv` (1.0 MB) | `english_otologic_final.csv` | 最終完成版を保持 |
| `sequential_audio_mapping.csv` (776 KB) | `sequential_audio_mapping_final.csv` | 最終版を保持 |
| `sequential_audio_mapping_no_preview.csv` (755 KB) | `sequential_audio_mapping_final.csv` | 最終版を保持 |
| `all_metrics_0723.csv` | `all_metrics.csv` | 統合版に含まれる |
| `all_metrics_0727.csv` | `all_metrics.csv` | 統合版に含まれる |

**推定削減容量**: 約30-35 MB

### 保持すべきファイル（重複ではない）

以下は似た名前ですが、異なる目的で使用されるため**両方とも保持**が必要です：

#### ✅ 両方必要：連続処理スクリプト

- `remove_preview_and_renumber.py` - プレビューファイル除去専用
- `remove_duplicates_and_renumber.py` - 重複ファイル除去専用
- これらは異なるステップで使用される独立したツール

#### ✅ 両方必要：データソース別スクリプト

- `otologic_downloader_complete.py` - OtoLogic専用
- `otologic_downloader_streaming.py` - メモリ効率化版（大規模ダウンロード用）
- 用途に応じて使い分ける

#### ✅ 両方必要：分析スクリプト

- `analyze_freeaudio_durations.py` - FreeAudio特化
- `analyze_long_audio_durations.py` - 長時間音声特化
- `analyze_preview_durations.py` - プレビューファイル特化

---

## 今後の改善点

### 計画中の機能

- [ ] より高度な重複検出アルゴリズム
- [ ] リアルタイム音声分析ダッシュボード
- [ ] 自動品質チェックパイプライン
- [ ] 多言語サポート拡張
- [ ] CLAPモデル自動ハイパーパラメータチューニング

### 最適化の機会

- 並列ダウンロード処理の実装
- データベースバックエンド統合（SQLite/PostgreSQL）
- Webベース管理インターフェース
- Docker化による環境の標準化

---

## 貢献ガイドライン

プロジェクトへの貢献を歓迎します：

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを開く

---

## 連絡先・サポート

問題が発生した場合や質問がある場合は、GitHubのIssuesセクションで報告してください。

---

## 謝辞

このプロジェクトは以下のオープンソースライブラリとデータソースに依存しています：

- **Freesound** - 大規模コミュニティ音声データベース
- **OtoLogic** - 高品質CC BY 4.0効果音
- **効果音ラボ（Taira Komori）** - 日本語カテゴリ分類済み効果音
- **OpenAI** - GPTベースの翻訳・説明文生成
- **Hugging Face** - Transformers、Sentence Transformers
- **LAION** - CLAPモデルフレームワーク

---

## プロジェクトサマリー

このプロジェクトは、以下を実現する高度な**音声データセットエンジニアリングシステム**です：

1. ✅ **統合** - 複数ソース（Freesound、OtoLogic、効果音ラボ）から音声を集約
2. ✅ **強化** - 翻訳とAI説明文生成でメタデータを充実化
3. ✅ **整理** - クリーンで重複のないトレーニングデータセットに編成
4. ✅ **分析** - T5埋め込みを用いたテキスト説明のセマンティック類似度分析
5. ✅ **トレーニング** - CLAPフレームワークを使用した音声-テキスト生成モデルの訓練
6. ✅ **評価** - 複数メトリクス（CLAP、FD、KLダイバージェンス）によるモデル性能評価

国際的なソースから約**426,000音声ファイル**を豊富なメタデータと共に統合し、音声AI アプリケーション用のトレーニング対応データセットを作成する、高度なデータエンジニアリング実践を示しています。

---

**最終更新**: 2025年11月9日
**バージョン**: 1.0.0
