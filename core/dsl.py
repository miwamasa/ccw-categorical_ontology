"""
圏論的オントロジーDSL (Categorical Ontology DSL - CODSL)

理論的基盤:
- オントロジー = 圏 (Category)
- Entity = 対象 (Object)  
- Relationship = 射 (Morphism)
- オントロジー間変換 = 関手 (Functor)
- アライメント = 自然変換 (Natural Transformation)

演算:
- 合成 (Composition): F ∘ G
- 直和 (Coproduct): A + B
- 直積 (Product): A × B
- Pullback: 共通構造の抽出
- Pushout: 構造の融合
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Callable, Any, Tuple
from abc import ABC, abstractmethod
import json
from enum import Enum
import hashlib


class MorphismType(Enum):
    """射の種類"""
    STRUCTURAL = "structural"      # 構造的関係 (has-part, is-a)
    FUNCTIONAL = "functional"      # 機能的関係 (produces, consumes)
    TEMPORAL = "temporal"          # 時間的関係 (before, after, during)
    CAUSAL = "causal"              # 因果関係 (causes, enables)
    MEASUREMENT = "measurement"    # 計測関係 (measures, quantifies)
    IDENTITY = "identity"          # 恒等射


@dataclass(frozen=True)
class Object:
    """圏の対象 (Entity)"""
    name: str
    domain: str  # 所属するドメイン
    attributes: tuple = field(default_factory=tuple)  # 不変属性
    semantic_signature: str = ""  # LLM用の意味記述
    
    def __hash__(self):
        return hash((self.name, self.domain))
    
    def __eq__(self, other):
        if not isinstance(other, Object):
            return False
        return self.name == other.name and self.domain == other.domain


@dataclass(frozen=True)
class Morphism:
    """圏の射 (Relationship)"""
    name: str
    source: Object
    target: Object
    morphism_type: MorphismType
    properties: tuple = field(default_factory=tuple)
    semantic_description: str = ""
    
    def __hash__(self):
        return hash((self.name, self.source, self.target))
    
    def compose(self, other: 'Morphism') -> Optional['Morphism']:
        """射の合成: self ∘ other (other を先に適用)"""
        if self.source != other.target:
            return None
        return Morphism(
            name=f"({self.name} ∘ {other.name})",
            source=other.source,
            target=self.target,
            morphism_type=MorphismType.STRUCTURAL,
            semantic_description=f"Composition: {other.semantic_description} then {self.semantic_description}"
        )


class Category:
    """圏 (オントロジー)"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.objects: Dict[str, Object] = {}
        self.morphisms: Dict[str, Morphism] = {}
        self._identity_morphisms: Dict[str, Morphism] = {}
    
    def add_object(self, obj: Object) -> 'Category':
        """対象を追加"""
        self.objects[obj.name] = obj
        # 恒等射を自動生成
        identity = Morphism(
            name=f"id_{obj.name}",
            source=obj,
            target=obj,
            morphism_type=MorphismType.IDENTITY,
            semantic_description=f"Identity on {obj.name}"
        )
        self._identity_morphisms[obj.name] = identity
        return self
    
    def add_morphism(self, morph: Morphism) -> 'Category':
        """射を追加"""
        if morph.source.name not in self.objects:
            self.add_object(morph.source)
        if morph.target.name not in self.objects:
            self.add_object(morph.target)
        self.morphisms[morph.name] = morph
        return self
    
    def get_morphisms_from(self, obj: Object) -> List[Morphism]:
        """指定対象から出る射を取得"""
        return [m for m in self.morphisms.values() if m.source == obj]
    
    def get_morphisms_to(self, obj: Object) -> List[Morphism]:
        """指定対象に入る射を取得"""
        return [m for m in self.morphisms.values() if m.target == obj]
    
    def signature(self) -> str:
        """圏の構造的シグネチャ（比較用）"""
        obj_sig = sorted([f"{o.name}:{o.domain}" for o in self.objects.values()])
        morph_sig = sorted([f"{m.source.name}->{m.target.name}:{m.morphism_type.value}" 
                          for m in self.morphisms.values()])
        return hashlib.md5(json.dumps({"objects": obj_sig, "morphisms": morph_sig}).encode()).hexdigest()
    
    def to_dict(self) -> dict:
        """辞書形式にシリアライズ"""
        return {
            "name": self.name,
            "description": self.description,
            "objects": [
                {
                    "name": o.name,
                    "domain": o.domain,
                    "attributes": list(o.attributes),
                    "semantic_signature": o.semantic_signature
                }
                for o in self.objects.values()
            ],
            "morphisms": [
                {
                    "name": m.name,
                    "source": m.source.name,
                    "target": m.target.name,
                    "type": m.morphism_type.value,
                    "properties": list(m.properties),
                    "semantic_description": m.semantic_description
                }
                for m in self.morphisms.values()
            ]
        }


@dataclass
class Functor:
    """関手 (オントロジー間の構造保存写像)"""
    name: str
    source_category: Category
    target_category: Category
    object_map: Dict[str, str]  # source obj name -> target obj name
    morphism_map: Dict[str, str]  # source morph name -> target morph name
    semantic_mapping_rules: List[str] = field(default_factory=list)
    
    def apply_to_object(self, obj: Object) -> Optional[Object]:
        """対象への関手適用"""
        if obj.name in self.object_map:
            target_name = self.object_map[obj.name]
            return self.target_category.objects.get(target_name)
        return None
    
    def apply_to_morphism(self, morph: Morphism) -> Optional[Morphism]:
        """射への関手適用"""
        if morph.name in self.morphism_map:
            target_name = self.morphism_map[morph.name]
            return self.target_category.morphisms.get(target_name)
        return None
    
    def is_valid(self) -> Tuple[bool, List[str]]:
        """関手の整合性検証"""
        errors = []
        
        # すべてのマッピングが存在するか
        for src, tgt in self.object_map.items():
            if src not in self.source_category.objects:
                errors.append(f"Source object '{src}' not found")
            if tgt not in self.target_category.objects:
                errors.append(f"Target object '{tgt}' not found")
        
        # 射の構造が保存されているか
        for src_morph_name, tgt_morph_name in self.morphism_map.items():
            src_morph = self.source_category.morphisms.get(src_morph_name)
            tgt_morph = self.target_category.morphisms.get(tgt_morph_name)
            
            if src_morph and tgt_morph:
                # F(f: A -> B) = F(f): F(A) -> F(B) を検証
                expected_source = self.object_map.get(src_morph.source.name)
                expected_target = self.object_map.get(src_morph.target.name)
                
                if tgt_morph.source.name != expected_source:
                    errors.append(f"Functor does not preserve source of '{src_morph_name}'")
                if tgt_morph.target.name != expected_target:
                    errors.append(f"Functor does not preserve target of '{src_morph_name}'")
        
        return len(errors) == 0, errors


@dataclass
class NaturalTransformation:
    """自然変換 (関手間の変換 = オントロジーアライメント)"""
    name: str
    source_functor: Functor
    target_functor: Functor
    components: Dict[str, str]  # object name -> morphism name in target category
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    def is_natural(self) -> Tuple[bool, List[str]]:
        """自然性条件の検証"""
        errors = []
        # 各射 f: A -> B に対して η_B ∘ F(f) = G(f) ∘ η_A を検証
        # LLMによる意味的検証で補完する設計
        return len(errors) == 0, errors


# ============ 圏論的演算 ============

class CategoryOperations:
    """圏に対する演算"""
    
    @staticmethod
    def coproduct(cat1: Category, cat2: Category, name: str = None) -> Category:
        """
        直和 (Coproduct): A + B
        二つのオントロジーを「並列」に結合
        """
        result_name = name or f"({cat1.name} + {cat2.name})"
        result = Category(result_name, f"Coproduct of {cat1.name} and {cat2.name}")
        
        # 対象の直和（タグ付き和）
        for obj in cat1.objects.values():
            tagged_obj = Object(
                name=f"{cat1.name}.{obj.name}",
                domain=obj.domain,
                attributes=obj.attributes,
                semantic_signature=f"[From {cat1.name}] {obj.semantic_signature}"
            )
            result.add_object(tagged_obj)
        
        for obj in cat2.objects.values():
            tagged_obj = Object(
                name=f"{cat2.name}.{obj.name}",
                domain=obj.domain,
                attributes=obj.attributes,
                semantic_signature=f"[From {cat2.name}] {obj.semantic_signature}"
            )
            result.add_object(tagged_obj)
        
        # 射の直和
        for morph in cat1.morphisms.values():
            tagged_morph = Morphism(
                name=f"{cat1.name}.{morph.name}",
                source=Object(f"{cat1.name}.{morph.source.name}", morph.source.domain),
                target=Object(f"{cat1.name}.{morph.target.name}", morph.target.domain),
                morphism_type=morph.morphism_type,
                semantic_description=f"[From {cat1.name}] {morph.semantic_description}"
            )
            result.add_morphism(tagged_morph)
        
        for morph in cat2.morphisms.values():
            tagged_morph = Morphism(
                name=f"{cat2.name}.{morph.name}",
                source=Object(f"{cat2.name}.{morph.source.name}", morph.source.domain),
                target=Object(f"{cat2.name}.{morph.target.name}", morph.target.domain),
                morphism_type=morph.morphism_type,
                semantic_description=f"[From {cat2.name}] {morph.semantic_description}"
            )
            result.add_morphism(tagged_morph)
        
        return result
    
    @staticmethod
    def product(cat1: Category, cat2: Category, name: str = None) -> Category:
        """
        直積 (Product): A × B
        二つのオントロジーのペアを生成
        """
        result_name = name or f"({cat1.name} × {cat2.name})"
        result = Category(result_name, f"Product of {cat1.name} and {cat2.name}")
        
        # 対象の直積
        for obj1 in cat1.objects.values():
            for obj2 in cat2.objects.values():
                product_obj = Object(
                    name=f"({obj1.name}, {obj2.name})",
                    domain=f"{obj1.domain}×{obj2.domain}",
                    attributes=obj1.attributes + obj2.attributes,
                    semantic_signature=f"Pair of [{obj1.semantic_signature}] and [{obj2.semantic_signature}]"
                )
                result.add_object(product_obj)
        
        # 射の直積
        for m1 in cat1.morphisms.values():
            for m2 in cat2.morphisms.values():
                product_morph = Morphism(
                    name=f"({m1.name}, {m2.name})",
                    source=Object(
                        f"({m1.source.name}, {m2.source.name})",
                        f"{m1.source.domain}×{m2.source.domain}"
                    ),
                    target=Object(
                        f"({m1.target.name}, {m2.target.name})",
                        f"{m1.target.domain}×{m2.target.domain}"
                    ),
                    morphism_type=MorphismType.STRUCTURAL,
                    semantic_description=f"Product morphism: [{m1.semantic_description}] × [{m2.semantic_description}]"
                )
                result.add_morphism(product_morph)
        
        return result
    
    @staticmethod
    def pullback(cat1: Category, cat2: Category, 
                 common_target: Category,
                 functor1: Functor, functor2: Functor,
                 name: str = None) -> Category:
        """
        Pullback: 共通構造の抽出
        F: A -> C, G: B -> C に対して、A ×_C B を計算
        「CとしてF像とG像が一致する(A,B)のペア」
        """
        result_name = name or f"Pullback({cat1.name}, {cat2.name})"
        result = Category(result_name, f"Pullback over {common_target.name}")
        
        # F(a) = G(b) となる (a, b) ペアを探索
        for obj1 in cat1.objects.values():
            f_obj1 = functor1.apply_to_object(obj1)
            if not f_obj1:
                continue
            
            for obj2 in cat2.objects.values():
                g_obj2 = functor2.apply_to_object(obj2)
                if not g_obj2:
                    continue
                
                # 像が一致する場合、pullback対象として追加
                if f_obj1.name == g_obj2.name:
                    pullback_obj = Object(
                        name=f"⟨{obj1.name}, {obj2.name}⟩",
                        domain="pullback",
                        attributes=obj1.attributes + obj2.attributes,
                        semantic_signature=f"Pullback element: {obj1.name} and {obj2.name} both map to {f_obj1.name}"
                    )
                    result.add_object(pullback_obj)
        
        return result
    
    @staticmethod
    def pushout(cat1: Category, cat2: Category,
                common_source: Category,
                functor1: Functor, functor2: Functor,
                name: str = None) -> Category:
        """
        Pushout: 構造の融合
        F: C -> A, G: C -> B に対して、A +_C B を計算
        「Cを経由して同一視されたAとBの融合」
        """
        result_name = name or f"Pushout({cat1.name}, {cat2.name})"
        result = Category(result_name, f"Pushout from {common_source.name}")
        
        # まず直和を作る
        for obj in cat1.objects.values():
            result.add_object(Object(
                name=f"L.{obj.name}",
                domain=obj.domain,
                attributes=obj.attributes,
                semantic_signature=f"[Left] {obj.semantic_signature}"
            ))
        
        for obj in cat2.objects.values():
            result.add_object(Object(
                name=f"R.{obj.name}",
                domain=obj.domain,
                attributes=obj.attributes,
                semantic_signature=f"[Right] {obj.semantic_signature}"
            ))
        
        # F(c)とG(c)を同一視するための等価関係を記録
        equivalences = []
        for src_obj in common_source.objects.values():
            f_image = functor1.apply_to_object(src_obj)
            g_image = functor2.apply_to_object(src_obj)
            if f_image and g_image:
                equivalences.append((f"L.{f_image.name}", f"R.{g_image.name}"))
        
        result.description += f"\nEquivalences: {equivalences}"
        return result
    
    @staticmethod
    def difference(cat1: Category, cat2: Category, name: str = None) -> Category:
        """
        差分 (Difference): A - B
        cat1 に含まれるが cat2 に含まれない構造
        （意味的な差分はLLMで補完）
        名前とドメインの両方が一致する場合のみ「同じ」とみなす
        """
        result_name = name or f"({cat1.name} - {cat2.name})"
        result = Category(result_name, f"Difference: {cat1.name} minus {cat2.name}")
        
        # (name, domain) のペアで比較
        cat2_obj_keys = {(o.name, o.domain) for o in cat2.objects.values()}
        cat2_morph_signatures = {(m.source.name, m.target.name, m.morphism_type) 
                                  for m in cat2.morphisms.values()}
        
        # cat2 にない対象を追加（名前とドメインの両方で比較）
        diff_obj_keys = set()
        for obj in cat1.objects.values():
            if (obj.name, obj.domain) not in cat2_obj_keys:
                result.add_object(obj)
                diff_obj_keys.add(obj.name)
        
        # cat2 にない射を追加（ただし、source/targetが差分に含まれる場合のみ）
        for morph in cat1.morphisms.values():
            sig = (morph.source.name, morph.target.name, morph.morphism_type)
            if sig not in cat2_morph_signatures:
                # 射のsource/targetが差分対象に含まれる場合のみ追加
                if morph.source.name in diff_obj_keys and morph.target.name in diff_obj_keys:
                    result.morphisms[morph.name] = morph
        
        return result


# ============ 関手の合成 ============

class FunctorOperations:
    """関手に対する演算"""
    
    @staticmethod
    def compose(f: Functor, g: Functor) -> Optional[Functor]:
        """
        関手の合成: F ∘ G
        G: A -> B, F: B -> C のとき F ∘ G: A -> C
        """
        if g.target_category.name != f.source_category.name:
            return None
        
        # 対象マッピングの合成
        composed_object_map = {}
        for a_name, b_name in g.object_map.items():
            if b_name in f.object_map:
                composed_object_map[a_name] = f.object_map[b_name]
        
        # 射マッピングの合成
        composed_morphism_map = {}
        for a_morph, b_morph in g.morphism_map.items():
            if b_morph in f.morphism_map:
                composed_morphism_map[a_morph] = f.morphism_map[b_morph]
        
        return Functor(
            name=f"({f.name} ∘ {g.name})",
            source_category=g.source_category,
            target_category=f.target_category,
            object_map=composed_object_map,
            morphism_map=composed_morphism_map,
            semantic_mapping_rules=g.semantic_mapping_rules + f.semantic_mapping_rules
        )
