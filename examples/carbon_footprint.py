"""
製造業カーボンフットプリント例題

シナリオ:
1. 工場Aの生産オントロジー
2. 工場Bの生産オントロジー  
3. GHGプロトコルに基づくレポートオントロジー
4. これらの間の変換（関手）と演算

演算例:
- 合成: 工場A + 工場B → 企業全体
- 変換: 生産オントロジー → GHGレポートオントロジー
- Pullback: 両工場の共通排出源の抽出
- 差分: 工場Aにあって工場Bにない排出源
"""

import sys
sys.path.insert(0, '/home/claude/categorical_ontology')

from core.dsl import (
    Object, Morphism, Category, Functor, NaturalTransformation,
    MorphismType, CategoryOperations, FunctorOperations
)
from core.validator import SemanticValidator, ValidationLevel, create_ghg_rules
import json


# ============================================
# 1. オントロジー定義
# ============================================

def create_factory_a_ontology() -> Category:
    """工場Aの生産オントロジー"""
    cat = Category(
        name="FactoryA",
        description="Factory A Production Ontology - Automotive Parts Manufacturing"
    )
    
    # === 対象（Entities）===
    
    # 設備
    cat.add_object(Object(
        name="BoilerA1",
        domain="equipment",
        attributes=("type:gas_boiler", "capacity:5MW", "fuel:natural_gas"),
        semantic_signature="天然ガス焚きボイラー、蒸気生成用、Scope1排出源"
    ))
    
    cat.add_object(Object(
        name="CNCMachine01",
        domain="equipment",
        attributes=("type:cnc_machine", "power:50kW"),
        semantic_signature="CNC加工機、電力消費、Scope2排出源"
    ))
    
    cat.add_object(Object(
        name="PaintBooth",
        domain="equipment",
        attributes=("type:paint_booth", "solvent:yes"),
        semantic_signature="塗装ブース、VOC排出、Scope1排出源"
    ))
    
    # プロセス
    cat.add_object(Object(
        name="SteamGeneration",
        domain="process",
        attributes=("input:natural_gas", "output:steam"),
        semantic_signature="蒸気生成プロセス"
    ))
    
    cat.add_object(Object(
        name="Machining",
        domain="process",
        attributes=("input:raw_material", "output:machined_part"),
        semantic_signature="機械加工プロセス"
    ))
    
    cat.add_object(Object(
        name="Painting",
        domain="process",
        attributes=("input:machined_part", "output:painted_part"),
        semantic_signature="塗装プロセス"
    ))
    
    # 排出
    cat.add_object(Object(
        name="CO2_Combustion",
        domain="emission",
        attributes=("type:CO2", "source:combustion", "scope:1"),
        semantic_signature="燃焼由来CO2排出"
    ))
    
    cat.add_object(Object(
        name="CO2_Electricity",
        domain="emission",
        attributes=("type:CO2", "source:electricity", "scope:2"),
        semantic_signature="電力由来CO2排出（間接）"
    ))
    
    cat.add_object(Object(
        name="VOC_Emission",
        domain="emission",
        attributes=("type:VOC", "source:painting", "scope:1"),
        semantic_signature="塗装由来VOC排出"
    ))
    
    # エネルギー
    cat.add_object(Object(
        name="NaturalGas",
        domain="energy",
        attributes=("type:fuel", "unit:m3"),
        semantic_signature="天然ガス（燃料）"
    ))
    
    cat.add_object(Object(
        name="Electricity",
        domain="energy",
        attributes=("type:purchased", "unit:kWh"),
        semantic_signature="購入電力"
    ))
    
    # === 射（Relationships）===
    
    cat.add_morphism(Morphism(
        name="boiler_consumes_gas",
        source=cat.objects["BoilerA1"],
        target=cat.objects["NaturalGas"],
        morphism_type=MorphismType.FUNCTIONAL,
        semantic_description="ボイラーが天然ガスを消費"
    ))
    
    cat.add_morphism(Morphism(
        name="boiler_generates_steam",
        source=cat.objects["BoilerA1"],
        target=cat.objects["SteamGeneration"],
        morphism_type=MorphismType.FUNCTIONAL,
        semantic_description="ボイラーが蒸気生成を行う"
    ))
    
    cat.add_morphism(Morphism(
        name="combustion_emits_co2",
        source=cat.objects["SteamGeneration"],
        target=cat.objects["CO2_Combustion"],
        morphism_type=MorphismType.CAUSAL,
        semantic_description="燃焼によりCO2が排出される"
    ))
    
    cat.add_morphism(Morphism(
        name="cnc_consumes_electricity",
        source=cat.objects["CNCMachine01"],
        target=cat.objects["Electricity"],
        morphism_type=MorphismType.FUNCTIONAL,
        semantic_description="CNC機械が電力を消費"
    ))
    
    cat.add_morphism(Morphism(
        name="electricity_causes_co2",
        source=cat.objects["Electricity"],
        target=cat.objects["CO2_Electricity"],
        morphism_type=MorphismType.CAUSAL,
        semantic_description="電力消費により間接的にCO2が排出される"
    ))
    
    cat.add_morphism(Morphism(
        name="painting_emits_voc",
        source=cat.objects["Painting"],
        target=cat.objects["VOC_Emission"],
        morphism_type=MorphismType.CAUSAL,
        semantic_description="塗装によりVOCが排出される"
    ))
    
    cat.add_morphism(Morphism(
        name="machining_to_painting",
        source=cat.objects["Machining"],
        target=cat.objects["Painting"],
        morphism_type=MorphismType.TEMPORAL,
        semantic_description="加工後に塗装工程"
    ))
    
    return cat


def create_factory_b_ontology() -> Category:
    """工場Bの生産オントロジー"""
    cat = Category(
        name="FactoryB", 
        description="Factory B Production Ontology - Electronics Manufacturing"
    )
    
    # === 対象（Entities）===
    
    # 設備
    cat.add_object(Object(
        name="SMTLine01",
        domain="equipment",
        attributes=("type:smt_line", "power:100kW"),
        semantic_signature="SMT実装ライン、電力消費、Scope2排出源"
    ))
    
    cat.add_object(Object(
        name="ReflowOven",
        domain="equipment",
        attributes=("type:reflow_oven", "power:30kW", "gas:nitrogen"),
        semantic_signature="リフロー炉、電力・窒素消費"
    ))
    
    cat.add_object(Object(
        name="CleanRoom",
        domain="equipment",
        attributes=("type:clean_room", "power:200kW"),
        semantic_signature="クリーンルーム、大電力消費、Scope2排出源"
    ))
    
    # プロセス
    cat.add_object(Object(
        name="PCBAssembly",
        domain="process",
        attributes=("input:pcb,components", "output:assembled_pcb"),
        semantic_signature="基板組立プロセス"
    ))
    
    cat.add_object(Object(
        name="Soldering",
        domain="process",
        attributes=("input:assembled_pcb", "output:soldered_pcb"),
        semantic_signature="はんだ付けプロセス"
    ))
    
    # 排出
    cat.add_object(Object(
        name="CO2_Electricity",
        domain="emission",
        attributes=("type:CO2", "source:electricity", "scope:2"),
        semantic_signature="電力由来CO2排出（間接）"
    ))
    
    cat.add_object(Object(
        name="N2O_Soldering",
        domain="emission",
        attributes=("type:N2O", "source:soldering", "scope:1"),
        semantic_signature="はんだ付け由来N2O排出"
    ))
    
    # エネルギー
    cat.add_object(Object(
        name="Electricity",
        domain="energy",
        attributes=("type:purchased", "unit:kWh"),
        semantic_signature="購入電力"
    ))
    
    cat.add_object(Object(
        name="Nitrogen",
        domain="energy",
        attributes=("type:industrial_gas", "unit:m3"),
        semantic_signature="窒素ガス"
    ))
    
    # === 射（Relationships）===
    
    cat.add_morphism(Morphism(
        name="smt_consumes_electricity",
        source=cat.objects["SMTLine01"],
        target=cat.objects["Electricity"],
        morphism_type=MorphismType.FUNCTIONAL,
        semantic_description="SMTラインが電力を消費"
    ))
    
    cat.add_morphism(Morphism(
        name="cleanroom_consumes_electricity",
        source=cat.objects["CleanRoom"],
        target=cat.objects["Electricity"],
        morphism_type=MorphismType.FUNCTIONAL,
        semantic_description="クリーンルームが電力を消費"
    ))
    
    cat.add_morphism(Morphism(
        name="electricity_causes_co2",
        source=cat.objects["Electricity"],
        target=cat.objects["CO2_Electricity"],
        morphism_type=MorphismType.CAUSAL,
        semantic_description="電力消費により間接的にCO2が排出される"
    ))
    
    cat.add_morphism(Morphism(
        name="reflow_consumes_nitrogen",
        source=cat.objects["ReflowOven"],
        target=cat.objects["Nitrogen"],
        morphism_type=MorphismType.FUNCTIONAL,
        semantic_description="リフロー炉が窒素を消費"
    ))
    
    cat.add_morphism(Morphism(
        name="soldering_emits_n2o",
        source=cat.objects["Soldering"],
        target=cat.objects["N2O_Soldering"],
        morphism_type=MorphismType.CAUSAL,
        semantic_description="はんだ付けによりN2Oが微量排出"
    ))
    
    return cat


def create_ghg_report_ontology() -> Category:
    """GHGプロトコルに基づくレポートオントロジー"""
    cat = Category(
        name="GHGReport",
        description="GHG Protocol Reporting Ontology"
    )
    
    # === 対象（Entities）===
    
    # Scope分類
    cat.add_object(Object(
        name="Scope1",
        domain="scope",
        attributes=("definition:direct_emissions",),
        semantic_signature="直接排出（燃料燃焼、プロセス排出、漏洩）"
    ))
    
    cat.add_object(Object(
        name="Scope2",
        domain="scope",
        attributes=("definition:indirect_energy",),
        semantic_signature="エネルギー起源間接排出（購入電力、熱）"
    ))
    
    cat.add_object(Object(
        name="Scope3",
        domain="scope",
        attributes=("definition:other_indirect",),
        semantic_signature="その他間接排出（サプライチェーン）"
    ))
    
    # 排出カテゴリ
    cat.add_object(Object(
        name="StationaryCombustion",
        domain="category",
        attributes=("scope:1", "source:fuel_combustion"),
        semantic_signature="固定燃焼源からの排出"
    ))
    
    cat.add_object(Object(
        name="ProcessEmissions",
        domain="category",
        attributes=("scope:1", "source:industrial_process"),
        semantic_signature="工業プロセスからの排出"
    ))
    
    cat.add_object(Object(
        name="PurchasedElectricity",
        domain="category",
        attributes=("scope:2", "source:electricity"),
        semantic_signature="購入電力からの排出"
    ))
    
    cat.add_object(Object(
        name="PurchasedHeat",
        domain="category",
        attributes=("scope:2", "source:heat_steam"),
        semantic_signature="購入熱・蒸気からの排出"
    ))
    
    # 排出量
    cat.add_object(Object(
        name="EmissionAmount",
        domain="measurement",
        attributes=("unit:tCO2e",),
        semantic_signature="CO2換算排出量"
    ))
    
    # 算定手法
    cat.add_object(Object(
        name="ActivityData",
        domain="calculation",
        attributes=("type:primary_data",),
        semantic_signature="活動量データ"
    ))
    
    cat.add_object(Object(
        name="EmissionFactor",
        domain="calculation",
        attributes=("type:factor",),
        semantic_signature="排出係数"
    ))
    
    # === 射（Relationships）===
    
    cat.add_morphism(Morphism(
        name="scope1_includes_combustion",
        source=cat.objects["Scope1"],
        target=cat.objects["StationaryCombustion"],
        morphism_type=MorphismType.STRUCTURAL,
        semantic_description="Scope1は固定燃焼を含む"
    ))
    
    cat.add_morphism(Morphism(
        name="scope1_includes_process",
        source=cat.objects["Scope1"],
        target=cat.objects["ProcessEmissions"],
        morphism_type=MorphismType.STRUCTURAL,
        semantic_description="Scope1はプロセス排出を含む"
    ))
    
    cat.add_morphism(Morphism(
        name="scope2_includes_electricity",
        source=cat.objects["Scope2"],
        target=cat.objects["PurchasedElectricity"],
        morphism_type=MorphismType.STRUCTURAL,
        semantic_description="Scope2は購入電力を含む"
    ))
    
    cat.add_morphism(Morphism(
        name="category_quantifies_emission",
        source=cat.objects["StationaryCombustion"],
        target=cat.objects["EmissionAmount"],
        morphism_type=MorphismType.MEASUREMENT,
        semantic_description="カテゴリは排出量として定量化される"
    ))
    
    cat.add_morphism(Morphism(
        name="activity_times_factor",
        source=cat.objects["ActivityData"],
        target=cat.objects["EmissionAmount"],
        morphism_type=MorphismType.FUNCTIONAL,
        semantic_description="活動量×排出係数=排出量"
    ))
    
    return cat


# ============================================
# 2. 関手（Functor）定義 - オントロジー変換
# ============================================

def create_factory_to_ghg_functor(factory_cat: Category, ghg_cat: Category) -> Functor:
    """工場オントロジー → GHGレポートオントロジー への関手"""
    
    # 対象マッピング
    object_map = {}
    
    # 排出関連のマッピング
    for obj in factory_cat.objects.values():
        if obj.domain == "emission":
            if "scope:1" in obj.attributes:
                if "combustion" in obj.name.lower() or "combustion" in str(obj.attributes):
                    object_map[obj.name] = "StationaryCombustion"
                else:
                    object_map[obj.name] = "ProcessEmissions"
            elif "scope:2" in obj.attributes:
                object_map[obj.name] = "PurchasedElectricity"
        elif obj.domain == "energy":
            if "fuel" in str(obj.attributes):
                object_map[obj.name] = "ActivityData"
            elif "purchased" in str(obj.attributes):
                object_map[obj.name] = "ActivityData"
    
    # 射マッピング
    morphism_map = {}
    for morph in factory_cat.morphisms.values():
        if morph.morphism_type == MorphismType.CAUSAL:
            if "co2" in morph.name.lower() or "emit" in morph.name.lower():
                morphism_map[morph.name] = "category_quantifies_emission"
    
    return Functor(
        name=f"F_{factory_cat.name}_to_GHG",
        source_category=factory_cat,
        target_category=ghg_cat,
        object_map=object_map,
        morphism_map=morphism_map,
        semantic_mapping_rules=[
            "Scope1排出源 → StationaryCombustion または ProcessEmissions",
            "Scope2排出源 → PurchasedElectricity",
            "エネルギー消費 → ActivityData",
            "排出関係 → category_quantifies_emission"
        ]
    )


# ============================================
# 3. 演算の実行と結果
# ============================================

def demonstrate_operations():
    """演算のデモンストレーション"""
    
    print("=" * 80)
    print("圏論的オントロジー演算 - 製造業カーボンフットプリント例題")
    print("=" * 80)
    
    # オントロジー生成
    factory_a = create_factory_a_ontology()
    factory_b = create_factory_b_ontology()
    ghg_report = create_ghg_report_ontology()
    
    print("\n" + "=" * 80)
    print("1. 基本オントロジー")
    print("=" * 80)
    
    print(f"\n【工場A】{factory_a.name}")
    print(f"  対象数: {len(factory_a.objects)}")
    print(f"  射数: {len(factory_a.morphisms)}")
    print(f"  対象: {list(factory_a.objects.keys())}")
    
    print(f"\n【工場B】{factory_b.name}")
    print(f"  対象数: {len(factory_b.objects)}")
    print(f"  射数: {len(factory_b.morphisms)}")
    print(f"  対象: {list(factory_b.objects.keys())}")
    
    print(f"\n【GHGレポート】{ghg_report.name}")
    print(f"  対象数: {len(ghg_report.objects)}")
    print(f"  射数: {len(ghg_report.morphisms)}")
    print(f"  対象: {list(ghg_report.objects.keys())}")
    
    # ============================================
    # 演算1: 直和（足し算）- 複数工場の統合
    # ============================================
    print("\n" + "=" * 80)
    print("2. 演算: 直和（足し算） A + B")
    print("   意味: 工場Aと工場Bのオントロジーを並列に統合")
    print("=" * 80)
    
    combined = CategoryOperations.coproduct(factory_a, factory_b, "CombinedFactories")
    
    print(f"\n【結果】{combined.name}")
    print(f"  対象数: {len(combined.objects)} (= {len(factory_a.objects)} + {len(factory_b.objects)})")
    print(f"  射数: {len(combined.morphisms)}")
    print(f"\n  タグ付き対象の例:")
    for name in list(combined.objects.keys())[:5]:
        print(f"    - {name}")
    
    # ============================================
    # 演算2: 関手適用 - GHGレポートへの変換
    # ============================================
    print("\n" + "=" * 80)
    print("3. 演算: 関手適用（変換） F: FactoryA → GHGReport")
    print("   意味: 生産オントロジーをGHGレポート形式に変換")
    print("=" * 80)
    
    functor_a = create_factory_to_ghg_functor(factory_a, ghg_report)
    
    print(f"\n【関手】{functor_a.name}")
    print(f"\n  対象マッピング:")
    for src, tgt in functor_a.object_map.items():
        print(f"    {src} → {tgt}")
    
    print(f"\n  射マッピング:")
    for src, tgt in functor_a.morphism_map.items():
        print(f"    {src} → {tgt}")
    
    print(f"\n  マッピングルール:")
    for rule in functor_a.semantic_mapping_rules:
        print(f"    • {rule}")
    
    # 検証
    is_valid, errors = functor_a.is_valid()
    print(f"\n  構造的整合性: {'✓ 有効' if is_valid else '✗ 無効'}")
    if errors:
        for e in errors:
            print(f"    - {e}")
    
    # ============================================
    # 演算3: Pullback - 共通構造の抽出
    # ============================================
    print("\n" + "=" * 80)
    print("4. 演算: Pullback（共通構造抽出）")
    print("   意味: 工場AとBがGHGレポートにおいて共通する排出構造を抽出")
    print("=" * 80)
    
    functor_b = create_factory_to_ghg_functor(factory_b, ghg_report)
    
    pullback = CategoryOperations.pullback(
        factory_a, factory_b, ghg_report,
        functor_a, functor_b,
        "CommonEmissionStructure"
    )
    
    print(f"\n【結果】{pullback.name}")
    print(f"  共通対象ペア:")
    for obj in pullback.objects.values():
        print(f"    - {obj.name}")
        print(f"      意味: {obj.semantic_signature}")
    
    # ============================================
    # 演算4: 差分 - 工場Aにあって工場Bにないもの
    # ============================================
    print("\n" + "=" * 80)
    print("5. 演算: 差分（引き算） A - B")
    print("   意味: 工場Aに固有の排出構造を抽出")
    print("=" * 80)
    
    diff = CategoryOperations.difference(factory_a, factory_b, "FactoryA_Unique")
    
    print(f"\n【結果】{diff.name}")
    print(f"  固有対象数: {len(diff.objects)}")
    print(f"  固有対象:")
    for obj in diff.objects.values():
        print(f"    - {obj.name} ({obj.domain})")
        print(f"      意味: {obj.semantic_signature}")
    
    # ============================================
    # 演算5: 関手の合成
    # ============================================
    print("\n" + "=" * 80)
    print("6. 演算: 関手の合成 G ∘ F")
    print("   意味: 複数段階の変換を1つの変換にまとめる")
    print("=" * 80)
    
    # 簡略化のため、概念的な説明
    print("""
    例: サプライチェーン全体のGHG算定
    
    F: 原材料調達オントロジー → 工場オントロジー
    G: 工場オントロジー → GHGレポートオントロジー
    
    G ∘ F: 原材料調達オントロジー → GHGレポートオントロジー
    
    これにより、Scope3 Category 1（購入物品）の排出を
    サプライヤーの生産データから直接算定可能
    """)
    
    # ============================================
    # LLM検証の例
    # ============================================
    print("\n" + "=" * 80)
    print("7. LLMによる意味的検証（結果意味論）")
    print("=" * 80)
    
    validator = SemanticValidator()
    
    validation_context = {
        "operation": "functor_application",
        "source": factory_a.to_dict(),
        "target": ghg_report.to_dict(),
        "object_map": functor_a.object_map,
        "morphism_map": functor_a.morphism_map
    }
    
    prompt = validator.generate_validation_prompt(validation_context)
    print("\n【生成されたLLM検証プロンプト（抜粋）】")
    print("-" * 40)
    print(prompt[:1500] + "...")
    
    # 検証実行
    result = validator.validate(validation_context, ValidationLevel.SEMANTIC)
    print(f"\n【検証結果】")
    print(f"  有効性: {'✓' if result.is_valid else '✗'}")
    print(f"  信頼度: {result.confidence}")
    print(f"  検証レベル: {result.level.value}")
    if result.issues:
        print(f"  問題点:")
        for issue in result.issues:
            print(f"    - {issue}")
    
    return {
        "factory_a": factory_a,
        "factory_b": factory_b,
        "ghg_report": ghg_report,
        "combined": combined,
        "functor_a": functor_a,
        "pullback": pullback,
        "diff": diff
    }


if __name__ == "__main__":
    results = demonstrate_operations()
    
    # JSON出力
    print("\n" + "=" * 80)
    print("8. シリアライズ出力（JSON）")
    print("=" * 80)
    
    output = {
        "factory_a": results["factory_a"].to_dict(),
        "combined": results["combined"].to_dict(),
        "pullback": results["pullback"].to_dict(),
        "diff": results["diff"].to_dict()
    }
    
    print("\n【直和の結果（一部）】")
    print(json.dumps(output["combined"]["objects"][:3], indent=2, ensure_ascii=False))
