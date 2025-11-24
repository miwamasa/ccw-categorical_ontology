"""
Categorical Ontology DSL (CODSL)

圏論に基づくオントロジー演算体系
"""

from .dsl import (
    Object,
    Morphism,
    Category,
    Functor,
    NaturalTransformation,
    MorphismType,
    CategoryOperations,
    FunctorOperations
)

from .validator import (
    SemanticValidator,
    ValidationLevel,
    ValidationResult,
    DomainRules,
    create_ghg_rules,
    create_manufacturing_rules
)

from .interpreter import (
    CODSLInterpreter,
    Lexer,
    Parser
)

__all__ = [
    # DSL Core
    'Object',
    'Morphism', 
    'Category',
    'Functor',
    'NaturalTransformation',
    'MorphismType',
    'CategoryOperations',
    'FunctorOperations',
    
    # Validator
    'SemanticValidator',
    'ValidationLevel',
    'ValidationResult',
    'DomainRules',
    'create_ghg_rules',
    'create_manufacturing_rules',
    
    # Interpreter
    'CODSLInterpreter',
    'Lexer',
    'Parser'
]
