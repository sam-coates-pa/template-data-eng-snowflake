
##############################################
# Snowflake + Prefect Makefile
##############################################

PYTHON := python3

## Install all dependencies
install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

## Run the Snowflake Prefect flow
run:
	$(PYTHON) flows/full_pipeline.py

## Format code using Black
format:
	black .

## Run linting with flake8
lint:
	flake8 src flows

## Run all unit tests
test:
	pytest -q

## Deploy Prefect blocks (optional)
deploy-blocks:
	$(PYTHON) scripts/deploy_blocks.py

## Deploy all Prefect flows
deploy:
	prefect deploy --all

## Clean Python caches
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
