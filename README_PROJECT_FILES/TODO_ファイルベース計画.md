# ファインチューニング実装TODO - ファイルベース計画書

本ドキュメントは、Stable Audio Toolsのファインチューニング実装における具体的なタスクをファイル単位で整理したものです。

---

## 1. 学習データの構成

### 1.1 データセット設定ファイルの作成

#### ファイル: `stable_audio_tools/configs/dataset_configs/finetune_mixed_dataset.json`
**目的**: 新規データ（学校のチャイムなど）と既存データ（汎用音）の混合データセット設定

**TODO**:
- [ ] 新規作成: 混合データセット用の設定ファイル
- [ ] `dataset_type`を`"audio_dir"`に設定
- [ ] `datasets`配列に複数のデータセットを定義:
  - 新規データパス（学校のチャイム等）
  - 既存の汎用データパス
- [ ] 各データセットの`weight`パラメータで混合比率を制御（例: 1:1なら両方1.0）
- [ ] `random_crop: true`を設定して多様性を確保

**設定例**:
```json
{
    "dataset_type": "audio_dir",
    "datasets": [
        {
            "id": "school_chime_dataset",
            "path": "/path/to/school_chimes/",
            "weight": 1.0,
            "custom_metadata_module": "/path/to/school_chime_metadata.py"
        },
        {
            "id": "general_audio_dataset",
            "path": "/path/to/general_audio/",
            "weight": 1.0,
            "custom_metadata_module": "/path/to/general_metadata.py"
        }
    ],
    "random_crop": true,
    "augment_phase": true
}
```

**関連ファイル**:
- 参考: [local_training_example.json](stable_audio_tools/configs/dataset_configs/local_training_example.json)
- 実装: [dataset.py](stable_audio_tools/data/dataset.py) (特に`SampleDataset`クラス)

---

#### ファイル: `stable_audio_tools/configs/dataset_configs/custom_metadata/school_chime_metadata.py`
**目的**: 学校のチャイム音のメタデータ（プロンプト等）を動的に生成

**TODO**:
- [ ] 新規作成: カスタムメタデータモジュール
- [ ] `get_custom_metadata(info: dict, audio: torch.Tensor) -> dict`関数を実装
- [ ] ファイル名やディレクトリ構造からプロンプトを抽出
- [ ] 例: "school chime, bell sound, announcement tone"などのテキスト記述を返す
- [ ] 音の長さ、タイプ（開始チャイム、終了チャイム等）を分類

**実装例**:
```python
import torch
import os

def get_custom_metadata(info: dict, audio: torch.Tensor) -> dict:
    """
    学校のチャイム音用のメタデータを生成
    """
    file_path = info.get('relpath', '')

    # ファイル名から情報を抽出
    prompt_text = "school chime, bell sound"

    if 'start' in file_path.lower():
        prompt_text += ", class start signal"
    elif 'end' in file_path.lower():
        prompt_text += ", class end signal"

    return {
        "prompt": prompt_text,
        "seconds_start": 0,
        "seconds_total": audio.shape[-1] / info.get('sample_rate', 44100)
    }
```

**関連ファイル**:
- 参考: [custom_md_example.py](stable_audio_tools/configs/dataset_configs/custom_metadata/custom_md_example.py)

---

#### ファイル: `stable_audio_tools/configs/dataset_configs/custom_metadata/general_metadata.py`
**目的**: 汎用音データのメタデータ生成

**TODO**:
- [ ] 新規作成: 汎用音用のカスタムメタデータモジュール
- [ ] 既存の汎用音データのプロンプト記述方法を確認
- [ ] メタデータJSONファイルがあればそれを読み込む処理を実装
- [ ] なければファイル名やタグから推測する処理を実装

---

### 1.2 データバランス調整のモニタリング

#### ファイル: `scripts/analyze_dataset_balance.py`
**目的**: データセットのバランス（各カテゴリのサンプル数、長さ等）を分析

**TODO**:
- [ ] 新規作成: データセット分析スクリプト
- [ ] 各データセットのサンプル数をカウント
- [ ] 音声の長さの分布を可視化
- [ ] カテゴリ別の統計情報を出力
- [ ] 混合比率の推奨値を提案

**実装内容**:
```python
import json
import os
import librosa
from pathlib import Path
from collections import defaultdict

def analyze_dataset(dataset_config_path):
    """
    データセット設定から統計情報を収集
    """
    with open(dataset_config_path) as f:
        config = json.load(f)

    stats = defaultdict(list)

    for dataset in config['datasets']:
        dataset_id = dataset['id']
        dataset_path = dataset['path']

        # 各オーディオファイルを分析
        for audio_file in Path(dataset_path).rglob('*.wav'):
            duration = librosa.get_duration(path=str(audio_file))
            stats[dataset_id].append({
                'file': str(audio_file),
                'duration': duration
            })

    # 統計情報を表示
    for dataset_id, samples in stats.items():
        print(f"\n{dataset_id}:")
        print(f"  Sample count: {len(samples)}")
        print(f"  Total duration: {sum(s['duration'] for s in samples):.2f}s")
        print(f"  Avg duration: {sum(s['duration'] for s in samples) / len(samples):.2f}s")

    return stats

if __name__ == '__main__':
    import sys
    analyze_dataset(sys.argv[1])
```

**関連ファイル**:
- 入力: [finetune_mixed_dataset.json](stable_audio_tools/configs/dataset_configs/finetune_mixed_dataset.json)

---

## 2. ファインチューニングの手法実装

### 2.1 フルファインチューニング設定

#### ファイル: `stable_audio_tools/configs/model_configs/finetune/stable_audio_finetune_full.json`
**目的**: フルファインチューニング用のモデル設定（破滅的忘却を防ぐための低学習率設定）

**TODO**:
- [ ] 新規作成: ファインチューニング用モデル設定
- [ ] ベースモデル設定（Stable Audio 2.0等）をコピー
- [ ] `training.learning_rate`を`5e-6`に変更（通常の1e-4から大幅に削減）
- [ ] `training.warmup_steps`を設定（例: 1000ステップ）
- [ ] `training.use_ema: true`を確認（音質安定化のため）
- [ ] `training.demo`設定で定期的なサンプリングを有効化

**設定例**:
```json
{
    "model_type": "diffusion_cond",
    "sample_size": 12582912,
    "sample_rate": 44100,
    "audio_channels": 2,
    "model": {
        "pretransform": {
            "type": "autoencoder",
            "config": {
                // 既存のVAE設定をそのまま使用
            }
        },
        "conditioning": {
            "configs": [
                {
                    "id": "prompt",
                    "type": "clap_text",
                    "config": {
                        "clap_ckpt_path": "/path/to/clap/model"
                    }
                }
            ]
        },
        "diffusion": {
            // 既存のDiT設定
        }
    },
    "training": {
        "learning_rate": 5e-6,
        "warmup_steps": 1000,
        "use_ema": true,
        "optimizer_configs": {
            "diffusion": {
                "optimizer": {
                    "type": "AdamW",
                    "config": {
                        "betas": [0.9, 0.999],
                        "weight_decay": 1e-3
                    }
                },
                "scheduler": {
                    "type": "InverseLR",
                    "config": {
                        "inv_gamma": 50000,
                        "power": 0.5,
                        "warmup": 0.95
                    }
                }
            }
        },
        "loss_configs": {
            "diffusion": {
                "type": "mse",
                "config": {
                    "mask_padding": true
                }
            }
        },
        "demo": {
            "demo_every": 5000,
            "demo_steps": 250,
            "num_demos": 4,
            "demo_cfg_scales": [3.0, 5.0, 7.0]
        }
    }
}
```

**関連ファイル**:
- 参考: [stable_audio_2_0.json](stable_audio_tools/configs/model_configs/txt2audio/stable_audio_2_0.json)
- 実装: [diffusion.py](stable_audio_tools/training/diffusion.py) (`DiffusionCondTrainingWrapper`)

---

### 2.2 LoRAファインチューニング実装（オプション）

#### ファイル: `stable_audio_tools/models/lora.py`
**目的**: LoRA（Low-Rank Adaptation）の実装

**TODO**:
- [ ] 新規作成: LoRAモジュール
- [ ] `torch.nn.Module`を継承した`LoRALayer`クラスを実装
- [ ] 低ランク行列（A, B）のパラメータ化
- [ ] 既存のLinear/Conv1dレイヤーをラップする機能
- [ ] LoRAパラメータのみを学習可能にする切り替え機能

**実装スケルトン**:
```python
import torch
import torch.nn as nn

class LoRALayer(nn.Module):
    def __init__(
        self,
        original_layer: nn.Module,
        r: int = 8,  # ランク
        lora_alpha: int = 16,
        lora_dropout: float = 0.0
    ):
        super().__init__()
        self.original_layer = original_layer
        self.r = r
        self.lora_alpha = lora_alpha

        # 元のレイヤーをフリーズ
        for param in self.original_layer.parameters():
            param.requires_grad = False

        # LoRA行列の初期化
        if isinstance(original_layer, nn.Linear):
            in_features = original_layer.in_features
            out_features = original_layer.out_features

            self.lora_A = nn.Parameter(torch.zeros(r, in_features))
            self.lora_B = nn.Parameter(torch.zeros(out_features, r))

            # 初期化
            nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
            nn.init.zeros_(self.lora_B)

        self.scaling = lora_alpha / r
        self.dropout = nn.Dropout(lora_dropout) if lora_dropout > 0 else None

    def forward(self, x):
        # 元のレイヤーの出力
        result = self.original_layer(x)

        # LoRA部分の追加
        if self.dropout:
            x = self.dropout(x)

        lora_out = (x @ self.lora_A.T) @ self.lora_B.T
        result = result + lora_out * self.scaling

        return result

def apply_lora_to_model(model, target_modules=['to_q', 'to_k', 'to_v'], r=8):
    """
    モデルの指定されたモジュールにLoRAを適用
    """
    for name, module in model.named_modules():
        if any(target in name for target in target_modules):
            # LinearレイヤーをLoRALayerで置き換え
            if isinstance(module, nn.Linear):
                parent_name = '.'.join(name.split('.')[:-1])
                child_name = name.split('.')[-1]
                parent = model.get_submodule(parent_name)
                setattr(parent, child_name, LoRALayer(module, r=r))
```

**注意**: 現在のコードベースにはLoRA実装がないため、フルファインチューニングを優先することを推奨

---

#### ファイル: `stable_audio_tools/configs/model_configs/finetune/stable_audio_finetune_lora.json`
**目的**: LoRAファインチューニング用の設定（実装後）

**TODO**:
- [ ] LoRA実装後に作成
- [ ] `lora`セクションを追加:
  - `r`: ランク（推奨: 8-16）
  - `lora_alpha`: スケーリング係数（推奨: 16-32）
  - `target_modules`: LoRAを適用するモジュール（例: attention層）

---

### 2.3 段階的学習（フェーズ分け）実装

#### ファイル: `scripts/phased_training.sh`
**目的**: 段階的ファインチューニングを自動化するスクリプト

**TODO**:
- [ ] 新規作成: フェーズ別学習の実行スクリプト
- [ ] Phase 1: 事前学習（pre-training continuation）
  - 既存の汎用データでウォームアップ
  - 学習率: 1e-5程度
  - ステップ数: 10k-20k
- [ ] Phase 2: 混合学習（mixed training）
  - 新規データと汎用データの混合
  - 学習率: 5e-6
  - ステップ数: 20k-50k
- [ ] Phase 3: 音質調整（quality refinement）
  - 新規データに集中
  - 学習率: 1e-6
  - ステップ数: 5k-10k

**実装例**:
```bash
#!/bin/bash

# Phase 1: Pre-training continuation
echo "Phase 1: Pre-training continuation..."
python train.py \
    --model-config stable_audio_tools/configs/model_configs/finetune/phase1_pretrain.json \
    --dataset-config stable_audio_tools/configs/dataset_configs/general_only_dataset.json \
    --pretrained-ckpt-path /path/to/base/model.ckpt \
    --save-dir checkpoints/phase1 \
    --batch-size 8 \
    --num-gpus 4 \
    --checkpoint-every 5000 \
    --name finetune_phase1

# Phase 2: Mixed training
echo "Phase 2: Mixed training..."
python train.py \
    --model-config stable_audio_tools/configs/model_configs/finetune/phase2_mixed.json \
    --dataset-config stable_audio_tools/configs/dataset_configs/finetune_mixed_dataset.json \
    --ckpt-path checkpoints/phase1/last.ckpt \
    --save-dir checkpoints/phase2 \
    --batch-size 8 \
    --num-gpus 4 \
    --checkpoint-every 5000 \
    --name finetune_phase2

# Phase 3: Quality refinement
echo "Phase 3: Quality refinement..."
python train.py \
    --model-config stable_audio_tools/configs/model_configs/finetune/phase3_refine.json \
    --dataset-config stable_audio_tools/configs/dataset_configs/school_chime_only_dataset.json \
    --ckpt-path checkpoints/phase2/last.ckpt \
    --save-dir checkpoints/phase3 \
    --batch-size 8 \
    --num-gpus 4 \
    --checkpoint-every 2500 \
    --name finetune_phase3

echo "Phased training completed!"
```

---

#### ファイル: `stable_audio_tools/configs/model_configs/finetune/phase1_pretrain.json`
**TODO**:
- [ ] 新規作成: Phase 1用設定
- [ ] 学習率: 1e-5
- [ ] その他はベース設定を継承

---

#### ファイル: `stable_audio_tools/configs/model_configs/finetune/phase2_mixed.json`
**TODO**:
- [ ] 新規作成: Phase 2用設定
- [ ] 学習率: 5e-6
- [ ] demo設定で両方のデータタイプをサンプリング

---

#### ファイル: `stable_audio_tools/configs/model_configs/finetune/phase3_refine.json`
**TODO**:
- [ ] 新規作成: Phase 3用設定
- [ ] 学習率: 1e-6
- [ ] demoステップ数を増やして高品質生成を確認

---

## 3. 音質・プロンプト忠実度の監視と評価

### 3.1 定性評価用デモコールバックの強化

#### ファイル: `stable_audio_tools/training/custom_demo_callback.py`
**目的**: ファインチューニング専用のデモコールバック（詳細なログとスペクトログラム生成）

**TODO**:
- [ ] 新規作成: カスタムデモコールバッククラス
- [ ] 既存の`DiffusionCondDemoCallback`を継承
- [ ] 以下の機能を追加:
  - スペクトログラム画像の自動生成と保存
  - 複数のCFGスケールでのサンプリング
  - 固定プロンプトセットでの一貫性チェック
  - 音声ファイルとスペクトログラムをW&B/Cometにログ

**実装例**:
```python
import torch
import matplotlib.pyplot as plt
import librosa
import librosa.display
import numpy as np
from stable_audio_tools.training.diffusion import DiffusionCondDemoCallback

class FinetuneMonitoringCallback(DiffusionCondDemoCallback):
    """
    ファインチューニング専用の拡張デモコールバック
    """

    def __init__(self, *args, fixed_prompts=None, **kwargs):
        super().__init__(*args, **kwargs)

        # 固定プロンプトセット（一貫性チェック用）
        self.fixed_prompts = fixed_prompts or [
            "school chime, bell sound, class start signal",
            "school chime, bell sound, class end signal",
            "ambient background music, calm atmosphere",
            "drum loop, 120 bpm, energetic"
        ]

    def generate_spectrogram(self, audio, sample_rate, title=""):
        """
        スペクトログラム画像を生成
        """
        audio_np = audio.cpu().numpy()

        fig, ax = plt.subplots(figsize=(10, 4))

        # メルスペクトログラム計算
        S = librosa.feature.melspectrogram(
            y=audio_np,
            sr=sample_rate,
            n_mels=128
        )
        S_dB = librosa.power_to_db(S, ref=np.max)

        # 描画
        img = librosa.display.specshow(
            S_dB,
            x_axis='time',
            y_axis='mel',
            sr=sample_rate,
            ax=ax
        )
        ax.set_title(title)
        fig.colorbar(img, ax=ax, format='%+2.0f dB')

        return fig

    def on_validation_epoch_end(self, trainer, pl_module):
        """
        検証エポック終了時に拡張デモを生成
        """
        # 元のデモ生成を実行
        super().on_validation_epoch_end(trainer, pl_module)

        # 固定プロンプトでの追加サンプリング
        for i, prompt in enumerate(self.fixed_prompts):
            conditioning = [{
                "prompt": prompt,
                "seconds_start": 0,
                "seconds_total": 30
            }]

            # サンプリング実行
            audio = self.generate_audio(pl_module, conditioning)

            # スペクトログラム生成
            spec_fig = self.generate_spectrogram(
                audio[0, 0],  # [batch, channels, samples]
                self.sample_rate,
                title=f"Fixed Prompt {i}: {prompt[:50]}..."
            )

            # W&B/Cometにログ
            if trainer.logger:
                trainer.logger.experiment.log({
                    f"fixed_prompt_{i}_audio": audio,
                    f"fixed_prompt_{i}_spectrogram": spec_fig
                })

            plt.close(spec_fig)
```

---

#### ファイル: `stable_audio_tools/configs/model_configs/finetune/stable_audio_finetune_full.json`（更新）
**TODO**:
- [ ] `training.demo`セクションを更新してカスタムコールバックを使用
- [ ] 固定プロンプトリストを設定に追加

---

### 3.2 CLAP-based評価指標の実装

#### ファイル: `stable_audio_tools/training/metrics/clap_score.py`
**目的**: CLAPモデルを使用したプロンプト忠実度の定量評価

**TODO**:
- [ ] 新規作成: CLAP Scoreメトリクス
- [ ] LAION-CLAPモデルのロード機能
- [ ] テキストエンコーディング機能
- [ ] オーディオエンコーディング機能
- [ ] コサイン類似度計算（CLIP Score相当）

**実装例**:
```python
import torch
import torch.nn as nn
from transformers import ClapModel, ClapProcessor

class CLAPScore(nn.Module):
    """
    CLAPモデルを使用したプロンプト忠実度スコア
    """

    def __init__(self, clap_model_name="laion/clap-htsat-unfused"):
        super().__init__()
        self.model = ClapModel.from_pretrained(clap_model_name)
        self.processor = ClapProcessor.from_pretrained(clap_model_name)
        self.model.eval()

    @torch.no_grad()
    def forward(self, audio, text_prompts, sample_rate=48000):
        """
        Args:
            audio: [batch, channels, samples] 音声tensor
            text_prompts: List[str] テキストプロンプトのリスト
            sample_rate: サンプリングレート

        Returns:
            scores: [batch] 各サンプルのCLAPスコア
        """
        # オーディオをCLAPの期待形式に変換
        audio_np = audio.cpu().numpy()

        # テキストとオーディオをエンコード
        inputs = self.processor(
            text=text_prompts,
            audios=audio_np,
            sampling_rate=sample_rate,
            return_tensors="pt",
            padding=True
        )

        inputs = {k: v.to(audio.device) for k, v in inputs.items()}

        # CLAPエンコーディング
        outputs = self.model(**inputs)

        # コサイン類似度を計算
        text_embeds = outputs.text_embeds
        audio_embeds = outputs.audio_embeds

        # 正規化
        text_embeds = text_embeds / text_embeds.norm(dim=-1, keepdim=True)
        audio_embeds = audio_embeds / audio_embeds.norm(dim=-1, keepdim=True)

        # コサイン類似度
        scores = (text_embeds * audio_embeds).sum(dim=-1)

        return scores
```

**依存関係**:
- `transformers`ライブラリのインストールが必要
- `pip install transformers`

---

#### ファイル: `scripts/evaluate_clap_score.py`
**目的**: チェックポイントのCLAPスコアを評価するスクリプト

**TODO**:
- [ ] 新規作成: CLAP評価スクリプト
- [ ] モデルとチェックポイントをロード
- [ ] テストプロンプトセットを定義
- [ ] 各プロンプトで音声を生成
- [ ] CLAPスコアを計算して統計情報を出力

**実装例**:
```python
import torch
import json
from stable_audio_tools.models import create_model_from_config
from stable_audio_tools.inference.generation import generate_diffusion_cond
from stable_audio_tools.training.metrics.clap_score import CLAPScore

def evaluate_checkpoint(
    model_config_path,
    ckpt_path,
    test_prompts,
    output_path="clap_scores.json"
):
    """
    チェックポイントのCLAPスコアを評価
    """
    # モデルロード
    with open(model_config_path) as f:
        model_config = json.load(f)

    model = create_model_from_config(model_config)
    model.load_state_dict(torch.load(ckpt_path)['state_dict'])
    model.eval()
    model.cuda()

    # CLAPスコア計算器
    clap_scorer = CLAPScore()
    clap_scorer.cuda()

    results = {}

    for prompt in test_prompts:
        print(f"Evaluating prompt: {prompt}")

        # 複数回生成して平均スコアを計算
        scores = []
        for _ in range(5):  # 5回生成
            # 音声生成
            conditioning = [{
                "prompt": prompt,
                "seconds_start": 0,
                "seconds_total": 30
            }]

            audio = generate_diffusion_cond(
                model,
                conditioning=conditioning,
                steps=250,
                cfg_scale=7.0,
                sample_size=model.sample_size,
                batch_size=1
            )

            # CLAPスコア計算
            score = clap_scorer(audio, [prompt], sample_rate=model.sample_rate)
            scores.append(score.item())

        # 統計情報
        results[prompt] = {
            "mean": sum(scores) / len(scores),
            "std": torch.std(torch.tensor(scores)).item(),
            "scores": scores
        }

    # 結果を保存
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_path}")
    return results

if __name__ == '__main__':
    test_prompts = [
        "school chime, bell sound, class start signal",
        "school chime, bell sound, class end signal",
        "ambient music, calm atmosphere",
        "drum loop, 120 bpm, energetic",
        "piano melody, emotional, slow tempo"
    ]

    evaluate_checkpoint(
        model_config_path="stable_audio_tools/configs/model_configs/finetune/stable_audio_finetune_full.json",
        ckpt_path="checkpoints/phase2/step-30000.ckpt",
        test_prompts=test_prompts
    )
```

---

### 3.3 早期停止判断のための異常検知

#### ファイル: `stable_audio_tools/training/callbacks/anomaly_detection.py`
**目的**: 生成音声の異常を検知して早期停止を判断

**TODO**:
- [ ] 新規作成: 異常検知コールバック
- [ ] 以下の異常パターンを検出:
  - クリッピング（振幅が閾値を超える）
  - 無音区間が異常に長い
  - スペクトル分布の異常（高周波ノイズ等）
  - NaNやInfの発生
- [ ] 異常検出時にフラグを立てる
- [ ] 連続して異常が検出された場合、学習を停止

**実装例**:
```python
import torch
import torch.nn as nn
import pytorch_lightning as pl
from typing import List, Dict
import numpy as np

class AnomalyDetectionCallback(pl.Callback):
    """
    生成音声の異常を検知するコールバック
    """

    def __init__(
        self,
        check_every_n_steps: int = 5000,
        anomaly_threshold: int = 3,  # 連続異常回数の閾値
        clip_threshold: float = 0.99,
        silence_threshold: float = 0.01,
        max_silence_ratio: float = 0.8
    ):
        super().__init__()
        self.check_every_n_steps = check_every_n_steps
        self.anomaly_threshold = anomaly_threshold
        self.clip_threshold = clip_threshold
        self.silence_threshold = silence_threshold
        self.max_silence_ratio = max_silence_ratio

        self.anomaly_count = 0
        self.anomaly_history = []

    def check_clipping(self, audio: torch.Tensor) -> bool:
        """
        クリッピング検出
        """
        max_val = audio.abs().max()
        return max_val > self.clip_threshold

    def check_silence(self, audio: torch.Tensor) -> bool:
        """
        異常な無音区間を検出
        """
        silence_mask = audio.abs() < self.silence_threshold
        silence_ratio = silence_mask.float().mean()
        return silence_ratio > self.max_silence_ratio

    def check_nan_inf(self, audio: torch.Tensor) -> bool:
        """
        NaN/Inf検出
        """
        return torch.isnan(audio).any() or torch.isinf(audio).any()

    def check_spectral_anomaly(self, audio: torch.Tensor, sample_rate: int) -> bool:
        """
        スペクトル異常を検出（高周波ノイズ等）
        """
        # FFT計算
        fft = torch.fft.rfft(audio, dim=-1)
        magnitude = fft.abs()

        # 高周波成分（Nyquist周波数の80%以上）のエネルギー比率
        nyquist_idx = magnitude.shape[-1]
        high_freq_start = int(nyquist_idx * 0.8)

        high_freq_energy = magnitude[..., high_freq_start:].pow(2).sum()
        total_energy = magnitude.pow(2).sum()

        high_freq_ratio = high_freq_energy / (total_energy + 1e-8)

        # 高周波成分が30%を超えたら異常
        return high_freq_ratio > 0.3

    def detect_anomalies(
        self,
        audios: List[torch.Tensor],
        sample_rate: int
    ) -> Dict[str, List[bool]]:
        """
        複数の音声サンプルから異常を検出
        """
        results = {
            'clipping': [],
            'silence': [],
            'nan_inf': [],
            'spectral': []
        }

        for audio in audios:
            results['clipping'].append(self.check_clipping(audio))
            results['silence'].append(self.check_silence(audio))
            results['nan_inf'].append(self.check_nan_inf(audio))
            results['spectral'].append(self.check_spectral_anomaly(audio, sample_rate))

        return results

    def on_train_batch_end(self, trainer, pl_module, outputs, batch, batch_idx):
        """
        学習ステップ終了時に定期的にチェック
        """
        global_step = trainer.global_step

        if global_step % self.check_every_n_steps != 0:
            return

        # デモ生成（簡易版）
        pl_module.eval()
        with torch.no_grad():
            # 固定プロンプトでサンプリング
            test_prompts = [
                "school chime, bell sound",
                "ambient music, calm",
                "drum loop, energetic"
            ]

            generated_audios = []
            for prompt in test_prompts:
                conditioning = [{
                    "prompt": prompt,
                    "seconds_start": 0,
                    "seconds_total": 10  # 短めでチェック
                }]

                # 生成（実装依存）
                # audio = pl_module.generate(conditioning)
                # generated_audios.append(audio)
                pass  # 実際の生成コードは環境に応じて実装

        pl_module.train()

        # 異常検出
        anomaly_results = self.detect_anomalies(
            generated_audios,
            pl_module.sample_rate
        )

        # 異常の有無を判定
        has_anomaly = False
        anomaly_types = []

        for anomaly_type, detections in anomaly_results.items():
            if any(detections):
                has_anomaly = True
                anomaly_types.append(anomaly_type)

        # ログ記録
        self.anomaly_history.append({
            'step': global_step,
            'has_anomaly': has_anomaly,
            'types': anomaly_types,
            'details': anomaly_results
        })

        if has_anomaly:
            self.anomaly_count += 1
            print(f"\n[WARNING] Anomaly detected at step {global_step}: {anomaly_types}")

            # 連続異常の場合、学習を停止
            if self.anomaly_count >= self.anomaly_threshold:
                print(f"\n[CRITICAL] {self.anomaly_count} consecutive anomalies detected. Stopping training.")
                trainer.should_stop = True
        else:
            # 正常な場合、カウンタリセット
            self.anomaly_count = 0
```

---

#### ファイル: `train.py`（更新）
**TODO**:
- [ ] 異常検知コールバックをトレーニングに追加
- [ ] `AnomalyDetectionCallback`をインポート
- [ ] `Trainer`の`callbacks`に追加

**変更箇所**:
```python
from stable_audio_tools.training.callbacks.anomaly_detection import AnomalyDetectionCallback

# Trainerの初期化時
callbacks = [
    # 既存のコールバック
    AnomalyDetectionCallback(
        check_every_n_steps=5000,
        anomaly_threshold=3
    )
]

trainer = pl.Trainer(
    ...,
    callbacks=callbacks
)
```

---

### 3.4 定期的な定性評価レポート生成

#### ファイル: `scripts/generate_evaluation_report.py`
**目的**: チェックポイントごとに定性評価レポート（音声+スペクトログラム）を生成

**TODO**:
- [ ] 新規作成: 評価レポート生成スクリプト
- [ ] チェックポイントディレクトリを走査
- [ ] 各チェックポイントで複数のプロンプトをサンプリング
- [ ] 音声ファイルとスペクトログラムをHTMLレポートにまとめる
- [ ] CLAPスコアも含める

**実装例**:
```python
import os
import json
import torch
from pathlib import Path
import matplotlib.pyplot as plt
import librosa
import librosa.display
from jinja2 import Template

def generate_report(
    checkpoint_dir: str,
    model_config_path: str,
    test_prompts: list,
    output_dir: str = "evaluation_reports"
):
    """
    チェックポイントディレクトリから評価レポートを生成
    """
    os.makedirs(output_dir, exist_ok=True)

    # チェックポイントファイルを取得
    ckpt_files = sorted(Path(checkpoint_dir).glob("*.ckpt"))

    report_data = []

    for ckpt_path in ckpt_files:
        print(f"Processing {ckpt_path.name}...")

        # モデルロードと生成
        # （evaluate_clap_score.pyと同様の処理）

        ckpt_report = {
            'name': ckpt_path.name,
            'samples': []
        }

        for prompt in test_prompts:
            # 音声生成
            # audio = generate(...)

            # スペクトログラム生成と保存
            # spec_path = save_spectrogram(audio, output_dir, ckpt_path.stem, prompt)

            # 音声ファイル保存
            # audio_path = save_audio(audio, output_dir, ckpt_path.stem, prompt)

            ckpt_report['samples'].append({
                'prompt': prompt,
                'audio_path': "audio_path",
                'spec_path': "spec_path",
                'clap_score': 0.85  # 実際の計算結果
            })

        report_data.append(ckpt_report)

    # HTMLレポート生成
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fine-tuning Evaluation Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .checkpoint { margin-bottom: 40px; border: 1px solid #ccc; padding: 20px; }
            .sample { margin-bottom: 20px; }
            img { max-width: 800px; }
        </style>
    </head>
    <body>
        <h1>Fine-tuning Evaluation Report</h1>
        {% for ckpt in checkpoints %}
        <div class="checkpoint">
            <h2>{{ ckpt.name }}</h2>
            {% for sample in ckpt.samples %}
            <div class="sample">
                <h3>{{ sample.prompt }}</h3>
                <p><strong>CLAP Score:</strong> {{ sample.clap_score }}</p>
                <audio controls src="{{ sample.audio_path }}"></audio>
                <br><br>
                <img src="{{ sample.spec_path }}" alt="Spectrogram">
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    </body>
    </html>
    """

    template = Template(html_template)
    html_content = template.render(checkpoints=report_data)

    report_path = os.path.join(output_dir, "evaluation_report.html")
    with open(report_path, 'w') as f:
        f.write(html_content)

    print(f"Report generated: {report_path}")

if __name__ == '__main__':
    generate_report(
        checkpoint_dir="checkpoints/phase2",
        model_config_path="stable_audio_tools/configs/model_configs/finetune/stable_audio_finetune_full.json",
        test_prompts=[
            "school chime, bell sound, class start signal",
            "school chime, bell sound, class end signal",
            "ambient music, calm atmosphere"
        ]
    )
```

---

## 4. インフラと実行環境

### 4.1 学習実行スクリプトの統合

#### ファイル: `scripts/run_finetune.sh`
**目的**: ファインチューニングの全プロセスを統合実行

**TODO**:
- [ ] 新規作成: ワンコマンドでファインチューニングを開始
- [ ] データセット分析
- [ ] 段階的学習（3フェーズ）
- [ ] 評価レポート生成
- [ ] モデルのアンラップ（推論用）

**実装例**:
```bash
#!/bin/bash

set -e  # エラー時に停止

# 設定
BASE_MODEL="/path/to/base/stable_audio_model.ckpt"
DATASET_CONFIG="stable_audio_tools/configs/dataset_configs/finetune_mixed_dataset.json"
OUTPUT_DIR="./finetune_output"
NUM_GPUS=4
BATCH_SIZE=8

echo "===== Stable Audio Fine-tuning Pipeline ====="
echo ""

# 1. データセット分析
echo "Step 1: Analyzing dataset..."
python scripts/analyze_dataset_balance.py $DATASET_CONFIG

# 2. Phase 1: Pre-training continuation
echo ""
echo "Step 2: Phase 1 - Pre-training continuation..."
python train.py \
    --model-config stable_audio_tools/configs/model_configs/finetune/phase1_pretrain.json \
    --dataset-config stable_audio_tools/configs/dataset_configs/general_only_dataset.json \
    --pretrained-ckpt-path $BASE_MODEL \
    --save-dir $OUTPUT_DIR/phase1 \
    --batch-size $BATCH_SIZE \
    --num-gpus $NUM_GPUS \
    --checkpoint-every 5000 \
    --name finetune_phase1 \
    --logger wandb

# 3. Phase 2: Mixed training
echo ""
echo "Step 3: Phase 2 - Mixed training..."
python train.py \
    --model-config stable_audio_tools/configs/model_configs/finetune/phase2_mixed.json \
    --dataset-config $DATASET_CONFIG \
    --ckpt-path $OUTPUT_DIR/phase1/last.ckpt \
    --save-dir $OUTPUT_DIR/phase2 \
    --batch-size $BATCH_SIZE \
    --num-gpus $NUM_GPUS \
    --checkpoint-every 5000 \
    --name finetune_phase2 \
    --logger wandb

# 4. Phase 3: Quality refinement
echo ""
echo "Step 4: Phase 3 - Quality refinement..."
python train.py \
    --model-config stable_audio_tools/configs/model_configs/finetune/phase3_refine.json \
    --dataset-config stable_audio_tools/configs/dataset_configs/school_chime_only_dataset.json \
    --ckpt-path $OUTPUT_DIR/phase2/last.ckpt \
    --save-dir $OUTPUT_DIR/phase3 \
    --batch-size $BATCH_SIZE \
    --num-gpus $NUM_GPUS \
    --checkpoint-every 2500 \
    --name finetune_phase3 \
    --logger wandb

# 5. 評価レポート生成
echo ""
echo "Step 5: Generating evaluation reports..."
python scripts/generate_evaluation_report.py \
    --checkpoint-dir $OUTPUT_DIR/phase3 \
    --model-config stable_audio_tools/configs/model_configs/finetune/phase3_refine.json \
    --output-dir $OUTPUT_DIR/evaluation_reports

# 6. CLAP評価
echo ""
echo "Step 6: Evaluating CLAP scores..."
python scripts/evaluate_clap_score.py \
    --model-config stable_audio_tools/configs/model_configs/finetune/phase3_refine.json \
    --ckpt-path $OUTPUT_DIR/phase3/last.ckpt \
    --output $OUTPUT_DIR/clap_scores.json

# 7. モデルのアンラップ（推論用）
echo ""
echo "Step 7: Unwrapping model for inference..."
python unwrap_model.py \
    --model-config stable_audio_tools/configs/model_configs/finetune/phase3_refine.json \
    --ckpt-path $OUTPUT_DIR/phase3/last.ckpt \
    --name finetuned_model \
    --output-dir $OUTPUT_DIR/inference_model

echo ""
echo "===== Fine-tuning Complete ====="
echo "Output directory: $OUTPUT_DIR"
echo "Inference model: $OUTPUT_DIR/inference_model/finetuned_model.ckpt"
```

---

### 4.2 環境構築スクリプト

#### ファイル: `scripts/setup_finetune_env.sh`
**目的**: ファインチューニング用の環境セットアップ

**TODO**:
- [ ] 新規作成: 環境構築自動化スクリプト
- [ ] 必要なPythonパッケージのインストール
- [ ] CLAPモデルのダウンロード
- [ ] ディレクトリ構造の作成

**実装例**:
```bash
#!/bin/bash

echo "Setting up fine-tuning environment..."

# Python依存関係のインストール
pip install -r requirements.txt
pip install transformers  # CLAP用

# 追加パッケージ
pip install librosa matplotlib jinja2

# ディレクトリ構造作成
mkdir -p data/school_chimes
mkdir -p data/general_audio
mkdir -p checkpoints
mkdir -p evaluation_reports

# CLAPモデルのキャッシュ（初回実行時にダウンロード）
python -c "from transformers import ClapModel, ClapProcessor; ClapModel.from_pretrained('laion/clap-htsat-unfused'); ClapProcessor.from_pretrained('laion/clap-htsat-unfused')"

echo "Environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Place your audio data in data/school_chimes/ and data/general_audio/"
echo "2. Update dataset config paths in stable_audio_tools/configs/dataset_configs/"
echo "3. Run: bash scripts/run_finetune.sh"
```

---

## 5. 設定ファイルテンプレートの作成

### 5.1 汎用音データセット設定

#### ファイル: `stable_audio_tools/configs/dataset_configs/general_only_dataset.json`
**TODO**:
- [ ] 新規作成: Phase 1用の汎用音データのみの設定
- [ ] 汎用音データのパスを指定

**設定例**:
```json
{
    "dataset_type": "audio_dir",
    "datasets": [
        {
            "id": "general_audio",
            "path": "/path/to/general_audio/",
            "custom_metadata_module": "stable_audio_tools/configs/dataset_configs/custom_metadata/general_metadata.py"
        }
    ],
    "random_crop": true,
    "augment_phase": true
}
```

---

### 5.2 学校のチャイム専用データセット設定

#### ファイル: `stable_audio_tools/configs/dataset_configs/school_chime_only_dataset.json`
**TODO**:
- [ ] 新規作成: Phase 3用の学校のチャイム音のみの設定

**設定例**:
```json
{
    "dataset_type": "audio_dir",
    "datasets": [
        {
            "id": "school_chime",
            "path": "/path/to/school_chimes/",
            "custom_metadata_module": "stable_audio_tools/configs/dataset_configs/custom_metadata/school_chime_metadata.py"
        }
    ],
    "random_crop": true,
    "augment_phase": false
}
```

---

## 6. ドキュメント整備

### 6.1 ファインチューニングガイド

#### ファイル: `README_PROJECT_FILES/FINETUNING_GUIDE.md`
**TODO**:
- [ ] 新規作成: ファインチューニングの実施手順書
- [ ] 以下の内容を含める:
  - データ準備方法
  - 設定ファイルのカスタマイズ方法
  - 学習の実行手順
  - 評価方法
  - トラブルシューティング

---

### 6.2 設定パラメータリファレンス

#### ファイル: `README_PROJECT_FILES/CONFIG_REFERENCE.md`
**TODO**:
- [ ] 新規作成: 設定パラメータの詳細説明
- [ ] モデル設定の各パラメータ
- [ ] データセット設定の各パラメータ
- [ ] 推奨値と注意事項

---

## 7. 実装の優先順位

### フェーズ1: 基本実装（最優先）
1. **データセット設定ファイル**
   - [finetune_mixed_dataset.json](stable_audio_tools/configs/dataset_configs/finetune_mixed_dataset.json)
   - [school_chime_metadata.py](stable_audio_tools/configs/dataset_configs/custom_metadata/school_chime_metadata.py)
   - [general_metadata.py](stable_audio_tools/configs/dataset_configs/custom_metadata/general_metadata.py)

2. **モデル設定ファイル**
   - [stable_audio_finetune_full.json](stable_audio_tools/configs/model_configs/finetune/stable_audio_finetune_full.json)

3. **学習実行スクリプト**
   - [run_finetune.sh](scripts/run_finetune.sh)
   - [setup_finetune_env.sh](scripts/setup_finetune_env.sh)

### フェーズ2: 評価機能（重要）
4. **評価スクリプト**
   - [clap_score.py](stable_audio_tools/training/metrics/clap_score.py)
   - [evaluate_clap_score.py](scripts/evaluate_clap_score.py)
   - [generate_evaluation_report.py](scripts/generate_evaluation_report.py)

5. **カスタムコールバック**
   - [custom_demo_callback.py](stable_audio_tools/training/custom_demo_callback.py)

### フェーズ3: 高度な機能（オプション）
6. **段階的学習設定**
   - [phased_training.sh](scripts/phased_training.sh)
   - [phase1_pretrain.json](stable_audio_tools/configs/model_configs/finetune/phase1_pretrain.json)
   - [phase2_mixed.json](stable_audio_tools/configs/model_configs/finetune/phase2_mixed.json)
   - [phase3_refine.json](stable_audio_tools/configs/model_configs/finetune/phase3_refine.json)

7. **異常検知**
   - [anomaly_detection.py](stable_audio_tools/training/callbacks/anomaly_detection.py)

8. **LoRA実装（オプション）**
   - [lora.py](stable_audio_tools/models/lora.py)
   - [stable_audio_finetune_lora.json](stable_audio_tools/configs/model_configs/finetune/stable_audio_finetune_lora.json)

### フェーズ4: ドキュメント整備
9. **ドキュメント**
   - [FINETUNING_GUIDE.md](README_PROJECT_FILES/FINETUNING_GUIDE.md)
   - [CONFIG_REFERENCE.md](README_PROJECT_FILES/CONFIG_REFERENCE.md)

---

## 8. まとめ

### ファイル作成数の概要
- **新規作成**: 約25ファイル
- **既存修正**: 約2ファイル（train.pyなど）

### 推定作業時間
- **フェーズ1（基本実装）**: 2-3日
- **フェーズ2（評価機能）**: 2-3日
- **フェーズ3（高度な機能）**: 3-4日
- **フェーズ4（ドキュメント）**: 1-2日

**合計**: 約8-12日（1人での作業を想定）

### 次のアクションステップ
1. データの準備（学校のチャイム音と汎用音データの収集）
2. フェーズ1の実装開始
3. 小規模データセットでの動作確認
4. フェーズ2の評価機能実装
5. 本格的なファインチューニング実行

---

このファイルベース計画書に沿って実装を進めることで、体系的かつ効率的にファインチューニングプロジェクトを完了できます。
