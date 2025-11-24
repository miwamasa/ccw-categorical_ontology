# CODSL Workbench 使い方ガイド

## 🚀 起動方法

```bash
# ワークベンチサーバーを起動
cd categorical_ontology
python workbench_server.py 8000

# ブラウザで以下のURLにアクセス
# http://localhost:8000/
```

## 📋 機能概要

CODSL Workbenchは、圏論的オントロジーDSLの対話的なWebインターフェースです。

### 主な機能

1. **例題の閲覧**: 組み込み例題とカスタム例題の一覧表示
2. **圏の視覚化**: 対象（Object）と射（Morphism）をグラフで表示
3. **演算の実行**: 直和、直積、差分、Pullback、関手適用
4. **結果の表示**: JSON形式での詳細な結果表示

## 🎯 使い方

### 1. 例題の選択

左サイドバーから例題を選択します：

- **カーボンフットプリント（工場A+B）**: 製造業のGHG排出量管理（組み込み例題）
- **シンプルなデータベーススキーマ**: 顧客管理と注文管理の統合
- **サプライチェーン管理**: 原材料から製品までのフロー

### 2. 圏の表示

例題を選択すると、各圏が以下の情報とともに表示されます：

- **圏名**: カテゴリの名前
- **説明**: カテゴリの概要
- **統計**: 対象数と射数
- **グラフ**: 対象と射の視覚的表現

### 3. 演算の実行

#### 直和 (Coproduct): A + B

二つの圏を並列に統合します。

**使用例**:
- 複数工場のデータ統合
- 異なるドメインの併合

**手順**:
1. 「直和 (A + B)」ボタンをクリック
2. 圏Aと圏Bを選択
3. 「実行」ボタンをクリック

**結果**:
- 両方の対象がタグ付きで含まれる
- 名前衝突を避けるため `cat1.X`, `cat2.X` の形式

#### 直積 (Product): A × B

二つの圏の全ペアを生成します。

**使用例**:
- クロス分析（製品×市場など）
- 多次元データモデリング

**手順**:
1. 「直積 (A × B)」ボタンをクリック
2. 圏Aと圏Bを選択
3. 「実行」ボタンをクリック

**結果**:
- 対象数: |A| × |B|
- ペア名: `(X, Y)` の形式

#### 差分 (Difference): A - B

Aに含まれるがBに含まれない構造を抽出します。

**使用例**:
- 差分レポート
- 固有機能の特定

**手順**:
1. 「差分 (A - B)」ボタンをクリック
2. 圏Aと圏Bを選択
3. 「実行」ボタンをクリック

**結果**:
- Aの固有対象と射のみが含まれる

#### Pullback

二つの圏が共通のターゲットに対して「同じもの」を指す部分を抽出します。

**使用例**:
- 異なるシステム間の共通概念抽出
- データ統合の接点特定

**手順**:
1. 「Pullback」ボタンをクリック
2. 圏A、圏B、ターゲット圏を選択
3. 関手1（A → Target）と関手2（B → Target）を選択
4. 「実行」ボタンをクリック

#### 関手適用

圏の変換を実行します。

**使用例**:
- スキーマ変換
- オントロジーマッピング

**手順**:
1. 「関手適用」ボタンをクリック
2. 関手を選択
3. 「実行」ボタンをクリック

**結果**:
- 対象マッピング
- 射マッピング
- 構造保存の検証結果

### 4. 結果の確認

演算を実行すると、「実行結果」タブに結果が表示されます：

- **圏情報**: 名前、対象数、射数
- **対象一覧**: 各対象の詳細情報
- **JSON出力**: 完全な結果データ

## 📝 カスタム例題の追加

### JSON形式での例題作成

`examples/`ディレクトリに新しいJSONファイルを作成します：

```json
{
  "title": "例題タイトル",
  "description": "例題の説明",
  "categories": [
    {
      "name": "Category1",
      "description": "カテゴリの説明",
      "objects": [
        {
          "name": "ObjectName",
          "domain": "ドメイン",
          "attributes": ["attr1", "attr2"],
          "semantic": "意味的な説明"
        }
      ],
      "morphisms": [
        {
          "name": "morphism_name",
          "source": "ObjectName1",
          "target": "ObjectName2",
          "type": "FUNCTIONAL",
          "semantic": "射の説明"
        }
      ]
    }
  ],
  "functors": [
    {
      "name": "Functor1",
      "source": "Category1",
      "target": "Category2",
      "description": "関手の説明",
      "object_map": {
        "SourceObject": "TargetObject"
      },
      "morphism_map": {
        "SourceMorphism": "TargetMorphism"
      }
    }
  ]
}
```

### 射のタイプ

- `FUNCTIONAL`: 関数的関係
- `CAUSAL`: 因果関係
- `STRUCTURAL`: 構造的関係
- `TEMPORAL`: 時間的関係

## 🔧 APIエンドポイント

ワークベンチはREST APIも提供しています：

### GET /api/examples

例題一覧を取得

**レスポンス**:
```json
[
  {
    "name": "example_name",
    "title": "Example Title",
    "description": "Description"
  }
]
```

### GET /api/example/{name}

特定の例題を取得

**レスポンス**: 例題の完全なJSON

### POST /api/execute

演算を実行

**リクエスト**:
```json
{
  "operation": "coproduct",
  "cat1": "CategoryName1",
  "cat2": "CategoryName2",
  "categories": [...],
  "functors": [...]
}
```

**レスポンス**: 演算結果の圏のJSON

### POST /api/save_example

例題を保存

**リクエスト**: 例題のJSON

**レスポンス**:
```json
{
  "success": true,
  "path": "/path/to/example.json"
}
```

## 🎨 カスタマイズ

### ポート番号の変更

```bash
python workbench_server.py 9000  # ポート9000で起動
```

### 例題ディレクトリ

例題は `examples/` ディレクトリに配置します。サーバーは自動的にJSONファイルを検出します。

## 🐛 トラブルシューティング

### ポートが使用中の場合

```bash
# プロセスを確認
lsof -i :8000

# プロセスを終了
pkill -f workbench_server
```

### ブラウザで接続できない場合

1. サーバーが起動しているか確認
2. ファイアウォール設定を確認
3. localhost以外からアクセスする場合は、`workbench_server.py`の`server_address`を変更

## 📚 参考情報

- メインREADME: `README.md`
- コアDSL: `core/dsl.py`
- テストスイート: `tests/test_codsl.py`
- 例題: `examples/carbon_footprint.py`

## 💡 ヒント

1. **グラフの見方**: 円形配置された対象（ノード）と、それらを結ぶ射（矢印）
2. **タブの切り替え**: 「圏の表示」と「実行結果」タブを切り替えて確認
3. **JSON出力**: プログラムから利用する場合は、JSON出力をコピーして使用
4. **例題の組み合わせ**: 複数の演算を組み合わせて複雑な変換を実現

## 🌟 実践例

### 例1: 二つの工場データを統合

1. 「カーボンフットプリント」例題を選択
2. 「直和 (A + B)」を選択
3. 圏A = FactoryA, 圏B = FactoryB
4. 実行 → 両工場の設備と排出源が統合される

### 例2: データベーススキーマの共通部分を抽出

1. 「シンプルなデータベーススキーマ」例題を選択
2. 「差分 (A - B)」を選択
3. 圏A = CustomerSchema, 圏B = OrderSchema
4. 実行 → CustomerSchema固有の要素が抽出される

### 例3: スキーマ変換の検証

1. 例題を選択
2. 「関手適用」を選択
3. 関手を選択
4. 実行 → マッピングの妥当性と構造保存が確認される

---

**Created**: 2025-11-24
**Version**: 1.0.0
**License**: MIT
