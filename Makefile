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

# ─── AWS (run `terraform apply` in infra/ first) ─────────────────────────────
# Lambda runs x86_64; build for amd64 explicitly (Apple Silicon defaults to arm64).
# --provenance=false: Lambda rejects the multi-manifest index buildx adds by default.

AWS_REGION ?= us-west-2

deploy-image:
	$(eval ECR_URL := $(shell terraform -chdir=infra output -raw ecr_repository_url))
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(firstword $(subst /, ,$(ECR_URL)))
	docker build --platform linux/amd64 --provenance=false -t $(ECR_URL):latest .
	docker push $(ECR_URL):latest
	aws lambda update-function-code --function-name yieldstream-qualify --image-uri $(ECR_URL):latest --region $(AWS_REGION) --no-cli-pager >/dev/null
	aws lambda update-function-code --function-name yieldstream-qualify-worker --image-uri $(ECR_URL):latest --region $(AWS_REGION) --no-cli-pager >/dev/null
	@echo "Deployed $(ECR_URL):latest to API + worker Lambdas"

# make smoke PDF=path/to/statement.pdf
smoke:
	.venv/bin/python scripts/smoke_async.py $$(terraform -chdir=infra output -raw api_url) $(PDF)
