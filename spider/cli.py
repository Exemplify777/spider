"""Command-line interface for SPIDER framework."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core.config import Config
from .core.logger import setup_logging, get_logger
from .core.engine import EngineFactory, EngineType
from .infrastructure.proxy import ProxyManager
from .infrastructure.captcha import CAPTCHAManager

# Create CLI app
app = typer.Typer(
    name="spider",
    help="SPIDER - Scalable Python Integrated Data Extraction & Retrieval",
    add_completion=False
)

# Rich console for better output
console = Console()


@app.command()
def init(
    config_path: str = typer.Option(
        "config/spider.yaml",
        "--config", "-c",
        help="Path to configuration file"
    ),
    environment: str = typer.Option(
        "development",
        "--env", "-e",
        help="Environment (development, staging, production)"
    )
):
    """Initialize SPIDER with default configuration."""
    console.print(f"[bold blue]Initializing SPIDER in {environment} environment...[/bold blue]")
    
    # Create default configuration
    config = Config(
        environment=environment,
        debug=(environment == "development")
    )
    
    # Create config directory
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save configuration
    config.to_file(config_file)
    
    console.print(f"[green]✓[/green] Configuration saved to {config_file}")
    console.print(f"[green]✓[/green] SPIDER initialized successfully!")


@app.command()
def run(
    config_path: str = typer.Option(
        "config/spider.yaml",
        "--config", "-c",
        help="Path to configuration file"
    ),
    urls: Optional[str] = typer.Option(
        None,
        "--urls", "-u",
        help="Comma-separated list of URLs to scrape"
    ),
    engine: str = typer.Option(
        "httpx",
        "--engine", "-e",
        help="Scraping engine (scrapy, playwright, httpx)"
    ),
    output: str = typer.Option(
        "data/output.json",
        "--output", "-o",
        help="Output file path"
    ),
    max_concurrent: int = typer.Option(
        16,
        "--max-concurrent", "-m",
        help="Maximum concurrent requests"
    )
):
    """Run SPIDER scraping job."""
    asyncio.run(_run_scraping(
        config_path=config_path,
        urls=urls,
        engine=engine,
        output=output,
        max_concurrent=max_concurrent
    ))


async def _run_scraping(
    config_path: str,
    urls: Optional[str],
    engine: str,
    output: str,
    max_concurrent: int
):
    """Run the actual scraping process."""
    try:
        # Load configuration
        config = Config.from_file(config_path)
        
        # Setup logging
        setup_logging(
            log_level=config.monitoring.log_level,
            log_dir=config.log_dir,
            enable_console=True,
            enable_file=True
        )
        
        logger = get_logger("spider.cli")
        logger.info("Starting SPIDER scraping job")
        
        # Parse URLs
        if urls:
            url_list = [url.strip() for url in urls.split(",")]
        else:
            # Default URLs for testing
            url_list = [
                "https://httpbin.org/html",
                "https://httpbin.org/json",
                "https://httpbin.org/xml"
            ]
        
        console.print(f"[bold blue]Scraping {len(url_list)} URLs with {engine} engine...[/bold blue]")
        
        # Create engine
        engine_type = EngineType(engine)
        engine_config = config.get_engine_config(engine)
        engine_instance = EngineFactory.create_engine(engine_type, engine_config)
        
        # Initialize infrastructure
        proxy_manager = ProxyManager(config.proxy.dict())
        captcha_manager = CAPTCHAManager(config.captcha.dict())
        
        await proxy_manager.initialize()
        
        # Run scraping with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Scraping URLs...", total=len(url_list))
            
            async with engine_instance:
                results = []
                
                for url in url_list:
                    progress.update(task, description=f"Scraping {url}")
                    
                    # Create scraping request
                    from .core.engine import ScrapingRequest
                    request = ScrapingRequest(url=url)
                    
                    # Scrape URL
                    response = await engine_instance.scrape(request)
                    results.append({
                        'url': url,
                        'status_code': response.status_code,
                        'success': response.success,
                        'content_length': len(response.content),
                        'error': response.error
                    })
                    
                    progress.advance(task)
        
        # Save results
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Display results
        _display_results(results)
        
        console.print(f"[green]✓[/green] Scraping completed! Results saved to {output_path}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Scraping failed: {e}")
        sys.exit(1)


def _display_results(results):
    """Display scraping results in a table."""
    table = Table(title="Scraping Results")
    table.add_column("URL", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Success", style="green")
    table.add_column("Content Length", style="blue")
    table.add_column("Error", style="red")
    
    for result in results:
        status_color = "green" if result['success'] else "red"
        success_icon = "✓" if result['success'] else "✗"
        
        table.add_row(
            result['url'],
            str(result['status_code']),
            f"[{status_color}]{success_icon}[/{status_color}]",
            str(result['content_length']),
            result['error'] or ""
        )
    
    console.print(table)


@app.command()
def status(
    config_path: str = typer.Option(
        "config/spider.yaml",
        "--config", "-c",
        help="Path to configuration file"
    )
):
    """Show SPIDER system status."""
    asyncio.run(_show_status(config_path))


async def _show_status(config_path: str):
    """Show system status."""
    try:
        # Load configuration
        config = Config.from_file(config_path)
        
        # Setup logging
        setup_logging(
            log_level=config.monitoring.log_level,
            log_dir=config.log_dir,
            enable_console=False,
            enable_file=False
        )
        
        console.print("[bold blue]SPIDER System Status[/bold blue]")
        console.print()
        
        # Configuration status
        console.print("[bold]Configuration:[/bold]")
        console.print(f"  Environment: {config.environment}")
        console.print(f"  Debug Mode: {config.debug}")
        console.print(f"  Max Concurrent Requests: {config.max_concurrent_requests}")
        console.print(f"  Request Delay: {config.request_delay}s")
        console.print()
        
        # Proxy status
        console.print("[bold]Proxy Configuration:[/bold]")
        console.print(f"  Enabled: {config.proxy.enabled}")
        console.print(f"  Providers: {len(config.proxy.providers)}")
        console.print()
        
        # CAPTCHA status
        console.print("[bold]CAPTCHA Configuration:[/bold]")
        console.print(f"  Enabled: {config.captcha.enabled}")
        console.print(f"  Providers: {len(config.captcha.providers)}")
        console.print()
        
        # Monitoring status
        console.print("[bold]Monitoring:[/bold]")
        console.print(f"  Enabled: {config.monitoring.enabled}")
        console.print(f"  Prometheus Port: {config.monitoring.prometheus_port}")
        console.print(f"  Health Check Port: {config.monitoring.health_check_port}")
        console.print()
        
        # Test infrastructure
        console.print("[bold]Testing Infrastructure:[/bold]")
        
        # Test proxy manager
        try:
            proxy_manager = ProxyManager(config.proxy.dict())
            await proxy_manager.initialize()
            proxy_count = len(proxy_manager.pool.proxies)
            console.print(f"  [green]✓[/green] Proxy Manager: {proxy_count} proxies available")
        except Exception as e:
            console.print(f"  [red]✗[/red] Proxy Manager: {e}")
        
        # Test CAPTCHA manager
        try:
            captcha_manager = CAPTCHAManager(config.captcha.dict())
            console.print(f"  [green]✓[/green] CAPTCHA Manager: {len(captcha_manager.providers)} providers")
        except Exception as e:
            console.print(f"  [red]✗[/red] CAPTCHA Manager: {e}")
        
        console.print()
        console.print("[green]SPIDER is ready for scraping![/green]")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to get status: {e}")
        sys.exit(1)


@app.command()
def test(
    config_path: str = typer.Option(
        "config/spider.yaml",
        "--config", "-c",
        help="Path to configuration file"
    ),
    url: str = typer.Option(
        "https://httpbin.org/html",
        "--url", "-u",
        help="URL to test"
    ),
    engine: str = typer.Option(
        "httpx",
        "--engine", "-e",
        help="Engine to test"
    )
):
    """Test SPIDER with a single URL."""
    asyncio.run(_test_scraping(config_path, url, engine))


async def _test_scraping(config_path: str, url: str, engine: str):
    """Test scraping with a single URL."""
    try:
        # Load configuration
        config = Config.from_file(config_path)
        
        # Setup logging
        setup_logging(
            log_level=config.monitoring.log_level,
            log_dir=config.log_dir,
            enable_console=True,
            enable_file=False
        )
        
        logger = get_logger("spider.test")
        logger.info(f"Testing SPIDER with URL: {url}")
        
        console.print(f"[bold blue]Testing SPIDER with {url}...[/bold blue]")
        
        # Create engine
        engine_type = EngineType(engine)
        engine_config = config.get_engine_config(engine)
        engine_instance = EngineFactory.create_engine(engine_type, engine_config)
        
        # Test scraping
        from .core.engine import ScrapingRequest
        request = ScrapingRequest(url=url)
        
        async with engine_instance:
            response = await engine_instance.scrape(request)
        
        # Display results
        if response.success:
            console.print(f"[green]✓[/green] Success! Status: {response.status_code}")
            console.print(f"Content Length: {len(response.content)} bytes")
            console.print(f"Response Time: {response.metadata.get('response_time', 'N/A')}s")
        else:
            console.print(f"[red]✗[/red] Failed: {response.error}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
