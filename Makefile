SRC_DIR := $(CURDIR)/src

format_black:
	@echo "Formatting code with Black..."
	black SRC_DIR
	@echo "Black formatting completed"

# Sort imports with isort
format_isort:
	@echo "Sorting imports with isort..."
	isort SRC_DIR
	@echo "Import sorting completed"

# Run all formatters
format_code: format_black format_isort
	@echo "All code formatting completed!"

scrape_update_db:
	PYTHONPATH=$(SRC_DIR) python -m db.scrape_and_update

.PHONY: format_black format_isort format_code scrape_update_db