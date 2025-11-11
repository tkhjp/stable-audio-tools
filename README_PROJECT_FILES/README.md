# プロジェクトファイル集（README記載ファイル）

このフォルダには、日本語README（README_ja.md）に記載されているすべての主要ファイルが含まれています。

## 📁 フォルダ構成

```
README_PROJECT_FILES/
├── documentation/          # すべてのREADMEドキュメント
│   ├── README_ja.md       # メイン日本語README（このプロジェクトの説明用）
│   ├── README.md
│   ├── README_audio_mappings_complete.md
│   ├── README_otologic.md
│   ├── README_freeaudio.md
│   └── README_tairakomori_mapping.md
│
├── scripts/               # すべてのPythonスクリプト
│   ├── データ収集スクリプト
│   ├── マッピング生成スクリプト
│   ├── 翻訳・処理スクリプト
│   ├── ファイル整理スクリプト
│   └── 分析スクリプト
│
├── csv_mappings/          # すべてのCSVマッピングファイルとJSONL
│   ├── freesound_filename_url_mapping.csv (262 MB)
│   ├── tairakomori_filename_url_mapping.csv
│   ├── otologic_mp3_to_zip_accurate.csv
│   ├── sequential_audio_mapping_final.csv
│   ├── prompts_update.jsonl (425,294行)
│   └── その他の翻訳・分析CSV
│
├── clap/                  # CLAPトレーニング・評価関連
│   ├── cal_metrics_improved.py
│   ├── train.csv, test.csv, val.csv
│   ├── combined_dataset.csv
│   ├── eval_prompts.csv
│   ├── config_example.json
│   └── README_improvements.md
│
├── ft/                    # ファインチューニングメトリクス
│   ├── all_metrics.csv
│   └── tf_analysis.ipynb
│
├── t5_eval/              # T5類似度分析スクリプト
│   ├── t5_similarity_finder.py
│   ├── analyze_csv_similarity.py
│   └── その他のT5関連スクリプト
│
└── requirements/          # 依存関係ファイル
    ├── requirements_otologic.txt
    ├── requirements_tairakomori.txt
    └── requirements_freeaudio.txt
```

## 📊 サイズ概要

| フォルダ | サイズ | 説明 |
|---------|--------|------|
| **csv_mappings/** | 331 MB | 最大：freesound_filename_url_mapping.csv含む |
| **clap/** | 14 MB | トレーニングデータセット含む |
| **scripts/** | 264 KB | 20個のPythonスクリプト |
| **documentation/** | 64 KB | 6個のREADMEファイル |
| **t5_eval/** | 56 KB | T5分析スクリプト |
| **ft/** | 32 KB | メトリクスとノートブック |
| **requirements/** | 12 KB | 3個の要件ファイル |
| **合計** | **約345 MB** | - |

## 🎯 使用目的

このフォルダは以下の目的で作成されました：

1. **プロジェクト説明用** - README_ja.mdに記載された全ファイルを一箇所に集約
2. **共有・移動用** - 他の人に説明する際に必要なファイルをまとめて提供
3. **アーカイブ用** - 重要ファイルのスナップショット

## 📝 含まれるファイル

### データ収集スクリプト
- `otologic_downloader_complete.py` - OtoLogicダウンローダー
- `freeaudio_annotator.py` - FreeAudioアノテーター
- `test_tairakomori_scraping.py` - 効果音ラボスクレイピングテスト

### マッピング生成スクリプト
- `generate_freesound_mapping.py` - Freesoundマッピング生成
- `generate_tairakomori_mapping.py` - 効果音ラボマッピング生成
- `generate_otologic_zip_mapping_accurate.py` - OtoLogic ZIPマッピング
- `fix_otologic_mapping_accurate.py` - OtoLogicマッピング修正

### 翻訳・処理スクリプト
- `translate_japanese.py` - 日本語翻訳
- `freeaudio_prompt_generator.py` - FreeAudio用プロンプト生成
- `otologic_prompt_generator_final.py` - OtoLogic用プロンプト生成

### ファイル整理スクリプト
- `copy_files_and_generate_csv.py` - ファイルコピーとマッピング生成
- `remove_preview_and_renumber.py` - プレビュー除去
- `remove_duplicates_and_renumber.py` - 重複除去
- `rename_from_csv_fixed.py` - CSVベースリネーム
- `extract_freeaudio_zips.py` - ZIP展開

### 分析スクリプト
- `analyze_freeaudio_durations.py` - 音声時間分析
- `analyze_long_audio_durations.py` - 長時間音声分析
- `analyze_preview_durations.py` - プレビュー時間分析
- `full_dataset_similarity.py` - 全データセット類似度分析
- `get_very_high_ids.py` - 高類似度ID抽出

### CSVマッピングファイル
- `freesound_filename_url_mapping.csv` (262 MB) - 420,543ファイル
- `tairakomori_filename_url_mapping.csv` (1.1 MB) - 5,466ファイル
- `otologic_mp3_to_zip_accurate.csv` (161 KB) - 465マッピング
- `sequential_audio_mapping_final.csv` (740 KB) - 最終マッピング
- `translated_onomatopoeia.csv` - 日本語→英語オノマトペ
- `translated_names.csv` - 日本語→英語名称
- `freeaudio_duration_analysis.csv` - 時間分析
- `long_audio_files_over_5.0s.csv` - 長時間ファイルリスト
- `prompts_update.jsonl` - 425,294プロンプト
- `before_ft_with_similarities.csv` - T5類似度スコア
- `before_ft_with_very_high_ids.csv` - 高類似度グルーピング

### CLAPファイル
- `cal_metrics_improved.py` - 包括的評価システム
- `combine_and_find_similar.py` - データセット結合
- `find_similar_captions.py` - 類似キャプション検索
- `config_example.json` - 設定例
- `train.csv` (6 MB) - トレーニングセット
- `test.csv` (388 KB) - テストセット
- `val.csv` (166 KB) - 検証セット
- `combined_dataset.csv` (7.3 MB) - 統合データセット
- `eval_prompts.csv` (11 KB) - 評価プロンプト
- `README_improvements.md` - CLAP改善ドキュメント

### T5評価スクリプト
- `t5_similarity_finder.py` - T5類似度検索
- `analyze_csv_similarity.py` - CSV類似度分析
- その他の補助スクリプト

### ファインチューニング
- `all_metrics.csv` - 統合メトリクス
- `tf_analysis.ipynb` - TensorFlow分析ノートブック

### ドキュメント
- `README_ja.md` - **メイン日本語README**（このプロジェクト説明用）
- `README.md` - T5類似度ファインダー
- `README_audio_mappings_complete.md` - マッピングシステム
- `README_otologic.md` - OtoLogicダウンローダー
- `README_freeaudio.md` - FreeAudioアノテーター
- `README_tairakomori_mapping.md` - 効果音ラボマッピング

### 依存関係
- `requirements_otologic.txt` - OtoLogic用
- `requirements_tairakomori.txt` - 効果音ラボ用
- `requirements_freeaudio.txt` - FreeAudio用

## 💡 次のステップ

このフォルダ全体を別の場所に移動またはアーカイブできます：

```bash
# 例：別の場所にコピー
cp -r README_PROJECT_FILES /path/to/destination/

# 例：ZIPアーカイブ作成
zip -r README_PROJECT_FILES.zip README_PROJECT_FILES/

# 例：tar.gz圧縮
tar -czf README_PROJECT_FILES.tar.gz README_PROJECT_FILES/
```

## 📌 注意事項

- このフォルダは**README_ja.mdに記載された最新版のみ**を含みます
- 旧バージョンファイル（duplicate files）は含まれていません
- 実際の音声ファイル（audio/）は含まれていません（サイズが大きいため）
- すべてのスクリプトとマッピングファイルは元のプロジェクトからコピーされたものです

## 📧 補足

プロジェクトの全体像を理解するには、まず`documentation/README_ja.md`をお読みください。
