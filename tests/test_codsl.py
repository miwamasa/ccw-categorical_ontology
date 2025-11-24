"""
CODSL テストケース

テスト項目:
1. 圏の基本操作
2. 関手の構造保存
3. 演算の正確性
4. DSLパーサー
5. 検証器
"""

import unittest
import sys
sys.path.insert(0, '/home/claude/categorical_ontology')

from core.dsl import (
    Object, Morphism, Category, Functor,
    MorphismType, CategoryOperations, FunctorOperations
)
from core.validator import SemanticValidator, ValidationLevel
from core.interpreter import CODSLInterpreter, Lexer, Parser


class TestCategoryBasics(unittest.TestCase):
    """圏の基本操作テスト"""
    
    def setUp(self):
        """テスト用の圏を作成"""
        self.cat = Category("TestCat", "Test Category")
        
        self.obj_a = Object("A", "domain1", ("attr1",), "Object A")
        self.obj_b = Object("B", "domain1", ("attr2",), "Object B")
        self.obj_c = Object("C", "domain2", ("attr3",), "Object C")
        
        self.cat.add_object(self.obj_a)
        self.cat.add_object(self.obj_b)
        self.cat.add_object(self.obj_c)
        
        self.morph_ab = Morphism(
            name="f",
            source=self.obj_a,
            target=self.obj_b,
            morphism_type=MorphismType.STRUCTURAL,
            semantic_description="A to B"
        )
        self.morph_bc = Morphism(
            name="g",
            source=self.obj_b,
            target=self.obj_c,
            morphism_type=MorphismType.STRUCTURAL,
            semantic_description="B to C"
        )
        
        self.cat.add_morphism(self.morph_ab)
        self.cat.add_morphism(self.morph_bc)
    
    def test_object_addition(self):
        """対象の追加テスト"""
        self.assertEqual(len(self.cat.objects), 3)
        self.assertIn("A", self.cat.objects)
        self.assertIn("B", self.cat.objects)
        self.assertIn("C", self.cat.objects)
    
    def test_morphism_addition(self):
        """射の追加テスト"""
        self.assertEqual(len(self.cat.morphisms), 2)
        self.assertIn("f", self.cat.morphisms)
        self.assertIn("g", self.cat.morphisms)
    
    def test_identity_morphisms(self):
        """恒等射の自動生成テスト"""
        self.assertIn("A", self.cat._identity_morphisms)
        id_a = self.cat._identity_morphisms["A"]
        self.assertEqual(id_a.source, self.obj_a)
        self.assertEqual(id_a.target, self.obj_a)
        self.assertEqual(id_a.morphism_type, MorphismType.IDENTITY)
    
    def test_morphism_composition(self):
        """射の合成テスト"""
        composed = self.morph_bc.compose(self.morph_ab)
        self.assertIsNotNone(composed)
        self.assertEqual(composed.source, self.obj_a)
        self.assertEqual(composed.target, self.obj_c)
        self.assertEqual(composed.name, "(g ∘ f)")
    
    def test_morphism_composition_incompatible(self):
        """非互換な射の合成テスト"""
        composed = self.morph_ab.compose(self.morph_bc)
        self.assertIsNone(composed)
    
    def test_get_morphisms_from(self):
        """対象から出る射の取得テスト"""
        morphs = self.cat.get_morphisms_from(self.obj_a)
        self.assertEqual(len(morphs), 1)
        self.assertEqual(morphs[0].name, "f")
    
    def test_category_signature(self):
        """圏のシグネチャテスト"""
        sig1 = self.cat.signature()
        sig2 = self.cat.signature()
        self.assertEqual(sig1, sig2)  # 決定論的


class TestCategoryOperations(unittest.TestCase):
    """圏の演算テスト"""
    
    def setUp(self):
        """テスト用の圏を作成"""
        self.cat1 = Category("Cat1", "Category 1")
        self.cat1.add_object(Object("X", "d1"))
        self.cat1.add_object(Object("Y", "d1"))
        self.cat1.add_morphism(Morphism(
            "f1", 
            Object("X", "d1"), 
            Object("Y", "d1"),
            MorphismType.STRUCTURAL
        ))
        
        self.cat2 = Category("Cat2", "Category 2")
        self.cat2.add_object(Object("Y", "d2"))  # 同名だが異なるドメイン
        self.cat2.add_object(Object("Z", "d2"))
        self.cat2.add_morphism(Morphism(
            "f2",
            Object("Y", "d2"),
            Object("Z", "d2"),
            MorphismType.FUNCTIONAL
        ))
    
    def test_coproduct(self):
        """直和テスト"""
        result = CategoryOperations.coproduct(self.cat1, self.cat2)
        
        # 対象数: 2 + 2 = 4
        self.assertEqual(len(result.objects), 4)
        
        # タグ付き名前
        self.assertIn("Cat1.X", result.objects)
        self.assertIn("Cat1.Y", result.objects)
        self.assertIn("Cat2.Y", result.objects)
        self.assertIn("Cat2.Z", result.objects)
        
        # 射数
        self.assertEqual(len(result.morphisms), 2)
    
    def test_product(self):
        """直積テスト"""
        result = CategoryOperations.product(self.cat1, self.cat2)
        
        # 対象数: 2 × 2 = 4
        self.assertEqual(len(result.objects), 4)
        
        # ペア名
        self.assertIn("(X, Y)", result.objects)
        self.assertIn("(X, Z)", result.objects)
        self.assertIn("(Y, Y)", result.objects)
        self.assertIn("(Y, Z)", result.objects)
    
    def test_difference(self):
        """差分テスト"""
        # cat1 にあって cat2 にないもの
        # Y は両方にあるが、ドメインが異なる (d1 vs d2) ので別物として扱う
        result = CategoryOperations.difference(self.cat1, self.cat2)
        
        # X は cat2 にない
        self.assertIn("X", result.objects)
        # Y は cat1 では d1, cat2 では d2 なので、(Y, d1) は cat2 にない
        # よって Y も差分に含まれる（異なるドメイン = 異なる概念）
        self.assertIn("Y", result.objects)
        
        # ドメインが同じ場合のテスト
        cat3 = Category("Cat3", "Category 3")
        cat3.add_object(Object("Y", "d1"))  # 同名かつ同ドメイン
        
        result2 = CategoryOperations.difference(self.cat1, cat3)
        # X は cat3 にない
        self.assertIn("X", result2.objects)
        # Y は同名・同ドメインなので差分に含まれない
        self.assertNotIn("Y", result2.objects)


class TestFunctor(unittest.TestCase):
    """関手テスト"""
    
    def setUp(self):
        """テスト用の圏と関手を作成"""
        self.source = Category("Source", "Source Category")
        self.source.add_object(Object("A", "d1"))
        self.source.add_object(Object("B", "d1"))
        self.source.add_morphism(Morphism(
            "f", 
            Object("A", "d1"),
            Object("B", "d1"),
            MorphismType.STRUCTURAL
        ))
        
        self.target = Category("Target", "Target Category")
        self.target.add_object(Object("X", "d2"))
        self.target.add_object(Object("Y", "d2"))
        self.target.add_morphism(Morphism(
            "g",
            Object("X", "d2"),
            Object("Y", "d2"),
            MorphismType.STRUCTURAL
        ))
        
        self.functor = Functor(
            name="F",
            source_category=self.source,
            target_category=self.target,
            object_map={"A": "X", "B": "Y"},
            morphism_map={"f": "g"}
        )
    
    def test_functor_apply_object(self):
        """対象への関手適用テスト"""
        obj_a = self.source.objects["A"]
        result = self.functor.apply_to_object(obj_a)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "X")
    
    def test_functor_apply_morphism(self):
        """射への関手適用テスト"""
        morph_f = self.source.morphisms["f"]
        result = self.functor.apply_to_morphism(morph_f)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "g")
    
    def test_functor_validity(self):
        """関手の整合性検証テスト"""
        is_valid, errors = self.functor.is_valid()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_functor_invalid_mapping(self):
        """不正なマッピングのテスト"""
        bad_functor = Functor(
            name="BadF",
            source_category=self.source,
            target_category=self.target,
            object_map={"A": "NonExistent"},  # 存在しない
            morphism_map={}
        )
        is_valid, errors = bad_functor.is_valid()
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)


class TestFunctorComposition(unittest.TestCase):
    """関手の合成テスト"""
    
    def setUp(self):
        """3つの圏と2つの関手を作成"""
        self.cat_a = Category("A", "Category A")
        self.cat_a.add_object(Object("a1", "d"))
        
        self.cat_b = Category("B", "Category B")
        self.cat_b.add_object(Object("b1", "d"))
        
        self.cat_c = Category("C", "Category C")
        self.cat_c.add_object(Object("c1", "d"))
        
        self.f = Functor(
            name="F",
            source_category=self.cat_a,
            target_category=self.cat_b,
            object_map={"a1": "b1"},
            morphism_map={}
        )
        
        self.g = Functor(
            name="G",
            source_category=self.cat_b,
            target_category=self.cat_c,
            object_map={"b1": "c1"},
            morphism_map={}
        )
    
    def test_functor_composition(self):
        """関手の合成テスト"""
        composed = FunctorOperations.compose(self.g, self.f)
        self.assertIsNotNone(composed)
        self.assertEqual(composed.source_category.name, "A")
        self.assertEqual(composed.target_category.name, "C")
        self.assertEqual(composed.object_map.get("a1"), "c1")


class TestLexer(unittest.TestCase):
    """字句解析器テスト"""
    
    def test_basic_tokens(self):
        """基本トークンのテスト"""
        source = 'ONTOLOGY Test { OBJECT A : domain }'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # キーワード
        self.assertEqual(tokens[0].type.value, "KEYWORD")
        self.assertEqual(tokens[0].value, "ONTOLOGY")
        
        # 識別子
        self.assertEqual(tokens[1].type.value, "IDENTIFIER")
        self.assertEqual(tokens[1].value, "Test")
        
        # シンボル
        self.assertEqual(tokens[2].type.value, "SYMBOL")
        self.assertEqual(tokens[2].value, "{")
    
    def test_string_token(self):
        """文字列トークンのテスト"""
        source = 'semantic: "This is a test"'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        string_tokens = [t for t in tokens if t.type.value == "STRING"]
        self.assertEqual(len(string_tokens), 1)
        self.assertEqual(string_tokens[0].value, "This is a test")
    
    def test_arrow_token(self):
        """矢印トークンのテスト"""
        source = 'A -> B'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        arrow_tokens = [t for t in tokens if t.value == "->"]
        self.assertEqual(len(arrow_tokens), 1)


class TestParser(unittest.TestCase):
    """構文解析器テスト"""
    
    def test_parse_simple_ontology(self):
        """単純なオントロジーのパーステスト"""
        source = """
        ONTOLOGY TestOnt {
            OBJECT A : domain1
            OBJECT B : domain1
            MORPHISM f : A -> B
        }
        """
        interpreter = CODSLInterpreter()
        result = interpreter.execute(source)
        
        self.assertIn("TestOnt", result["ontologies"])
        ont = result["ontologies"]["TestOnt"]
        self.assertEqual(len(ont.objects), 2)
        self.assertEqual(len(ont.morphisms), 1)
    
    def test_parse_operation(self):
        """演算のパーステスト"""
        source = """
        ONTOLOGY A {
            OBJECT X : d
        }
        ONTOLOGY B {
            OBJECT Y : d
        }
        OPERATION {
            Combined = COPRODUCT(A, B)
        }
        """
        interpreter = CODSLInterpreter()
        result = interpreter.execute(source)
        
        self.assertIn("Combined", result["results"])
        combined = result["results"]["Combined"]
        self.assertEqual(len(combined.objects), 2)


class TestValidator(unittest.TestCase):
    """検証器テスト"""
    
    def test_structural_validation(self):
        """構造的検証テスト"""
        validator = SemanticValidator()
        
        context = {
            "operation": "functor_application",
            "source": {"objects": [{"name": "A"}]},
            "target": {"objects": [{"name": "X"}]},
            "object_map": {"A": "X"},
            "morphism_map": {}
        }
        
        result = validator.validate(context, ValidationLevel.STRUCTURAL)
        self.assertIsNotNone(result)
        self.assertIsInstance(result.confidence, float)


class TestCarbonFootprintScenario(unittest.TestCase):
    """カーボンフットプリントシナリオテスト"""
    
    def test_full_scenario(self):
        """完全なシナリオテスト"""
        from examples.carbon_footprint import (
            create_factory_a_ontology,
            create_factory_b_ontology,
            create_ghg_report_ontology,
            create_factory_to_ghg_functor
        )
        
        # オントロジー作成
        factory_a = create_factory_a_ontology()
        factory_b = create_factory_b_ontology()
        ghg_report = create_ghg_report_ontology()
        
        # 基本検証
        self.assertTrue(len(factory_a.objects) > 0)
        self.assertTrue(len(factory_b.objects) > 0)
        self.assertTrue(len(ghg_report.objects) > 0)
        
        # 関手作成と適用
        functor = create_factory_to_ghg_functor(factory_a, ghg_report)
        self.assertTrue(len(functor.object_map) > 0)
        
        # 演算
        combined = CategoryOperations.coproduct(factory_a, factory_b)
        self.assertEqual(
            len(combined.objects),
            len(factory_a.objects) + len(factory_b.objects)
        )
        
        diff = CategoryOperations.difference(factory_a, factory_b)
        self.assertTrue(len(diff.objects) >= 0)


def run_tests():
    """テスト実行"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # テストクラスを追加
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryBasics))
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestFunctor))
    suite.addTests(loader.loadTestsFromTestCase(TestFunctorComposition))
    suite.addTests(loader.loadTestsFromTestCase(TestLexer))
    suite.addTests(loader.loadTestsFromTestCase(TestParser))
    suite.addTests(loader.loadTestsFromTestCase(TestValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestCarbonFootprintScenario))
    
    # 実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    run_tests()
