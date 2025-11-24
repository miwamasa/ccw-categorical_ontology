# 圏論的オントロジーDSL (CODSL)

## 概要

CODSL (Categorical Ontology DSL) は、圏論に基づくオントロジーの形式的記述と演算を行うためのドメイン特化言語およびランタイムシステムです。

### 理論的背景

従来のオントロジー（Entity-Relationship モデル）には以下の限界があります：

1. **演算の閉包性がない**: オントロジー同士の足し算、引き算などが形式的に定義されていない
2. **意味的距離が未定義**: オントロジー間の「近さ」を測る尺度がない
3. **変換の構造保存が保証されない**: マッピング時に重要な関係が失われる可能性

CODSLは、オントロジーを**圏（Category）**として捉えることで、これらの問題を解決します：

| 概念 | 従来のオントロジー | 圏論的オントロジー |
|------|-------------------|-------------------|
| 概念 | Entity | 対象 (Object) |
| 関係 | Relationship | 射 (Morphism) |
| 変換 | マッピング | 関手 (Functor) |
| アライメント | 類似度計算 | 自然変換 (Natural Transformation) |
| 合成 | 未定義 | 関手の合成 |

### 結果意味論

従来の操作的意味論（各ステップを完全に形式化）ではなく、**結果意味論**を採用：

- **構造的整合性**: 圏論の法則で保証
- **意味的妥当性**: LLMによる検証
- **実用的正確性**: ドメインルールによる検証

これにより、形式的な厳密性と実用的な柔軟性を両立させています。

## インストール

```bash
# リポジトリのクローン
git clone <repository>
cd categorical_ontology

# 依存関係なし（標準ライブラリのみ）
python -m examples.carbon_footprint
```

## クイックスタート

### Python API

```python
from core import (
    Object, Morphism, Category, Functor,
    MorphismType, CategoryOperations
)

# 圏（オントロジー）の作成
cat = Category("MyOntology", "サンプルオントロジー")

# 対象（Entity）の追加
obj_a = Object(
    name="Product",
    domain="manufacturing",
    attributes=("type:physical",),
    semantic_signature="製造される物理的製品"
)
cat.add_object(obj_a)

# 射（Relationship）の追加
morph = Morphism(
    name="produces",
    source=factory_obj,
    target=product_obj,
    morphism_type=MorphismType.FUNCTIONAL,
    semantic_description="工場が製品を生産する"
)
cat.add_morphism(morph)

# 演算: 直和（並列統合）
combined = CategoryOperations.coproduct(cat1, cat2)

# 演算: 差分
diff = CategoryOperations.difference(cat1, cat2)
```

### DSL構文

```
ONTOLOGY FactoryA {
    OBJECT Boiler : equipment {
        attributes: [gas_boiler, 5MW]
        semantic: "天然ガス焚きボイラー"
    }
    
    OBJECT CO2Emission : emission {
        attributes: [scope1, combustion]
        semantic: "燃焼由来CO2排出"
    }
    
    MORPHISM emits : Boiler -> CO2Emission {
        type: CAUSAL
        semantic: "ボイラー運転によりCO2が排出される"
    }
}

FUNCTOR F : FactoryA -> GHGReport {
    MAP OBJECT CO2Emission -> StationaryCombustion
    RULE "Scope1排出源は固定燃焼にマップ"
}

OPERATION {
    Combined = COPRODUCT(FactoryA, FactoryB)
    OnlyA = DIFFERENCE(FactoryA, FactoryB)
}
```

## 演算リファレンス

### 1. 直和 (Coproduct): A + B

二つのオントロジーを**並列に**結合します。

```python
result = CategoryOperations.coproduct(cat1, cat2)
```

**特徴**:
- 両方の対象と射がすべて含まれる
- 名前衝突を避けるためタグ付け: `cat1.X`, `cat2.X`
- 新しい関係は追加されない

**ユースケース**: 
- 複数工場のデータ統合
- 異なるドメインの併合

### 2. 直積 (Product): A × B

二つのオントロジーの**全ペア**を生成します。

```python
result = CategoryOperations.product(cat1, cat2)
```

**特徴**:
- 対象数: |A| × |B|
- 射数: |A射| × |B射|
- ペア名: `(X, Y)`

**ユースケース**:
- クロス分析（製品×市場など）
- 多次元データモデリング

### 3. 差分 (Difference): A - B

Aに含まれるがBに含まれない構造を抽出します。

```python
result = CategoryOperations.difference(cat1, cat2)
```

**特徴**:
- 名前とドメインの両方で比較
- 同名でもドメインが異なれば別物
- 孤立した射は含まれない

**ユースケース**:
- 差分レポート
- 固有機能の特定

### 4. Pullback: 共通構造抽出

二つのオントロジーが共通のターゲットに対して「同じもの」を指す部分を抽出します。

```python
result = CategoryOperations.pullback(
    cat1, cat2, common_target,
    functor1, functor2
)
```

**数学的定義**:
```
F: A → C, G: B → C に対して
A ×_C B = {(a,b) | F(a) = G(b)}
```

**ユースケース**:
- 異なるシステム間の共通概念抽出
- データ統合の接点特定

### 5. Pushout: 構造融合

共通の源から分岐した二つのオントロジーを融合します。

```python
result = CategoryOperations.pushout(
    cat1, cat2, common_source,
    functor1, functor2
)
```

**ユースケース**:
- スキーマ統合
- バージョン分岐のマージ

### 6. 関手の合成: G ∘ F

複数段階の変換を一つの変換にまとめます。

```python
composed = FunctorOperations.compose(g, f)
# G: B → C, F: A → B のとき
# G ∘ F: A → C
```

**ユースケース**:
- サプライチェーン全体の変換
- 多段階のデータフロー

## 製造業カーボンフットプリント例題

### シナリオ

```
工場A（自動車部品）     工場B（電子機器）
    ↓                      ↓
    └──────┬───────────────┘
           ↓
    GHGプロトコルレポート
```

### オントロジー構造

**工場A**:
- 設備: ボイラー、CNC機械、塗装ブース
- プロセス: 蒸気生成、機械加工、塗装
- 排出: CO2（燃焼）、CO2（電力）、VOC

**工場B**:
- 設備: SMTライン、リフロー炉、クリーンルーム
- プロセス: 基板組立、はんだ付け
- 排出: CO2（電力）、N2O

**GHGレポート**:
- Scope分類: Scope1、Scope2、Scope3
- カテゴリ: 固定燃焼、プロセス排出、購入電力

### 演算結果

1. **直和** (A + B): 20対象、12射
   - すべての設備、プロセス、排出が統合

2. **関手** (Factory → GHG): 変換マッピング
   - CO2_Combustion → StationaryCombustion
   - CO2_Electricity → PurchasedElectricity
   - VOC_Emission → ProcessEmissions

3. **Pullback**: 共通構造
   - 両工場の電力由来CO2排出
   - プロセス排出（VOC と N2O）

4. **差分** (A - B): 工場A固有の9対象
   - ボイラー、CNC機械、塗装ブース
   - 燃焼由来CO2、VOC排出、天然ガス

## LLM検証

### 検証プロンプトの自動生成

```python
from core import SemanticValidator, ValidationLevel

validator = SemanticValidator(llm_client)
result = validator.validate(context, ValidationLevel.SEMANTIC)
```

### 検証項目

1. **意味的対応**: マッピングは意味的に妥当か？
2. **情報損失**: 重要な情報が失われていないか？
3. **構造保存**: 関係性の本質が保存されているか？

### 検証レベル

| レベル | 説明 | 検証内容 |
|--------|------|----------|
| STRUCTURAL | 構造的検証のみ | 型チェック、参照整合性 |
| SEMANTIC | 意味的検証を含む | LLMによる意味分析 |
| PRAGMATIC | 実用的検証 | ドメイン固有ルール |

## ドメインルール

### GHGレポート用ルール

```python
from core import create_ghg_rules

rules = create_ghg_rules()
issues = rules.validate("ghg", data)
```

**組み込みルール**:
- Scope分類の必須
- 排出量は非負
- 単位はCO2換算

### カスタムルール追加

```python
rules.add_rule(
    "ghg",
    lambda data: data.get("reporting_year") >= 2020,
    "報告年は2020年以降"
)
```

## アーキテクチャ

```
categorical_ontology/
├── core/
│   ├── dsl.py          # コアDSL（Category, Functor, 演算）
│   ├── validator.py    # LLM検証器、ドメインルール
│   └── interpreter.py  # DSLパーサー、インタープリター
├── examples/
│   └── carbon_footprint.py  # カーボンフットプリント例題
└── tests/
    └── test_codsl.py   # テストスイート
```

## テスト実行

```bash
cd categorical_ontology
python -m tests.test_codsl
```

**テストカバレッジ**:
- 圏の基本操作
- 演算の正確性
- 関手の構造保存
- DSLパーサー
- 検証器
- 完全シナリオ

## 拡張ポイント

### 新しい演算の追加

`CategoryOperations` クラスに静的メソッドを追加:

```python
@staticmethod
def my_operation(cat1: Category, cat2: Category) -> Category:
    result = Category("Result", "My operation result")
    # 実装
    return result
```

### 新しい射タイプの追加

`MorphismType` enumに追加:

```python
class MorphismType(Enum):
    # 既存...
    MY_TYPE = "my_type"
```

### LLMクライアントの統合

```python
class MyLLMClient:
    def complete(self, prompt: str) -> str:
        # API呼び出し
        return response

validator = SemanticValidator(MyLLMClient())
```

## ライセンス

MIT License

## 参考文献

1. Spivak, D.I. "Ologs: A Categorical Framework for Knowledge Representation"
2. Baez, J.C. & Stay, M. "Physics, Topology, Logic and Computation: A Rosetta Stone"
3. GHG Protocol Corporate Standard
