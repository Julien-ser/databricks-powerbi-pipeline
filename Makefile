.PHONY: help install test lint format docker-build docker-run validate deploy clean

help:
	@echo "Databricks PowerBI Pipeline - Available commands:"
	@echo ""
	@echo "  make install        Install dependencies and package"
	@echo "  make test           Run all tests with coverage"
	@echo "  make unit-test      Run unit tests only"
	@echo "  make integration-test Run integration tests"
	@echo "  make lint           Run linters (flake8, black, mypy)"
	@echo "  make format         Auto-format code with black"
	@echo "  make validate       Validate deployment configuration"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-run     Run Docker container"
	@echo "  make deploy         Deploy notebooks and run pipeline"
	@echo "  make clean          Clean build artifacts and logs"
	@echo "  make clean-all      Clean everything including virtualenv"

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

unit-test:
	pytest tests/unit/ -v

integration-test:
	pytest tests/integration/ -v

lint:
	flake8 src/ tests/
	black --check src/ tests/
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/

validate:
	python src/validate_deployment.py

docker-build:
	docker build -t databricks-powerbi-pipeline:latest .

docker-run:
	docker run -it --rm \
		-v $(pwd)/config:/app/config \
		-v $(pwd)/data:/app/data \
		-v $(pwd)/logs:/app/logs \
		databricks-powerbi-pipeline:latest

deploy:
	python src/deploy_notebooks.py
	python src/monitor_pipeline.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf logs/*.log 2>/dev/null || true
	rm -f .coverage coverage.xml

clean-all: clean
	find . -type d -name "venv" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache 2>/dev/null || true
