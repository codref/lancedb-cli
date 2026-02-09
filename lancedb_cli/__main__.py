import typer
import lancedb
import duckdb
from pathlib import Path
from typing import Optional, Dict, List, Any
from rich.table import Table
from rich.console import Console
from rich.json import JSON
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.completion import WordCompleter
from pygments.lexers.sql import SqlLexer

app = typer.Typer(
    help="lsql - A minimal command line application for managing LanceDB databases"
)
console = Console()

# Maximum field length before truncation
MAX_FIELD_LENGTH = 50


def truncate_value(value: str, max_len: int = MAX_FIELD_LENGTH) -> str:
    """Truncate long values and add ellipsis."""
    value_str = str(value)
    if len(value_str) > max_len:
        return value_str[:max_len] + "..."
    return value_str


def get_table_names(db: lancedb.DBConnection) -> List[str]:
    """Get list of table names from database."""
    result = db.list_tables()
    return result.tables if hasattr(result, 'tables') else result


def validate_table_exists(db: lancedb.DBConnection, table_name: str) -> bool:
    """Check if table exists in database. Prints error message if not."""
    table_names = get_table_names(db)
    if table_name not in table_names:
        console.print(f"[red]Error: Table '{table_name}' not found in database[/red]")
        return False
    return True


def parse_set_clause(set_clause: str) -> Dict[str, Any]:
    """Parse SET clause into key-value pairs with type conversion."""
    update_values = {}
    
    # Split on comma, but be careful about commas within quoted strings
    pairs = []
    current = ""
    in_quotes = False
    quote_char = None
    
    for char in set_clause:
        if char in ('"', "'") and (not in_quotes or char == quote_char):
            in_quotes = not in_quotes
            if in_quotes:
                quote_char = char
            else:
                quote_char = None
        if char == "," and not in_quotes:
            pairs.append(current)
            current = ""
        else:
            current += char
    if current:
        pairs.append(current)
    
    for pair in pairs:
        pair = pair.strip()
        if "=" not in pair:
            raise ValueError("Invalid SET clause format. Use key=value pairs separated by commas")
        
        key, value = pair.split("=", 1)
        key = key.strip()
        value = value.strip()
        update_values[key] = convert_value(value)
    
    return update_values


def convert_value(value: str) -> Any:
    """Convert a string value to appropriate type."""
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    elif value.lower() in ("null", "none"):
        return None
    elif (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    else:
        try:
            if '.' not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            return value


def render_results(results, title: str = "Results", output_format: str = "table") -> None:
    """Render query results in specified format."""
    if output_format == "json":
        console.print(JSON(results.to_json(orient="records")))
    else:
        rich_table = Table(title=title)
        for col in results.columns:
            rich_table.add_column(str(col), style="cyan")
        for _, row in results.iterrows():
            rich_table.add_row(*[truncate_value(v) for v in row])
        console.print(rich_table)


@app.command()
def list_tables(db_path: str = typer.Argument(..., help="Path to the lancedb database")) -> None:
    """List all tables in a lancedb database."""
    try:
        db = lancedb.connect(db_path)
        tables = get_table_names(db)
        
        table = Table(title=f"Tables in {db_path}")
        table.add_column("Table Name", style="cyan")
        
        for tbl_name in tables:
            table.add_row(tbl_name)
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def query(
    db_path: str = typer.Argument(..., help="Path to the lancedb database"),
    table: str = typer.Argument(..., help="Table name to query"),
    limit: int = typer.Option(10, help="Number of rows to return"),
    where: Optional[str] = typer.Option(None, help="Where clause filter (SQL syntax)"),
    select: Optional[str] = typer.Option(None, help="Columns to select (comma-separated)"),
    output: str = typer.Option("table", help="Output format (table, json)"),
) -> None:
    """Query a table from a lancedb database."""
    try:
        db = lancedb.connect(db_path)
        
        if not validate_table_exists(db, table):
            raise typer.Exit(1)
        
        tbl = db.open_table(table)
        
        # Build query
        if where:
            results = tbl.search().where(where).to_pandas()
        else:
            results = tbl.to_pandas()
        
        # Apply limit
        if limit and len(results) > limit:
            results = results.head(limit)
        
        # Select columns
        if select:
            cols = [c.strip() for c in select.split(",")]
            results = results[[c for c in cols if c in results.columns]]
        
        # Output
        render_results(results, title=f"Query results from {table}", output_format=output)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def schema(
    db_path: str = typer.Argument(..., help="Path to the lancedb database"),
    table: str = typer.Argument(..., help="Table name"),
) -> None:
    """Show schema of a table in a lancedb database."""
    try:
        db = lancedb.connect(db_path)
        
        if not validate_table_exists(db, table):
            raise typer.Exit(1)
        
        tbl = db.open_table(table)
        console.print(f"\n[bold cyan]Schema for {table}:[/bold cyan]\n")
        console.print(tbl.schema)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def sql(
    db_path: str = typer.Argument(..., help="Path to the lancedb database"),
    sql_query: str = typer.Argument(..., help="SQL query to execute"),
    output: str = typer.Option("table", help="Output format (table, json)"),
) -> None:
    """Execute a SQL query against a lancedb database."""
    try:
        db = lancedb.connect(db_path)
        
        # Register all tables in duckdb
        for table_name in get_table_names(db):
            table = db.open_table(table_name)
            arrow_table = table.to_lance()
            duckdb.sql(f"CREATE TEMP VIEW {table_name} AS SELECT * FROM arrow_table")
        
        # Execute SQL query
        results = duckdb.sql(sql_query).to_df()
        
        # Output
        render_results(results, title="SQL Query Results", output_format=output)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def delete(
    db_path: str = typer.Argument(..., help="Path to the lancedb database"),
    table: str = typer.Argument(..., help="Table name to delete from"),
    where: str = typer.Option(..., help="WHERE clause to specify rows to delete (SQL syntax)"),
) -> None:
    """Delete rows from a table in a lancedb database."""
    try:
        db = lancedb.connect(db_path)
        
        if not validate_table_exists(db, table):
            raise typer.Exit(1)
        
        tbl = db.open_table(table)
        
        # Count rows before and after deletion
        rows_before = len(tbl.to_pandas())
        tbl.delete(where)
        rows_after = len(tbl.to_pandas())
        rows_deleted = rows_before - rows_after
        
        console.print(f"[green]Successfully deleted {rows_deleted} row(s)[/green]")
        console.print(f"[cyan]Rows before: {rows_before}, Rows after: {rows_after}[/cyan]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def empty(
    db_path: str = typer.Argument(..., help="Path to the lancedb database"),
    table: str = typer.Argument(..., help="Table name to empty"),
) -> None:
    """Empty a table by deleting all rows."""
    try:
        db = lancedb.connect(db_path)
        
        if not validate_table_exists(db, table):
            raise typer.Exit(1)
        
        tbl = db.open_table(table)
        
        # Count rows before and after deletion
        rows_before = len(tbl.to_pandas())
        tbl.delete("1=1")
        rows_after = len(tbl.to_pandas())
        rows_deleted = rows_before - rows_after
        
        console.print(f"[green]Successfully emptied table '{table}' - deleted {rows_deleted} row(s)[/green]")
        console.print(f"[cyan]Rows before: {rows_before}, Rows after: {rows_after}[/cyan]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def drop(
    db_path: str = typer.Argument(..., help="Path to the lancedb database"),
    table: str = typer.Argument(..., help="Table name to drop"),
    confirm: bool = typer.Option(False, "--confirm", help="Confirm deletion without prompt"),
) -> None:
    """Drop (delete) an entire table from the database."""
    try:
        db = lancedb.connect(db_path)
        
        if not validate_table_exists(db, table):
            raise typer.Exit(1)
        
        # Ask for confirmation unless --confirm flag is provided
        if not confirm:
            console.print(f"[yellow]Warning: You are about to delete the entire table '{table}'[/yellow]")
            console.print("[yellow]This action cannot be undone.[/yellow]")
            response = input("Are you sure? (yes/no): ").strip().lower()
            if response != "yes":
                console.print("[cyan]Operation cancelled[/cyan]")
                raise typer.Exit(0)
        
        # Drop the table
        db.drop_table(table)
        
        console.print(f"[green]Successfully dropped table '{table}'[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def update(
    db_path: str = typer.Argument(..., help="Path to the lancedb database"),
    table: str = typer.Argument(..., help="Table name to update"),
    set_clause: str = typer.Option(..., help="SET clause with column=value pairs (e.g., 'col1=10,col2=value')"),
    where: str = typer.Option(..., help="WHERE clause to specify rows to update (SQL syntax)"),
) -> None:
    """Update rows in a table that match a given expression."""
    try:
        db = lancedb.connect(db_path)
        
        if not validate_table_exists(db, table):
            raise typer.Exit(1)
        
        tbl = db.open_table(table)
        
        # Parse SET clause into key-value pairs
        try:
            update_values = parse_set_clause(set_clause)
        except ValueError as ve:
            console.print(f"[red]Error: {ve}[/red]")
            raise typer.Exit(1)
        
        # Update rows
        try:
            tbl.update(where=where, values=update_values)
        except Exception as update_err:
            console.print(f"[red]Update failed. Details:[/red]")
            console.print(f"[red]  Columns: {update_values}[/red]")
            console.print(f"[red]  WHERE: {where}[/red]")
            console.print(f"[red]  Error: {update_err}[/red]")
            raise
        
        console.print(f"[green]Successfully updated rows in '{table}'[/green]")
        console.print(f"[cyan]Updated columns: {list(update_values.keys())}[/cyan]")
        console.print(f"[cyan]WHERE condition: {where}[/cyan]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def interactive(
    db_path: str = typer.Argument(..., help="Path to the lancedb database"),
) -> None:
    """Interactive CLI for querying lancedb database."""
    try:
        db = lancedb.connect(db_path)
        
        # sql_keywords list
        sql_keywords = ["SELECT", "FROM", "WHERE", "LIMIT", "ORDER BY", "GROUP BY", "INSERT", "DELETE", "UPDATE", "JOIN", "LEFT JOIN", "INNER JOIN", "ON", "AND", "OR", "NOT", "IN", "LIKE", "BETWEEN", "DISTINCT", "COUNT", "SUM", "AVG", "MIN", "MAX"]
        
        # Set up history file
        history_file = Path.home() / ".lancedb_history"
        
        console.print(f"[bold cyan]Connected to: {db_path}[/bold cyan]")
        console.print("[yellow]Commands:[/yellow]")
        console.print("  .tables       - List all tables")
        console.print("  .schema       - Show schema of a table (.schema <table_name>)")
        console.print("  .refresh      - Refresh all table views")
        console.print("  .update       - Update rows (.update <table> <set_clause> <where_clause>)")
        console.print("  .delete       - Delete rows (.delete <table> <where_clause>)")
        console.print("  .empty        - Empty a table (.empty <table>)")
        console.print("  .drop         - Drop an entire table (.drop <table>)")
        console.print("  .exit         - Exit interactive mode")
        console.print("[yellow]Or type SQL queries directly[/yellow]\n")
        
        # Cache for table DataFrames
        table_cache = {}
        
        def get_table_names_interactive():
            """Get table names for interactive mode."""
            return get_table_names(db)
        
        def refresh_views():
            """Refresh all DuckDB views from LanceDB tables."""
            table_cache.clear()
            for table_name in get_table_names_interactive():
                try:
                    table = db.open_table(table_name)
                    df = table.to_pandas()
                    table_cache[table_name] = df
                    duckdb.sql(f"DROP VIEW IF EXISTS {table_name}")
                    duckdb.register(table_name, df)
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not refresh view for {table_name}: {e}[/yellow]")
        
        def execute_update(tbl_name: str, set_clause: str, where_clause: str) -> bool:
            """Execute update command. Returns True on success."""
            if tbl_name not in get_table_names_interactive():
                console.print(f"[red]Error: Table '{tbl_name}' not found[/red]")
                return False
            
            try:
                tbl = db.open_table(tbl_name)
                update_values = parse_set_clause(set_clause)
                tbl.update(where=where_clause, values=update_values)
                
                # Refresh duckdb view with updated data
                df = tbl.to_pandas()
                table_cache[tbl_name] = df
                duckdb.register(tbl_name, df)
                
                console.print(f"[green]Successfully updated rows in '{tbl_name}'[/green]")
                console.print(f"[cyan]Updated columns: {list(update_values.keys())}[/cyan]")
                console.print(f"[cyan]WHERE condition: {where_clause}[/cyan]")
                return True
            except ValueError as ve:
                console.print(f"[red]Error: {ve}[/red]")
                return False
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                return False
        
        def execute_delete(tbl_name: str, where_clause: str) -> bool:
            """Execute delete command. Returns True on success."""
            if tbl_name not in get_table_names_interactive():
                console.print(f"[red]Error: Table '{tbl_name}' not found[/red]")
                return False
            
            try:
                tbl = db.open_table(tbl_name)
                rows_before = len(tbl.to_pandas())
                tbl.delete(where_clause)
                rows_after = len(tbl.to_pandas())
                rows_deleted = rows_before - rows_after
                
                # Refresh duckdb view
                df = tbl.to_pandas()
                table_cache[tbl_name] = df
                duckdb.register(tbl_name, df)
                
                console.print(f"[green]Successfully deleted {rows_deleted} row(s)[/green]")
                console.print(f"[cyan]Rows before: {rows_before}, Rows after: {rows_after}[/cyan]")
                return True
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                return False
        
        def execute_empty(tbl_name: str) -> bool:
            """Execute empty command. Returns True on success."""
            if tbl_name not in get_table_names_interactive():
                console.print(f"[red]Error: Table '{tbl_name}' not found[/red]")
                return False
            
            try:
                tbl = db.open_table(tbl_name)
                rows_before = len(tbl.to_pandas())
                tbl.delete("1=1")
                rows_after = len(tbl.to_pandas())
                rows_deleted = rows_before - rows_after
                
                # Refresh duckdb view
                df = tbl.to_pandas()
                table_cache[tbl_name] = df
                duckdb.register(tbl_name, df)
                
                console.print(f"[green]Successfully emptied table '{tbl_name}' - deleted {rows_deleted} row(s)[/green]")
                console.print(f"[cyan]Rows before: {rows_before}, Rows after: {rows_after}[/cyan]")
                return True
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                return False
        
        def execute_drop(tbl_name: str) -> bool:
            """Execute drop command. Returns True on success."""
            if tbl_name not in get_table_names_interactive():
                console.print(f"[red]Error: Table '{tbl_name}' not found[/red]")
                return False
            
            try:
                console.print(f"[yellow]Warning: You are about to delete the entire table '{tbl_name}'[/yellow]")
                console.print("[yellow]This action cannot be undone.[/yellow]")
                response = input("Are you sure? (yes/no): ").strip().lower()
                if response != "yes":
                    console.print("[cyan]Operation cancelled[/cyan]")
                    return False
                
                db.drop_table(tbl_name)
                duckdb.sql(f"DROP VIEW IF EXISTS {tbl_name}")
                
                console.print(f"[green]Successfully dropped table '{tbl_name}'[/green]")
                return True
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                return False
        
        # Register all tables in duckdb upfront
        refresh_views()
        
        # Set up prompt session
        dot_commands = [".tables", ".schema", ".refresh", ".update", ".delete", ".empty", ".drop", ".exit"]
        all_completions = sql_keywords + dot_commands + get_table_names_interactive()
        session = PromptSession(
            history=FileHistory(str(history_file)),
            lexer=PygmentsLexer(SqlLexer),
            completer=WordCompleter(all_completions, ignore_case=True),
        )
        
        while True:
            try:
                query_input = session.prompt("lancedb> ")
                query_input = query_input.strip()
                
                if not query_input:
                    continue
                
                # Handle special commands
                if query_input.lower() == ".tables":
                    tables = get_table_names_interactive()
                    table = Table(title="Available Tables")
                    table.add_column("Table Name", style="cyan")
                    for tbl_name in tables:
                        table.add_row(tbl_name)
                    console.print(table)
                    continue
                
                if query_input.lower().startswith(".schema"):
                    parts = query_input.split(None, 1)
                    if len(parts) < 2:
                        console.print("[red]Usage: .schema <table_name>[/red]")
                        continue
                    tbl_name = parts[1]
                    if tbl_name not in get_table_names_interactive():
                        console.print(f"[red]Error: Table '{tbl_name}' not found[/red]")
                        continue
                    tbl = db.open_table(tbl_name)
                    console.print(f"\n[bold cyan]Schema for {tbl_name}:[/bold cyan]\n")
                    console.print(tbl.schema)
                    console.print()
                    continue
                
                if query_input.lower() == ".exit":
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                
                if query_input.lower() == ".refresh":
                    console.print("[cyan]Refreshing all table views...[/cyan]")
                    refresh_views()
                    console.print("[green]All views refreshed successfully[/green]")
                    continue
                
                if query_input.lower().startswith(".update"):
                    parts = query_input.split(None, 3)
                    if len(parts) < 4:
                        console.print("[red]Usage: .update <table> <set_clause> <where_clause>[/red]")
                        console.print("[yellow]Example: .update speakers name='John' id=1[/yellow]")
                        continue
                    execute_update(parts[1], parts[2], parts[3])
                    continue
                
                if query_input.lower().startswith(".delete"):
                    parts = query_input.split(None, 2)
                    if len(parts) < 3:
                        console.print("[red]Usage: .delete <table> <where_clause>[/red]")
                        continue
                    execute_delete(parts[1], parts[2])
                    continue
                
                if query_input.lower().startswith(".empty"):
                    parts = query_input.split(None, 1)
                    if len(parts) < 2:
                        console.print("[red]Usage: .empty <table>[/red]")
                        continue
                    execute_empty(parts[1])
                    continue
                
                if query_input.lower().startswith(".drop"):
                    parts = query_input.split(None, 1)
                    if len(parts) < 2:
                        console.print("[red]Usage: .drop <table>[/red]")
                        continue
                    execute_drop(parts[1])
                    continue
                
                # Execute SQL query
                try:
                    results = duckdb.sql(query_input).to_df()
                except Exception as e:
                    # Check if it's a schema mismatch error
                    if "types don't match" in str(e) or "Contents of view were altered" in str(e):
                        console.print("[yellow]Table schema has changed. Refreshing views...[/yellow]")
                        refresh_views()
                        console.print("[cyan]Retrying query...[/cyan]")
                        try:
                            results = duckdb.sql(query_input).to_df()
                        except Exception as retry_e:
                            console.print(f"[red]Error: {retry_e}[/red]")
                            continue
                    else:
                        raise
                
                if len(results) == 0:
                    console.print("[yellow]No results[/yellow]")
                else:
                    rich_table = Table(title=f"Query Results ({len(results)} rows)")
                    for col in results.columns:
                        rich_table.add_column(str(col), style="cyan")
                    for _, row in results.iterrows():
                        rich_table.add_row(*[truncate_value(v) for v in row])
                    console.print(rich_table)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                continue
            except EOFError:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def main() -> None:
    """Entry point for the CLI."""
    app(prog_name="lsql")


if __name__ == "__main__":
    main()
