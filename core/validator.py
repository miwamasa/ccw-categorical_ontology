"""
LLMベースの意味論的検証器

結果意味論: 
- 操作の結果をLLMに検証させる
- 構造的整合性は圏論で保証
- 意味的妥当性はLLMで判定
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum
import json


class ValidationLevel(Enum):
    """検証レベル"""
    STRUCTURAL = "structural"    # 構造的検証のみ
    SEMANTIC = "semantic"        # 意味的検証を含む
    PRAGMATIC = "pragmatic"      # 実用的検証（ドメイン固有ルール）


@dataclass
class ValidationResult:
    """検証結果"""
    is_valid: bool
    level: ValidationLevel
    confidence: float  # 0.0 - 1.0
    issues: List[str]
    suggestions: List[str]
    semantic_analysis: Optional[str] = None


class SemanticValidator:
    """意味論的検証器（LLM連携）"""
    
    def __init__(self, llm_client=None):
        """
        llm_client: LLM APIクライアント（None の場合はシミュレーション）
        """
        self.llm_client = llm_client
        self.validation_history: List[ValidationResult] = []
    
    def generate_validation_prompt(self, context: dict) -> str:
        """検証用プロンプトを生成"""
        operation = context.get("operation", "unknown")
        
        if operation == "functor_application":
            return self._functor_validation_prompt(context)
        elif operation == "coproduct":
            return self._coproduct_validation_prompt(context)
        elif operation == "pullback":
            return self._pullback_validation_prompt(context)
        elif operation == "alignment":
            return self._alignment_validation_prompt(context)
        else:
            return self._generic_validation_prompt(context)
    
    def _functor_validation_prompt(self, context: dict) -> str:
        return f"""
以下のオントロジー変換（関手）の意味的妥当性を検証してください。

【ソースオントロジー】
{json.dumps(context.get('source', {}), indent=2, ensure_ascii=False)}

【ターゲットオントロジー】
{json.dumps(context.get('target', {}), indent=2, ensure_ascii=False)}

【マッピング】
- 対象: {context.get('object_map', {})}
- 射: {context.get('morphism_map', {})}

【検証項目】
1. 意味的対応: 各マッピングは意味的に妥当か？
2. 情報損失: 重要な情報が失われていないか？
3. 構造保存: 関係性の本質が保存されているか？

JSON形式で回答:
{{"is_valid": bool, "confidence": float, "issues": [...], "suggestions": [...]}}
"""
    
    def _coproduct_validation_prompt(self, context: dict) -> str:
        return f"""
以下の二つのオントロジーの直和（並列結合）の意味的妥当性を検証してください。

【オントロジー1】
{json.dumps(context.get('cat1', {}), indent=2, ensure_ascii=False)}

【オントロジー2】
{json.dumps(context.get('cat2', {}), indent=2, ensure_ascii=False)}

【結果】
{json.dumps(context.get('result', {}), indent=2, ensure_ascii=False)}

【検証項目】
1. 名前衝突: 同名の概念が異なる意味を持つ場合の問題はないか？
2. 概念の一貫性: 結合された概念体系は一貫しているか？
3. 実用性: 結合結果は実用的に意味があるか？

JSON形式で回答:
{{"is_valid": bool, "confidence": float, "issues": [...], "suggestions": [...]}}
"""
    
    def _pullback_validation_prompt(self, context: dict) -> str:
        return f"""
以下のPullback（共通構造抽出）の意味的妥当性を検証してください。

【オントロジーA】
{json.dumps(context.get('cat1', {}), indent=2, ensure_ascii=False)}

【オントロジーB】
{json.dumps(context.get('cat2', {}), indent=2, ensure_ascii=False)}

【共通ターゲット】
{json.dumps(context.get('common', {}), indent=2, ensure_ascii=False)}

【抽出された共通構造】
{json.dumps(context.get('result', {}), indent=2, ensure_ascii=False)}

【検証項目】
1. 共通性の妥当性: 抽出された共通点は本当に「同じもの」か？
2. 漏れの有無: 他に共通すべき構造はないか？
3. 偶然の一致: 偶然の名前一致を共通構造と誤認していないか？

JSON形式で回答:
{{"is_valid": bool, "confidence": float, "issues": [...], "suggestions": [...]}}
"""
    
    def _alignment_validation_prompt(self, context: dict) -> str:
        return f"""
以下のオントロジーアライメント（自然変換）の意味的妥当性を検証してください。

【関手F】
{json.dumps(context.get('functor_f', {}), indent=2, ensure_ascii=False)}

【関手G】
{json.dumps(context.get('functor_g', {}), indent=2, ensure_ascii=False)}

【アライメント成分】
{json.dumps(context.get('components', {}), indent=2, ensure_ascii=False)}

【検証項目】
1. 自然性: 変換は構造を保存しているか？
2. 双方向性: 逆変換は可能か？
3. 情報量: 変換における情報の増減は？

JSON形式で回答:
{{"is_valid": bool, "confidence": float, "issues": [...], "suggestions": [...]}}
"""
    
    def _generic_validation_prompt(self, context: dict) -> str:
        return f"""
以下のオントロジー操作の意味的妥当性を検証してください。

【操作】
{context.get('operation', 'unknown')}

【入力】
{json.dumps(context.get('input', {}), indent=2, ensure_ascii=False)}

【出力】
{json.dumps(context.get('output', {}), indent=2, ensure_ascii=False)}

【検証項目】
1. 意味的妥当性
2. 構造の保存
3. 実用性

JSON形式で回答:
{{"is_valid": bool, "confidence": float, "issues": [...], "suggestions": [...]}}
"""
    
    def validate(self, context: dict, level: ValidationLevel = ValidationLevel.SEMANTIC) -> ValidationResult:
        """検証を実行"""
        issues = []
        suggestions = []
        
        # 1. 構造的検証（常に実行）
        structural_result = self._structural_validation(context)
        issues.extend(structural_result.get("issues", []))
        
        if level == ValidationLevel.STRUCTURAL:
            return ValidationResult(
                is_valid=len(issues) == 0,
                level=level,
                confidence=1.0 if len(issues) == 0 else 0.5,
                issues=issues,
                suggestions=suggestions
            )
        
        # 2. 意味的検証（LLMを使用）
        if self.llm_client:
            prompt = self.generate_validation_prompt(context)
            semantic_result = self._llm_validation(prompt)
            issues.extend(semantic_result.get("issues", []))
            suggestions.extend(semantic_result.get("suggestions", []))
            confidence = semantic_result.get("confidence", 0.5)
            semantic_analysis = semantic_result.get("analysis", "")
        else:
            # LLMがない場合はシミュレーション
            confidence = 0.7
            semantic_analysis = "[LLM未接続: 意味的検証はスキップ]"
        
        result = ValidationResult(
            is_valid=len(issues) == 0,
            level=level,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions,
            semantic_analysis=semantic_analysis
        )
        
        self.validation_history.append(result)
        return result
    
    def _structural_validation(self, context: dict) -> dict:
        """構造的検証"""
        issues = []
        operation = context.get("operation", "")
        
        if operation == "functor_application":
            # 対象マッピングの検証
            obj_map = context.get("object_map", {})
            morph_map = context.get("morphism_map", {})
            
            if not obj_map:
                issues.append("Object mapping is empty")
            
            # 射の構造保存検証
            source = context.get("source", {})
            for morph in source.get("morphisms", []):
                if morph["name"] in morph_map:
                    # ソースとターゲットのマッピングが存在するか確認
                    if morph["source"] not in obj_map:
                        issues.append(f"Morphism source '{morph['source']}' not mapped")
                    if morph["target"] not in obj_map:
                        issues.append(f"Morphism target '{morph['target']}' not mapped")
        
        elif operation == "coproduct":
            cat1 = context.get("cat1", {})
            cat2 = context.get("cat2", {})
            
            # 名前衝突の検出
            names1 = {o["name"] for o in cat1.get("objects", [])}
            names2 = {o["name"] for o in cat2.get("objects", [])}
            conflicts = names1 & names2
            if conflicts:
                issues.append(f"Name conflicts detected: {conflicts}")
        
        return {"issues": issues}
    
    def _llm_validation(self, prompt: str) -> dict:
        """LLMによる検証（実際のAPI呼び出し）"""
        try:
            # ここで実際のLLM APIを呼び出す
            # response = self.llm_client.complete(prompt)
            # return json.loads(response)
            
            # プレースホルダー
            return {
                "is_valid": True,
                "confidence": 0.8,
                "issues": [],
                "suggestions": [],
                "analysis": "LLM validation placeholder"
            }
        except Exception as e:
            return {
                "is_valid": False,
                "confidence": 0.0,
                "issues": [f"LLM validation error: {str(e)}"],
                "suggestions": ["Check LLM client configuration"]
            }


class DomainRules:
    """ドメイン固有の検証ルール"""
    
    def __init__(self):
        self.rules: Dict[str, List[callable]] = {}
    
    def add_rule(self, domain: str, rule: callable, description: str = ""):
        """ドメインルールを追加"""
        if domain not in self.rules:
            self.rules[domain] = []
        self.rules[domain].append({
            "rule": rule,
            "description": description
        })
    
    def validate(self, domain: str, data: Any) -> List[str]:
        """ドメインルールで検証"""
        issues = []
        if domain in self.rules:
            for rule_info in self.rules[domain]:
                try:
                    result = rule_info["rule"](data)
                    if not result:
                        issues.append(f"Rule failed: {rule_info['description']}")
                except Exception as e:
                    issues.append(f"Rule error: {str(e)}")
        return issues


# ドメイン固有ルールのプリセット
def create_ghg_rules() -> DomainRules:
    """GHGレポート用のドメインルール"""
    rules = DomainRules()
    
    # Scope 1, 2, 3 の整合性
    rules.add_rule(
        "ghg",
        lambda data: "scope" in str(data).lower(),
        "GHG data must include scope classification"
    )
    
    # 排出量は非負
    rules.add_rule(
        "ghg",
        lambda data: all(v >= 0 for v in data.get("emissions", {}).values() if isinstance(v, (int, float))),
        "Emission values must be non-negative"
    )
    
    # 単位の一貫性
    rules.add_rule(
        "ghg",
        lambda data: data.get("unit") in ["tCO2e", "kgCO2e", "gCO2e", None],
        "Unit must be in CO2 equivalent"
    )
    
    return rules


def create_manufacturing_rules() -> DomainRules:
    """製造業用のドメインルール"""
    rules = DomainRules()
    
    # 生産量は非負
    rules.add_rule(
        "manufacturing",
        lambda data: all(v >= 0 for v in data.get("production", {}).values() if isinstance(v, (int, float))),
        "Production values must be non-negative"
    )
    
    # 原材料 → 製品 の関係
    rules.add_rule(
        "manufacturing",
        lambda data: "input" in data and "output" in data,
        "Manufacturing process must have input and output"
    )
    
    return rules
