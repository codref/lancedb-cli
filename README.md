# lancedb-cli

A minimal command line application for managing LanceDB databases. This CLI tool provides an easy interface to query, update, and manage data stored in LanceDB.

## Features

- **Query Tables**: Retrieve data from LanceDB tables with filtering and column selection
- **Interactive Mode**: Interactive SQL shell with command history and completion
- **Direct SQL Execution**: Run complex SQL queries against LanceDB databases via DuckDB integration
- **Data Management**: Insert, update, delete, and drop records
- **Schema Inspection**: View the schema of tables
- **Import/Export**: Load data from CSV files and dump tables to CSV format
- **Multiple Output Formats**: Display results as formatted tables or JSON
- **Auto-completion**: Interactive mode includes SQL keywords and table name completion
- **Safe Operations**: Confirmation prompts for destructive operations

## Installation

Install the package using pip:

```bash
pip install lancedb-cli
```

## Usage

### Command Line

#### Database and Table Management

List all tables in a database:

```bash
lsql list-tables /path/to/database
```

View table schema:

```bash
lsql schema /path/to/database my_table
```

#### Querying Data

Query a table with filtering and limits:

```bash
lsql query /path/to/database my_table --limit 10
lsql query /path/to/database my_table --where "age > 25" --limit 20
lsql query /path/to/database my_table --select "name,email" --where "active=true"
```

Execute SQL queries directly (using DuckDB):

```bash
lsql sql /path/to/database "SELECT * FROM my_table WHERE id > 5"
lsql sql /path/to/database "SELECT name, COUNT(*) FROM my_table GROUP BY name"
```

#### Data Modification

Update records:

```bash
lsql update /path/to/database my_table \
  --set-clause "name='John',age=30" \
  --where "id=1"
```

Delete specific records:

```bash
lsql delete /path/to/database my_table --where "id=1"
lsql delete /path/to/database my_table --where "age < 18"
```

Empty a table (delete all rows):

```bash
lsql empty /path/to/database my_table
```

Drop a table permanently:

```bash
lsql drop /path/to/database my_table --confirm
```

#### Import/Export

Load data from a CSV file:

```bash
lsql load /path/to/database my_file.csv my_table
lsql load /path/to/database my_file.csv my_table --overwrite
```

Export a table to CSV:

```bash
lsql dump /path/to/database my_table output.csv
lsql dump /path/to/database employees export.csv --overwrite
```

### Interactive Mode

Start an interactive session:

```bash
lsql interactive /path/to/database
```

Inside the interactive shell, you can:

- Type SQL queries directly
- Use special commands:
  - `.tables` - List all tables
  - `.schema <table>` - Show table schema
  - `.refresh` - Refresh all table views
  - `.update <table> <set> <where>` - Update rows
  - `.delete <table> <where>` - Delete rows
  - `.empty <table>` - Empty a table
  - `.drop <table>` - Drop a table
  - `.exit` - Exit the interactive shell

## Command Options

### Common Options

- `--create`: Create the database if it doesn't exist (available on most commands)
- `--output <format>`: Output format - `table` (default) or `json` (for query and sql commands)

### Query Command Options

- `--limit N`: Limit results to N rows (default: 10)
- `--where <condition>`: Filter rows with SQL WHERE clause
- `--select <columns>`: Select specific columns (comma-separated)

### Update/Delete Options

- `--set-clause <values>`: Column=value pairs for updates (e.g., "name='John',age=30")
- `--where <condition>`: SQL WHERE clause to specify which rows to modify

### Import/Export Options

- `--overwrite`: Overwrite existing table (load) or file (dump) if it exists

### Safety Options

- `--confirm`: Skip confirmation prompts for destructive operations (drop command)

## Development

To set up a development environment:

```bash
git clone https://github.com/yourusername/lancedb-cli.git
cd lancedb-cli
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## Requirements

- Python 3.8 or higher
- lancedb
- duckdb
- typer
- rich
- prompt-toolkit
- pygments

## Examples

### Complete Workflow Example

```bash
# Create a new database and load data
lsql load ./my_db employees.csv employees --create

# Query the data
lsql query ./my_db employees --limit 5

# Run SQL analytics
lsql sql ./my_db "SELECT department, AVG(salary) FROM employees GROUP BY department"

# Update specific records
lsql update ./my_db employees --set-clause "salary=50000" --where "id=10"

# Export results
lsql dump ./my_db employees employees_backup.csv

# Interactive exploration
lsql interactive ./my_db
```

## License

Apache License 2.0 - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Issues

If you encounter any issues or have suggestions, please open an issue on GitHub.
