# 効果音生成モデル ファインチューニング 詳細TODO計画書

**プロジェクト**: CASIO向け効果音生成モデルの品質改善
**フレームワーク**: stable-audio-tools (Stability AI)
**作成日**: 2025-11-11
**担当**: 尾崎様、石原様、チーム

---

## 目次

1. [データ収集・準備](#1-データ収集準備)
2. [モデル学習計画](#2-モデル学習計画)
3. [モニタリング・評価](#3-モニタリング評価)
4. [不具合調査と改善策検討](#4-不具合調査と改善策検討)
5. [提案準備](#5-提案準備)
6. [関連ファイル一覧](#6-関連ファイル一覧)

---

## 1. データ収集・準備

### 1.1 新規音声データの収集

**目的**: 学校のチャイムなど、強化したい特定の効果音データを収集

#### タスク
- [ ] **1.1.1 対象効果音のリストアップ**
  - 学校のチャイム
  - その他CASIO様が要望する特定効果音
  - 各カテゴリで必要な音声数の見積もり（最低10～50サンプル/カテゴリを推奨）

- [ ] **1.1.2 音声データソースの選定**
  - 録音オプション: 自社で録音、専門音響スタジオ委託
  - 購入オプション: 商用音声ライブラリ（AudioJungle、Soundly等）
  - ライセンス確認: 商用利用・AI学習への利用許諾を確認

- [ ] **1.1.3 音声データ取得**
  - **フォーマット要件**: WAV形式、44.1kHz以上（可能なら48kHz）、16bit以上、ステレオまたはモノラル
  - **品質要件**: クリーンな音源（ノイズ・クリッピングなし）
  - ファイル命名規則: `{category}_{id}_hq.wav`（例: `school_bell_001_hq.wav`）

#### 関連ファイル
- **保存先**: `/home/casio/localssd/new_sfx_data/` （新規作成推奨）
- **参考スクリプト**: [README_PROJECT_FILES/scripts/copy_files_and_generate_csv.py](README_PROJECT_FILES/scripts/copy_files_and_generate_csv.py)

---

### 1.2 汎用音声データの収集

**目的**: 犬の鳴き声、水音など一般的な効果音データを収集し、既存機能の維持を図る

#### タスク
- [ ] **1.2.1 データソースの選定**
  - **推奨**: Freesound.org（CC0/CC-BYライセンス）
  - **有償オプション**: AudioSparx、Sounddogs、BBC Sound Effects Library
  - ライセンスと使用条件の確認

- [ ] **1.2.2 カテゴリ別データ収集**
  - 動物（犬、猫、鳥等）
  - 自然音（水、風、雨、雷等）
  - 日常音（ドア、足音、車等）
  - 楽器音（ドラム、ピアノ、ギター等）
  - 各カテゴリで50～200サンプルを目安

- [ ] **1.2.3 音声データダウンロードと整理**
  - **フォーマット要件**: WAV形式、44.1kHz以上、16bit以上
  - Freesoundからの一括ダウンロードスクリプト実行

#### 関連ファイル
- **既存データ**: [/home/casio/localssd/freesound_audio/](/home/casio/localssd/freesound_audio/)
- **ダウンロードスクリプト**: [README_PROJECT_FILES/scripts/freesound_download.py](README_PROJECT_FILES/scripts/freesound_download.py)
- **展開スクリプト**: [README_PROJECT_FILES/scripts/extract_freeaudio_zips.py](README_PROJECT_FILES/scripts/extract_freeaudio_zips.py)

---

### 1.3 データフォーマット統一

**目的**: MP3形式の音声をWAV形式に変換し、高周波数成分の損失を防ぐ

#### タスク
- [ ] **1.3.1 既存データのフォーマット調査**
  - 現在のデータセット内のMP3ファイル数を特定
  - MP3ファイルのビットレート・サンプルレート確認
  ```bash
  # MP3ファイルの検索
  find /home/casio/localssd/freesound_audio/ -name "*.mp3" | wc -l
  ```

- [ ] **1.3.2 MP3→WAV変換実施**
  - **推奨ツール**: ffmpeg、SoX
  - **コマンド例**:
  ```bash
  # 単一ファイル変換
  ffmpeg -i input.mp3 -ar 44100 -ac 2 -sample_fmt s16 output.wav

  # バッチ変換
  for file in *.mp3; do
    ffmpeg -i "$file" -ar 44100 -ac 2 -sample_fmt s16 "${file%.mp3}.wav"
  done
  ```

- [ ] **1.3.3 変換後の品質確認**
  - スペクトログラム比較（Audacity、librosa等で確認）
  - 高周波成分（10kHz以上）の保持確認

- [ ] **1.3.4 理想的対応: 元データの再取得**
  - 可能な限りMP3ではなく、元のWAV/FLAC形式で再取得
  - Freesoundでは元フォーマットでダウンロード可能

#### 注意事項
> **重要**: MP3からWAVへの変換では失われた高周波数成分は復元されません。理想的には元のロスレス音源を入手してください。

#### 関連ファイル
- **参考**: [README_ja.md](README_ja.md) - データフォーマットに関する記載
- **データセット設定**: [configs/dataset_config.json](configs/dataset_config.json)

---

### 1.4 データセットのバランス調整

**目的**: 新規データと既存データを適切な比率で混合し、破滅的忘却を防ぐ

#### タスク
- [ ] **1.4.1 データ量の把握**
  - 新規データ: 学校チャイム等の特定効果音の総サンプル数
  - 既存データ: Freesound等の汎用効果音の総サンプル数
  - カテゴリごとのデータ分布を記録

- [ ] **1.4.2 混合比率の決定**
  - **推奨比率**: 新規データ : 既存データ = 1:1～1:2
  - 新規データが少ない場合はデータ拡張を検討（ピッチシフト、時間伸縮等）
  - **重要**: 既存汎用データを過度に削減しない（破滅的忘却のリスク増大）

- [ ] **1.4.3 カテゴリバランスの調整**
  - 各カテゴリ（動物、自然音、日常音等）のサンプル数を均等化
  - 極端に多いカテゴリはサブサンプリング、少ないカテゴリはデータ拡張

- [ ] **1.4.4 統合データセットの作成**
  - 新規データと既存データを単一ディレクトリに統合
  - または、dataset_config.jsonで複数datasetsを指定（推奨）

#### データ拡張の例
```python
# Pitchシフト、タイムストレッチの例（librosa使用）
import librosa
import soundfile as sf

# ピッチシフト（半音単位）
y, sr = librosa.load('input.wav', sr=44100)
y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=2)
sf.write('output_pitch_up.wav', y_shifted, sr)

# タイムストレッチ（速度変更）
y_stretched = librosa.effects.time_stretch(y, rate=1.1)
sf.write('output_stretched.wav', y_stretched, sr)
```

#### 関連ファイル
- **データセット設定**: [configs/dataset_config.json](configs/dataset_config.json)
- **データ統計スクリプト**: `README_PROJECT_FILES/scripts/analyze_dataset_balance.py`（要作成）

---

### 1.5 メタデータとラベル整理

**目的**: 収集した音声に適切なプロンプトや説明を付与し、学習データセットとして整理

#### タスク
- [ ] **1.5.1 プロンプト作成方針の策定**
  - **形式**: 短文記述（10～50単語程度）
  - **内容**: 音の種類、特徴、シーン、感情等
  - **例**:
    - 新規音: `"学校のチャイムが鳴る音、明るく澄んだ鐘の音"` / `"School bell chime, clear and bright tone"`
    - 汎用音: `"犬が遠吠えする音、中型犬、屋外"` / `"Dog howling, medium-sized dog, outdoor"`

- [ ] **1.5.2 プロンプトの言語選択**
  - **推奨**: 英語プロンプト（事前学習モデルが英語ベースの場合）
  - 日本語プロンプトの場合は多言語対応のCLAPモデルが必要
  - または、日本語→英語翻訳を実施

- [ ] **1.5.3 JSONL形式でのメタデータ作成**
  - **ファイル名**: `prompts.jsonl`
  - **フォーマット**: 1行1サンプル、JSON形式
  ```json
  {"id": 0, "prompt": "School bell chime, clear and bright tone"}
  {"id": 1, "prompt": "Dog barking, aggressive tone, large breed"}
  {"id": 2, "prompt": "Water flowing in a stream, gentle babbling sound"}
  ```

- [ ] **1.5.4 IDと音声ファイルのマッピング**
  - ファイル命名: `{id}_hq.wav` または `{id}_hq.mp3`
  - 例: `0_hq.wav`, `1_hq.wav`, ...
  - IDは0から連番で付与（または既存のFreesound IDを利用）

- [ ] **1.5.5 カスタムメタデータモジュールの更新**
  - [custom_metadata_2.py](custom_metadata_2.py)を編集し、新しいプロンプトファイルのパスを指定
  - 必要に応じてメタデータ読み込みロジックを調整

#### プロンプト生成の自動化
既存のスクリプトを参考に、プロンプトを自動生成:
- **参考スクリプト**:
  - [README_PROJECT_FILES/scripts/freeaudio_prompt_generator.py](README_PROJECT_FILES/scripts/freeaudio_prompt_generator.py)
  - [README_PROJECT_FILES/scripts/otologic_prompt_generator_final.py](README_PROJECT_FILES/scripts/otologic_prompt_generator_final.py)
  - [README_PROJECT_FILES/scripts/translate_japanese.py](README_PROJECT_FILES/scripts/translate_japanese.py)

#### 関連ファイル
- **プロンプトファイル**: [/home/casio/localssd/prompts.jsonl](/home/casio/localssd/prompts.jsonl)
- **カスタムメタデータモジュール**: [custom_metadata_2.py](custom_metadata_2.py)
- **データセット設定**: [configs/dataset_config.json](configs/dataset_config.json)

---

### 1.6 データセット設定ファイルの更新

**目的**: データローダーに新しいデータセットを認識させる

#### タスク
- [ ] **1.6.1 dataset_config.jsonの編集**
  - 新規データと既存データを別々のdatasetsとして定義（推奨）
  - または、統合ディレクトリへのパスを指定

  **推奨設定例**:
  ```json
  {
    "dataset_type": "audio_dir",
    "datasets": [
      {
        "id": "freesound_general",
        "path": "/home/casio/localssd/freesound_audio",
        "custom_metadata_module": "custom_metadata_2.py"
      },
      {
        "id": "new_sfx",
        "path": "/home/casio/localssd/new_sfx_data",
        "custom_metadata_module": "custom_metadata_new_sfx.py"
      }
    ],
    "random_crop": true,
    "sample_size": 65536,
    "sample_rate": 44100,
    "random_crop": true
  }
  ```

- [ ] **1.6.2 データローダーのテスト**
  - データセットが正しく読み込まれるか確認
  ```python
  from stable_audio_tools.data.dataset import create_dataloader_from_config
  import json

  with open('configs/dataset_config.json') as f:
      config = json.load(f)

  dataloader = create_dataloader_from_config(
      config,
      batch_size=4,
      num_workers=4,
      sample_size=65536,
      sample_rate=44100
  )

  # 最初のバッチを取得
  batch = next(iter(dataloader))
  print(batch.keys())
  print(batch['audio'].shape)  # [batch_size, channels, samples]
  print(batch['prompt'])
  ```

#### 関連ファイル
- **データセット設定**: [configs/dataset_config.json](configs/dataset_config.json)
- **データローダー実装**: [stable_audio_tools/data/dataset.py](stable_audio_tools/data/dataset.py)
- **カスタムメタデータ**: [custom_metadata_2.py](custom_metadata_2.py)

---

## 2. モデル学習計画

### 2.1 学習環境の確認

**目的**: stable-audio-toolsフレームワークの環境と依存ライブラリが最新で安定していることを確認

#### タスク
- [ ] **2.1.1 Pythonとライブラリのバージョン確認**
  ```bash
  python --version  # Python 3.8以上推奨
  pip list | grep torch
  pip list | grep lightning
  pip list | grep einops
  ```

- [ ] **2.1.2 GPU環境の確認**
  ```bash
  nvidia-smi  # GPU稼働状況、VRAM容量確認
  python -c "import torch; print(torch.cuda.is_available())"
  python -c "import torch; print(torch.cuda.device_count())"
  ```

- [ ] **2.1.3 stable-audio-toolsの最新化**
  - リポジトリを最新版に更新（必要に応じて）
  - 依存関係の再インストール
  ```bash
  cd /Volumes/mac_hd/work/stable-audio-tools-tkh
  git pull origin main  # または該当ブランチ
  pip install -e .
  ```

- [ ] **2.1.4 ストレージ容量の確認**
  - チェックポイント保存用に十分な空き容量があるか確認（100GB以上推奨）
  - データセット配置用の容量確認

#### 関連ファイル
- **環境構築**: [README_ja.md](README_ja.md) - インストール手順
- **依存関係**: `setup.py`, `requirements.txt`

---

### 2.2 ファインチューニング手法の選択

**目的**: モデル全体のフルファインチューニングを基本としつつ、軽量手法も検討

#### タスク
- [ ] **2.2.1 フルファインチューニングの準備**
  - **手法**: モデル全体の重みを更新（全パラメータ学習）
  - **利点**: 大きな変化を得られる、新規タスクへの適応性が高い
  - **欠点**: VRAM消費が大きい、過学習リスク、計算コスト高
  - **推奨条件**: 十分なデータ量（数千サンプル以上）と計算資源がある場合

- [ ] **2.2.2 LoRA（Low-Rank Adaptation）の検討**
  - **手法**: モデルの一部（Attention層等）に低ランク行列を追加し、その部分のみ学習
  - **利点**: VRAM消費が少ない、学習速度が速い、過学習しにくい
  - **欠点**: 大きな変化を得にくい
  - **適用方法**: stable-audio-toolsにLoRAが実装されているか確認
    - 未実装の場合はPEFT（Parameter-Efficient Fine-Tuning）ライブラリの統合を検討

- [ ] **2.2.3 手法の決定**
  - **推奨**: まずフルファインチューニングで実験
  - データ量やVRAM制約がある場合はLoRAを検討
  - 学習結果を比較し、最終手法を決定

#### 参考情報
- LoRA論文: [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
- PEFTライブラリ: https://github.com/huggingface/peft

#### 関連ファイル
- **トレーニングラッパー**: [stable_audio_tools/training/diffusion.py](stable_audio_tools/training/diffusion.py)
- **モデル定義**: [stable_audio_tools/models/diffusion.py](stable_audio_tools/models/diffusion.py)

---

### 2.3 破滅的忘却への対策

**目的**: 既存機能の劣化を防ぎつつ、新規音の学習を実現

#### タスク
- [ ] **2.3.1 データ混合学習の実施**
  - **手法**: 新規データと既存データを混ぜて学習（セクション1.4で調整済み）
  - **設定**: [configs/dataset_config.json](configs/dataset_config.json)で複数datasetsを指定
  - **比率**: 新規:既存 = 1:1～1:2（バランス調整済み）

- [ ] **2.3.2 Elastic Weight Consolidation (EWC) の検討**
  - **手法**: 既存タスクで重要なパラメータの変更にペナルティを課す正則化
  - **利点**: 破滅的忘却を抑制しつつ新規学習が可能
  - **欠点**: 実装が複雑、計算コスト増、ハイパーパラメータ調整が必要
  - **実装可否の評価**:
    - stable-audio-toolsにEWC実装があるか確認
    - 未実装の場合は外部ライブラリ（Avalanche等）の統合を検討
    - **判断**: まずはデータ混合学習で対応し、必要に応じてEWCを追加

- [ ] **2.3.3 チェックポイント継承の準備**
  - **手法**: 事前学習済みモデルの重みから学習を開始
  - **利点**: 既存知識を活かし、学習時間を短縮
  - **設定**:
    - `train.py`に`--pretrained-ckpt-path`パラメータでチェックポイントを指定
    - 事前学習済みモデルは[unwrap_model.py](unwrap_model.py)でアンラップ済みのものを使用

#### EWC参考実装
```python
# EWCの概念的実装例（actual implementationはプロジェクトに応じて調整）
class EWCLoss:
    def __init__(self, model, previous_tasks_data, lambda_ewc=1000):
        self.model = model
        self.lambda_ewc = lambda_ewc
        self.fisher_information = self._compute_fisher(previous_tasks_data)
        self.optimal_params = {n: p.clone() for n, p in model.named_parameters()}

    def _compute_fisher(self, dataloader):
        # Fisher情報行列の計算（各パラメータの重要度）
        fisher = {n: torch.zeros_like(p) for n, p in self.model.named_parameters()}
        # ... 実装詳細 ...
        return fisher

    def penalty(self):
        loss = 0
        for n, p in self.model.named_parameters():
            loss += (self.fisher_information[n] * (p - self.optimal_params[n]) ** 2).sum()
        return self.lambda_ewc * loss
```

#### 関連ファイル
- **トレーニングスクリプト**: [train.py](train.py)
- **データセット設定**: [configs/dataset_config.json](configs/dataset_config.json)
- **参考**: Avalanche (Continual Learning Library): https://github.com/ContinualAI/avalanche

---

### 2.4 ハイパーパラメータ設定

**目的**: 学習率、エポック数、正則化パラメータを慎重に設定し、音質劣化を抑える

#### タスク
- [ ] **2.4.1 学習率の設定**
  - **従来の学習**: 1e-4程度（事前学習時）
  - **ファインチューニング推奨**: **5e-6 ～ 1e-5**（より低い学習率）
  - **理由**: 急激な重み更新を避け、既存知識の破壊を防ぐ
  - **設定箇所**: [configs/autoencoder_model_config.json](configs/autoencoder_model_config.json)の`training.learning_rate`

  **設定例**:
  ```json
  {
    "training": {
      "learning_rate": 5e-6,
      "warmup_steps": 1000,
      "use_ema": true,
      ...
    }
  }
  ```

- [ ] **2.4.2 エポック数・ステップ数の設定**
  - **推奨**: まずは少なめのエポックで実験（5～10エポック）
  - **過学習の兆候**: 検証損失が上昇、汎用音の品質劣化
  - **早期停止**: 検証損失が改善しなくなった時点で停止
  - **設定箇所**: [defaults.ini](defaults.ini)の`max_epochs`または`--max_epochs`パラメータ

- [ ] **2.4.3 バッチサイズの設定**
  - **現在の設定**: `batch_size=4`（[defaults.ini](defaults.ini)）
  - **推奨**: GPU VRAMに応じて調整（VRAM 24GBなら8～16も可能）
  - **注意**: バッチサイズを変更した場合、学習率も調整（線形スケーリング則）

- [ ] **2.4.4 正則化パラメータの設定**
  - **Weight Decay**: 0.01～0.1（過学習抑制）
  - **Dropout**: モデル内のDropout率を確認（通常0.1～0.3）
  - **EWC lambda**: EWC導入時は1000～10000で実験
  - **設定箇所**: [configs/autoencoder_model_config.json](configs/autoencoder_model_config.json)の`training`セクション

- [ ] **2.4.5 学習率スケジューラの設定**
  - **推奨**: Cosine Annealing with Warmup
  - **Warmup**: 最初の1000～5000ステップで学習率を徐々に上昇
  - **Cosine Decay**: その後、徐々に学習率を減少
  - **設定例**:
  ```json
  {
    "training": {
      "learning_rate": 5e-6,
      "warmup_steps": 1000,
      "lr_scheduler": "cosine",
      "lr_scheduler_params": {
        "T_max": 100000
      }
    }
  }
  ```

#### ハイパーパラメータ調整の指針
| パラメータ | 初期値 | 調整方針 |
|----------|--------|---------|
| 学習率 | 5e-6 | 汎用音が劣化したら下げる、新規音が学習されなければ上げる |
| エポック数 | 5～10 | 検証損失を見て早期停止 |
| バッチサイズ | 4～16 | VRAM容量に応じて最大化 |
| Weight Decay | 0.01 | 過学習の兆候があれば増やす（0.1まで） |

#### 関連ファイル
- **トレーニング設定**: [defaults.ini](defaults.ini)
- **モデル設定**: [configs/autoencoder_model_config.json](configs/autoencoder_model_config.json)
- **学習率スケジューラ実装**: [stable_audio_tools/training/utils.py](stable_audio_tools/training/utils.py)

---

### 2.5 段階的学習（フェーズ分け）

**目的**: 学習プロセスをフェーズに分け、段階的に品質を向上

#### タスク
- [ ] **2.5.1 フェーズ1: 基礎調整**
  - **目的**: 新規音データを中心に学習し、モデルに新しい音を覚えさせる
  - **データ比率**: 新規データ60% + 汎用データ40%
  - **学習率**: 5e-6
  - **エポック数**: 5～10エポック
  - **期待結果**: 学校チャイム等の新規音が生成可能になる

  **実行コマンド例**:
  ```bash
  python train.py \
    --dataset-config configs/dataset_config_phase1.json \
    --model-config configs/autoencoder_model_config.json \
    --pretrained-ckpt-path /path/to/base_model_unwrapped.ckpt \
    --name phase1_base_adjustment \
    --save-dir /path/to/checkpoints \
    --max-epochs 10 \
    --batch-size 8
  ```

- [ ] **2.5.2 フェーズ2: 品質調整**
  - **目的**: 全データで追加学習し、音質とプロンプト忠実度を最適化
  - **データ比率**: 新規データ50% + 汎用データ50%
  - **学習率**: 2e-6（フェーズ1より低く設定）
  - **エポック数**: 5～10エポック
  - **期待結果**: 高音質維持、汎用音の劣化なし、全体バランスの最適化

  **実行コマンド例**:
  ```bash
  python train.py \
    --dataset-config configs/dataset_config_phase2.json \
    --model-config configs/autoencoder_model_config_phase2.json \
    --pretrained-ckpt-path /path/to/checkpoints/phase1_base_adjustment/last.ckpt \
    --name phase2_quality_adjustment \
    --save-dir /path/to/checkpoints \
    --max-epochs 10 \
    --batch-size 8
  ```

- [ ] **2.5.3 フェーズ3: 最終調整（必要に応じて）**
  - **目的**: 特定の問題（高音域ノイズ等）に特化した追加学習
  - **データ**: 問題が発生する音に特化したデータセット
  - **学習率**: 1e-6（さらに低く）
  - **エポック数**: 3～5エポック
  - **条件**: フェーズ2で特定の問題が残った場合のみ実施

#### フェーズごとのデータセット設定
各フェーズで異なる`dataset_config.json`を作成:
- `configs/dataset_config_phase1.json`: 新規データ重視
- `configs/dataset_config_phase2.json`: バランス重視
- `configs/dataset_config_phase3.json`: 問題特化データ

#### 関連ファイル
- **トレーニングスクリプト**: [train.py](train.py)
- **データセット設定（テンプレート）**: [configs/dataset_config.json](configs/dataset_config.json)
- **モデル設定**: [configs/autoencoder_model_config.json](configs/autoencoder_model_config.json)

---

### 2.6 チェックポイント管理

**目的**: モデルの重みを適切に保存・管理し、常に復元可能な状態を維持

#### タスク
- [ ] **2.6.1 ベースモデルの保存**
  - **対象**: ファインチューニング前の事前学習済みモデル
  - **保存先**: `/path/to/checkpoints/base_model/base_model_unwrapped.ckpt`
  - **手順**:
    1. 事前学習済みモデルをダウンロードまたは既存チェックポイントを取得
    2. [unwrap_model.py](unwrap_model.py)でアンラップ（推論用に変換）
    ```bash
    python unwrap_model.py \
      /path/to/wrapped_checkpoint.ckpt \
      /path/to/checkpoints/base_model/base_model_unwrapped.ckpt
    ```

- [ ] **2.6.2 中間チェックポイントの自動保存**
  - **設定箇所**: [defaults.ini](defaults.ini)の`checkpoint_every`
  - **推奨間隔**: 5000～10000ステップごと
  - **保存パス**: `{save_dir}/{name}/checkpoints/epoch={epoch}-step={step}.ckpt`
  - **設定例**:
  ```ini
  [train]
  checkpoint_every = 5000
  save_dir = /path/to/checkpoints
  ```

- [ ] **2.6.3 フェーズごとの最終モデル保存**
  - **フェーズ1終了時**: `phase1_base_adjustment/last.ckpt`を保存
  - **フェーズ2終了時**: `phase2_quality_adjustment/last.ckpt`を保存
  - **フェーズ3終了時**: `phase3_final_adjustment/last.ckpt`を保存（該当する場合）

- [ ] **2.6.4 ベストモデルの選定と保存**
  - 各フェーズの中間チェックポイントから、検証損失が最も低いものを選定
  - または、主観評価で最も品質が高いものを選定
  - `best_model.ckpt`として別途保存

- [ ] **2.6.5 モデルのアンラップ**
  - 最終的なファインチューニングモデルをアンラップ（推論用に変換）
  ```bash
  python unwrap_model.py \
    /path/to/checkpoints/phase2_quality_adjustment/last.ckpt \
    /path/to/checkpoints/final_model_unwrapped.ckpt
  ```

#### チェックポイントの構造
- **Wrapped Checkpoint**（学習中に保存）:
  - モデルの重み
  - オプティマイザの状態
  - Discriminatorの重み（オートエンコーダー学習時）
  - EMAモデルの重み
  - 学習ステップ・エポック情報
  - サイズ: 数GB～10GB以上

- **Unwrapped Checkpoint**（推論用）:
  - モデルの重みのみ
  - サイズ: 1GB前後（大幅に削減）

#### 関連ファイル
- **チェックポイント管理**: [train.py](train.py)
- **アンラップスクリプト**: [unwrap_model.py](unwrap_model.py)
- **設定**: [defaults.ini](defaults.ini)

---

### 2.7 実際のトレーニング実行

**目的**: 設定したパラメータでトレーニングを実行

#### タスク
- [ ] **2.7.1 フェーズ1の実行**
  ```bash
  python train.py \
    --dataset-config configs/dataset_config_phase1.json \
    --model-config configs/autoencoder_model_config.json \
    --pretrained-ckpt-path /path/to/base_model_unwrapped.ckpt \
    --name phase1_base_adjustment \
    --save-dir /path/to/checkpoints \
    --num-gpus 2 \
    --batch-size 8 \
    --num-workers 12 \
    --precision bf16-mixed \
    --checkpoint-every 5000
  ```

- [ ] **2.7.2 フェーズ1の結果確認**
  - 学習曲線の確認（Weights & BiasesまたはTensorBoard）
  - 中間デモ音声の確認
  - 汎用音の品質劣化がないか確認

- [ ] **2.7.3 フェーズ2の実行**
  - フェーズ1の最終チェックポイントから継続
  - 学習率をさらに低く設定（2e-6等）

- [ ] **2.7.4 フェーズ2の結果確認**
  - 音質の全体的な向上を確認
  - プロンプト忠実度の向上を確認

- [ ] **2.7.5 必要に応じてフェーズ3の実行**
  - 特定の問題が残っている場合のみ

#### トレーニング中のモニタリング
- **ログ確認**: リアルタイムでlossやlearning rateを確認
- **GPU使用率**: `nvidia-smi`で確認
- **デモ音声**: トレーニング中に自動生成されるデモ音声を定期確認

#### 関連ファイル
- **トレーニングスクリプト**: [train.py](train.py)
- **設定**: [defaults.ini](defaults.ini)
- **トレーニングガイド**: [README_ja.md](README_ja.md)

---

## 3. モニタリング・評価

### 3.1 評価プロンプトの設定

**目的**: モデルの出力を定期評価するための代表的なプロンプトを用意

#### タスク
- [ ] **3.1.1 新規音用プロンプトの作成**
  - 学校のチャイム: `"School bell chime, clear and bright tone"`
  - その他新規効果音に対応するプロンプト
  - 各カテゴリで3～5種類のバリエーション

- [ ] **3.1.2 汎用音用プロンプトの作成**
  - 犬の鳴き声: `"Dog barking, aggressive tone, large breed"`
  - 水の音: `"Water flowing in a stream, gentle babbling sound"`
  - 足音: `"Footsteps on wooden floor, slow pace"`
  - ドアの音: `"Door opening and closing, creaking sound"`
  - 各カテゴリで3～5種類

- [ ] **3.1.3 評価プロンプトCSVの作成**
  - **ファイル名**: `eval_prompts.csv`
  - **フォーマット**: `category,prompt`
  ```csv
  category,prompt
  new_sfx,School bell chime, clear and bright tone
  new_sfx,School bell chime, multiple bells ringing
  general,Dog barking, aggressive tone, large breed
  general,Water flowing in a stream, gentle babbling sound
  ...
  ```

- [ ] **3.1.4 評価プロンプトの配置**
  - 保存先: [README_PROJECT_FILES/clap/eval_prompts.csv](README_PROJECT_FILES/clap/eval_prompts.csv)

#### 関連ファイル
- **既存の評価プロンプト**: [README_PROJECT_FILES/clap/eval_prompts.csv](README_PROJECT_FILES/clap/eval_prompts.csv)
- **評価スクリプト**: [README_PROJECT_FILES/clap/cal_metrics_improved.py](README_PROJECT_FILES/clap/cal_metrics_improved.py)

---

### 3.2 定期的なサンプル出力確認

**目的**: 学習の進行中、一定間隔でモデルから音声を生成し品質をチェック

#### タスク
- [ ] **3.2.1 デモコールバックの設定**
  - **設定箇所**: [configs/autoencoder_model_config.json](configs/autoencoder_model_config.json)の`training.demo`
  - **設定例**:
  ```json
  {
    "training": {
      "demo_every": 2000,
      "demo_steps": 250,
      "num_demos": 4,
      "demo_cond": [
        {"prompt": "School bell chime, clear and bright tone"},
        {"prompt": "Dog barking, aggressive tone, large breed"},
        {"prompt": "Water flowing in a stream, gentle babbling sound"},
        {"prompt": "Footsteps on wooden floor, slow pace"}
      ]
    }
  }
  ```

- [ ] **3.2.2 汎用音の品質チェック**
  - デモ音声を聴き、以下を確認:
    - ノイズっぽく劣化していないか
    - 前回問題となった「ノイズ化」現象が再発していないか
    - 音の明瞭さ、リアリティが維持されているか

- [ ] **3.2.3 プロンプト忠実度のチェック**
  - 各プロンプトに対して期待通りの音が出ているか
  - 例: 「犬の鳴き声」のプロンプトで安定して犬の音が出るか
  - 意図しない音（猫、車等）が混ざっていないか

- [ ] **3.2.4 新規音の生成品質チェック**
  - 学校チャイム等の新規音が高品質に生成されるか
  - スペクトログラム確認（Audacity、librosa等で表示）
  - 高周波成分（10kHz以上）まで出ているか確認

#### スペクトログラム表示例
```python
import librosa
import librosa.display
import matplotlib.pyplot as plt

# 音声読み込み
y, sr = librosa.load('demo_audio.wav', sr=None)

# スペクトログラム計算
D = librosa.stft(y)
S_db = librosa.amplitude_to_db(abs(D), ref=np.max)

# 表示
plt.figure(figsize=(10, 4))
librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='hz')
plt.colorbar(format='%+2.0f dB')
plt.title('Spectrogram')
plt.tight_layout()
plt.savefig('spectrogram.png')
```

#### 関連ファイル
- **デモ生成コールバック**: [stable_audio_tools/training/diffusion.py](stable_audio_tools/training/diffusion.py)
- **モデル設定**: [configs/autoencoder_model_config.json](configs/autoencoder_model_config.json)

---

### 3.3 自動評価指標の活用

**目的**: CLAPモデル等を用いて、生成音声とプロンプトの類似度を数値評価

#### タスク
- [ ] **3.3.1 CLAP評価スクリプトの準備**
  - **スクリプト**: [README_PROJECT_FILES/clap/cal_metrics_improved.py](README_PROJECT_FILES/clap/cal_metrics_improved.py)
  - CLAPモデルのダウンロードと配置
  - 依存ライブラリのインストール（laion-clap等）

- [ ] **3.3.2 評価音声の生成**
  - 各チェックポイントで評価プロンプトに対する音声を生成
  - 保存先: `/path/to/evaluation_outputs/{checkpoint_name}/`

  **生成スクリプト例**:
  ```python
  from stable_audio_tools.inference.generation import generate_diffusion_cond
  import pandas as pd

  # 評価プロンプト読み込み
  prompts_df = pd.read_csv('README_PROJECT_FILES/clap/eval_prompts.csv')

  # モデル読み込み
  model, model_config = load_model('/path/to/checkpoint.ckpt')

  # 各プロンプトで音声生成
  for idx, row in prompts_df.iterrows():
      prompt = row['prompt']
      audio = generate_diffusion_cond(
          model,
          steps=250,
          cfg_scale=7.0,
          conditioning={'prompt': prompt},
          sample_rate=44100,
          sample_size=262144
      )
      save_audio(audio, f'eval_{idx}.wav')
  ```

- [ ] **3.3.3 CLAP類似度スコアの計算**
  - 生成音声とプロンプトのCLAP embeddingを計算
  - コサイン類似度を算出

  **実行例**:
  ```bash
  python README_PROJECT_FILES/clap/cal_metrics_improved.py \
    --audio-dir /path/to/evaluation_outputs/checkpoint_10000/ \
    --prompts-csv README_PROJECT_FILES/clap/eval_prompts.csv \
    --output-csv metrics_checkpoint_10000.csv
  ```

- [ ] **3.3.4 メトリクスの記録と分析**
  - 各チェックポイントのCLAPスコアをCSVに記録
  - カテゴリ別（新規音 vs 汎用音)の平均スコアを比較
  - ベースモデルとの比較

  **メトリクスCSV例**:
  ```csv
  checkpoint,category,avg_clap_score,std_clap_score
  base_model,new_sfx,0.65,0.05
  base_model,general,0.78,0.03
  checkpoint_5000,new_sfx,0.72,0.04
  checkpoint_5000,general,0.76,0.03
  checkpoint_10000,new_sfx,0.80,0.03
  checkpoint_10000,general,0.77,0.03
  ```

#### CLAPスコアの解釈
- **0.8以上**: 非常に高い一致度（理想的）
- **0.7～0.8**: 高い一致度（許容範囲）
- **0.6～0.7**: 中程度の一致度（改善の余地あり）
- **0.6未満**: 低い一致度（問題あり）

#### 関連ファイル
- **CLAP評価スクリプト**: [README_PROJECT_FILES/clap/cal_metrics_improved.py](README_PROJECT_FILES/clap/cal_metrics_improved.py)
- **評価プロンプト**: [README_PROJECT_FILES/clap/eval_prompts.csv](README_PROJECT_FILES/clap/eval_prompts.csv)
- **メトリクス記録**: [README_PROJECT_FILES/ft/all_metrics.csv](README_PROJECT_FILES/ft/all_metrics.csv)

---

### 3.4 早期停止の判断

**目的**: 異常な兆候が見られた場合に訓練を中断し、良好なチェックポイントを採用

#### タスク
- [ ] **3.4.1 異常検出の基準策定**
  - **異常なノイズ**: 意図しないノイズや破綻した音が出始めた
  - **汎用音の劣化**: 以前は正常だった犬の鳴き声が出なくなる等
  - **検証損失の急上昇**: 過学習の兆候
  - **CLAPスコアの低下**: プロンプト忠実度の悪化

- [ ] **3.4.2 モニタリングの実施**
  - 学習曲線の定期確認（Weights & Biases/TensorBoard）
  - デモ音声の定期試聴（2000ステップごと等）
  - CLAPスコアの推移確認

- [ ] **3.4.3 早期停止の実行**
  - 異常が検出された場合、直ちにトレーニングを停止（Ctrl+C）
  - または、PyTorch LightningのEarlyStopping callbackを使用

  **EarlyStopping設定例**:
  ```python
  from pytorch_lightning.callbacks import EarlyStopping

  early_stop_callback = EarlyStopping(
      monitor='val_loss',
      patience=3,  # 3エポック改善しなければ停止
      mode='min'
  )
  ```

- [ ] **3.4.4 良好なチェックポイントの特定**
  - 異常発生直前のチェックポイントを特定
  - そのチェックポイントを最終モデル候補とする
  - 複数のチェックポイントで比較評価を実施

#### 関連ファイル
- **トレーニングスクリプト**: [train.py](train.py)
- **コールバック実装**: [stable_audio_tools/training/utils.py](stable_audio_tools/training/utils.py)

---

### 3.5 最終モデルの評価

**目的**: ファインチューニング完了後、ベースモデルとの比較評価を実施

#### タスク
- [ ] **3.5.1 特定音の生成性能評価**
  - **対象**: 学校チャイム等の新規効果音
  - **評価方法**:
    - ベースモデルとファインチューニングモデルで同じプロンプトから音声生成
    - 主観評価（音質、リアリティ、プロンプト一致度）
    - CLAPスコアで定量評価
  - **期待結果**: ファインチューニングモデルでのみ高品質な新規音が生成される

- [ ] **3.5.2 汎用音の維持評価**
  - **対象**: 犬、水音等の元からできていた音
  - **評価方法**:
    - ベースモデルとファインチューニングモデルで同じプロンプトから音声生成
    - 主観評価（劣化やプロンプト無視の有無）
    - スペクトログラム比較
    - CLAPスコアで定量評価
  - **期待結果**: 両モデルで同等の品質、劣化なし

- [ ] **3.5.3 音質の全体チェック**
  - **ノイズレベル**: ベースモデルとファインチューニングモデルのノイズを比較
  - **周波数レンジ**: スペクトログラムで高音域（10kHz以上）の有無を確認
  - **カットオフ問題**: 高音域のカットオフ問題が改善しているか検証

  **スペクトル解析スクリプト**:
  ```python
  import librosa
  import numpy as np

  def analyze_frequency_range(audio_path):
      y, sr = librosa.load(audio_path, sr=None)

      # フーリエ変換
      fft = np.fft.rfft(y)
      freqs = np.fft.rfftfreq(len(y), 1/sr)
      magnitude = np.abs(fft)

      # 10kHz以上のエネルギー
      high_freq_energy = np.sum(magnitude[freqs >= 10000])
      total_energy = np.sum(magnitude)
      high_freq_ratio = high_freq_energy / total_energy

      print(f"High frequency (>10kHz) energy ratio: {high_freq_ratio:.4f}")
      return high_freq_ratio
  ```

- [ ] **3.5.4 プロンプト忠実度の定量評価**
  - **評価プロンプト**: [README_PROJECT_FILES/clap/eval_prompts.csv](README_PROJECT_FILES/clap/eval_prompts.csv)
  - **CLAPスコア計算**: 各プロンプトのスコアを算出
  - **比較表作成**:

  | プロンプト | ベースモデル | FTモデル | 改善度 |
  |----------|-------------|----------|--------|
  | School bell chime | 0.65 | 0.82 | +0.17 |
  | Dog barking | 0.78 | 0.77 | -0.01 |
  | Water flowing | 0.80 | 0.79 | -0.01 |
  | ... | ... | ... | ... |
  | **平均（新規音）** | 0.65 | 0.80 | +0.15 |
  | **平均（汎用音）** | 0.78 | 0.77 | -0.01 |

- [ ] **3.5.5 結果の記録と整理**
  - 主観評価シートの作成（評価者: 尾崎様、石原様、チーム）
  - 音声サンプルの保存（ベースモデル vs FTモデルのペア）
  - CLAPスコアのCSV記録
  - スペクトログラム画像の保存
  - 結果サマリーレポートの作成

#### 主観評価シート例
```csv
evaluator,prompt,base_quality,ft_quality,base_fidelity,ft_fidelity,notes
尾崎,School bell chime,2,5,2,5,FTモデルで明確に改善
石原,Dog barking,4,4,5,4,ほぼ同等、若干劣化?
...
```
（評価スケール: 1=非常に悪い、5=非常に良い）

#### 関連ファイル
- **評価スクリプト**: [README_PROJECT_FILES/clap/cal_metrics_improved.py](README_PROJECT_FILES/clap/cal_metrics_improved.py)
- **評価プロンプト**: [README_PROJECT_FILES/clap/eval_prompts.csv](README_PROJECT_FILES/clap/eval_prompts.csv)
- **結果記録**: [README_PROJECT_FILES/ft/all_metrics.csv](README_PROJECT_FILES/ft/all_metrics.csv)

---

## 4. 不具合調査と改善策検討

### 4.1 高音域カットオフ問題の原因調査

**目的**: 学習結果の音声から高周波数成分が不足していないかチェックし、原因を特定

#### タスク
- [ ] **4.1.1 出力音声の周波数分析**
  - 生成音声のスペクトログラムを確認
  - 10kHz以上の高音域成分の有無を定量評価
  - 参照音（元データ）との比較

- [ ] **4.1.2 トレーニングデータ側の問題検証**
  - **仮説**: MP3由来データの使用が原因
  - **検証方法**:
    - トレーニングデータのスペクトログラム確認
    - MP3ファイルと WAVファイルの周波数範囲比較
    - MP3のビットレート確認（128kbps以下は高音域カット）
  - **対策**: セクション1.3のデータフォーマット統一を実施

- [ ] **4.1.3 モデル構造上の制約調査**
  - **仮説**: VAEや生成ネットワークの帯域幅制限
  - **検証方法**:
    - モデル設定の確認: [configs/autoencoder_model_config.json](configs/autoencoder_model_config.json)
    - サンプリングレート: 44100Hzで十分か（理論上22kHzまでカバー）
    - VAEのダウンサンプリング比: 2048（現在の設定）が適切か
    - Oobleckアーキテクチャの周波数特性確認
  - **対策候補**:
    - サンプリングレートを48kHzに上げる（24kHzまでカバー）
    - VAEのダウンサンプリング比を調整（ただし大きな変更は再学習が必要）

- [ ] **4.1.4 推論時のサンプリング設定確認**
  - デモ生成時のサンプリング設定を確認
  - `demo_steps`が十分か（250ステップ以上推奨）
  - CFG scaleの影響（高すぎると音質劣化の可能性）

#### 周波数分析スクリプト
```python
import librosa
import numpy as np
import matplotlib.pyplot as plt

def compare_frequency_spectrum(original_path, generated_path):
    # 元データと生成データを読み込み
    y_orig, sr_orig = librosa.load(original_path, sr=None)
    y_gen, sr_gen = librosa.load(generated_path, sr=None)

    # FFT
    fft_orig = np.abs(np.fft.rfft(y_orig))
    fft_gen = np.abs(np.fft.rfft(y_gen))
    freqs_orig = np.fft.rfftfreq(len(y_orig), 1/sr_orig)
    freqs_gen = np.fft.rfftfreq(len(y_gen), 1/sr_gen)

    # プロット
    plt.figure(figsize=(12, 6))
    plt.semilogy(freqs_orig, fft_orig, label='Original', alpha=0.7)
    plt.semilogy(freqs_gen, fft_gen, label='Generated', alpha=0.7)
    plt.axvline(x=10000, color='r', linestyle='--', label='10kHz')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Magnitude')
    plt.legend()
    plt.title('Frequency Spectrum Comparison')
    plt.grid(True)
    plt.savefig('frequency_comparison.png')

    # 10kHz以上のエネルギー比率
    high_orig = np.sum(fft_orig[freqs_orig >= 10000]) / np.sum(fft_orig)
    high_gen = np.sum(fft_gen[freqs_gen >= 10000]) / np.sum(fft_gen)
    print(f"Original high-freq ratio: {high_orig:.4f}")
    print(f"Generated high-freq ratio: {high_gen:.4f}")
```

#### 関連ファイル
- **モデル設定**: [configs/autoencoder_model_config.json](configs/autoencoder_model_config.json)
- **VAE実装**: [stable_audio_tools/models/autoencoders.py](stable_audio_tools/models/autoencoders.py)
- **参考**: [README_ja.md](README_ja.md) - サンプリングレートに関する記載

---

### 4.2 特定ノイズ混入の原因調査

**目的**: 出力に繰り返し現れる特定ノイズの原因を突き止める

#### タスク
- [ ] **4.2.1 ノイズ発生パターンの分析**
  - どのプロンプトでノイズが発生するか記録
  - ノイズの種類（ホワイトノイズ、クリック音、低周波ノイズ等）を分類
  - 発生頻度（常時 / 特定条件下）を記録

- [ ] **4.2.2 トレーニングデータ内のノイズ確認**
  - **仮説**: 学習データ内に類似のノイズが含まれている
  - **検証方法**:
    - トレーニングデータを聴き、ノイズ混入サンプルを特定
    - ノイズが多いサンプルのIDをリストアップ
  - **対策**: 該当サンプルをデータセットから除外、またはノイズ除去処理

  **ノイズ除去例（noisereduce使用）**:
  ```python
  import noisereduce as nr
  import soundfile as sf

  # 音声読み込み
  audio, sr = sf.read('noisy_audio.wav')

  # ノイズ除去
  reduced_noise = nr.reduce_noise(y=audio, sr=sr)

  # 保存
  sf.write('cleaned_audio.wav', reduced_noise, sr)
  ```

- [ ] **4.2.3 モデルの過学習・モード崩壊の確認**
  - **過学習の兆候**: トレーニング損失は低下するが、検証損失が上昇
  - **モード崩壊の兆候**: 多様性の低下、同じようなノイズが繰り返される
  - **確認方法**:
    - 学習曲線の確認
    - 複数プロンプトでの生成音声の多様性確認
  - **対策**:
    - 早期停止（セクション3.4）
    - 正則化強化（Weight Decay増加、Dropout追加）
    - データ拡張

- [ ] **4.2.4 サンプリングアルゴリズムの影響確認**
  - **仮説**: サンプリングステップ数やCFG scaleが不適切
  - **検証方法**:
    - サンプリングステップ数を変更（100～500で実験）
    - CFG scaleを変更（3.0～10.0で実験）
  - **期待結果**: 適切な設定でノイズが減少

#### 関連ファイル
- **サンプリング実装**: [stable_audio_tools/inference/sampling.py](stable_audio_tools/inference/sampling.py)
- **デモ設定**: [configs/autoencoder_model_config.json](configs/autoencoder_model_config.json)の`training.demo`

---

### 4.3 改善策の実施

**目的**: 特定された原因に応じて対応策を実施

#### タスク
- [ ] **4.3.1 データ不足への対応**
  - **対策**: 追加データ収集（セクション1.1～1.2）
  - **対策**: データ拡張（ピッチシフト、タイムストレッチ、ノイズ付加等）

  **データ拡張スクリプト例**:
  ```python
  import librosa
  import soundfile as sf
  import numpy as np

  def augment_audio(input_path, output_dir):
      y, sr = librosa.load(input_path, sr=44100)

      # 1. ピッチシフト
      for n_steps in [-2, -1, 1, 2]:
          y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)
          sf.write(f'{output_dir}/pitch_{n_steps}.wav', y_shifted, sr)

      # 2. タイムストレッチ
      for rate in [0.9, 0.95, 1.05, 1.1]:
          y_stretched = librosa.effects.time_stretch(y, rate=rate)
          sf.write(f'{output_dir}/stretch_{rate}.wav', y_stretched, sr)

      # 3. ノイズ付加
      noise = np.random.normal(0, 0.005, y.shape)
      y_noisy = y + noise
      sf.write(f'{output_dir}/noisy.wav', y_noisy, sr)
  ```

- [ ] **4.3.2 モデル帯域幅制限への対応**
  - **対策**: サンプリングレートを48kHzに変更
    - [configs/autoencoder_model_config.json](configs/autoencoder_model_config.json)の`sample_rate`を48000に変更
    - **注意**: サンプリングレート変更はVAEの再学習を伴う可能性（大きな変更）
  - **対策**: VAEの再学習または高品質な事前学習済みVAEの使用

- [ ] **4.3.3 ノイズ混入データのクリーニング**
  - ノイズ混入が確認されたサンプルをデータセットから除外
  - または、ノイズ除去処理を適用して再度データセットに追加

- [ ] **4.3.4 正則化とハイパーパラメータの調整**
  - Weight Decayを増やす（0.01 → 0.1）
  - Dropoutを追加または増やす
  - 学習率をさらに下げる（5e-6 → 2e-6）

- [ ] **4.3.5 再学習の実施**
  - 改善策を適用した設定で再度ファインチューニングを実施
  - セクション2の手順に従い、フェーズ1から再実行

#### 関連ファイル
- **モデル設定**: [configs/autoencoder_model_config.json](configs/autoencoder_model_config.json)
- **データセット設定**: [configs/dataset_config.json](configs/dataset_config.json)
- **トレーニングスクリプト**: [train.py](train.py)

---


## 5. 関連ファイル一覧

### 5.1 プロジェクト構造

```
stable-audio-tools-tkh/
├── train.py                           # メイントレーニングスクリプト
├── unwrap_model.py                    # モデルアンラップスクリプト
├── run_gradio.py                      # Gradio UIスクリプト
├── defaults.ini                       # トレーニングデフォルト設定
├── custom_metadata.py                 # カスタムメタデータモジュール
├── custom_metadata_2.py              # カスタムメタデータモジュール（使用中）
│
├── configs/                          # プロジェクト固有の設定
│   ├── dataset_config.json          # データセット設定（使用中）
│   ├── dataset_config_phase1.json   # フェーズ1用（要作成）
│   ├── dataset_config_phase2.json   # フェーズ2用（要作成）
│   └── autoencoder_model_config.json # モデル設定（使用中）
│
├── stable_audio_tools/               # メインフレームワーク
│   ├── data/
│   │   ├── dataset.py              # データセット実装
│   │   └── utils.py                # データユーティリティ
│   ├── models/
│   │   ├── diffusion.py           # 拡散モデル
│   │   ├── autoencoders.py        # オートエンコーダー
│   │   └── conditioners.py        # コンディショニング
│   ├── training/
│   │   ├── diffusion.py           # 拡散モデルトレーニング
│   │   ├── autoencoders.py        # オートエンコーダートレーニング
│   │   ├── utils.py               # トレーニングユーティリティ
│   │   └── losses/                # 損失関数
│   ├── inference/
│   │   ├── generation.py          # 音声生成
│   │   └── sampling.py            # サンプリング
│   └── configs/
│       ├── dataset_configs/        # データセット設定例
│       └── model_configs/          # モデル設定例
│
├── README_PROJECT_FILES/            # プロジェクト固有ファイル
│   ├── TODO_詳細計画書.md          # このファイル
│   ├── クイックリファレンス.md      # クイックリファレンス
│   ├── clap/                       # CLAP評価
│   │   ├── cal_metrics_improved.py
│   │   └── eval_prompts.csv
│   ├── t5_eval/                    # T5評価
│   ├── scripts/                    # データ処理スクリプト
│   │   ├── copy_files_and_generate_csv.py
│   │   ├── extract_freeaudio_zips.py
│   │   ├── freeaudio_prompt_generator.py
│   │   └── ...
│   └── proposal/                   # 提案資料（要作成）
│       ├── CASIO_ファインチューニング提案_2025.pptx
│       └── sample_audio/
│
├── README_ja.md                   # 日本語トレーニングガイド
└── /home/casio/localssd/          # データ保存先（サーバー上）
    ├── freesound_audio/           # 既存汎用データ
    ├── new_sfx_data/              # 新規データ（要作成）
    └── prompts.jsonl              # プロンプトファイル
```

### 6.2 重要ファイル一覧表

| カテゴリ | ファイルパス | 用途 |
|---------|-------------|------|
| **トレーニング** | [train.py](train.py) | メイントレーニングスクリプト |
| | [defaults.ini](defaults.ini) | トレーニング設定 |
| | [configs/autoencoder_model_config.json](configs/autoencoder_model_config.json) | モデル設定 |
| | [configs/dataset_config.json](configs/dataset_config.json) | データセット設定 |
| **データ** | [stable_audio_tools/data/dataset.py](stable_audio_tools/data/dataset.py) | データローダー |
| | [custom_metadata_2.py](custom_metadata_2.py) | カスタムメタデータ |
| | `/home/casio/localssd/prompts.jsonl` | プロンプトファイル |
| **評価** | [README_PROJECT_FILES/clap/cal_metrics_improved.py](README_PROJECT_FILES/clap/cal_metrics_improved.py) | CLAP評価 |
| | [README_PROJECT_FILES/clap/eval_prompts.csv](README_PROJECT_FILES/clap/eval_prompts.csv) | 評価プロンプト |
| **ユーティリティ** | [unwrap_model.py](unwrap_model.py) | モデルアンラップ |
| | [run_gradio.py](run_gradio.py) | Gradio UI |
| **ドキュメント** | [README_ja.md](README_ja.md) | 日本語ガイド |
| | [README_PROJECT_FILES/TODO_詳細計画書.md](README_PROJECT_FILES/TODO_詳細計画書.md) | このファイル |

---

## 次のステップ

このTODOリストに従い、以下の順序で作業を進めてください:

1. **Week 1: データ準備**
   - セクション1の全タスクを実施
   - データセット設定ファイルの作成・更新

2. **Week 2: トレーニング実行**
   - セクション2の全タスクを実施
   - フェーズ1、2の学習実行

3. **Week 3: 評価と提案**
   - セクション3、4の評価・調査実施
   - セクション5の提案資料作成
   - チーム内レビュー、CASIO様提案

各タスクの完了時にチェックボックスにチェックを入れ、進捗を管理してください。

---

**作成者**: Claude Code
**最終更新**: 2025-11-11
**バージョン**: 1.0