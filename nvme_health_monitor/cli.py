"""
Command Line Interface for NVMe health monitoring utility.

This module provides the main CLI interface using Click framework,
with commands for device listing, health collection, monitoring, and testing.
"""

import click
import sys
import signal
import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .core.nvme_interface import list_nvme_devices, check_nvme_cli_availability
from .core.data_collector import DataCollector
from .core.data_processor import DataProcessor
from .output.formatters import (
    format_health_snapshot_json, format_multiple_snapshots_json,
    format_smart_data_csv, format_error_summary_csv,
    format_health_summary_text, format_device_comparison_table
)
from .utils.config import load_default_config, load_config_from_file
from .utils.logging_config import setup_logging, configure_cli_logging, create_monitoring_logger
from .models.exceptions import NVMeError, NVMeCommandError, NVMeDeviceNotFoundError


class CLIContext:
    """Context object for CLI commands."""
    
    def __init__(self):
        self.config = load_default_config()
        self.logger = None
        self.data_collector = None
        self.data_processor = None


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--verbose', '-v', count=True, help='Increase verbosity (use multiple times)')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output except errors')
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], verbose: int, quiet: bool):
    """NVMe SSD Health Monitoring Utility."""
    ctx.ensure_object(CLIContext)
    cli_ctx = ctx.obj
    
    if quiet:
        verbose = 0
    
    configure_cli_logging(verbose)
    cli_ctx.logger = setup_logging('DEBUG' if verbose >= 3 else 'INFO')
    
    if config:
        try:
            cli_ctx.config = load_config_from_file(config)
            cli_ctx.logger.info(f"Loaded configuration from {config}")
        except Exception as e:
            click.echo(f"Error loading configuration: {e}", err=True)
            sys.exit(1)
    
    try:
        if not check_nvme_cli_availability():
            click.echo("Error: nvme-cli utility not found. Please install nvme-cli.", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error checking nvme-cli availability: {e}", err=True)
        sys.exit(1)
    
    cli_ctx.data_collector = DataCollector()
    cli_ctx.data_processor = DataProcessor(cli_ctx.config)


@cli.command()
@click.option('--format', '-f', type=click.Choice(['json', 'text', 'csv']), default='text',
              help='Output format')
@click.pass_context
def list_devices(ctx: click.Context, format: str):
    """List all available NVMe devices."""
    cli_ctx = ctx.obj
    
    try:
        devices = list_nvme_devices()
        
        if not devices:
            click.echo("No NVMe devices found.")
            return
        
        if format == 'json':
            click.echo(json.dumps(devices, indent=2))
        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=devices[0].keys())
            writer.writeheader()
            writer.writerows(devices)
            click.echo(output.getvalue())
        else:
            click.echo("Available NVMe Devices:")
            click.echo("=" * 60)
            for device in devices:
                click.echo(f"Device: {device.get('device_path', 'N/A')}")
                click.echo(f"  Model: {device.get('model', 'N/A')}")
                click.echo(f"  Serial: {device.get('serial_number', 'N/A')}")
                click.echo(f"  Size: {device.get('usage', 'N/A')}")
                click.echo(f"  Firmware: {device.get('firmware_revision', 'N/A')}")
                click.echo()
                
    except NVMeError as e:
        click.echo(f"Error listing devices: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        cli_ctx.logger.error(f"Unexpected error listing devices: {e}")
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--device', '-d', help='Specific device path (e.g., /dev/nvme0)')
@click.option('--all', '-a', is_flag=True, help='Collect data from all devices')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'text']), default='json',
              help='Output format')
@click.option('--include-self-test', is_flag=True, help='Include self-test data')
@click.option('--include-errors', is_flag=True, help='Include error log data')
@click.pass_context
def health(ctx: click.Context, device: Optional[str], all: bool, output: Optional[str],
           format: str, include_self_test: bool, include_errors: bool):
    """Collect health data from NVMe devices."""
    cli_ctx = ctx.obj
    
    if not device and not all:
        click.echo("Error: Must specify either --device or --all", err=True)
        sys.exit(1)
    
    if device and all:
        click.echo("Error: Cannot specify both --device and --all", err=True)
        sys.exit(1)
    
    try:
        snapshots = []
        
        if all:
            with click.progressbar(label='Collecting health data from all devices') as bar:
                snapshots = cli_ctx.data_collector.collect_all_devices_health()
                bar.update(len(snapshots))
        else:
            with click.progressbar(length=1, label=f'Collecting health data from {device}') as bar:
                snapshot = cli_ctx.data_collector.collect_device_health(
                    device, 
                    include_self_test=include_self_test,
                    include_error_logs=include_errors
                )
                snapshots = [snapshot]
                bar.update(1)
        
        if not snapshots:
            click.echo("No health data collected.")
            return
        
        if format == 'json':
            if len(snapshots) == 1:
                output_data = format_health_snapshot_json(snapshots[0])
            else:
                output_data = format_multiple_snapshots_json(snapshots)
        elif format == 'csv':
            if include_errors:
                output_data = format_error_summary_csv(snapshots)
            else:
                output_data = format_smart_data_csv(snapshots)
        else:
            if len(snapshots) == 1:
                output_data = format_health_summary_text(snapshots[0])
            else:
                output_data = format_device_comparison_table(snapshots)
        
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output_data, encoding='utf-8')
            click.echo(f"Health data written to {output}")
        else:
            click.echo(output_data)
            
    except NVMeDeviceNotFoundError as e:
        click.echo(f"Device not found: {e}", err=True)
        sys.exit(1)
    except NVMeError as e:
        click.echo(f"Error collecting health data: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        cli_ctx.logger.error(f"Unexpected error collecting health data: {e}")
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--device', '-d', help='Specific device to monitor (default: all devices)')
@click.option('--interval', '-i', type=int, default=300, help='Monitoring interval in seconds')
@click.option('--duration', '-t', type=int, help='Total monitoring duration in seconds')
@click.option('--output-dir', '-o', type=click.Path(), default='./monitoring_output',
              help='Directory for output files')
@click.option('--threshold-alerts', is_flag=True, help='Enable threshold-based alerts')
@click.option('--format', '-f', type=click.Choice(['json', 'csv']), default='json',
              help='Output format for monitoring data')
@click.pass_context
def monitor(ctx: click.Context, device: Optional[str], interval: int, duration: Optional[int],
            output_dir: str, threshold_alerts: bool, format: str):
    """Continuously monitor NVMe device health."""
    cli_ctx = ctx.obj
    
    if interval < 10:
        click.echo("Warning: Monitoring interval less than 10 seconds may impact system performance")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    monitor_logger = create_monitoring_logger(output_dir)
    
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=duration) if duration else None
    
    monitoring_data = []
    
    def signal_handler(signum, frame):
        monitor_logger.info("Monitoring stopped by user")
        _save_monitoring_data(monitoring_data, output_path, format)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    monitor_logger.info(f"Starting monitoring with {interval}s interval")
    if device:
        monitor_logger.info(f"Monitoring device: {device}")
    else:
        monitor_logger.info("Monitoring all devices")
    
    try:
        iteration = 0
        while True:
            iteration += 1
            current_time = datetime.now()
            
            if end_time and current_time >= end_time:
                monitor_logger.info("Monitoring duration completed")
                break
            
            try:
                if device:
                    snapshot = cli_ctx.data_collector.collect_device_health(device)
                    snapshots = [snapshot]
                else:
                    snapshots = cli_ctx.data_collector.collect_all_devices_health()
                
                for snapshot in snapshots:
                    monitoring_data.append({
                        'iteration': iteration,
                        'timestamp': current_time.isoformat(),
                        'snapshot': snapshot.model_dump()
                    })
                    
                    if threshold_alerts:
                        alerts = cli_ctx.data_processor.check_health_thresholds(snapshot)
                        for alert in alerts:
                            monitor_logger.warning(f"ALERT: {alert['message']}")
                
                monitor_logger.info(f"Iteration {iteration}: Collected data from {len(snapshots)} device(s)")
                
                if iteration % 10 == 0:
                    _save_monitoring_data(monitoring_data, output_path, format)
                    monitor_logger.info(f"Saved monitoring data (iteration {iteration})")
                
            except Exception as e:
                monitor_logger.error(f"Error in monitoring iteration {iteration}: {e}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        monitor_logger.info("Monitoring interrupted")
    finally:
        _save_monitoring_data(monitoring_data, output_path, format)
        monitor_logger.info("Monitoring completed")


@cli.command()
@click.option('--device', '-d', required=True, help='Device path for self-test')
@click.option('--type', '-t', type=click.Choice(['short', 'extended', 'vendor']), 
              default='short', help='Self-test type')
@click.option('--wait', '-w', is_flag=True, help='Wait for test completion')
@click.option('--abort', is_flag=True, help='Abort running test')
@click.option('--status', '-s', is_flag=True, help='Show test status only')
@click.pass_context
def self_test(ctx: click.Context, device: str, type: str, wait: bool, abort: bool, status: bool):
    """Manage NVMe device self-tests."""
    cli_ctx = ctx.obj
    
    if sum([wait, abort, status]) > 1:
        click.echo("Error: Can only specify one of --wait, --abort, or --status", err=True)
        sys.exit(1)
    
    try:
        if status:
            snapshot = cli_ctx.data_collector.collect_device_health(device, include_self_test=True)
            if snapshot.self_test_log and snapshot.self_test_log.entries:
                latest_test = snapshot.self_test_log.entries[0]
                click.echo(f"Latest self-test on {device}:")
                click.echo(f"  Type: {latest_test.test_type.value}")
                click.echo(f"  Result: {latest_test.result.value}")
                if latest_test.completion_timestamp:
                    click.echo(f"  Completed: {latest_test.completion_timestamp}")
                if latest_test.power_on_hours:
                    click.echo(f"  Power-on hours: {latest_test.power_on_hours}")
            else:
                click.echo(f"No self-test data available for {device}")
        
        elif abort:
            click.echo(f"Aborting self-test on {device}...")
            click.echo("Note: Self-test abort functionality requires direct nvme-cli integration")
        
        else:
            click.echo(f"Starting {type} self-test on {device}...")
            click.echo("Note: Self-test start functionality requires direct nvme-cli integration")
            
            if wait:
                click.echo("Waiting for test completion...")
                click.echo("Note: Test completion monitoring requires direct nvme-cli integration")
                
    except NVMeDeviceNotFoundError as e:
        click.echo(f"Device not found: {e}", err=True)
        sys.exit(1)
    except NVMeError as e:
        click.echo(f"Error managing self-test: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        cli_ctx.logger.error(f"Unexpected error in self-test: {e}")
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


def validate_cli_arguments(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    """
    Validate CLI argument values.
    
    Args:
        ctx: Click context
        param: Parameter being validated
        value: Parameter value
        
    Returns:
        Validated parameter value
        
    Raises:
        click.BadParameter: If validation fails
    """
    if param.name == 'device' and value:
        if not value.startswith('/dev/nvme'):
            raise click.BadParameter('Device path must start with /dev/nvme')
        
        if not Path(value).exists():
            raise click.BadParameter(f'Device path does not exist: {value}')
    
    elif param.name == 'interval' and value:
        if value < 1:
            raise click.BadParameter('Interval must be at least 1 second')
        if value > 86400:
            raise click.BadParameter('Interval cannot exceed 24 hours (86400 seconds)')
    
    elif param.name == 'duration' and value:
        if value < 1:
            raise click.BadParameter('Duration must be at least 1 second')
        if value > 604800:
            raise click.BadParameter('Duration cannot exceed 7 days (604800 seconds)')
    
    return value


def setup_cli_logging(verbose: int) -> None:
    """
    Set up logging based on CLI verbosity level.
    
    Args:
        verbose: Verbosity level (0=ERROR, 1=WARNING, 2=INFO, 3=DEBUG)
    """
    configure_cli_logging(verbose)


def handle_cli_exceptions(func):
    """
    Decorator to handle CLI exceptions gracefully.
    
    Args:
        func: CLI function to wrap
        
    Returns:
        Wrapped function with exception handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NVMeDeviceNotFoundError as e:
            click.echo(f"Device not found: {e}", err=True)
            click.echo("Hint: Check device path and ensure you have proper permissions", err=True)
            sys.exit(1)
        except NVMeCommandError as e:
            click.echo(f"Command failed: {e}", err=True)
            click.echo("Hint: Ensure nvme-cli is installed and you have proper permissions", err=True)
            sys.exit(1)
        except NVMeError as e:
            click.echo(f"NVMe error: {e}", err=True)
            sys.exit(1)
        except PermissionError as e:
            click.echo(f"Permission denied: {e}", err=True)
            click.echo("Hint: Try running with sudo or check device permissions", err=True)
            sys.exit(1)
        except KeyboardInterrupt:
            click.echo("\nOperation cancelled by user", err=True)
            sys.exit(130)
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            click.echo("Hint: Run with -vvv for detailed debug information", err=True)
            sys.exit(1)
    
    return wrapper


def _save_monitoring_data(data: List[Dict[str, Any]], output_dir: Path, format: str) -> None:
    """Save monitoring data to file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if format == 'json':
        output_file = output_dir / f'monitoring_data_{timestamp}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    else:
        output_file = output_dir / f'monitoring_data_{timestamp}.csv'
        if data:
            import csv
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['iteration', 'timestamp', 'device_path', 'health_status'])
                writer.writeheader()
                for entry in data:
                    snapshot_data = entry['snapshot']
                    writer.writerow({
                        'iteration': entry['iteration'],
                        'timestamp': entry['timestamp'],
                        'device_path': snapshot_data.get('device_info', {}).get('device_path', 'unknown'),
                        'health_status': snapshot_data.get('smart_data', {}).get('health_status', 'unknown')
                    })


if __name__ == '__main__':
    cli()
