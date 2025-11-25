#!/bin/bash
# サーバーを再起動して最新のコードで動作確認

echo "==================================================================="
echo "Workbench Server 再起動スクリプト"
echo "==================================================================="

# 既存のサーバープロセスを停止
echo "1. 既存のサーバーを停止中..."
pkill -f "python.*workbench_server.py" 2>/dev/null
sleep 1

# 最新のコードを確認
echo "2. Gitの状態を確認..."
git status

# サーバーを起動
echo "3. サーバーを起動中..."
python workbench_server.py &
SERVER_PID=$!
sleep 2

echo ""
echo "==================================================================="
echo "サーバー起動完了: PID=$SERVER_PID"
echo "URL: http://localhost:8000/"
echo "==================================================================="
echo ""

# テスト実行
echo "4. API動作確認..."
curl -X POST http://localhost:8000/api/compute_instances \
  -H "Content-Type: application/json" \
  -d @examples/carbon_footprint_with_instances.json \
  -s | python -c "
import sys, json
try:
    r = json.load(sys.stdin)
    if r['success']:
        print('✅ API動作正常')
        print(f\"   日次排出量: {r['results']['total_emissions_daily']:.2f} kg-CO2/day\")
        print(f\"   年間排出量: {r['results']['total_emissions_annual']:.2f} t-CO2/year\")
    else:
        print('❌ エラー:', r.get('error'))
except Exception as e:
    print('❌ 解析エラー:', e)
"

echo ""
echo "==================================================================="
echo "サーバーを停止する場合: kill $SERVER_PID"
echo "==================================================================="
