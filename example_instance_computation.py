#!/usr/bin/env python3
"""
カーボンフットプリント計算の実例
工場のインスタンスデータからGHG排出量を計算
"""

from core import (
    Object, Morphism, Category, Functor,
    MorphismType, CategoryOperations,
    Instance, InstanceSet, create_ghg_computation_rules
)

# =================================================================
# 1. オントロジー定義（スキーマ）
# =================================================================

# 工場Aのオントロジー
factory_a = Category("FactoryA", "Factory A Production Ontology")

# 対象
boiler = Object("Boiler", "equipment", ("type:gas_boiler",), "天然ガス焚きボイラー")
cnc_machine = Object("CNCMachine", "equipment", ("type:cnc",), "CNC加工機")
co2_combustion = Object("CO2_Combustion", "emission", ("scope:1",), "燃焼由来CO2")
co2_electricity = Object("CO2_Electricity", "emission", ("scope:2",), "電力由来CO2")

factory_a.add_object(boiler)
factory_a.add_object(cnc_machine)
factory_a.add_object(co2_combustion)
factory_a.add_object(co2_electricity)

# 射
emits_combustion = Morphism(
    "emits_combustion",
    boiler, co2_combustion,
    MorphismType.CAUSAL,
    "ボイラーがCO2を排出"
)
emits_electricity = Morphism(
    "emits_electricity",
    cnc_machine, co2_electricity,
    MorphismType.CAUSAL,
    "CNC機械が電力由来CO2を排出"
)

factory_a.add_morphism(emits_combustion)
factory_a.add_morphism(emits_electricity)

# GHGレポートのオントロジー
ghg_report = Category("GHGReport", "GHG Protocol Report Structure")

# 対象
scope1 = Object("Scope1", "scope", (), "直接排出")
scope2 = Object("Scope2", "scope", (), "間接排出（電力）")
stationary_combustion = Object("StationaryCombustion", "category", ("scope:1",), "固定燃焼")
purchased_electricity = Object("PurchasedElectricity", "category", ("scope:2",), "購入電力")
emission_amount = Object("EmissionAmount", "data", (), "排出量データ")

ghg_report.add_object(scope1)
ghg_report.add_object(scope2)
ghg_report.add_object(stationary_combustion)
ghg_report.add_object(purchased_electricity)
ghg_report.add_object(emission_amount)

# 射
scope1_includes = Morphism(
    "scope1_includes_combustion",
    scope1, stationary_combustion,
    MorphismType.STRUCTURAL,
    "Scope1は固定燃焼を含む"
)
scope2_includes = Morphism(
    "scope2_includes_electricity",
    scope2, purchased_electricity,
    MorphismType.STRUCTURAL,
    "Scope2は購入電力を含む"
)

ghg_report.add_morphism(scope1_includes)
ghg_report.add_morphism(scope2_includes)

# 関手（工場A → GHGレポート）
functor_a_to_ghg = Functor(
    name="F_FactoryA_to_GHG",
    source_category=factory_a,
    target_category=ghg_report,
    object_map={
        "CO2_Combustion": "StationaryCombustion",
        "CO2_Electricity": "PurchasedElectricity"
    },
    morphism_map={},
    semantic_mapping_rules=["工場AからGHGレポートへの変換"]
)

# =================================================================
# 2. インスタンスデータ（実際の工場データ）
# =================================================================

factory_a_instances = InstanceSet(
    name="FactoryA_Data_2024",
    category=factory_a,
    description="工場Aの2024年実績データ"
)

# ボイラーのインスタンス
boiler_001 = Instance(
    name="BoilerA1_001",
    object_type=boiler,
    attributes={
        "fuel_type": "natural_gas",
        "fuel_consumption": 1000,  # kg/day
        "capacity": 5,  # MW
        "operating_hours": 24
    },
    description="天然ガスボイラー#1"
)

# CNC機械のインスタンス
cnc_001 = Instance(
    name="CNCMachine01_001",
    object_type=cnc_machine,
    attributes={
        "power_consumption": 50,  # kW
        "operating_hours": 20,  # hours/day
        "model": "DMU-650"
    },
    description="CNC加工機#1"
)

cnc_002 = Instance(
    name="CNCMachine02_001",
    object_type=cnc_machine,
    attributes={
        "power_consumption": 45,  # kW
        "operating_hours": 18,  # hours/day
        "model": "DMU-600"
    },
    description="CNC加工機#2"
)

factory_a_instances.add_instance(boiler_001)
factory_a_instances.add_instance(cnc_001)
factory_a_instances.add_instance(cnc_002)

# =================================================================
# 3. 計算ルールの適用
# =================================================================

print("=" * 70)
print("カーボンフットプリント計算 - 工場A")
print("=" * 70)
print()

print("【工場Aのインスタンスデータ】")
print(f"  ボイラー: {boiler_001.name}")
print(f"    - 燃料種類: {boiler_001.get_attribute('fuel_type')}")
print(f"    - 燃料消費量: {boiler_001.get_attribute('fuel_consumption')} kg/day")
print(f"    - 稼働時間: {boiler_001.get_attribute('operating_hours')} h/day")
print()
print(f"  CNC機械: {cnc_001.name}")
print(f"    - 消費電力: {cnc_001.get_attribute('power_consumption')} kW")
print(f"    - 稼働時間: {cnc_001.get_attribute('operating_hours')} h/day")
print()
print(f"  CNC機械: {cnc_002.name}")
print(f"    - 消費電力: {cnc_002.get_attribute('power_consumption')} kW")
print(f"    - 稼働時間: {cnc_002.get_attribute('operating_hours')} h/day")
print()

# 計算コンテキスト（排出係数など）
context = {
    'emission_factors': {
        'natural_gas': 2.75,  # kg-CO2/kg-fuel (天然ガスの排出係数)
        'coal': 3.2,
        'diesel': 3.1
    },
    'electricity_factor': 0.512  # kg-CO2/kWh (電力の排出係数、日本の平均)
}

# 計算ルールを作成
computation_rules = create_ghg_computation_rules()

# 関手と計算ルールを適用してGHGレポートを生成
ghg_instances = computation_rules.apply(
    source_instances=factory_a_instances,
    functor=functor_a_to_ghg,
    context=context
)

print("=" * 70)
print("【計算結果：GHGレポート】")
print("=" * 70)
print()

total_emissions = 0
for inst in ghg_instances.instances.values():
    emission_amount = inst.get_attribute('emission_amount', 0)
    total_emissions += emission_amount

    print(f"排出源: {inst.name}")
    print(f"  - 元設備: {inst.get_attribute('source')}")
    print(f"  - 排出量: {emission_amount:.2f} {inst.get_attribute('unit')}")
    print(f"  - カテゴリ: {inst.object_type.name}")
    if inst.get_attribute('fuel_type'):
        print(f"  - 燃料種類: {inst.get_attribute('fuel_type')}")
    if inst.get_attribute('energy_consumption'):
        print(f"  - エネルギー消費: {inst.get_attribute('energy_consumption'):.2f} kWh/day")
    print()

print("=" * 70)
print(f"【合計CO2排出量】: {total_emissions:.2f} kg-CO2/day")
print(f"【年間排出量（推定）】: {total_emissions * 365 / 1000:.2f} t-CO2/year")
print("=" * 70)
print()

# =================================================================
# 4. JSON出力
# =================================================================

print("【JSON出力】")
import json
output_data = {
    "factory": "FactoryA",
    "period": "2024",
    "instances": factory_a_instances.to_dict(),
    "ghg_report": ghg_instances.to_dict(),
    "summary": {
        "total_daily_emissions_kg": total_emissions,
        "total_annual_emissions_tons": total_emissions * 365 / 1000,
        "emission_factors_used": context['emission_factors'],
        "electricity_factor": context['electricity_factor']
    }
}

print(json.dumps(output_data, indent=2, ensure_ascii=False))
