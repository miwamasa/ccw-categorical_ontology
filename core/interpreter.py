"""
CODSL パーサーと実行エンジン

DSL構文:
---------
ONTOLOGY <name> {
    OBJECT <name> : <domain> {
        attributes: [<attr1>, <attr2>, ...]
        semantic: "<description>"
    }
    
    MORPHISM <name> : <source> -> <target> {
        type: <STRUCTURAL|FUNCTIONAL|CAUSAL|TEMPORAL|MEASUREMENT>
        semantic: "<description>"
    }
}

FUNCTOR <name> : <source_ontology> -> <target_ontology> {
    MAP OBJECT <src> -> <tgt>
    MAP MORPHISM <src> -> <tgt>
    RULE "<semantic rule>"
}

OPERATION {
    <result> = COPRODUCT(<ont1>, <ont2>)
    <result> = PRODUCT(<ont1>, <ont2>)
    <result> = PULLBACK(<ont1>, <ont2>, <common>, <f1>, <f2>)
    <result> = DIFFERENCE(<ont1>, <ont2>)
    <result> = APPLY(<functor>, <ontology>)
    <result> = COMPOSE(<functor1>, <functor2>)
}

VALIDATE <target> WITH <level>
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import sys
sys.path.insert(0, '/home/claude/categorical_ontology')

from core.dsl import (
    Object, Morphism, Category, Functor, NaturalTransformation,
    MorphismType, CategoryOperations, FunctorOperations
)
from core.validator import SemanticValidator, ValidationLevel


class TokenType(Enum):
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    SYMBOL = "SYMBOL"
    NUMBER = "NUMBER"
    NEWLINE = "NEWLINE"
    EOF = "EOF"


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int


class Lexer:
    """字句解析器"""
    
    KEYWORDS = {
        "ONTOLOGY", "OBJECT", "MORPHISM", "FUNCTOR",
        "OPERATION", "VALIDATE", "WITH",
        "MAP", "RULE",
        "COPRODUCT", "PRODUCT", "PULLBACK", "PUSHOUT", "DIFFERENCE",
        "APPLY", "COMPOSE",
        "attributes", "semantic", "type"
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self._skip_whitespace()
            if self.pos >= len(self.source):
                break
            
            char = self.source[self.pos]
            
            # コメント
            if char == '#':
                self._skip_line()
                continue
            
            # 文字列
            if char == '"':
                self.tokens.append(self._read_string())
                continue
            
            # シンボル
            if char in '{}[]():,->=' :
                if char == '-' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '>':
                    self.tokens.append(Token(TokenType.SYMBOL, '->', self.line, self.column))
                    self.pos += 2
                    self.column += 2
                else:
                    self.tokens.append(Token(TokenType.SYMBOL, char, self.line, self.column))
                    self.pos += 1
                    self.column += 1
                continue
            
            # 識別子/キーワード
            if char.isalpha() or char == '_':
                self.tokens.append(self._read_identifier())
                continue
            
            # 数値
            if char.isdigit():
                self.tokens.append(self._read_number())
                continue
            
            # 改行
            if char == '\n':
                self.line += 1
                self.column = 1
                self.pos += 1
                continue
            
            # その他（スキップ）
            self.pos += 1
            self.column += 1
        
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens
    
    def _skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in ' \t\r':
            self.pos += 1
            self.column += 1
    
    def _skip_line(self):
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self.pos += 1
        if self.pos < len(self.source):
            self.pos += 1
            self.line += 1
            self.column = 1
    
    def _read_string(self) -> Token:
        start_col = self.column
        self.pos += 1  # Skip opening quote
        self.column += 1
        start = self.pos
        
        while self.pos < len(self.source) and self.source[self.pos] != '"':
            if self.source[self.pos] == '\n':
                self.line += 1
                self.column = 1
            self.pos += 1
            self.column += 1
        
        value = self.source[start:self.pos]
        self.pos += 1  # Skip closing quote
        self.column += 1
        return Token(TokenType.STRING, value, self.line, start_col)
    
    def _read_identifier(self) -> Token:
        start_col = self.column
        start = self.pos
        
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] in '_'):
            self.pos += 1
            self.column += 1
        
        value = self.source[start:self.pos]
        token_type = TokenType.KEYWORD if value in self.KEYWORDS else TokenType.IDENTIFIER
        return Token(token_type, value, self.line, start_col)
    
    def _read_number(self) -> Token:
        start_col = self.column
        start = self.pos
        
        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
            self.pos += 1
            self.column += 1
        
        value = self.source[start:self.pos]
        return Token(TokenType.NUMBER, value, self.line, start_col)


class Parser:
    """構文解析器"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.ontologies: Dict[str, Category] = {}
        self.functors: Dict[str, Functor] = {}
        self.results: Dict[str, Any] = {}
    
    def parse(self) -> Dict[str, Any]:
        """パース実行"""
        while not self._is_at_end():
            self._parse_declaration()
        
        return {
            "ontologies": self.ontologies,
            "functors": self.functors,
            "results": self.results
        }
    
    def _parse_declaration(self):
        """宣言をパース"""
        if self._check(TokenType.KEYWORD, "ONTOLOGY"):
            self._parse_ontology()
        elif self._check(TokenType.KEYWORD, "FUNCTOR"):
            self._parse_functor()
        elif self._check(TokenType.KEYWORD, "OPERATION"):
            self._parse_operation()
        elif self._check(TokenType.KEYWORD, "VALIDATE"):
            self._parse_validation()
        else:
            self._advance()  # Skip unknown
    
    def _parse_ontology(self):
        """オントロジー定義をパース"""
        self._consume(TokenType.KEYWORD, "ONTOLOGY")
        name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.SYMBOL, "{")
        
        cat = Category(name, f"Ontology: {name}")
        
        while not self._check(TokenType.SYMBOL, "}"):
            if self._check(TokenType.KEYWORD, "OBJECT"):
                obj = self._parse_object()
                cat.add_object(obj)
            elif self._check(TokenType.KEYWORD, "MORPHISM"):
                morph = self._parse_morphism(cat)
                cat.add_morphism(morph)
            else:
                break
        
        self._consume(TokenType.SYMBOL, "}")
        self.ontologies[name] = cat
    
    def _parse_object(self) -> Object:
        """対象定義をパース"""
        self._consume(TokenType.KEYWORD, "OBJECT")
        name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.SYMBOL, ":")
        domain = self._consume(TokenType.IDENTIFIER).value
        
        attributes = []
        semantic = ""
        
        if self._check(TokenType.SYMBOL, "{"):
            self._consume(TokenType.SYMBOL, "{")
            
            while not self._check(TokenType.SYMBOL, "}"):
                if self._check(TokenType.KEYWORD, "attributes"):
                    self._consume(TokenType.KEYWORD, "attributes")
                    self._consume(TokenType.SYMBOL, ":")
                    self._consume(TokenType.SYMBOL, "[")
                    while not self._check(TokenType.SYMBOL, "]"):
                        attr = self._consume(TokenType.IDENTIFIER).value
                        attributes.append(attr)
                        if self._check(TokenType.SYMBOL, ","):
                            self._advance()
                    self._consume(TokenType.SYMBOL, "]")
                elif self._check(TokenType.KEYWORD, "semantic"):
                    self._consume(TokenType.KEYWORD, "semantic")
                    self._consume(TokenType.SYMBOL, ":")
                    semantic = self._consume(TokenType.STRING).value
                else:
                    break
            
            self._consume(TokenType.SYMBOL, "}")
        
        return Object(
            name=name,
            domain=domain,
            attributes=tuple(attributes),
            semantic_signature=semantic
        )
    
    def _parse_morphism(self, cat: Category) -> Morphism:
        """射定義をパース"""
        self._consume(TokenType.KEYWORD, "MORPHISM")
        name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.SYMBOL, ":")
        source_name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.SYMBOL, "->")
        target_name = self._consume(TokenType.IDENTIFIER).value
        
        morph_type = MorphismType.STRUCTURAL
        semantic = ""
        
        if self._check(TokenType.SYMBOL, "{"):
            self._consume(TokenType.SYMBOL, "{")
            
            while not self._check(TokenType.SYMBOL, "}"):
                if self._check(TokenType.KEYWORD, "type"):
                    self._consume(TokenType.KEYWORD, "type")
                    self._consume(TokenType.SYMBOL, ":")
                    type_name = self._consume(TokenType.IDENTIFIER).value
                    morph_type = MorphismType[type_name.upper()]
                elif self._check(TokenType.KEYWORD, "semantic"):
                    self._consume(TokenType.KEYWORD, "semantic")
                    self._consume(TokenType.SYMBOL, ":")
                    semantic = self._consume(TokenType.STRING).value
                else:
                    break
            
            self._consume(TokenType.SYMBOL, "}")
        
        source = cat.objects.get(source_name, Object(source_name, "unknown"))
        target = cat.objects.get(target_name, Object(target_name, "unknown"))
        
        return Morphism(
            name=name,
            source=source,
            target=target,
            morphism_type=morph_type,
            semantic_description=semantic
        )
    
    def _parse_functor(self):
        """関手定義をパース"""
        self._consume(TokenType.KEYWORD, "FUNCTOR")
        name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.SYMBOL, ":")
        source_name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.SYMBOL, "->")
        target_name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.SYMBOL, "{")
        
        object_map = {}
        morphism_map = {}
        rules = []
        
        while not self._check(TokenType.SYMBOL, "}"):
            if self._check(TokenType.KEYWORD, "MAP"):
                self._consume(TokenType.KEYWORD, "MAP")
                if self._check(TokenType.KEYWORD, "OBJECT"):
                    self._consume(TokenType.KEYWORD, "OBJECT")
                    src = self._consume(TokenType.IDENTIFIER).value
                    self._consume(TokenType.SYMBOL, "->")
                    tgt = self._consume(TokenType.IDENTIFIER).value
                    object_map[src] = tgt
                elif self._check(TokenType.KEYWORD, "MORPHISM"):
                    self._consume(TokenType.KEYWORD, "MORPHISM")
                    src = self._consume(TokenType.IDENTIFIER).value
                    self._consume(TokenType.SYMBOL, "->")
                    tgt = self._consume(TokenType.IDENTIFIER).value
                    morphism_map[src] = tgt
            elif self._check(TokenType.KEYWORD, "RULE"):
                self._consume(TokenType.KEYWORD, "RULE")
                rule = self._consume(TokenType.STRING).value
                rules.append(rule)
            else:
                break
        
        self._consume(TokenType.SYMBOL, "}")
        
        source_cat = self.ontologies.get(source_name)
        target_cat = self.ontologies.get(target_name)
        
        if source_cat and target_cat:
            functor = Functor(
                name=name,
                source_category=source_cat,
                target_category=target_cat,
                object_map=object_map,
                morphism_map=morphism_map,
                semantic_mapping_rules=rules
            )
            self.functors[name] = functor
    
    def _parse_operation(self):
        """演算定義をパース"""
        self._consume(TokenType.KEYWORD, "OPERATION")
        self._consume(TokenType.SYMBOL, "{")
        
        while not self._check(TokenType.SYMBOL, "}"):
            result_name = self._consume(TokenType.IDENTIFIER).value
            self._consume(TokenType.SYMBOL, "=")
            
            if self._check(TokenType.KEYWORD, "COPRODUCT"):
                self._consume(TokenType.KEYWORD, "COPRODUCT")
                self._consume(TokenType.SYMBOL, "(")
                ont1 = self._consume(TokenType.IDENTIFIER).value
                self._consume(TokenType.SYMBOL, ",")
                ont2 = self._consume(TokenType.IDENTIFIER).value
                self._consume(TokenType.SYMBOL, ")")
                
                cat1 = self.ontologies.get(ont1) or self.results.get(ont1)
                cat2 = self.ontologies.get(ont2) or self.results.get(ont2)
                
                if cat1 and cat2:
                    result = CategoryOperations.coproduct(cat1, cat2, result_name)
                    self.results[result_name] = result
            
            elif self._check(TokenType.KEYWORD, "PRODUCT"):
                self._consume(TokenType.KEYWORD, "PRODUCT")
                self._consume(TokenType.SYMBOL, "(")
                ont1 = self._consume(TokenType.IDENTIFIER).value
                self._consume(TokenType.SYMBOL, ",")
                ont2 = self._consume(TokenType.IDENTIFIER).value
                self._consume(TokenType.SYMBOL, ")")
                
                cat1 = self.ontologies.get(ont1) or self.results.get(ont1)
                cat2 = self.ontologies.get(ont2) or self.results.get(ont2)
                
                if cat1 and cat2:
                    result = CategoryOperations.product(cat1, cat2, result_name)
                    self.results[result_name] = result
            
            elif self._check(TokenType.KEYWORD, "DIFFERENCE"):
                self._consume(TokenType.KEYWORD, "DIFFERENCE")
                self._consume(TokenType.SYMBOL, "(")
                ont1 = self._consume(TokenType.IDENTIFIER).value
                self._consume(TokenType.SYMBOL, ",")
                ont2 = self._consume(TokenType.IDENTIFIER).value
                self._consume(TokenType.SYMBOL, ")")
                
                cat1 = self.ontologies.get(ont1) or self.results.get(ont1)
                cat2 = self.ontologies.get(ont2) or self.results.get(ont2)
                
                if cat1 and cat2:
                    result = CategoryOperations.difference(cat1, cat2, result_name)
                    self.results[result_name] = result
            
            else:
                break
        
        self._consume(TokenType.SYMBOL, "}")
    
    def _parse_validation(self):
        """検証をパース"""
        self._consume(TokenType.KEYWORD, "VALIDATE")
        target = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.KEYWORD, "WITH")
        level_name = self._consume(TokenType.IDENTIFIER).value
        
        level = ValidationLevel[level_name.upper()]
        # 検証ロジックは別途実装
    
    # ヘルパーメソッド
    def _check(self, token_type: TokenType, value: str = None) -> bool:
        if self._is_at_end():
            return False
        token = self.tokens[self.pos]
        if token.type != token_type:
            return False
        if value is not None and token.value != value:
            return False
        return True
    
    def _advance(self) -> Token:
        if not self._is_at_end():
            self.pos += 1
        return self.tokens[self.pos - 1]
    
    def _consume(self, token_type: TokenType, value: str = None) -> Token:
        if self._check(token_type, value):
            return self._advance()
        raise SyntaxError(f"Expected {token_type} {value or ''} at position {self.pos}")
    
    def _is_at_end(self) -> bool:
        return self.tokens[self.pos].type == TokenType.EOF


class CODSLInterpreter:
    """CODSL インタープリター"""
    
    def __init__(self, llm_client=None):
        self.validator = SemanticValidator(llm_client)
    
    def execute(self, source: str) -> Dict[str, Any]:
        """ソースコードを実行"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        parser = Parser(tokens)
        result = parser.parse()
        
        return result
    
    def execute_file(self, filepath: str) -> Dict[str, Any]:
        """ファイルから実行"""
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        return self.execute(source)


# サンプルDSLコード
SAMPLE_DSL = """
# 工場Aの生産オントロジー（簡略版）
ONTOLOGY FactoryA {
    OBJECT Boiler : equipment {
        attributes: [gas_boiler, 5MW]
        semantic: "天然ガス焚きボイラー"
    }
    
    OBJECT NaturalGas : energy {
        attributes: [fuel, m3]
        semantic: "天然ガス燃料"
    }
    
    OBJECT CO2Emission : emission {
        attributes: [scope1, combustion]
        semantic: "燃焼由来CO2排出"
    }
    
    MORPHISM consumes : Boiler -> NaturalGas {
        type: FUNCTIONAL
        semantic: "ボイラーが天然ガスを消費"
    }
    
    MORPHISM emits : NaturalGas -> CO2Emission {
        type: CAUSAL
        semantic: "燃焼によりCO2排出"
    }
}

# 工場Bの生産オントロジー（簡略版）
ONTOLOGY FactoryB {
    OBJECT SMTLine : equipment {
        attributes: [smt, 100kW]
        semantic: "SMT実装ライン"
    }
    
    OBJECT Electricity : energy {
        attributes: [purchased, kWh]
        semantic: "購入電力"
    }
    
    OBJECT CO2Indirect : emission {
        attributes: [scope2, electricity]
        semantic: "電力由来CO2排出"
    }
    
    MORPHISM uses : SMTLine -> Electricity {
        type: FUNCTIONAL
        semantic: "SMTが電力を使用"
    }
    
    MORPHISM causes : Electricity -> CO2Indirect {
        type: CAUSAL
        semantic: "電力使用によりCO2排出"
    }
}

# GHGレポートオントロジー
ONTOLOGY GHGReport {
    OBJECT Scope1 : scope {
        semantic: "直接排出"
    }
    
    OBJECT Scope2 : scope {
        semantic: "間接排出（エネルギー）"
    }
    
    OBJECT StationaryCombustion : category {
        semantic: "固定燃焼源"
    }
    
    OBJECT PurchasedElectricity : category {
        semantic: "購入電力"
    }
    
    MORPHISM includes_combustion : Scope1 -> StationaryCombustion {
        type: STRUCTURAL
        semantic: "Scope1は固定燃焼を含む"
    }
    
    MORPHISM includes_electricity : Scope2 -> PurchasedElectricity {
        type: STRUCTURAL
        semantic: "Scope2は購入電力を含む"
    }
}

# 関手定義：工場A → GHGレポート
FUNCTOR F_A_to_GHG : FactoryA -> GHGReport {
    MAP OBJECT CO2Emission -> StationaryCombustion
    MAP OBJECT NaturalGas -> StationaryCombustion
    MAP MORPHISM emits -> includes_combustion
    RULE "Scope1排出源は固定燃焼にマップ"
}

# 演算
OPERATION {
    Combined = COPRODUCT(FactoryA, FactoryB)
    OnlyA = DIFFERENCE(FactoryA, FactoryB)
}
"""


if __name__ == "__main__":
    print("=" * 80)
    print("CODSL (Categorical Ontology DSL) インタープリター")
    print("=" * 80)
    
    interpreter = CODSLInterpreter()
    result = interpreter.execute(SAMPLE_DSL)
    
    print("\n【パース結果】")
    print(f"\nオントロジー数: {len(result['ontologies'])}")
    for name, cat in result['ontologies'].items():
        print(f"  - {name}: {len(cat.objects)} objects, {len(cat.morphisms)} morphisms")
    
    print(f"\n関手数: {len(result['functors'])}")
    for name, func in result['functors'].items():
        print(f"  - {name}: {func.source_category.name} -> {func.target_category.name}")
    
    print(f"\n演算結果数: {len(result['results'])}")
    for name, res in result['results'].items():
        if isinstance(res, Category):
            print(f"  - {name}: {len(res.objects)} objects, {len(res.morphisms)} morphisms")
    
    print("\n【直和結果の対象（Combined）】")
    if 'Combined' in result['results']:
        for obj_name in list(result['results']['Combined'].objects.keys()):
            print(f"  - {obj_name}")
    
    print("\n【差分結果の対象（OnlyA）】")
    if 'OnlyA' in result['results']:
        for obj_name in list(result['results']['OnlyA'].objects.keys()):
            print(f"  - {obj_name}")
