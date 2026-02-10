# GitHub Copilot Instructions for lancedb-cli

## Project Overview

This is a Python CLI application for managing LanceDB databases. The tool provides an intuitive command-line interface for querying, updating, and managing data stored in LanceDB with SQL support via DuckDB integration.

**Command Name:** `lsql`  
**Main Technologies:** LanceDB, DuckDB, Typer, Rich, pandas, prompt-toolkit

## Code Style and Conventions

### Python Style
- Follow PEP 8 conventions
- Use type hints for all function parameters and return values
- Maximum line length: 100 characters
- Use descriptive variable names that reflect the LanceDB/SQL domain

### Function Documentation
- Every function must have a docstring explaining purpose, args, and return values
- Use Google-style docstrings
- Example:
  ```python
  def validate_table_exists(db: lancedb.DBConnection, table_name: str) -> bool:
      """Check if table exists in database. Prints error message if not."""
      # implementation
  ```

### Error Handling
- Always validate database paths before operations
- Use Rich console for user-facing error messages with color coding:
  - Red `[red]` for errors
  - Green `[green]` for success messages
  - Yellow `[yellow]` for warnings
- Provide clear, actionable error messages

### CLI Design Patterns
- Use Typer for all CLI commands
- All database operations should accept a `db_path` as the first argument
- Use `Optional` types with sensible defaults
- Include `--help` text for all commands and options
- Command structure: `lsql <command> <db_path> [arguments] [options]`

## Architecture

### Key Components

1. **Database Connection**: Use `lancedb.connect(db_path)` for all connections
2. **Query Execution**: DuckDB integration for SQL queries against LanceDB tables
3. **Output Formatting**: Rich tables for tabular data, JSON for structured output
4. **Interactive Mode**: prompt-toolkit for REPL with history and completion

### Common Patterns

#### Database Validation
```python
if not validate_database_exists(db_path):
    raise typer.Exit(1)
db = lancedb.connect(db_path)
```

#### Table Operations
```python
if not validate_table_exists(db, table_name):
    raise typer.Exit(1)
table = db.open_table(table_name)
```

#### Output Display
```python
# For tabular data
table = Table(title="Results")
# Add columns and rows
console.print(table)

# For JSON output
console.print(JSON(json.dumps(data)))
```

## Feature Development Guidelines

### Adding New Commands
1. Define command using `@app.command()`
2. Add comprehensive help text
3. Validate inputs (database path, table names, etc.)
4. Handle errors gracefully with user-friendly messages
5. Support both JSON and table output formats where applicable
6. Add `--verbose` flag for detailed operations if needed

### SQL Operations
- Always use DuckDB for SQL execution
- Pattern: `duckdb.connect().execute(query, [pandas_df]).df()`
- Validate SQL syntax errors and provide clear feedback
- Support both direct SQL and abstracted commands

### Data Type Handling
- Use `parse_set_clause()` for parsing key-value updates
- Automatically convert strings to appropriate types (int, float, bool)
- Handle JSON strings in data fields
- Truncate long field values in table display (MAX_FIELD_LENGTH = 50)

### Interactive Mode
- Use prompt-toolkit for the REPL
- Provide SQL keyword completion
- Include table name completion from current database
- Maintain command history in user's home directory
- Support multi-line input for complex queries

## Testing Considerations

- Test with various LanceDB database structures
- Verify behavior with empty databases/tables
- Test SQL edge cases (special characters, complex queries)
- Ensure proper cleanup of database connections
- Test file I/O operations (CSV imports/exports)

## Dependencies

**Core:**
- `lancedb>=0.1.0` - Vector database engine
- `duckdb>=0.5.0` - SQL query execution
- `pandas>=1.0.0` - Data manipulation
- `typer[all]>=0.9.0` - CLI framework
- `rich>=13.0.0` - Terminal formatting
- `prompt-toolkit>=3.0.0` - Interactive shell
- `pygments>=2.0.0` - Syntax highlighting

**Dev:**
- pytest, pytest-cov - Testing
- black, isort - Code formatting
- flake8, mypy - Linting and type checking

## Common Tasks

### Adding a New Query Command
1. Create function under `@app.command()`
2. Accept `db_path: str` and `table_name: str`
3. Add optional filters/parameters
4. Validate database and table existence
5. Execute query using DuckDB
6. Format output with Rich
7. Handle exceptions with clear messages

### Supporting New Data Formats
1. Update import/export commands
2. Use pandas for format conversion
3. Validate file paths and formats
4. Provide progress feedback for large files
5. Support overwrite protection

### Improving Interactive Mode
1. Extend WordCompleter with new keywords/commands
2. Add special commands (e.g., `.tables`, `.schema`)
3. Improve error messages within REPL
4. Consider multi-DB session support

## Security and Best Practices

- Never execute arbitrary code from user input without validation
- Sanitize file paths to prevent directory traversal
- Use parameterized queries where possible
- Warn users before destructive operations (DROP, DELETE without WHERE)
- Respect file system permissions

## Performance Considerations

- Limit default query results (use LIMIT clauses)
- Truncate display output for very wide tables
- Stream large result sets when possible
- Close database connections properly
- Consider batch operations for bulk inserts/updates

## Documentation

- Keep README.md updated with new commands
- Include usage examples for complex features
- Document any non-obvious SQL integration details
- Maintain changelog for version updates
