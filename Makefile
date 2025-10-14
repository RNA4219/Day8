.PHONY: bootstrap test report clean

bootstrap:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip

# 仮のテスト導線。CI のダミー出力と合わせてログを生成する。
test:
	mkdir -p logs
	echo '{"name":"sample::ok","status":"pass","duration_ms":120}' > logs/test.jsonl
	echo '{"name":"sample::fail","status":"fail","duration_ms":900}' >> logs/test.jsonl

report:
	. .venv/bin/activate && python scripts/analyze.py

clean:
	rm -rf .venv logs/test.jsonl reports/today.md reports/issue_suggestions.md
