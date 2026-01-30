"""CLI for semantic memory search."""

import click
from pathlib import Path

from .memory_search import MemorySearch


@click.group()
@click.option('--db', default='memory_search.db', help='Path to SQLite database')
@click.option('--model', default=None, help='Path to embedding model')
@click.pass_context
def cli(ctx, db, model):
    """Semantic Memory Search - Local embedding search for agent memory."""
    ctx.ensure_object(dict)
    ctx.obj['search'] = MemorySearch(
        model_path=model,
        db_path=db
    )


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--pattern', default='*.md', help='File pattern to index')
@click.option('--db', default='memory_search.db', help='Database path')
@click.option('--model', default=None, help='Model path')
def index(directory, pattern, db, model):
    """Index memory files in a directory."""
    search = MemorySearch(model_path=model, db_path=db)
    stats = search.index_directory(directory, pattern)
    
    if stats['chunks_indexed'] == 0:
        click.echo("No files found matching pattern.")
    

@cli.command()
@click.argument('query')
@click.option('--top-k', default=5, help='Number of results')
@click.option('--db', default='memory_search.db', help='Database path')
@click.option('--model', default=None, help='Model path')
def search(query, top_k, db, model):
    """Search indexed memories."""
    search = MemorySearch(model_path=model, db_path=db)
    
    results = search.search(query, top_k=top_k)
    
    if not results:
        click.echo("No results found.")
        return
    
    click.echo(f"\nQuery: '{query}'\n")
    click.echo("-" * 60)
    
    for i, (chunk, score, match_type) in enumerate(results, 1):
        source = Path(chunk.source).name
        click.echo(f"\n{i}. [{match_type}] {source}:{chunk.start_line} (score: {score:.3f})")
        click.echo(f"   {chunk.text[:150]}...")


@cli.command()
@click.option('--db', default='memory_search.db', help='Database path')
@click.option('--model', default=None, help='Model path')
def stats(db, model):
    """Show index statistics."""
    search = MemorySearch(model_path=model, db_path=db)
    s = search.get_stats()
    
    click.echo(f"\nIndex Statistics")
    click.echo("-" * 30)
    click.echo(f"Total chunks: {s['total_chunks']}")
    click.echo(f"Unique files: {s['unique_files']}")
    click.echo(f"Embedding dim: {s['embedding_dim']}")


@cli.command()
@click.option('--db', default='memory_search.db', help='Database path')
@click.option('--model', default=None, help='Model path')
def clear(db, model):
    """Clear the index."""
    search = MemorySearch(model_path=model, db_path=db)
    search.clear()
    click.echo("Index cleared.")


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--pattern', default='*.md', help='File pattern')
@click.option('--db', default='memory_search.db', help='Database path')
@click.option('--model', default=None, help='Model path')
def watch(directory, pattern, db, model):
    """Watch directory for changes and auto-reindex (not yet implemented)."""
    click.echo("Watch mode not yet implemented. Use 'index' command for now.")


def main():
    cli()


if __name__ == '__main__':
    main()
