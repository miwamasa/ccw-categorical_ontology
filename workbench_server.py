#!/usr/bin/env python3
"""
CODSL Workbench Server
標準ライブラリのみを使用したWebベースのワークベンチ
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
from pathlib import Path

# coreモジュールをインポート
sys.path.insert(0, str(Path(__file__).parent))
from core import (
    Object, Morphism, Category, Functor,
    MorphismType, CategoryOperations, FunctorOperations
)


class WorkbenchHandler(BaseHTTPRequestHandler):
    """ワークベンチのHTTPリクエストハンドラ"""

    def do_GET(self):
        """GETリクエストの処理"""
        parsed = urlparse(self.path)

        if parsed.path == '/' or parsed.path == '/index.html':
            self.serve_file('workbench_ui.html', 'text/html')
        elif parsed.path == '/favicon.ico':
            # faviconリクエストには204 No Contentを返す
            self.send_response(204)
            self.end_headers()
        elif parsed.path == '/api/examples':
            self.handle_list_examples()
        elif parsed.path.startswith('/api/example/'):
            example_name = parsed.path.split('/')[-1]
            self.handle_get_example(example_name)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """POSTリクエストの処理"""
        parsed = urlparse(self.path)

        if parsed.path == '/api/execute':
            self.handle_execute()
        elif parsed.path == '/api/save_example':
            self.handle_save_example()
        else:
            self.send_error(404, "Not Found")

    def serve_file(self, filename, content_type):
        """ファイルを配信"""
        try:
            filepath = Path(__file__).parent / filename
            with open(filepath, 'rb') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, f"File not found: {filename}")

    def handle_list_examples(self):
        """例題一覧を返す"""
        examples_dir = Path(__file__).parent / 'examples'
        examples = []

        # 組み込み例題
        examples.append({
            'name': 'carbon_footprint',
            'title': 'カーボンフットプリント（工場A+B）',
            'description': '製造業のGHG排出量管理の例題'
        })

        # カスタム例題（JSONファイル）
        if examples_dir.exists():
            for json_file in examples_dir.glob('*.json'):
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        examples.append({
                            'name': json_file.stem,
                            'title': data.get('title', json_file.stem),
                            'description': data.get('description', '')
                        })
                except:
                    pass

        self.send_json_response(examples)

    def handle_get_example(self, example_name):
        """特定の例題を取得"""
        if example_name == 'carbon_footprint':
            # 組み込み例題を返す
            example_data = self.get_carbon_footprint_example()
            self.send_json_response(example_data)
        else:
            # カスタム例題を読み込み
            json_file = Path(__file__).parent / 'examples' / f'{example_name}.json'
            try:
                with open(json_file) as f:
                    data = json.load(f)
                self.send_json_response(data)
            except FileNotFoundError:
                self.send_error(404, f"Example not found: {example_name}")

    def handle_execute(self):
        """オントロジー演算を実行"""
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        request_data = json.loads(body.decode('utf-8'))

        try:
            result = self.execute_operation(request_data)
            self.send_json_response(result)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"Error: {tb}")
            self.send_json_response({
                'error': str(e),
                'type': type(e).__name__,
                'traceback': tb
            }, status=400)

    def handle_save_example(self):
        """例題を保存"""
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body.decode('utf-8'))

        examples_dir = Path(__file__).parent / 'examples'
        examples_dir.mkdir(exist_ok=True)

        filename = data.get('name', 'custom_example')
        filepath = examples_dir / f'{filename}.json'

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.send_json_response({'success': True, 'path': str(filepath)})

    def execute_operation(self, request_data):
        """演算を実行して結果を返す"""
        operation = request_data.get('operation')
        categories_data = request_data.get('categories', [])
        functors_data = request_data.get('functors', [])

        # カテゴリを構築
        categories = {}
        for cat_data in categories_data:
            cat = self.build_category(cat_data)
            categories[cat_data['name']] = cat

        # 関手を構築
        functors = {}
        for func_data in functors_data:
            func = self.build_functor(func_data, categories)
            functors[func_data['name']] = func

        # 演算を実行
        result = {}

        if operation == 'coproduct':
            cat1_name = request_data.get('cat1')
            cat2_name = request_data.get('cat2')
            result_cat = CategoryOperations.coproduct(
                categories[cat1_name],
                categories[cat2_name]
            )
            result = self.category_to_dict(result_cat)

        elif operation == 'product':
            cat1_name = request_data.get('cat1')
            cat2_name = request_data.get('cat2')
            result_cat = CategoryOperations.product(
                categories[cat1_name],
                categories[cat2_name]
            )
            result = self.category_to_dict(result_cat)

        elif operation == 'difference':
            cat1_name = request_data.get('cat1')
            cat2_name = request_data.get('cat2')
            result_cat = CategoryOperations.difference(
                categories[cat1_name],
                categories[cat2_name]
            )
            result = self.category_to_dict(result_cat)

        elif operation == 'pullback':
            cat1_name = request_data.get('cat1')
            cat2_name = request_data.get('cat2')
            target_name = request_data.get('target')
            func1_name = request_data.get('functor1')
            func2_name = request_data.get('functor2')

            result_cat = CategoryOperations.pullback(
                categories[cat1_name],
                categories[cat2_name],
                categories[target_name],
                functors[func1_name],
                functors[func2_name]
            )
            result = self.category_to_dict(result_cat)

        elif operation == 'apply_functor':
            func_name = request_data.get('functor')
            functor = functors[func_name]

            # 関手の情報を返す
            result = {
                'functor': func_name,
                'source': functor.source.name,
                'target': functor.target.name,
                'object_mappings': {
                    obj.name: functor.apply_to_object(obj).name
                    for obj in functor.source.objects
                    if obj.name in functor.object_map
                },
                'morphism_mappings': {
                    morph.name: functor.apply_to_morphism(morph).name
                    for morph in functor.source.morphisms
                    if morph.name in functor.morphism_map
                },
                'is_valid': functor.is_valid()[0],
                'validation_errors': functor.is_valid()[1]
            }

        return result

    def build_category(self, cat_data):
        """JSONデータからCategoryオブジェクトを構築"""
        cat = Category(cat_data['name'], cat_data.get('description', ''))

        # 対象を追加
        obj_map = {}
        for obj_data in cat_data.get('objects', []):
            obj = Object(
                name=obj_data['name'],
                domain=obj_data.get('domain', ''),
                attributes=tuple(obj_data.get('attributes', [])),
                semantic_signature=obj_data.get('semantic', '')
            )
            cat.add_object(obj)
            obj_map[obj.name] = obj

        # 射を追加
        for morph_data in cat_data.get('morphisms', []):
            morph = Morphism(
                name=morph_data['name'],
                source=obj_map[morph_data['source']],
                target=obj_map[morph_data['target']],
                morphism_type=MorphismType[morph_data.get('type', 'FUNCTIONAL')],
                semantic_description=morph_data.get('semantic', '')
            )
            cat.add_morphism(morph)

        return cat

    def build_functor(self, func_data, categories):
        """JSONデータからFunctorオブジェクトを構築"""
        source = categories[func_data['source']]
        target = categories[func_data['target']]

        functor = Functor(
            name=func_data['name'],
            source=source,
            target=target,
            description=func_data.get('description', '')
        )

        # オブジェクトマッピング
        for src_name, tgt_name in func_data.get('object_map', {}).items():
            src_obj = next(o for o in source.objects if o.name == src_name)
            tgt_obj = next(o for o in target.objects if o.name == tgt_name)
            functor.add_object_mapping(src_obj, tgt_obj)

        # 射マッピング
        for src_name, tgt_name in func_data.get('morphism_map', {}).items():
            src_morph = next(m for m in source.morphisms if m.name == src_name)
            tgt_morph = next(m for m in target.morphisms if m.name == tgt_name)
            functor.add_morphism_mapping(src_morph, tgt_morph)

        return functor

    def category_to_dict(self, cat):
        """CategoryオブジェクトをJSONシリアライズ可能な辞書に変換"""
        return {
            'name': cat.name,
            'description': cat.description,
            'objects': [
                {
                    'name': obj.name,
                    'domain': obj.domain,
                    'attributes': list(obj.attributes),
                    'semantic': obj.semantic_signature
                }
                for obj in cat.objects.values()
            ],
            'morphisms': [
                {
                    'name': morph.name,
                    'source': morph.source.name,
                    'target': morph.target.name,
                    'type': morph.morphism_type.name,
                    'semantic': morph.semantic_description
                }
                for morph in cat.morphisms.values()
            ],
            'object_count': len(cat.objects),
            'morphism_count': len(cat.morphisms)
        }

    def get_carbon_footprint_example(self):
        """カーボンフットプリント例題のデータを返す"""
        return {
            'title': 'カーボンフットプリント（工場A+B）',
            'description': '製造業のGHG排出量管理の例題',
            'categories': [
                {
                    'name': 'FactoryA',
                    'description': 'Factory A - Automotive Parts',
                    'objects': [
                        {
                            'name': 'BoilerA1',
                            'domain': 'equipment',
                            'attributes': ['type:gas_boiler', 'capacity:5MW'],
                            'semantic': '天然ガス焚きボイラー'
                        },
                        {
                            'name': 'CNCMachine01',
                            'domain': 'equipment',
                            'attributes': ['type:cnc_machine', 'power:50kW'],
                            'semantic': 'CNC加工機'
                        },
                        {
                            'name': 'CO2_Combustion',
                            'domain': 'emission',
                            'attributes': ['scope:1'],
                            'semantic': '燃焼由来CO2'
                        },
                        {
                            'name': 'CO2_Electricity',
                            'domain': 'emission',
                            'attributes': ['scope:2'],
                            'semantic': '電力由来CO2'
                        }
                    ],
                    'morphisms': [
                        {
                            'name': 'boiler_emits',
                            'source': 'BoilerA1',
                            'target': 'CO2_Combustion',
                            'type': 'CAUSAL',
                            'semantic': 'ボイラーがCO2を排出'
                        },
                        {
                            'name': 'cnc_emits',
                            'source': 'CNCMachine01',
                            'target': 'CO2_Electricity',
                            'type': 'CAUSAL',
                            'semantic': 'CNC機械が電力由来CO2を排出'
                        }
                    ]
                },
                {
                    'name': 'FactoryB',
                    'description': 'Factory B - Electronics',
                    'objects': [
                        {
                            'name': 'SMTLine01',
                            'domain': 'equipment',
                            'attributes': ['type:smt_line', 'power:100kW'],
                            'semantic': 'SMT生産ライン'
                        },
                        {
                            'name': 'CO2_Electricity',
                            'domain': 'emission',
                            'attributes': ['scope:2'],
                            'semantic': '電力由来CO2'
                        }
                    ],
                    'morphisms': [
                        {
                            'name': 'smt_emits',
                            'source': 'SMTLine01',
                            'target': 'CO2_Electricity',
                            'type': 'CAUSAL',
                            'semantic': 'SMTラインが電力由来CO2を排出'
                        }
                    ]
                },
                {
                    'name': 'GHGReport',
                    'description': 'GHG Protocol Report Structure',
                    'objects': [
                        {
                            'name': 'Scope1',
                            'domain': 'scope',
                            'attributes': [],
                            'semantic': '直接排出'
                        },
                        {
                            'name': 'Scope2',
                            'domain': 'scope',
                            'attributes': [],
                            'semantic': '間接排出（電力）'
                        },
                        {
                            'name': 'StationaryCombustion',
                            'domain': 'category',
                            'attributes': ['scope:1'],
                            'semantic': '固定燃焼'
                        },
                        {
                            'name': 'PurchasedElectricity',
                            'domain': 'category',
                            'attributes': ['scope:2'],
                            'semantic': '購入電力'
                        }
                    ],
                    'morphisms': [
                        {
                            'name': 'scope1_includes_combustion',
                            'source': 'Scope1',
                            'target': 'StationaryCombustion',
                            'type': 'STRUCTURAL',
                            'semantic': 'Scope1は固定燃焼を含む'
                        },
                        {
                            'name': 'scope2_includes_electricity',
                            'source': 'Scope2',
                            'target': 'PurchasedElectricity',
                            'type': 'STRUCTURAL',
                            'semantic': 'Scope2は購入電力を含む'
                        }
                    ]
                }
            ],
            'functors': [
                {
                    'name': 'F_A_to_GHG',
                    'source': 'FactoryA',
                    'target': 'GHGReport',
                    'description': '工場AからGHGレポートへの変換',
                    'object_map': {
                        'CO2_Combustion': 'StationaryCombustion',
                        'CO2_Electricity': 'PurchasedElectricity'
                    },
                    'morphism_map': {}
                },
                {
                    'name': 'F_B_to_GHG',
                    'source': 'FactoryB',
                    'target': 'GHGReport',
                    'description': '工場BからGHGレポートへの変換',
                    'object_map': {
                        'CO2_Electricity': 'PurchasedElectricity'
                    },
                    'morphism_map': {}
                }
            ]
        }

    def send_json_response(self, data, status=200):
        """JSON形式でレスポンスを返す"""
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        json_bytes = json_data.encode('utf-8')

        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(json_bytes))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json_bytes)

    def log_message(self, format, *args):
        """ログメッセージをカスタマイズ"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(port=8000):
    """サーバーを起動"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, WorkbenchHandler)
    print(f"""
================================================================================
CODSL Workbench Server 起動
================================================================================
URL: http://localhost:{port}/
終了: Ctrl+C
================================================================================
""")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nサーバーを停止しています...")
        httpd.shutdown()


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
