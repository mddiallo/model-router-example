.PHONY: install run clean help

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt

run:  ## Run the router test with defaults
	python -m src.router_test --prompts src/prompts.json --raw-json

test:  ## Run unit tests
	python -m pytest tests/ -v

clean:  ## Remove output files
	rm -rf out/
