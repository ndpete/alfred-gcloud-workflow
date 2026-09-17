TARGET_DIR := target
WORKFLOW_FILE := $(TARGET_DIR)/alfred-gcloud-workflow.alfredworkflow

.PHONY: all clean test lint format workflow install sort-products

all: test workflow

clean:
	@rm -rf $(TARGET_DIR) bin .pytest_cache .ruff_cache

$(TARGET_DIR):
	@mkdir -p $(TARGET_DIR)

lint:
	uv run --extra dev ruff check .

format:
	uv run --extra dev ruff format .

test:
	uv run --extra dev pytest -v

workflow: | $(TARGET_DIR)
	@rm -f $(WORKFLOW_FILE)
	zip -r $(WORKFLOW_FILE) \
		info.plist \
		icon.png \
		products.json \
		README.md \
		src/ \
		-x "*/__pycache__/*" "*.pyc" "*.DS_Store*"

install: workflow
	open $(WORKFLOW_FILE)

sort-products:
	cat products.json | jq -s '.[] | sort_by(.name)' > products_sorted.json
	cp products_sorted.json products.json
	rm products_sorted.json
