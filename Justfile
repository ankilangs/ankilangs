# AnkiLangs - Task Runner
# See https://github.com/casey/just for installation and usage

# Default recipe - show available commands
default:
    @just --list

# Run all tests
test:
    uv run pytest

# Update golden test files (expected output)
test-update-golden:
    uv run pytest --update-golden

# Format code with ruff
format:
    uv run ruff format .

# Check code with ruff (linting)
check:
    uv run ruff check .

# Run all code quality checks (format + check + test)
verify-code: format check test

# Import CSV files to SQLite database
csv2sqlite input="src/data" db="data.db":
    uv run al-tools csv2sqlite -i {{input}} -d {{db}}

# Export SQLite database back to CSV files
sqlite2csv db="data.db" output="src/data":
    uv run al-tools sqlite2csv -d {{db}} -o {{output}}

# Generate derived CSV files
generate output="src/data/generated":
    uv run al-tools generate -o {{output}}

# Check for ambiguous words missing hints
check-data:
    uv run al-tools check

# Build 625 words decks
build-625:
    uv run brainbrew run recipes/source_to_anki_625_words.yaml

# Build minimal pairs decks
build-minimal-pairs:
    uv run brainbrew run recipes/source_to_anki_minimal_pairs.yaml

# Build all decks
build-all: generate check-data build-625 build-minimal-pairs

# Verify data changes (export + generate + check + build)
verify-data: sqlite2csv generate check-data build-all

# Full verification before commit (code + data)
verify: verify-code verify-data
