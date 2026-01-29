# AnkiLangs - Task Runner

default:
    @just --list

# Run all tests
test:
    uv run pytest

# Update golden test files
test-update-golden:
    uv run pytest --update-golden

# Check code (format + lint)
check-code:
    uv run ruff format .
    uv run ruff check .

# Check data for ambiguous words missing hints
check-data:
    uv run al-tools check

# Run all checks (code + data)
check: check-code check-data

# Import CSV files to SQLite database
csv2sqlite input="src/data" db="data.db":
    uv run al-tools csv2sqlite -i {{input}} -d {{db}}

# Export SQLite database to CSV files
sqlite2csv db="data.db" output="src/data":
    uv run al-tools sqlite2csv -d {{db}} -o {{output}}

# Build all decks
build: sqlite2csv
    uv run al-tools generate -o src/data/generated
    uv run brainbrew run recipes/source_to_anki_625_words.yaml
    uv run brainbrew run recipes/source_to_anki_minimal_pairs.yaml
    uv run al-tools csv2sqlite -i src/data -d data.db --force
