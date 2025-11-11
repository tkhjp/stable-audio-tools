# stable-audio-tools トレーニングガイド（初心者向け）

Stability AI製の音声生成モデルのトレーニングツールキット

## 目次
- [プロジェクト概要](#プロジェクト概要)
- [環境要件とインストール](#環境要件とインストール)
- [トレーニングの準備](#トレーニングの準備)
- [defaults.iniの設定パラメータ](#defaultsiniの設定パラメータ)
- [モデル設定ファイル](#モデル設定ファイル)
- [データセット設定ファイル](#データセット設定ファイル)
- [トレーニングの実行](#トレーニングの実行)
- [モデルのアンラップと利用](#モデルのアンラップと利用)
- [よくある問題と解決方法](#よくある問題と解決方法)

---

## プロジェクト概要

**stable-audio-tools**は、Stability AIが提供する音声生成モデルのトレーニング・推論フレームワークです。

### このツールでできること

- カスタムデータセットで音声生成モデルをトレーニング
- 事前学習済みモデルのファインチューニング
- マルチGPU・マルチノードでの分散トレーニング
- 6種類のモデルタイプに対応
  - **Autoencoder（自己符号化器）**: 音声を圧縮・再構成
  - **Diffusion（拡散モデル）**: 条件付き/無条件の音声生成
  - **Diffusion Inpainting**: 音声の一部を補完
  - **Diffusion Autoencoder**: 拡散モデル型の自己符号化器
  - **Language Model**: 言語モデルベースの音声生成

### トレーニングの基本フロー

```
1. 環境構築（Python、PyTorch、CUDA）
2. 音声データセットの準備
3. 設定ファイルの作成（defaults.ini、model_config.json、dataset_config.json）
4. トレーニング実行（train.py）
5. チェックポイントのアンラップ（unwrap_model.py）
6. 推論・評価
```

---

## 環境要件とインストール

### 必須環境

- **Python**: 3.10以上
- **PyTorch**: 2.5以上（Flash Attention、Flex Attentionサポートのため）
- **CUDA**: GPUトレーニングには必須
- **Weights & Biases**: トレーニングログ管理（無料アカウント作成が必要）

### インストール手順

```bash
# リポジトリをクローン
git clone https://github.com/Stability-AI/stable-audio-tools.git
cd stable-audio-tools

# パッケージをインストール
pip install .

# Weights & Biasesにログイン
wandb login
```

---

## トレーニングの準備

トレーニングを始める前に、以下の3つの設定ファイルが必要です:

1. **defaults.ini**: トレーニングのデフォルト設定（リポジトリのルートに存在）
2. **model_config.json**: モデルの構造とハイパーパラメータ
3. **dataset_config.json**: データセットのパスと読み込み設定

---

## defaults.iniの設定パラメータ

`defaults.ini`はトレーニングスクリプト（train.py）のデフォルト設定を定義するファイルです。このファイルの各パラメータを理解することで、トレーニングを最適化できます。

### 基本設定

#### `name`（実行名）
```ini
name = stable_audio_tools
```
- **説明**: トレーニング実行の名前
- **用途**: Weights & Biasesのログやチェックポイントの識別に使用
- **推奨**: プロジェクトや実験内容がわかる名前を付ける（例: `music_gen_v1`, `voice_finetune_20240101`）

#### `project`（プロジェクト名）
```ini
project = None
```
- **説明**: Weights & Biasesのプロジェクト名
- **用途**: 複数の実験をグループ化して管理
- **推奨**: `None`のままだと`name`がプロジェクト名になります

#### `batch_size`（バッチサイズ）
```ini
batch_size = 4
```
- **説明**: GPU1台あたりの1バッチに含まれるサンプル数
- **重要**: GPUメモリに収まる最大値に設定すると学習効率が向上
- **目安**:
  - 24GB VRAM（RTX 3090/4090）: 4-8
  - 16GB VRAM（RTX 4080）: 2-4
  - 48GB VRAM（A6000）: 8-16
- **注意**: メモリ不足（OOM）エラーが出たら値を減らす

### トレーニング継続・チェックポイント管理

#### `recover`（トレーニング再開）
```ini
recover = false
```
- **説明**: `true`にすると最新のチェックポイントから自動的にトレーニングを再開
- **用途**: 中断したトレーニングを続行する場合
- **注意**: 各実行ごとに一意の設定ファイル名が必要

#### `save_top_k`（保存するチェックポイント数）
```ini
save_top_k = -1
```
- **説明**: 保存するモデルチェックポイントの数
- **設定値**:
  - `-1`: すべてのチェックポイントを保存
  - `1`: 最良のモデルのみ保存
  - `3`: 上位3つを保存
- **推奨**: ディスク容量が限られている場合は`1`または`3`

#### `checkpoint_every`（チェックポイント保存間隔）
```ini
checkpoint_every = 10000
```
- **説明**: 何ステップごとにモデルを保存するか
- **目安**:
  - 実験段階: 1000-5000（頻繁に保存）
  - 本格トレーニング: 10000-50000
- **注意**: 値が小さいほどディスク使用量が増加

### マルチGPU・分散トレーニング設定

#### `num_nodes`（ノード数）
```ini
num_nodes = 2
```
- **説明**: トレーニングに使用するサーバー（ノード）の数
- **通常**: 1台のサーバーなら`1`
- **用途**: 複数の物理マシンで分散トレーニングする場合に使用

#### `strategy`（マルチGPU戦略）
```ini
strategy = "ddp"
```
- **説明**: PyTorch Lightningの分散学習戦略
- **選択肢**:
  - `"ddp"`: DistributedDataParallel（標準、推奨）
  - `"deepspeed"`: DeepSpeed ZeRO Stage 2（メモリ効率が高い、超大規模モデル向け）
  - `None`（空文字）: 単一GPU
- **推奨**:
  - 複数GPU: `"ddp"`
  - 巨大モデル: `"deepspeed"`

#### `num_workers`（データローダーのワーカー数）
```ini
num_workers = 12
```
- **説明**: データ読み込みに使用するCPUプロセス数
- **推奨**: CPUコア数の50-75%程度
- **例**: 16コアCPUなら8-12
- **注意**: 多すぎるとメモリを圧迫、少なすぎるとGPUが待機状態に

### 精度・最適化設定

#### `precision`（演算精度）
```ini
precision = "bf16-mixed"
```
- **説明**: トレーニング時の浮動小数点精度
- **選択肢**:
  - `"bf16-mixed"`: BFloat16混合精度（推奨、Ampere以降のGPU）
  - `"16-mixed"`: FP16混合精度（古いGPU対応）
  - `"32"`: 全精度FP32（遅いが安定）
- **効果**: 低精度ほど高速でメモリ節約、学習の安定性は若干低下
- **推奨**: RTX 3000/4000シリーズ以降なら`"bf16-mixed"`

#### `accum_batches`（勾配累積バッチ数）
```ini
accum_batches = 1
```
- **説明**: 勾配を更新する前に累積するバッチ数
- **用途**: GPUメモリが足りない時、実質的なバッチサイズを増やす
- **例**: `batch_size=2`、`accum_batches=4` → 実質バッチサイズ8
- **デメリット**: トレーニング速度が低下

#### `gradient_clip_val`（勾配クリッピング）
```ini
gradient_clip_val = 0.0
```
- **説明**: 勾配の最大値を制限（0.0は無効）
- **用途**: 勾配爆発を防ぐ
- **推奨**: 学習が不安定な場合は`1.0`や`5.0`を試す

### その他の重要設定

#### `seed`（乱数シード）
```ini
seed = 42
```
- **説明**: 乱数生成の初期値
- **用途**: 再現性のある実験を行う
- **注意**: 同じシードでも完全に同一の結果にならない場合がある（GPU並列化の影響）

#### `val_every`（検証実行間隔）
```ini
val_every = -1
```
- **説明**: 何ステップごとに検証データセットで評価するか
- **設定値**:
  - `-1`: 検証を実行しない
  - `1000`: 1000ステップごとに検証
- **推奨**: 検証データがある場合は5000-10000

### ファイルパス設定

#### `model_config`（モデル設定ファイル）
```ini
model_config = ''
```
- **説明**: モデル構造を定義するJSONファイルのパス
- **必須**: トレーニング時に必ずコマンドライン引数で指定

#### `dataset_config`（データセット設定ファイル）
```ini
dataset_config = ''
```
- **説明**: トレーニングデータの場所と形式を定義するJSONファイル
- **必須**: トレーニング時に必ずコマンドライン引数で指定

#### `save_dir`（保存ディレクトリ）
```ini
save_dir = ''
```
- **説明**: チェックポイントを保存するディレクトリ
- **推奨**: 大容量ディスクのパスを指定（1チェックポイント = 数GB）

#### `ckpt_path`（チェックポイントパス）
```ini
ckpt_path = ''
```
- **説明**: トレーニングを継続するための「ラップされた」チェックポイント
- **用途**: 中断したトレーニングを再開

#### `pretrained_ckpt_path`（事前学習済みモデルパス）
```ini
pretrained_ckpt_path = ''
```
- **説明**: ファインチューニングの起点となる「アンラップされた」モデル
- **用途**: 既存モデルの重みを初期値として使用

#### `pretransform_ckpt_path`（事前変換モデルパス）
```ini
pretransform_ckpt_path = ''
```
- **説明**: 潜在拡散モデルで使用するAutoEncoderのパス
- **用途**: 音声を低次元に圧縮するエンコーダー・デコーダーを読み込む

---

## モデル設定ファイル

`model_config.json`はモデルのアーキテクチャを定義します。以下は基本的な構造です:

### 基本構造

```json
{
  "model_type": "diffusion_cond",
  "sample_size": 4194304,
  "sample_rate": 44100,
  "audio_channels": 2,
  "model": {
    "pretransform": { ... },
    "conditioning": { ... },
    "diffusion": { ... }
  },
  "training": {
    "learning_rate": 1e-4,
    ...
  }
}
```

### 主要パラメータ

- **`model_type`**: モデルの種類（`diffusion_cond`, `autoencoder`, など）
- **`sample_size`**: トレーニング時の音声サンプル長（サンプル数）
  - 例: `4194304` = 44100Hz × 約95秒
- **`sample_rate`**: サンプリングレート（Hz）
  - 標準: `44100` (CD品質), `48000` (プロ品質), `16000` (音声)
- **`audio_channels`**: チャンネル数（`1` = モノラル、`2` = ステレオ）

**重要**: モデル設定の詳細は、[stable_audio_tools/configs/model_configs/](stable_audio_tools/configs/model_configs/)内のサンプルを参照してください。

---

## データセット設定ファイル

`dataset_config.json`はトレーニングデータの場所と読み込み方法を指定します。

### ローカルディレクトリを使用する場合

```json
{
  "dataset_type": "audio_dir",
  "datasets": [
    {
      "id": "my_audio",
      "path": "/path/to/audio/dataset/"
    }
  ],
  "random_crop": true
}
```

- **`dataset_type`**: `"audio_dir"`（ローカルディレクトリ）
- **`path`**: 音声ファイルがあるディレクトリ（サブディレクトリも再帰的に検索）
- **`random_crop`**:
  - `true`: ランダムな位置から切り出し
  - `false`: 常に先頭から切り出し

### Amazon S3のWebDatasetを使用する場合

```json
{
  "dataset_type": "s3",
  "datasets": [
    {
      "id": "s3-audio",
      "s3_path": "s3://my-bucket/datasets/audio/"
    }
  ],
  "random_crop": true
}
```

### カスタムメタデータの追加

条件付き生成（プロンプトベース生成など）には、メタデータが必要です:

```json
{
  "dataset_type": "audio_dir",
  "datasets": [
    {
      "id": "my_audio",
      "path": "/path/to/audio/dataset/",
      "custom_metadata_module": "/path/to/custom_metadata.py"
    }
  ],
  "random_crop": true
}
```

**custom_metadata.pyの例**:
```python
def get_custom_metadata(info, audio):
    # ファイルパスをプロンプトとして使用
    return {"prompt": info["relpath"]}
```

---

## トレーニングの実行

### 基本的なトレーニングコマンド

```bash
python3 ./train.py \
  --dataset-config /path/to/dataset_config.json \
  --model-config /path/to/model_config.json \
  --name my_training_run
```

### よく使う実践的なコマンド例

#### 例1: シングルGPUでの基本トレーニング

```bash
python3 ./train.py \
  --dataset-config ./configs/my_dataset.json \
  --model-config ./configs/my_model.json \
  --name music_gen_exp01 \
  --batch-size 4 \
  --save-dir ./checkpoints \
  --checkpoint-every 5000
```

#### 例2: 4GPUでの分散トレーニング

```bash
python3 ./train.py \
  --dataset-config ./configs/my_dataset.json \
  --model-config ./configs/my_model.json \
  --name music_gen_exp02 \
  --batch-size 8 \
  --num-gpus 4 \
  --strategy ddp \
  --save-dir ./checkpoints \
  --num-workers 16
```

#### 例3: 勾配累積を使ったメモリ節約トレーニング

```bash
python3 ./train.py \
  --dataset-config ./configs/my_dataset.json \
  --model-config ./configs/my_model.json \
  --name music_gen_lowmem \
  --batch-size 2 \
  --accum-batches 4 \
  --save-dir ./checkpoints
```
※実質バッチサイズ = 2 × 4 = 8

#### 例4: 事前学習済みモデルのファインチューニング

```bash
python3 ./train.py \
  --dataset-config ./configs/my_dataset.json \
  --model-config ./configs/my_model.json \
  --pretrained-ckpt-path ./pretrained/stable_audio_open_unwrapped.ckpt \
  --name finetune_stable_audio \
  --batch-size 4 \
  --save-dir ./checkpoints
```

### トレーニング中の監視

- **Weights & Biases**: ブラウザで`https://wandb.ai/`にアクセスし、リアルタイムでロスや生成サンプルを確認
- **ターミナル出力**: ステップごとのロス値やGPU使用率を表示

---

## モデルのアンラップと利用

### アンラップとは？

トレーニング中に保存されるチェックポイントには、以下が含まれています:
- モデルの重み
- オプティマイザの状態
- EMAモデル
- ディスクリミネータ（Autoencoder使用時）

これらをすべて含むファイルは非常に大きいため、推論時には不要な情報を削除した「アンラップ」を行います。

### アンラップの実行

```bash
python3 ./unwrap_model.py \
  --model-config /path/to/model_config.json \
  --ckpt-path /path/to/wrapped_checkpoint.ckpt \
  --name model_unwrapped
```

### アンラップされたモデルの用途

- Gradioインターフェースでの推論
- 他のモデルの事前変換（pretransform）として使用
- ファインチューニングの起点として使用

---

## よくある問題と解決方法

### 1. GPUメモリ不足（CUDA Out of Memory）

**症状**: `RuntimeError: CUDA out of memory`

**解決策**:
- `batch_size`を減らす（4 → 2 → 1）
- `accum_batches`を増やして実質バッチサイズを維持
- `precision`を`"bf16-mixed"`に変更
- `model_config.json`のモデルサイズを小さくする

### 2. データローダーが遅い

**症状**: GPU使用率が低い、トレーニングが進まない

**解決策**:
- `num_workers`を増やす（8 → 12 → 16）
- データを高速なSSD/NVMeに移動
- `random_crop = false`で試す

### 3. トレーニングが不安定（ロスがNaNになる）

**症状**: Loss値が`NaN`や`inf`になる

**解決策**:
- `gradient_clip_val`を設定（例: `1.0`）
- 学習率を下げる（`model_config.json`の`learning_rate`を`1e-5`に）
- `precision`を`"32"`（全精度）に変更

### 4. Weights & Biasesにログインできない

**解決策**:
```bash
wandb login
# APIキーをブラウザ（https://wandb.ai/authorize）から取得して入力
```

または、W&Bを使わない場合:
```bash
python3 ./train.py --logger None ...
```

### 5. チェックポイントが大きすぎる

**解決策**:
- `save_top_k`を`1`または`3`に設定
- `checkpoint_every`を大きくする（10000 → 50000）
- トレーニング後にアンラップしたモデルのみ保管

---

## 追加リソースとヘルプ

- **公式リポジトリ**: https://github.com/Stability-AI/stable-audio-tools
- **サンプル設定**: [stable_audio_tools/configs/](stable_audio_tools/configs/)
- **データセット詳細**: [docs/datasets.md](docs/datasets.md)
- **Weights & Biases**: https://wandb.ai/
- **PyTorch Lightning**: https://lightning.ai/docs/pytorch/

---

このガイドを参考に、独自の音声生成モデルのトレーニングを始めましょう！
