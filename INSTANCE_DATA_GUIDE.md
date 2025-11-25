# インスタンスデータと計算機能ガイド

## 概要

CODSLにインスタンスデータ機能が追加されました。これにより、オントロジー（スキーマ）だけでなく、実際のデータを扱い、計算を実行できるようになりました。

## インスタンスデータとは

### オントロジー vs インスタンス

| 概念 | オントロジー（スキーマ） | インスタンス（データ） |
|------|------------------------|----------------------|
| 目的 | 構造の定義 | 実際のデータ |
| 例（工場） | `Boiler`（ボイラーという概念） | `BoilerA1_001`（実際のボイラー#1） |
| 属性 | `type:gas_boiler` | `fuel_consumption:1000 kg/day` |
| 関係 | `emits`（排出するという関係） | `BoilerA1が2750kg/dayのCO2を排出` |

## アーキテクチャ

```
オントロジー（スキーマ）
    ↓ インスタンス化
インスタンスデータ（実データ）
    ↓ 関手 + 計算ルール
計算結果（変換後のインスタンス）
```

## コアクラス

### 1. Instance

オントロジーの対象のインスタンス

```python
from core import Instance, Object

boiler_type = Object("Boiler", "equipment", (), "ボイラー")

boiler_001 = Instance(
    name="BoilerA1_001",
    object_type=boiler_type,
    attributes={
        "fuel_type": "natural_gas",
        "fuel_consumption": 1000,  # kg/day
        "capacity": 5  # MW
    },
    description="天然ガスボイラー#1"
)

# 属性の取得
fuel = boiler_001.get_attribute("fuel_consumption")  # 1000
```

### 2. InstanceSet

インスタンスのコレクション（特定のカテゴリに属する）

```python
from core import InstanceSet, Category

factory_a = Category("FactoryA", "工場A")

instances = InstanceSet(
    name="FactoryA_Data_2024",
    category=factory_a,
    description="工場Aの2024年データ"
)

instances.add_instance(boiler_001)
```

### 3. ComputationRule

計算ルールの定義と適用

```python
from core import ComputationRule, create_ghg_computation_rules

# GHG排出量計算ルール（組み込み）
rules = create_ghg_computation_rules()

# 計算コンテキスト（排出係数など）
context = {
    'emission_factors': {
        'natural_gas': 2.75,  # kg-CO2/kg-fuel
        'coal': 3.2
    },
    'electricity_factor': 0.512  # kg-CO2/kWh
}

# 関手と計算ルールを適用
result = rules.apply(
    source_instances=factory_instances,
    functor=functor_a_to_ghg,
    context=context
)
```

## 使用例：カーボンフットプリント計算

### ステップ1: オントロジー定義

```python
from core import Category, Object, Morphism, MorphismType

# 工場のオントロジー
factory = Category("Factory", "工場オントロジー")

boiler = Object("Boiler", "equipment", (), "ボイラー")
co2 = Object("CO2_Emission", "emission", (), "CO2排出")

emits = Morphism("emits", boiler, co2, MorphismType.CAUSAL, "排出する")

factory.add_object(boiler)
factory.add_object(co2)
factory.add_morphism(emits)
```

### ステップ2: インスタンスデータ作成

```python
from core import Instance, InstanceSet

instances = InstanceSet("FactoryData", factory)

# ボイラーのインスタンス
boiler_001 = Instance(
    name="Boiler001",
    object_type=boiler,
    attributes={
        "fuel_type": "natural_gas",
        "fuel_consumption": 1000  # kg/day
    }
)

instances.add_instance(boiler_001)
```

### ステップ3: 計算実行

```python
from core import Functor, create_ghg_computation_rules

# GHGレポートへの変換関手
functor = Functor(
    name="F_to_GHG",
    source_category=factory,
    target_category=ghg_report,
    object_map={"CO2_Emission": "StationaryCombustion"},
    morphism_map={}
)

# 計算ルール適用
rules = create_ghg_computation_rules()
ghg_results = rules.apply(instances, functor, context={
    'emission_factors': {'natural_gas': 2.75},
    'electricity_factor': 0.512
})

# 結果表示
for inst in ghg_results.instances.values():
    print(f"{inst.name}: {inst.get_attribute('emission_amount')} kg-CO2")
```

## 実行例

```bash
# カーボンフットプリント計算例題を実行
python example_instance_computation.py
```

### 出力例

```
======================================================================
カーボンフットプリント計算 - 工場A
======================================================================

【工場Aのインスタンスデータ】
  ボイラー: BoilerA1_001
    - 燃料種類: natural_gas
    - 燃料消費量: 1000 kg/day

  CNC機械: CNCMachine01_001
    - 消費電力: 50 kW
    - 稼働時間: 20 h/day

======================================================================
【計算結果：GHGレポート】
======================================================================

排出源: BoilerA1_001_CO2_emission
  - 元設備: BoilerA1_001
  - 排出量: 2750.00 kg-CO2
  - カテゴリ: StationaryCombustion

排出源: CNCMachine01_001_electricity_CO2
  - 元設備: CNCMachine01_001
  - 排出量: 512.00 kg-CO2
  - カテゴリ: PurchasedElectricity

======================================================================
【合計CO2排出量】: 3676.72 kg-CO2/day
【年間排出量（推定）】: 1342.00 t-CO2/year
======================================================================
```

## 組み込み計算ルール

### create_ghg_computation_rules()

GHG（温室効果ガス）排出量を自動計算するルール：

1. **燃焼排出計算**
   - 燃料消費量 × 排出係数 = CO2排出量
   - 対応燃料: natural_gas, coal, diesel

2. **電力排出計算**
   - 電力消費量（kW） × 稼働時間（h） × 電力排出係数 = CO2排出量

### 排出係数

| 燃料種類 | 排出係数 | 単位 |
|---------|---------|-----|
| 天然ガス | 2.75 | kg-CO2/kg-fuel |
| 石炭 | 3.2 | kg-CO2/kg-fuel |
| ディーゼル | 3.1 | kg-CO2/kg-fuel |
| 電力（日本平均） | 0.512 | kg-CO2/kWh |

## JSON形式

### インスタンスデータのJSON

```json
{
  "instances": {
    "FactoryA_Data_2024": {
      "category": "FactoryA",
      "description": "工場Aの2024年データ",
      "instances": [
        {
          "name": "BoilerA1_001",
          "object_type": "Boiler",
          "attributes": {
            "fuel_type": "natural_gas",
            "fuel_consumption": 1000,
            "capacity": 5
          }
        }
      ]
    }
  },
  "computation_context": {
    "emission_factors": {
      "natural_gas": 2.75
    },
    "electricity_factor": 0.512
  }
}
```

## カスタム計算ルールの作成

```python
from core import ComputationRule

def create_custom_rules():
    rules = ComputationRule("CustomRules", "カスタム計算")

    def my_calculation(source_inst, target_inst, functor, context):
        # カスタム計算ロジック
        for inst in source_inst.instances.values():
            value = inst.get_attribute('input_value')
            result = value * 2  # 例：2倍にする

            # 結果インスタンスを作成
            # ...

        return target_inst

    rules.add_rule(my_calculation)
    return rules
```

## ベストプラクティス

1. **オントロジーとインスタンスの分離**
   - オントロジー: 変化しない構造定義
   - インスタンス: 変化するデータ

2. **属性の命名規則**
   - 小文字とアンダースコア: `fuel_consumption`, `operating_hours`
   - 単位を明確に: コメントまたは別の属性で単位を記録

3. **計算コンテキストの管理**
   - 排出係数などの定数は`context`に格納
   - 異なるシナリオで簡単に切り替え可能

4. **検証**
   - 計算前に必須属性の存在確認
   - 単位の一貫性チェック
   - 結果の妥当性検証

## 今後の拡張

- [ ] Workbench UIでのインスタンスデータ入力機能
- [ ] グラフィカルな計算結果表示
- [ ] カスタム計算ルールのGUI作成
- [ ] 時系列データの対応
- [ ] データインポート/エクスポート機能

---

**Created**: 2025-11-25
**Version**: 1.0.0
