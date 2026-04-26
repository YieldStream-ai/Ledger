dev:
	.venv/bin/uvicorn app.main:app --port 8100 --reload

test:
	.venv/bin/python -m pytest tests/ -v

build:
	docker build -t yieldstream-qualify .

build-local:
	docker build -f Dockerfile.local -t yieldstream-qualify-local .

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

up:
	docker compose up --build

down:
	docker compose down
