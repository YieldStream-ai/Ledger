dev:
	.venv/bin/uvicorn app.main:app --port 8100 --reload

test:
	.venv/bin/python -m pytest tests/ -v

build:
	docker build -t yieldstream-qualify .

build-local:
	docker build -f Dockerfile.local -t yieldstream-qualify-local .
