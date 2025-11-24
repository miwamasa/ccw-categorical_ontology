#!/usr/bin/env python3
"""ワークベンチの動作テスト"""

from core import (
    Object, Morphism, Category, Functor,
    MorphismType, CategoryOperations
)

# 圏1: CustomerSchema
cat1 = Category("CustomerSchema", "顧客管理スキーマ")

customer1 = Object(
    name="Customer",
    domain="entity",
    attributes=("id", "name", "email"),
    semantic_signature="顧客エンティティ"
)
cat1.add_object(customer1)

address1 = Object(
    name="Address",
    domain="entity",
    attributes=("street", "city"),
    semantic_signature="住所"
)
cat1.add_object(address1)

has_address = Morphism(
    name="has_address",
    source=customer1,
    target=address1,
    morphism_type=MorphismType.FUNCTIONAL,
    semantic_description="顧客は住所を持つ"
)
cat1.add_morphism(has_address)

# 圏2: OrderSchema
cat2 = Category("OrderSchema", "注文管理スキーマ")

customer2 = Object(
    name="Customer",
    domain="entity",
    attributes=("id", "name"),
    semantic_signature="顧客（注文側）"
)
cat2.add_object(customer2)

order = Object(
    name="Order",
    domain="entity",
    attributes=("id", "date", "total"),
    semantic_signature="注文"
)
cat2.add_object(order)

places_order = Morphism(
    name="places_order",
    source=customer2,
    target=order,
    morphism_type=MorphismType.FUNCTIONAL,
    semantic_description="顧客は注文を行う"
)
cat2.add_morphism(places_order)

# 直和演算
print("=" * 60)
print("直和演算: CustomerSchema + OrderSchema")
print("=" * 60)

result = CategoryOperations.coproduct(cat1, cat2)

print(f"結果の圏名: {result.name}")
print(f"対象数: {len(result.objects)}")
print(f"射数: {len(result.morphisms)}")
print()

print("対象一覧:")
for obj_name, obj in result.objects.items():
    print(f"  - {obj_name}: {obj.semantic_signature}")
print()

print("射一覧:")
for morph_name, morph in result.morphisms.items():
    print(f"  - {morph_name}: {morph.source.name} → {morph.target.name}")
    print(f"    説明: {morph.semantic_description}")
print()

print("✅ 直和演算が正常に動作しました！")
