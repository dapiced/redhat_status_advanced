#!/usr/bin/env python3
"""
Red Hat Status Checker - Main Entry Point

This is the main entry point for the modular Red Hat Status Checker.
It provides all the functionality of the original script but with
improved organization and maintainability.

Usage:
    python3 main.py [options]
    
For backward compatibility, this maintains the same CLI interface
as the original redhat_summary_status.py script.

Author: Red Hat Status Checker v3.1.0 - Modular Edition
"""

import sys
import os
import argparse
import json
import csv
import time
import logging
from typing import Dict, Any
import logging
import json
import time
from datetime import datetime
from pathlib import Path
from pathlib import Path

# Ensure the project root is in the Python path for package imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import our modular components
from redhat_status.config.config_manager import get_config
from redhat_status.core.api_client import get_api_client, fetch_status_data
from redhat_status.core.data_models import PerformanceMetrics, AlertSeverity
from redhat_status.utils.decorators import performance_monitor, Timer
from redhat_status.presentation.presenter import Presenter

# Initialize enterprise features if enabled
try:
    from redhat_status.analytics import get_analytics
    from redhat_status.database import get_database_manager
    from redhat_status.notifications import get_notification_manager
    ENTERPRISE_FEATURES = True
except ImportError:
    ENTERPRISE_FEATURES = False


class RedHatStatusChecker:
    """Main application class for Red Hat Status Checker"""
    
    def __init__(self, exporter_module=None):
        """
        Initialize the application.

        Args:
            exporter_module: An optional module to handle metrics exporting (e.g., Prometheus).
        """
        self.config = get_config()
        self.api_client = get_api_client()
        self.presenter = Presenter()
        self.performance = PerformanceMetrics(start_time=datetime.now())
        self.exporter_module = exporter_module
        
        # Initialize enterprise features if available
        self.analytics = None
        self.db_manager = None
        self.notification_manager = None
        
        if ENTERPRISE_FEATURES:
            try:
                # Initialize AI analytics if enabled
                if self._get_config_value('ai_analytics', 'enabled', False):
                    self.analytics = get_analytics()
                    logging.info("AI Analytics enabled")
                
                # Initialize database if enabled
                if self._get_config_value('database', 'enabled', False):
                    self.db_manager = get_database_manager()
                    logging.info("Database management enabled")
                
                # Initialize notifications if enabled
                email_config = self._get_config_value('notifications', 'email', {})
                webhook_config = self._get_config_value('notifications', 'webhooks', {})
                if (email_config.get('enabled', False) or webhook_config.get('enabled', False)):
                    self.notification_manager = get_notification_manager()
                    logging.info("Notification system enabled")
                else:
                    logging.info("Notifications disabled in configuration")
                
            except Exception as e:
                logging.warning(f"Failed to initialize enterprise features: {e}")
                # Don't modify global variable here, just set instance variables
                self.analytics = None
                self.db_manager = None
                self.notification_manager = None

    def _get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """Helper to get configuration values from either dict or ConfigManager"""
        try:
            if hasattr(self.config, 'get') and hasattr(self.config.get, '__code__') and self.config.get.__code__.co_argcount > 2:
                # It's a ConfigManager with get(section, key, default) method
                return self.config.get(section, key, default)
            elif hasattr(self.config, 'get'):
                # It's likely a mock or object with get method, try calling it directly
                try:
                    return self.config.get(section, key, default)
                except TypeError:
                    # If the get method doesn't accept 3 args, it might be a dict-like get
                    return self.config.get(section, {}).get(key, default)
            else:
                # It's a dictionary, use nested key access
                if isinstance(self.config, dict):
                    return self.config.get(section, {}).get(key, default)
                return default
        except Exception:
            # Fallback to default if anything goes wrong
            return default

    @performance_monitor
    def quick_status_check(self, quiet_mode: bool = False) -> None:
        """Perform quick status check with global availability percentage"""
        try:
            response = fetch_status_data()
            if not response.success:
                self.presenter.present_error(f"Failed to fetch status data: {response.error_message}")
                return

            data = response.data
            if not data:
                self.presenter.present_error("No data received")
                return

            health_metrics = self.api_client.get_service_health_metrics(data)
            
            self.presenter.present_quick_status(health_metrics, data.get('_metadata', {}).get('cached', False), quiet_mode)

            # Update metrics if exporter is enabled
            if self.exporter_module:
                from redhat_status.core.cache_manager import get_cache_manager
                cache_info = get_cache_manager().get_cache_info()
                # Ensure response_time exists on the response object, default to a value if not.
                response_time = getattr(response, 'response_time', 0.0)
                perf_data = {'cache_info': cache_info.__dict__, 'api_response_time': response_time}
                self.exporter_module.update_metrics(health_metrics, data.get('components', []), perf_data)

            # Save metrics if enterprise features enabled
            if self.db_manager:
                try:
                    self.db_manager.save_service_snapshot(health_metrics, data.get('components', []))
                except Exception as e:
                    logging.error(f"Failed to save metrics: {e}")
            
        except Exception as e:
            logging.error(f"Quick status check failed: {e}")
            self.presenter.present_error(f"Error during status check: {e}")
    
    def _present_quick_status(self, health_metrics: Dict[str, Any], cached: bool = False, quiet_mode: bool = False) -> None:
        """Present quick status results (internal method for testing)
        
        Args:
            health_metrics: Health metrics dictionary
            cached: Whether data was cached
            quiet_mode: Whether to use quiet output mode
        """
        self.presenter.present_quick_status(health_metrics, cached, quiet_mode)
    
    def simple_check_only(self) -> None:
        """Check main services only"""
        try:
            response = fetch_status_data()
            
            if not response.success:
                self.presenter.present_error(f"Failed to fetch data: {response.error_message}")
                return
            
            data = response.data
            components = data.get('components', [])
            
            self.presenter.present_simple_check(components)
                
        except Exception as e:
            logging.error(f"Simple check failed: {e}")
            self.presenter.present_error(f"Error during simple check: {e}")
    
    def full_check_with_services(self) -> None:
        """Complete service hierarchy check"""
        try:
            response = fetch_status_data()
            
            if not response.success:
                self.presenter.present_error(f"Failed to fetch data: {response.error_message}")
                return
            
            data = response.data
            components = data.get('components', [])
            
            self.presenter.present_full_check(components)
                    
        except Exception as e:
            logging.error(f"Full check failed: {e}")
            self.presenter.present_error(f"Error during full check: {e}")
    
    def export_to_file(self, output_dir: str = ".") -> None:
        """Export data to files"""
        self.presenter.present_message("\n💾 DATA EXPORT")
        self.presenter.present_message("-" * 40)
        
        try:
            response = fetch_status_data()
            
            if not response.success:
                self.presenter.present_error(f"Failed to fetch data for export: {response.error_message}")
                return
            
            data = response.data
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime(self._get_config_value('output', 'timestamp_format', '%Y%m%d_%H%M%S'))
            filename = os.path.join(output_dir, f"redhat_status_{timestamp}.json")
            
            # Export JSON data
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Get file size
            file_size = os.path.getsize(filename)
            file_size_kb = file_size / 1024
            
            self.presenter.present_message(f"✅ Data exported to: {filename}")
            self.presenter.present_message(f"📊 File size: {file_size_kb:.1f} KB ({file_size} bytes)")
            self.presenter.present_message(f"📅 Export time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Create summary report
            if self._get_config_value('output', 'create_summary_report', True):
                self._create_summary_report(data, output_dir, timestamp)
                
        except Exception as e:
            logging.error(f"Export failed: {e}")
            self.presenter.present_error(f"Export error: {str(e)}")
    
    def _create_summary_report(self, data: dict, output_dir: str, timestamp: str) -> None:
        """Create human-readable summary report"""
        try:
            summary_filename = os.path.join(output_dir, f"redhat_summary_{timestamp}.txt")
            health_metrics = self.api_client.get_service_health_metrics(data)
            
            with open(summary_filename, 'w', encoding='utf-8') as f:
                f.write("RED HAT STATUS SUMMARY REPORT\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Page: {health_metrics['page_name']}\n")
                f.write(f"URL: {health_metrics['page_url']}\n")
                f.write(f"Last Update: {health_metrics['last_updated']}\n\n")
                
                f.write(f"Status: {health_metrics['overall_status']}\n")
                f.write(f"Indicator: {health_metrics['status_indicator']}\n\n")
                
                f.write(f"Global Availability: {health_metrics['availability_percentage']:.1f}%\n")
                f.write(f"Total Services: {health_metrics['total_services']}\n")
                f.write(f"Operational: {health_metrics['operational_services']}\n")
                f.write(f"With Issues: {health_metrics['services_with_issues']}\n\n")
                
                f.write(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            self.presenter.present_message(f"📋 Summary report created: {summary_filename}")
            
        except Exception as e:
            logging.error(f"Failed to create summary report: {e}")
            self.presenter.present_error(f"Error creating summary report: {str(e)}")
    
    def show_performance_metrics(self) -> None:
        """Display performance metrics"""
        try:
            from redhat_status.core.cache_manager import get_cache_manager
            cache_manager = get_cache_manager()
            cache_info = cache_manager.get_cache_info()
            
            db_stats = None
            if self.db_manager:
                try:
                    db_stats = self.db_manager.get_database_stats()
                except Exception as e:
                    logging.error(f"Failed to get database stats: {e}")

            notif_stats = None
            if self.notification_manager:
                try:
                    notif_stats = self.notification_manager.get_notification_stats()
                except Exception as e:
                    logging.error(f"Failed to get notification stats: {e}")

            self.presenter.present_performance_metrics(self.performance, cache_info, db_stats, notif_stats)
                
        except Exception as e:
            logging.error(f"Performance metrics display failed: {e}")
            self.presenter.present_error(f"Error displaying performance metrics: {e}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="Red Hat Status Checker - Monitor Red Hat services status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Interactive mode
  %(prog)s quick              # Quick status only
  %(prog)s simple             # Main services check
  %(prog)s full               # Complete structure
  %(prog)s export             # Export data to files
  %(prog)s all                # Display everything
  %(prog)s quick --quiet      # Minimal output
  %(prog)s export --output ./reports  # Export to specific directory
  %(prog)s --performance      # Show performance metrics
  
Advanced Features:
  %(prog)s --ai-insights       # Show detailed AI analysis
  %(prog)s --health-report     # Generate comprehensive health report
  %(prog)s --anomaly-analysis  # Advanced anomaly detection
  %(prog)s --trends           # Show availability trends
  %(prog)s --slo-dashboard    # View SLO tracking dashboard
  %(prog)s --export-ai-report # Export AI analysis to file
  %(prog)s --filter issues    # Show only services with issues
  %(prog)s --search "registry" # Search for specific services
  %(prog)s --watch 30         # Live monitoring (30s refresh)
  %(prog)s --benchmark        # Performance benchmarking
  %(prog)s --no-cache         # Bypass cache for fresh data
  %(prog)s --enable-exporter  # Run Prometheus exporter
        """
    )
    
    parser.add_argument(
        'mode',
        nargs='?',
        choices=['quick', 'simple', 'full', 'export', 'all'],
        default=None,
        help='Operation mode (if not specified, interactive mode is used)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='.',
        help='Output directory for exported files (default: current directory)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode - minimal output'
    )
    
    parser.add_argument(
        '--performance',
        action='store_true',
        help='Show performance metrics'
    )
    
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear all cached data'
    )
    
    parser.add_argument(
        '--config-check',
        action='store_true',
        help='Validate configuration and display settings'
    )
    
    parser.add_argument(
        '--test-notifications',
        action='store_true',
        help='Test all notification channels'
    )
    
    parser.add_argument(
        '--analytics-summary',
        action='store_true',
        help='Show AI analytics summary (enterprise feature)'
    )
    
    parser.add_argument(
        '--db-maintenance',
        action='store_true',
        help='Perform database maintenance (enterprise feature)'
    )
    
    # === AI Analytics & Insights ===
    parser.add_argument(
        '--ai-insights',
        action='store_true',
        help='Show detailed AI analysis and insights'
    )
    
    parser.add_argument(
        '--anomaly-analysis',
        action='store_true',
        help='Perform advanced anomaly detection analysis'
    )
    
    parser.add_argument(
        '--health-report',
        action='store_true',
        help='Generate comprehensive health analysis report'
    )
    
    parser.add_argument(
        '--insights',
        action='store_true',
        help='Show system insights and patterns'
    )
    
    parser.add_argument(
        '--trends',
        action='store_true',
        help='Show availability trends and predictions'
    )
    
    parser.add_argument(
        '--slo-dashboard',
        action='store_true',
        dest='slo_dashboard',
        help='View SLO tracking and objectives'
    )
    
    # === Export & Reporting ===
    parser.add_argument(
        '--export-ai-report',
        action='store_true',
        help='Generate and export AI analysis report'
    )
    
    parser.add_argument(
        '--export-history',
        action='store_true',
        help='Export historical data to files'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'csv', 'txt'],
        default='json',
        help='Output format for exports (default: json)'
    )
    
    # === Service Operations ===
    parser.add_argument(
        '--filter',
        choices=['all', 'issues', 'operational', 'degraded'],
        default='all',
        help='Filter services by status'
    )
    
    parser.add_argument(
        '--search',
        type=str,
        help='Search services by name (case-insensitive)'
    )
    
    parser.add_argument(
        '--concurrent-check',
        action='store_true',
        help='Enable multi-threaded health checks'
    )
    
    # === Monitoring & Live Features ===
    parser.add_argument(
        '--watch',
        type=int,
        metavar='SECONDS',
        help='Live monitoring mode with refresh interval'
    )
    
    parser.add_argument(
        '--notify',
        action='store_true',
        help='Send notifications for current status'
    )
    
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Run performance benchmarking tests'
    )
    
    # === Configuration & Debug ===
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Bypass cache and force fresh data'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--enable-monitoring',
        action='store_true',
        help='Enable continuous monitoring mode'
    )
    
    # --- Exporter Arguments ---
    parser.add_argument(
        '--enable-exporter',
        action='store_true',
        help='Enable the Prometheus exporter to expose metrics on /metrics'
    )

    parser.add_argument(
        '--exporter-port',
        type=int,
        default=8000,
        help='Port for the Prometheus exporter (default: 8000)'
    )

    parser.add_argument(
        '--setup',
        action='store_true',
        help='Run configuration setup wizard'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Red Hat Status Checker v3.1.0 - Modular Edition'
    )
    
    return parser


def main():
    """Main function with improved argument handling"""
    try:
        parser = create_argument_parser()
        args = parser.parse_args()

        
        exporter_module = None
        if args.enable_exporter:
            from redhat_status.exporters.prometheus_exporter import get_prometheus_exporter
            exporter_module = get_prometheus_exporter(port=args.exporter_port, enabled=True)
            if exporter_module.start_server():
                print(f"📈 Prometheus exporter started on http://localhost:{args.exporter_port}")
            else:
                print("❌ Failed to start Prometheus exporter")

        app = RedHatStatusChecker(exporter_module=exporter_module)
        presenter = app.presenter

        # Create a dispatch table for special operations
        dispatch_table = {
            'clear_cache': handle_clear_cache,
            'config_check': handle_config_check,
            'test_notifications': handle_test_notifications,
            'analytics_summary': handle_analytics_summary,
            'db_maintenance': handle_db_maintenance,
            'ai_insights': handle_ai_insights,
            'anomaly_analysis': handle_anomaly_analysis,
            'health_report': handle_health_report,
            'insights': handle_insights,
            'trends': handle_trends,
            'slo_dashboard': handle_slo_dashboard,
            'export_ai_report': handle_export_ai_report,
            'export_history': handle_export_history,
            'watch': handle_watch,
            'notify': handle_notify,
            'benchmark': handle_benchmark,
            'setup': handle_setup,
        }

        # Handle special flags that exit immediately
        for arg, handler in dispatch_table.items():
            if getattr(args, arg):
                handler(app, args)
                return

        # Handle pre-run configurations
        if args.no_cache:
            presenter.present_message("🚫 CACHE BYPASS ENABLED")
            app.api_client._bypass_cache = True
        
        if args.log_level:
            level = getattr(logging, args.log_level.upper())
            logging.getLogger().setLevel(level)
            presenter.present_message(f"🔧 Log level set to: {args.log_level}")
        
        if args.concurrent_check:
            presenter.present_message("⚡ ENABLING MULTI-THREADED HEALTH CHECKS")
            app.api_client._concurrent_mode = True

        if args.enable_monitoring:
            presenter.present_message("📊 CONTINUOUS MONITORING ENABLED")
            if app.analytics:
                app.analytics._monitoring_enabled = True

        # Show header unless in quiet mode
        if not args.quiet:
            presenter.present_message("🎯 RED HAT STATUS CHECKER - MODULAR EDITION v3.1.0")
            presenter.present_message("=" * 60)
        
        mode = args.mode
        
        # Handle interactive mode
        if mode is None and not args.quiet and not (args.filter != 'all' or args.search):
            # If exporter is enabled, check if user wants to run in exporter-only mode
            if args.enable_exporter:
                presenter.present_message("Available modes:")
                presenter.present_message("  quick    - Global status only")
                presenter.present_message("  simple   - Main services")
                presenter.present_message("  full     - Complete structure")
                presenter.present_message("  export   - Export data")
                presenter.present_message("  all      - Display all")
                presenter.present_message("  (or press Enter to run exporter only)")
                print()
                user_input = input("Choose a mode (or press Enter for exporter only): ").lower()
                if user_input:
                    if user_input in ['quick', 'simple', 'full', 'export', 'all']:
                        mode = user_input
                    else:
                        presenter.present_error(f"Mode '{user_input}' not recognized, running exporter only")
                        mode = None
                # If user just pressed Enter, mode remains None for exporter-only
            else:
                mode = get_interactive_mode(presenter)

        # If no mode is specified (e.g. only --enable-exporter is used),
        # keep the application alive to serve metrics.
        if mode is None and args.enable_exporter:
            presenter.present_message("Exporter is running. No mode selected. Application will idle.")
            presenter.present_message("Perform a check in another terminal to populate metrics, e.g., `python3 redhat_status.py quick`")
            presenter.present_message("Press Ctrl+C to stop.")
            while True:
                time.sleep(1)

        # Default to quick mode if no mode specified
        if mode is None:
            mode = "quick"
        
        # Handle filtering and search, which is a distinct operation
        if args.filter != 'all' or args.search:
            handle_filter_and_search(app, args)
            return
        
        # Execute the requested primary mode
        execute_main_mode(app, mode, args)

    except KeyboardInterrupt:
        print(f"\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Application error: {e}", exc_info=True)
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)

def execute_main_mode(app, mode, args):
    """Executes the primary operation mode (quick, simple, etc.)."""
    with Timer("Operation", log_result=False) as timer:
        if mode == "quick":
            app.quick_status_check(quiet_mode=args.quiet)
        elif mode == "simple":
            app.quick_status_check(quiet_mode=args.quiet)
            app.simple_check_only()
        elif mode == "full":
            app.quick_status_check(quiet_mode=args.quiet)
            app.simple_check_only()
            app.full_check_with_services()
        elif mode == "export":
            app.export_to_file(args.output)
        elif mode == "all":
            app.quick_status_check(quiet_mode=args.quiet)
            app.simple_check_only()
            app.full_check_with_services()
            app.export_to_file(args.output)

    if args.performance:
        app.show_performance_metrics()

    if not args.quiet:
        app.presenter.present_message(f"\n✅ Operation completed successfully in {timer.duration:.2f}s!")

def get_interactive_mode(presenter):
    """Handles interactive mode selection."""
    presenter.present_message("Available modes:")
    presenter.present_message("  quick    - Global status only")
    presenter.present_message("  simple   - Main services")
    presenter.present_message("  full     - Complete structure")
    presenter.present_message("  export   - Export data")
    presenter.present_message("  all      - Display all")
    print()
    mode = input("Choose a mode (or press Enter for 'quick'): ").lower()
    if not mode:
        mode = "quick"

    if mode not in ['quick', 'simple', 'full', 'export', 'all']:
        presenter.present_error(f"Mode '{mode}' not recognized, using 'quick'")
        mode = "quick"
    return mode

# --- Handler Functions for Dispatch Table ---

def handle_clear_cache(app, args):
    from redhat_status.core.cache_manager import get_cache_manager
    cache_manager = get_cache_manager()
    cleared = cache_manager.clear()
    # Use both print and presenter for compatibility with tests
    message = f"✅ Cache cleared: {cleared} files removed"
    print(message)
    if hasattr(app, 'presenter') and app.presenter:
        app.presenter.present_message(message)

def handle_config_check(app, args):
    config = get_config()
    validation = config.validate()
    
    # Use both print and presenter for compatibility with tests
    header = "🔧 CONFIGURATION VALIDATION"
    separator = "=" * 40
    status = f"Status: {'✅ Valid' if validation['valid'] else '❌ Invalid'}"
    
    print(header)
    print(separator)
    print(status)
    
    if hasattr(app, 'presenter') and app.presenter:
        app.presenter.present_message(header)
        app.presenter.present_message(separator)
        app.presenter.present_message(status)

    if validation['errors']:
        errors_header = "\nErrors:"
        print(errors_header)
        if hasattr(app, 'presenter') and app.presenter:
            app.presenter.present_message(errors_header)
        for error in validation['errors']:
            error_msg = f"  {error}"
            print(error_msg)
            if hasattr(app, 'presenter') and app.presenter:
                app.presenter.present_error(error_msg)

    if validation['warnings']:
        warnings_header = "\nWarnings:"
        print(warnings_header)
        if hasattr(app, 'presenter') and app.presenter:
            app.presenter.present_message(warnings_header)
        for warning in validation['warnings']:
            warning_msg = f"  ⚠️  {warning}"
            print(warning_msg)
            if hasattr(app, 'presenter') and app.presenter:
                app.presenter.present_message(warning_msg)

def handle_test_notifications(app, args):
    if not app.notification_manager:
        app.presenter.present_error("Notification system not available (enterprise feature disabled)")
        return

    app.presenter.present_message("🧪 TESTING NOTIFICATION CHANNELS")
    app.presenter.present_message("=" * 40)
    results = app.notification_manager.test_all_channels()

    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)

    for channel, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        app.presenter.present_message(f"{channel}: {status}")

    app.presenter.present_message("-" * 40)
    app.presenter.present_message(f"📊 Results: {success_count}/{total_count} channels passed")

    if success_count < total_count:
        app.presenter.present_message("💡 Note: Failures may be due to test/invalid credentials in config.json")

def handle_filter_and_search(app, args):
    """Handles the logic for filtering and searching services."""
    app.presenter.present_message(f"🔍 FILTERING SERVICES")
    if args.filter != 'all':
        app.presenter.present_message(f"📋 Filter: {args.filter}")
    if args.search:
        app.presenter.present_message(f"🔎 Search: '{args.search}'")
    app.presenter.present_message("=" * 40)

    response = app.api_client.fetch_status_data()
    if not response.success:
        app.presenter.present_error(f"Failed to fetch services: {response.error_message}")
        return

    services = response.data.get('components', [])
    filtered_services = []

    for service in services:
        status_match = True
        if args.filter != 'all':
            if args.filter == 'issues' and service.get('status') == 'operational':
                status_match = False
            elif args.filter == 'operational' and service.get('status') != 'operational':
                status_match = False
            elif args.filter == 'degraded' and service.get('status') not in ['degraded_performance', 'partial_outage']:
                status_match = False

        search_match = True
        if args.search:
            if args.search.lower() not in service.get('name', '').lower():
                search_match = False

        if status_match and search_match:
            filtered_services.append(service)

    app.presenter.present_message(f"📊 Found {len(filtered_services)} services matching criteria:")
    for service in filtered_services[:20]:
        status_emoji = "🟢" if service.get('status') == 'operational' else "🟡" if 'degraded' in service.get('status', '') else "🔴"
        app.presenter.present_message(f"  {status_emoji} {service.get('name', 'Unknown')}: {service.get('status', 'unknown')}")

    if len(filtered_services) > 20:
        app.presenter.present_message(f"  ... and {len(filtered_services) - 20} more services")

# Add other handlers (handle_analytics_summary, handle_db_maintenance, etc.) here
# for brevity, they are not all shown but would follow the same pattern.
def handle_analytics_summary(app, args):
    if not app.analytics:
        app.presenter.present_error("AI Analytics not available (enterprise feature disabled)")
        return
    app.presenter.present_message("🤖 AI ANALYTICS SUMMARY")
    app.presenter.present_message("=" * 40)
    summary = app.analytics.get_analytics_summary()
    if summary:
        app.presenter.present_message(f"📊 Data Quality: {summary.get('data_quality', {}).get('total_metrics', 0)} metrics")
        app.presenter.present_message(f"🔍 Anomalies (24h): {sum(summary.get('anomaly_counts', {}).values())}")
        app.presenter.present_message(f"🔮 Predictions (24h): {sum(summary.get('prediction_counts', {}).values())}")
        app.presenter.present_message(f"📈 Service Health: {len(summary.get('service_health', []))} services monitored")
    else:
        app.presenter.present_error("No analytics data available")

def handle_db_maintenance(app, args):
    if not app.db_manager:
        app.presenter.present_error("Database system not available (enterprise feature disabled)")
        return
    app.presenter.present_message("🔧 DATABASE MAINTENANCE")
    app.presenter.present_message("=" * 40)
    app.presenter.present_message("Running cleanup...")
    cleanup_results = app.db_manager.cleanup_old_data()
    for table, count in cleanup_results.items():
        app.presenter.present_message(f"  {table}: {count} records cleaned")

    app.presenter.present_message("\nRunning vacuum...")
    vacuum_success = app.db_manager.vacuum_database()
    app.presenter.present_message(f"  Vacuum: {'✅ Success' if vacuum_success else '❌ Failed'}")

    app.presenter.present_message("\nRunning analyze...")
    analyze_success = app.db_manager.analyze_database()
    app.presenter.present_message(f"  Analyze: {'✅ Success' if analyze_success else '❌ Failed'}")

def handle_ai_insights(app, args):
    """Show AI-powered insights and analytics"""
    app.presenter.present_message("\n🤖 AI INSIGHTS & ANALYTICS")
    app.presenter.present_message("=" * 40)
    
    try:
        from redhat_status.analytics.ai_analytics import AIAnalytics
        
        # Get current data for analysis
        response = fetch_status_data()
        if not response.success:
            app.presenter.present_error(f"Failed to fetch data: {response.error_message}")
            return
        
        data = response.data
        ai_analytics = AIAnalytics()
        
        # Get recent anomalies using historical data
        app.presenter.present_message("\n🔍 Anomaly Analysis:")
        try:
            # Try to get historical data for anomaly detection
            if hasattr(app, 'db_manager') and app.db_manager.is_enabled():
                historical_data = app.db_manager.get_status_history(limit=50)
                if historical_data:
                    anomalies = ai_analytics.detect_anomalies(historical_data)
                    if isinstance(anomalies, list) and anomalies:
                        for anomaly in anomalies[:5]:  # Show top 5
                            severity_emoji = "🔴" if anomaly.severity == AlertSeverity.CRITICAL else "🟡" if anomaly.severity == AlertSeverity.WARNING else "🔵"
                            app.presenter.present_message(f"  {severity_emoji} {anomaly.service_name}: {anomaly.description}")
                    else:
                        app.presenter.present_message("  ✅ No significant anomalies detected")
                else:
                    app.presenter.present_message("  ℹ️ Insufficient historical data for anomaly detection")
            else:
                app.presenter.present_message("  ⚠️ Database not available for anomaly analysis")
        except Exception as e:
            app.presenter.present_message(f"  ⚠️ Anomaly detection failed: {e}")
        
        # Get current health insights
        app.presenter.present_message("\n💡 Current Health Analysis:")
        try:
            health_metrics = app.api_client.get_service_health_metrics(data)
            
            # Generate health score
            health_score_data = ai_analytics.generate_health_score(data)
            if health_score_data:
                app.presenter.present_message(f"  📊 Health Score: {health_score_data}")
            
            # Provide basic health analysis
            availability = health_metrics.get('availability_percentage', 0)
            if availability >= 99.0:
                app.presenter.present_message("  ✅ Excellent health: All systems operating normally")
            elif availability >= 95.0:
                app.presenter.present_message("  🟡 Good health: Minor issues detected")
            else:
                app.presenter.present_message("  🔴 Health concern: Significant service disruptions")
                
            # Try to generate predictions for main services
            app.presenter.present_message("\n🔮 Predictive Analysis:")
            try:
                predictions = ai_analytics.generate_predictions("Red Hat", hours_ahead=24)
                if predictions:
                    for prediction in predictions[:2]:  # Show top 2
                        app.presenter.present_message(f"  📈 {prediction.title}: {prediction.description}")
                else:
                    app.presenter.present_message("  ℹ️ Insufficient data for predictions")
            except Exception as e:
                app.presenter.present_message(f"  ⚠️ Prediction analysis failed: {e}")
                
        except Exception as e:
            app.presenter.present_message(f"  ⚠️ Health analysis failed: {e}")
            
    except Exception as e:
        app.presenter.present_error(f"Error generating AI insights: {e}")

def handle_anomaly_analysis(app, args):
    """Run focused anomaly detection analysis"""
    app.presenter.present_message("\n🔍 ANOMALY DETECTION ANALYSIS")
    app.presenter.present_message("=" * 45)
    
    try:
        from redhat_status.analytics.ai_analytics import AIAnalytics
        
        if not hasattr(app, 'db_manager') or not app.db_manager.is_enabled():
            app.presenter.present_message("❌ Database not available for anomaly analysis")
            app.presenter.present_message("💡 Run the application with normal modes first to collect data")
            return
        
        ai_analytics = AIAnalytics()
        
        # Get historical data for analysis
        app.presenter.present_message("\n📊 Collecting Historical Data...")
        historical_data = app.db_manager.get_status_history(limit=100)
        
        if not historical_data:
            app.presenter.present_message("  ⚠️ No historical data available")
            app.presenter.present_message("  💡 Run 'quick' or 'simple' mode a few times to collect baseline data")
            return
        
        app.presenter.present_message(f"  ✅ Analyzing {len(historical_data)} data points")
        
        # Perform anomaly detection
        app.presenter.present_message("\n🔍 Running Anomaly Detection...")
        try:
            anomalies = ai_analytics.detect_anomalies(historical_data)
            
            if isinstance(anomalies, dict):
                # Handle dictionary response
                anomaly_count = anomalies.get('anomaly_count', 0)
                if anomaly_count > 0:
                    app.presenter.present_message(f"  🚨 Found {anomaly_count} anomalies")
                    
                    # Show anomaly details if available
                    if 'anomalies' in anomalies:
                        for i, anomaly in enumerate(anomalies['anomalies'][:5]):
                            app.presenter.present_message(f"  {i+1}. {anomaly}")
                else:
                    app.presenter.present_message("  ✅ No anomalies detected - system appears stable")
                    
                # Show statistical summary if available
                if 'statistics' in anomalies:
                    stats = anomalies['statistics']
                    app.presenter.present_message(f"\n📈 Statistical Summary:")
                    for key, value in stats.items():
                        app.presenter.present_message(f"  • {key}: {value}")
                        
            elif isinstance(anomalies, list):
                # Handle list response
                if anomalies:
                    app.presenter.present_message(f"  🚨 Found {len(anomalies)} anomalies")
                    for i, anomaly in enumerate(anomalies[:5]):
                        severity_emoji = "🔴" if hasattr(anomaly, 'severity') and anomaly.severity == AlertSeverity.CRITICAL else "🟡"
                        service_name = getattr(anomaly, 'service_name', 'Unknown')
                        description = getattr(anomaly, 'description', 'No description')
                        app.presenter.present_message(f"  {severity_emoji} {service_name}: {description}")
                else:
                    app.presenter.present_message("  ✅ No anomalies detected - system appears stable")
            else:
                app.presenter.present_message("  ℹ️ Anomaly analysis completed (no structured results)")
                
        except Exception as e:
            app.presenter.present_message(f"  ❌ Anomaly detection failed: {e}")
        
        # Provide recommendations
        app.presenter.present_message("\n💡 Recommendations:")
        app.presenter.present_message("  • Continue monitoring for pattern establishment")
        app.presenter.present_message("  • Set up alerts for critical anomalies")
        app.presenter.present_message("  • Review historical trends weekly")
        
    except Exception as e:
        app.presenter.present_error(f"Error running anomaly analysis: {e}")

def handle_health_report(app, args):
    """Generate comprehensive health report"""
    app.presenter.present_message("\n🏥 COMPREHENSIVE HEALTH REPORT")
    app.presenter.present_message("=" * 50)
    
    try:
        # Get current status
        response = fetch_status_data()
        if not response.success:
            app.presenter.present_error(f"Failed to fetch data: {response.error_message}")
            return
        
        data = response.data
        health_metrics = app.api_client.get_service_health_metrics(data)
        
        # Overall Health Score
        app.presenter.present_message(f"\n📊 Overall Health Score: {health_metrics['availability_percentage']:.1f}%")
        
        # Service breakdown
        app.presenter.present_message(f"\n📈 Service Statistics:")
        app.presenter.present_message(f"  • Total Services: {health_metrics['total_services']}")
        app.presenter.present_message(f"  • Operational: {health_metrics['operational_services']}")
        app.presenter.present_message(f"  • With Issues: {health_metrics['services_with_issues']}")
        
        # Performance metrics if available
        if hasattr(app, 'db_manager') and app.db_manager.is_enabled():
            try:
                recent_snapshots = app.db_manager.get_status_history(limit=5)
                if recent_snapshots:
                    app.presenter.present_message(f"\n📊 Recent Status History:")
                    for snapshot in recent_snapshots:
                        timestamp = snapshot.get('timestamp', 'Unknown')
                        availability = snapshot.get('availability_percentage', 0)
                        app.presenter.present_message(f"  • {timestamp}: {availability:.1f}%")
            except Exception as e:
                app.presenter.present_message(f"  ⚠️ Historical data unavailable: {e}")
        
        # Current status details
        app.presenter.present_message(f"\n🎯 Current Status:")
        app.presenter.present_message(f"  • Page: {health_metrics['page_name']}")
        app.presenter.present_message(f"  • Last Updated: {health_metrics['last_updated']}")
        app.presenter.present_message(f"  • Status: {health_metrics['overall_status']}")
        
    except Exception as e:
        app.presenter.present_error(f"Error generating health report: {e}")

def handle_insights(app, args):
    """Show comprehensive system insights and patterns"""
    try:
        app.presenter.present_message("\n💡 SYSTEM INSIGHTS & PATTERNS")
        app.presenter.present_message("=" * 50)
        
        # Get current status data for analysis
        app.presenter.present_message("\n📊 Fetching current service data...")
        api_response = fetch_status_data(app.api_client)
        
        if not api_response.success or not api_response.data:
            app.presenter.present_error("Failed to fetch data for insights analysis")
            return
        
        status_data = api_response.data
        health_metrics = app.api_client.get_service_health_metrics(status_data)
        
        # Current System Health Insights
        app.presenter.present_message("\n🏥 CURRENT HEALTH INSIGHTS")
        app.presenter.present_message("-" * 35)
        
        availability = health_metrics.get('availability_percentage', 0)
        total_services = health_metrics.get('total_services', 0)
        operational_services = health_metrics.get('operational_services', 0)
        services_with_issues = health_metrics.get('services_with_issues', 0)
        
        # Health categorization and insights
        if availability >= 99.5:
            health_status = "EXCELLENT"
            health_emoji = "🟢"
            insight = "System is performing exceptionally well with minimal issues"
        elif availability >= 97.0:
            health_status = "GOOD"
            health_emoji = "🟡"
            insight = "System is stable with minor issues that should be monitored"
        elif availability >= 90.0:
            health_status = "FAIR"
            health_emoji = "🟠"
            insight = "System has notable issues requiring attention"
        else:
            health_status = "POOR"
            health_emoji = "🔴"
            insight = "System has significant issues requiring immediate action"
        
        app.presenter.present_message(f"{health_emoji} Health Status: {health_status}")
        app.presenter.present_message(f"📋 Insight: {insight}")
        app.presenter.present_message(f"📊 Service Ratio: {operational_services}/{total_services} operational")
        
        # Service Distribution Analysis
        app.presenter.present_message("\n📈 SERVICE DISTRIBUTION ANALYSIS")
        app.presenter.present_message("-" * 40)
        
        components = status_data.get('components', [])
        
        # Analyze service status distribution
        status_distribution = {}
        for component in components:
            status = component.get('status', 'unknown')
            if status not in status_distribution:
                status_distribution[status] = 0
            status_distribution[status] += 1
        
        app.presenter.present_message("Status Distribution:")
        for status, count in sorted(status_distribution.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_services * 100) if total_services > 0 else 0
            status_emoji = "🟢" if status == 'operational' else "🟡" if 'degraded' in status else "🔴"
            app.presenter.present_message(f"  {status_emoji} {status.title()}: {count} services ({percentage:.1f}%)")
        
        # Service Category Analysis
        app.presenter.present_message("\n🏷️ SERVICE CATEGORY INSIGHTS")
        app.presenter.present_message("-" * 35)
        
        # Analyze services by name patterns to identify categories
        categories = {
            'OpenShift': [c for c in components if 'openshift' in c.get('name', '').lower()],
            'Red Hat Enterprise Linux': [c for c in components if any(term in c.get('name', '').lower() for term in ['rhel', 'enterprise linux'])],
            'Ansible': [c for c in components if 'ansible' in c.get('name', '').lower()],
            'Cloud Services': [c for c in components if any(term in c.get('name', '').lower() for term in ['cloud', 'hybrid'])],
            'Developer Tools': [c for c in components if any(term in c.get('name', '').lower() for term in ['developer', 'ide', 'build'])],
            'Container': [c for c in components if any(term in c.get('name', '').lower() for term in ['container', 'registry', 'quay'])],
            'Support & Documentation': [c for c in components if any(term in c.get('name', '').lower() for term in ['support', 'documentation', 'portal'])],
        }
        
        for category, services in categories.items():
            if services:
                operational_count = len([s for s in services if s.get('status') == 'operational'])
                category_availability = (operational_count / len(services) * 100) if services else 0
                
                if category_availability >= 99:
                    category_emoji = "🟢"
                elif category_availability >= 95:
                    category_emoji = "🟡"
                else:
                    category_emoji = "🔴"
                
                app.presenter.present_message(f"  {category_emoji} {category}: {operational_count}/{len(services)} operational ({category_availability:.1f}%)")
        
        # Performance Insights
        app.presenter.present_message("\n⚡ PERFORMANCE INSIGHTS")
        app.presenter.present_message("-" * 30)
        
        # Calculate response time metrics if available
        try:
            import time
            start_time = time.time()
            # Make a test API call to measure response time
            test_response = fetch_status_data(app.api_client)
            response_time = time.time() - start_time
            
            if response_time < 1.0:
                perf_emoji = "🟢"
                perf_status = "EXCELLENT"
            elif response_time < 3.0:
                perf_emoji = "🟡"
                perf_status = "GOOD"
            else:
                perf_emoji = "🔴"
                perf_status = "SLOW"
            
            app.presenter.present_message(f"{perf_emoji} API Response Time: {response_time:.3f}s ({perf_status})")
            
        except Exception as e:
            app.presenter.present_message(f"⚠️ Could not measure API performance: {e}")
        
        # Historical Insights (if available)
        if hasattr(app, 'db_manager') and app.db_manager and hasattr(app.db_manager, 'is_enabled') and app.db_manager.is_enabled():
            app.presenter.present_message("\n📜 HISTORICAL INSIGHTS")
            app.presenter.present_message("-" * 25)
            
            try:
                recent_snapshots = app.db_manager.get_status_history(limit=10)
                if recent_snapshots:
                    # Calculate trend analysis
                    availabilities = [s.get('availability_percentage', 0) for s in recent_snapshots]
                    
                    if len(availabilities) >= 2:
                        latest_avg = sum(availabilities[:3]) / min(3, len(availabilities))
                        older_avg = sum(availabilities[-3:]) / min(3, len(availabilities[-3:]))
                        trend = latest_avg - older_avg
                        
                        if abs(trend) < 0.5:
                            trend_emoji = "➡️"
                            trend_desc = "Stable"
                            trend_insight = "Service availability is consistent"
                        elif trend > 0:
                            trend_emoji = "📈"
                            trend_desc = f"Improving (+{trend:.1f}%)"
                            trend_insight = "Service reliability is trending upward"
                        else:
                            trend_emoji = "📉"
                            trend_desc = f"Declining ({trend:.1f}%)"
                            trend_insight = "Service reliability needs attention"
                        
                        app.presenter.present_message(f"{trend_emoji} Trend: {trend_desc}")
                        app.presenter.present_message(f"💡 Insight: {trend_insight}")
                    
                    # Pattern analysis
                    max_availability = max(availabilities)
                    min_availability = min(availabilities)
                    volatility = max_availability - min_availability
                    
                    if volatility < 1.0:
                        stability_emoji = "🟢"
                        stability_desc = "VERY STABLE"
                    elif volatility < 5.0:
                        stability_emoji = "🟡"
                        stability_desc = "STABLE"
                    else:
                        stability_emoji = "🔴"
                        stability_desc = "VOLATILE"
                    
                    app.presenter.present_message(f"{stability_emoji} Stability: {stability_desc} (±{volatility:.1f}%)")
                    
                else:
                    app.presenter.present_message("ℹ️ No historical data available for trend analysis")
                    app.presenter.present_message("💡 Run status checks regularly to build historical insights")
                    
            except Exception as e:
                app.presenter.present_message(f"⚠️ Historical analysis failed: {e}")
        else:
            app.presenter.present_message("\n📜 HISTORICAL INSIGHTS")
            app.presenter.present_message("-" * 25)
            app.presenter.present_message("ℹ️ Database not enabled for historical insights")
            app.presenter.present_message("💡 Enable database in config.json for trend analysis")
        
        # AI-Powered Insights (if available)
        if app.analytics:
            app.presenter.present_message("\n🤖 AI-POWERED INSIGHTS")
            app.presenter.present_message("-" * 30)
            
            try:
                # Generate health score insights
                health_score_data = app.analytics.generate_health_score(status_data)
                if health_score_data:
                    app.presenter.present_message(f"🎯 AI Health Score: {health_score_data}")
                
                # Service reliability predictions
                try:
                    predictions = app.analytics.generate_predictions("Red Hat Services", hours_ahead=24)
                    if predictions:
                        app.presenter.present_message("🔮 24-Hour Predictions:")
                        if isinstance(predictions, list):
                            for prediction in predictions[:3]:
                                app.presenter.present_message(f"   • {prediction}")
                        else:
                            app.presenter.present_message(f"   • {predictions}")
                except Exception as e:
                    app.presenter.present_message(f"   ⚠️ Prediction generation failed: {e}")
                
            except Exception as e:
                app.presenter.present_message(f"⚠️ AI analysis failed: {e}")
        else:
            app.presenter.present_message("\n🤖 AI-POWERED INSIGHTS")
            app.presenter.present_message("-" * 30)
            app.presenter.present_message("ℹ️ AI analytics not enabled")
            app.presenter.present_message("💡 Enable AI analytics in config.json for advanced insights")
        
        # Recommendations
        app.presenter.present_message("\n💡 ACTIONABLE RECOMMENDATIONS")
        app.presenter.present_message("-" * 35)
        
        recommendations = []
        
        # Service availability recommendations
        if availability < 95:
            recommendations.append("🚨 URGENT: Address service availability issues immediately")
        elif availability < 99:
            recommendations.append("⚠️ Monitor affected services closely for resolution")
        
        # Category-specific recommendations
        for category, services in categories.items():
            if services:
                category_availability = len([s for s in services if s.get('status') == 'operational']) / len(services) * 100
                if category_availability < 90:
                    recommendations.append(f"🔧 Focus attention on {category} services")
        
        # General recommendations
        if not hasattr(app, 'db_manager') or not app.db_manager:
            recommendations.append("📊 Enable database features for better insights")
        
        if not app.analytics:
            recommendations.append("🤖 Enable AI analytics for predictive insights")
        
        if availability >= 99:
            recommendations.append("✅ Continue current monitoring practices")
            recommendations.append("📈 Consider implementing proactive monitoring")
        
        # Display recommendations
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                app.presenter.present_message(f"{i}. {rec}")
        else:
            app.presenter.present_message("✅ No specific recommendations at this time")
        
        # Summary
        app.presenter.present_message("\n" + "=" * 50)
        app.presenter.present_message(f"💡 Insights analysis completed at {datetime.now().strftime('%H:%M:%S')}")
        app.presenter.present_message(f"📊 System Health: {health_status} ({availability:.1f}% availability)")
        app.presenter.present_message(f"🎯 Key Focus: {insight}")
        
    except Exception as e:
        app.presenter.present_error(f"Error generating system insights: {e}")
        logging.error(f"System insights error: {e}", exc_info=True)

def handle_trends(app, args):
    """Show availability trends and historical data"""
    app.presenter.present_message("\n📈 AVAILABILITY TRENDS")
    app.presenter.present_message("=" * 40)
    
    try:
        if not hasattr(app, 'db_manager') or not app.db_manager.is_enabled():
            app.presenter.present_message("❌ Database not available for trend analysis")
            return
        
        # Get historical data
        app.presenter.present_message("\n📊 Recent Status History:")
        recent_snapshots = app.db_manager.get_status_history(limit=10)
        
        if not recent_snapshots:
            app.presenter.present_message("  ℹ️ No historical data available")
            return
        
        # Display trend data
        total_availability = 0
        for i, snapshot in enumerate(recent_snapshots):
            timestamp = snapshot.get('timestamp', 'Unknown')
            availability = snapshot.get('availability_percentage', 0)
            total_services = snapshot.get('total_services', 0)
            operational = snapshot.get('operational_services', 0)
            
            # Format timestamp for display
            try:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                else:
                    time_str = str(timestamp)
            except:
                time_str = str(timestamp)
            
            status_emoji = "🟢" if availability >= 99.0 else "🟡" if availability >= 95.0 else "🔴"
            app.presenter.present_message(f"  {status_emoji} {time_str}: {availability:.1f}% ({operational}/{total_services})")
            total_availability += availability
        
        # Calculate average
        avg_availability = total_availability / len(recent_snapshots)
        app.presenter.present_message(f"\n📊 Average Availability (24h): {avg_availability:.1f}%")
        
        # Trend analysis
        if len(recent_snapshots) >= 2:
            latest = recent_snapshots[0].get('availability_percentage', 0)
            oldest = recent_snapshots[-1].get('availability_percentage', 0)
            trend = latest - oldest
            
            if abs(trend) < 0.1:
                trend_emoji = "➡️"
                trend_desc = "Stable"
            elif trend > 0:
                trend_emoji = "📈"
                trend_desc = f"Improving (+{trend:.1f}%)"
            else:
                trend_emoji = "📉"
                trend_desc = f"Declining ({trend:.1f}%)"
            
            app.presenter.present_message(f"🎯 Trend: {trend_emoji} {trend_desc}")
        
    except Exception as e:
        app.presenter.present_error(f"Error analyzing trends: {e}")

def handle_slo_dashboard(app, args):
    """Handle SLO dashboard display"""
    try:
        app.presenter.present_message("📊 SLO DASHBOARD")
        app.presenter.present_message("=" * 60)
        
        # Get SLO configuration - check if we have direct access to config dict
        if hasattr(app.config, 'config') and isinstance(app.config.config, dict):
            slo_config = app.config.config.get('slo', {})
        elif isinstance(app.config, dict):
            slo_config = app.config.get('slo', {})
        else:
            # Try to get individual config values
            slo_enabled = app._get_config_value('slo', 'enabled', False)
            if slo_enabled is None:
                slo_enabled = False
            slo_config = {
                'enabled': slo_enabled,
                'targets': {
                    'global_availability': 99.9,
                    'response_time': 2.0,
                    'uptime_monthly': 99.5
                },
                'tracking_period': 'monthly',
                'alert_on_breach': True
            }
        
        if not slo_config.get('enabled', False):
            app.presenter.present_message("⚠️  SLO tracking is disabled in configuration")
            return
        
        # Get SLO targets from config
        slo_targets = slo_config.get('targets', {})
        app.presenter.present_message(f"🎯 SLO TARGETS:")
        for metric, target in slo_targets.items():
            app.presenter.present_message(f"   • {metric.replace('_', ' ').title()}: {target}%")
        
        # Get current status data for analysis
        app.presenter.present_message("\n📈 Fetching current service status...")
        api_response = fetch_status_data(app.api_client)
        
        if not api_response.success or not api_response.data:
            app.presenter.present_message("❌ Could not fetch status data for SLO analysis")
            return
        
        status_data = api_response.data
        
        # Calculate current SLO metrics
        total_services = len(status_data.get('components', []))
        operational_services = len([c for c in status_data.get('components', []) 
                                   if c.get('status') == 'operational'])
        
        if total_services > 0:
            current_availability = (operational_services / total_services) * 100
        else:
            current_availability = 0
        
        app.presenter.present_message(f"\n📊 CURRENT SLO PERFORMANCE:")
        app.presenter.present_message(f"   • Global Availability: {current_availability:.2f}%")
        
        # Check against targets
        availability_target = slo_targets.get('global_availability', 99.9)
        if current_availability >= availability_target:
            status_emoji = "✅"
            status_text = "MEETING TARGET"
        else:
            status_emoji = "❌"
            status_text = "BELOW TARGET"
            
        app.presenter.present_message(f"   • Status: {status_emoji} {status_text} (Target: {availability_target}%)")
        
        # If analytics is available, get more detailed SLO analysis
        if app.analytics:
            app.presenter.present_message(f"\n🔍 DETAILED SLO ANALYSIS:")
            
            # Prepare data for SLO analysis
            analysis_data = []
            for component in status_data.get('components', []):
                analysis_data.append({
                    'name': component.get('name', 'Unknown'),
                    'status': component.get('status', 'unknown'),
                    'availability': 100.0 if component.get('status') == 'operational' else 0.0
                })
            
            # Generate SLO analysis
            slo_analysis = app.analytics.generate_slo_analysis(
                analysis_data, 
                availability_target
            )
            
            if slo_analysis:
                # Display SLO compliance
                compliance = slo_analysis.get('slo_compliance', {})
                for metric, value in compliance.items():
                    target = slo_targets.get(metric, 99.0)
                    status = "✅" if value >= target else "❌"
                    app.presenter.present_message(f"   • {metric.replace('_', ' ').title()}: {value:.1f}% {status}")
                
                # Display breach analysis if available
                breach_info = slo_analysis.get('breach_analysis', {})
                if breach_info:
                    app.presenter.present_message(f"\n⚠️  BREACH ANALYSIS:")
                    app.presenter.present_message(f"   • Total Breaches: {breach_info.get('total_breaches', 0)}")
                    app.presenter.present_message(f"   • Total Duration: {breach_info.get('breach_duration', 'N/A')}")
                    app.presenter.present_message(f"   • Most Affected: {breach_info.get('most_affected_service', 'N/A')}")
                
                # Display recommendations
                recommendations = slo_analysis.get('recommendations', [])
                if recommendations:
                    app.presenter.present_message(f"\n💡 RECOMMENDATIONS:")
                    for i, rec in enumerate(recommendations, 1):
                        app.presenter.present_message(f"   {i}. {rec}")
        else:
            app.presenter.present_message(f"\n💡 Enable AI analytics for detailed SLO analysis")
        
        # Display tracking period and alert settings
        tracking_period = slo_config.get('tracking_period', 'monthly')
        alert_on_breach = slo_config.get('alert_on_breach', False)
        
        app.presenter.present_message(f"\n⚙️  CONFIGURATION:")
        app.presenter.present_message(f"   • Tracking Period: {tracking_period.title()}")
        app.presenter.present_message(f"   • Alert on Breach: {'Enabled' if alert_on_breach else 'Disabled'}")
        
        app.presenter.present_message("\n" + "=" * 60)
        
    except Exception as e:
        app.presenter.present_error(f"Error displaying SLO dashboard: {e}")
        logging.error(f"SLO dashboard error: {e}", exc_info=True)

def handle_export_ai_report(app, args):
    """Generate and export comprehensive AI analysis report"""
    try:
        app.presenter.present_message("📊 GENERATING AI ANALYSIS REPORT")
        app.presenter.present_message("=" * 50)
        
        # Check if AI analytics is available
        if not app.analytics:
            app.presenter.present_error("AI Analytics not available (enterprise feature disabled)")
            app.presenter.present_message("💡 Enable AI analytics in config.json to use this feature")
            return
        
        # Get current status data
        app.presenter.present_message("\n📈 Fetching current service status...")
        api_response = fetch_status_data(app.api_client)
        
        if not api_response.success or not api_response.data:
            app.presenter.present_error("Failed to fetch status data for AI analysis")
            return
        
        status_data = api_response.data
        health_metrics = app.api_client.get_service_health_metrics(status_data)
        
        # Generate timestamp for file naming
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Ensure output directory exists
        output_dir = getattr(args, 'output', '.')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate comprehensive AI analysis
        app.presenter.present_message("\n🤖 Running AI analysis...")
        
        ai_report = {
            'metadata': {
                'report_type': 'AI Analysis Report',
                'generated_at': datetime.now().isoformat(),
                'version': '3.1.0',
                'data_source': 'Red Hat Status API'
            },
            'executive_summary': {},
            'current_status': health_metrics,
            'ai_insights': {},
            'anomaly_analysis': {},
            'predictive_analysis': {},
            'slo_analysis': {},
            'recommendations': [],
            'raw_data': status_data
        }
        
        # Executive Summary
        app.presenter.present_message("   • Generating executive summary...")
        ai_report['executive_summary'] = {
            'overall_health_score': health_metrics.get('availability_percentage', 0),
            'total_services': health_metrics.get('total_services', 0),
            'operational_services': health_metrics.get('operational_services', 0),
            'services_with_issues': health_metrics.get('services_with_issues', 0),
            'report_timestamp': datetime.now().isoformat(),
            'status_indicator': health_metrics.get('status_indicator', 'unknown')
        }
        
        # AI Insights
        app.presenter.present_message("   • Analyzing service patterns...")
        try:
            # Generate health score analysis
            health_score_data = app.analytics.generate_health_score(status_data)
            ai_report['ai_insights']['health_score_analysis'] = health_score_data or "No health score data available"
            
            # Service pattern analysis
            service_patterns = []
            components = status_data.get('components', [])
            for component in components[:10]:  # Analyze top 10 services
                pattern = {
                    'name': component.get('name', 'Unknown'),
                    'status': component.get('status', 'unknown'),
                    'reliability_score': 100.0 if component.get('status') == 'operational' else 0.0
                }
                service_patterns.append(pattern)
            
            ai_report['ai_insights']['service_patterns'] = service_patterns
            
        except Exception as e:
            ai_report['ai_insights']['error'] = f"Failed to generate insights: {e}"
        
        # Anomaly Analysis
        app.presenter.present_message("   • Performing anomaly detection...")
        try:
            if hasattr(app, 'db_manager') and app.db_manager and hasattr(app.db_manager, 'is_enabled') and app.db_manager.is_enabled():
                historical_data = app.db_manager.get_status_history(limit=50)
                if historical_data:
                    anomalies = app.analytics.detect_anomalies(historical_data)
                    ai_report['anomaly_analysis'] = {
                        'analysis_performed': True,
                        'data_points_analyzed': len(historical_data),
                        'results': anomalies
                    }
                else:
                    ai_report['anomaly_analysis'] = {
                        'analysis_performed': False,
                        'reason': 'No historical data available'
                    }
            else:
                ai_report['anomaly_analysis'] = {
                    'analysis_performed': False,
                    'reason': 'Database not available for historical analysis'
                }
        except Exception as e:
            ai_report['anomaly_analysis'] = {
                'analysis_performed': False,
                'error': str(e)
            }
        
        # Predictive Analysis
        app.presenter.present_message("   • Generating predictions...")
        try:
            predictions = app.analytics.generate_predictions("Red Hat Services", hours_ahead=24)
            ai_report['predictive_analysis'] = {
                'forecast_horizon': '24 hours',
                'predictions': predictions if predictions else []
            }
        except Exception as e:
            ai_report['predictive_analysis'] = {
                'error': f"Prediction generation failed: {e}"
            }
        
        # SLO Analysis
        app.presenter.present_message("   • Analyzing SLO compliance...")
        try:
            # Get SLO configuration
            if hasattr(app.config, 'config') and isinstance(app.config.config, dict):
                slo_config = app.config.config.get('slo', {})
            elif isinstance(app.config, dict):
                slo_config = app.config.get('slo', {})
            else:
                slo_config = {'enabled': False}
            
            if slo_config.get('enabled', False):
                slo_targets = slo_config.get('targets', {})
                availability_target = slo_targets.get('global_availability', 99.9)
                
                # Prepare data for SLO analysis
                analysis_data = []
                for component in status_data.get('components', []):
                    analysis_data.append({
                        'name': component.get('name', 'Unknown'),
                        'status': component.get('status', 'unknown'),
                        'availability': 100.0 if component.get('status') == 'operational' else 0.0
                    })
                
                slo_analysis = app.analytics.generate_slo_analysis(analysis_data, availability_target)
                ai_report['slo_analysis'] = {
                    'enabled': True,
                    'targets': slo_targets,
                    'current_performance': {
                        'global_availability': health_metrics.get('availability_percentage', 0)
                    },
                    'detailed_analysis': slo_analysis
                }
            else:
                ai_report['slo_analysis'] = {
                    'enabled': False,
                    'reason': 'SLO tracking disabled in configuration'
                }
        except Exception as e:
            ai_report['slo_analysis'] = {
                'error': f"SLO analysis failed: {e}"
            }
        
        # Generate Recommendations
        app.presenter.present_message("   • Generating recommendations...")
        recommendations = []
        
        # Health-based recommendations
        availability = health_metrics.get('availability_percentage', 0)
        if availability < 95:
            recommendations.append({
                'category': 'Critical',
                'title': 'Address Service Availability Issues',
                'description': f'Current availability ({availability:.1f}%) is below acceptable thresholds',
                'priority': 'High'
            })
        elif availability < 99:
            recommendations.append({
                'category': 'Optimization',
                'title': 'Improve Service Reliability',
                'description': f'Availability could be improved from {availability:.1f}%',
                'priority': 'Medium'
            })
        
        # Monitoring recommendations
        recommendations.append({
            'category': 'Monitoring',
            'title': 'Enhance Monitoring Coverage',
            'description': 'Consider implementing more comprehensive monitoring and alerting',
            'priority': 'Medium'
        })
        
        # Analytics recommendations
        if not hasattr(app, 'db_manager') or not app.db_manager:
            recommendations.append({
                'category': 'Analytics',
                'title': 'Enable Historical Data Collection',
                'description': 'Enable database features for better trend analysis and anomaly detection',
                'priority': 'Low'
            })
        
        ai_report['recommendations'] = recommendations
        
        # Export to JSON file
        json_filename = os.path.join(output_dir, f"ai_analysis_report_{timestamp}.json")
        app.presenter.present_message(f"\n💾 Exporting JSON report...")
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(ai_report, f, indent=2, ensure_ascii=False, default=str)
        
        # Export to human-readable report
        txt_filename = os.path.join(output_dir, f"ai_analysis_report_{timestamp}.txt")
        app.presenter.present_message(f"📋 Generating human-readable report...")
        
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write("RED HAT STATUS AI ANALYSIS REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            # Executive Summary
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 20 + "\n")
            exec_summary = ai_report['executive_summary']
            f.write(f"Report Generated: {exec_summary['report_timestamp']}\n")
            f.write(f"Overall Health Score: {exec_summary['overall_health_score']:.1f}%\n")
            f.write(f"Total Services: {exec_summary['total_services']}\n")
            f.write(f"Operational Services: {exec_summary['operational_services']}\n")
            f.write(f"Services with Issues: {exec_summary['services_with_issues']}\n")
            f.write(f"Status Indicator: {exec_summary['status_indicator']}\n\n")
            
            # Current Status
            f.write("CURRENT STATUS DETAILS\n")
            f.write("-" * 25 + "\n")
            f.write(f"Page: {health_metrics.get('page_name', 'Unknown')}\n")
            f.write(f"Last Updated: {health_metrics.get('last_updated', 'Unknown')}\n")
            f.write(f"Overall Status: {health_metrics.get('overall_status', 'Unknown')}\n\n")
            
            # AI Insights
            f.write("AI INSIGHTS\n")
            f.write("-" * 15 + "\n")
            insights = ai_report['ai_insights']
            if 'health_score_analysis' in insights:
                f.write(f"Health Score Analysis: {insights['health_score_analysis']}\n")
            
            if 'service_patterns' in insights:
                f.write(f"\nService Pattern Analysis:\n")
                for pattern in insights['service_patterns'][:5]:
                    f.write(f"  • {pattern['name']}: {pattern['status']} (Reliability: {pattern['reliability_score']:.1f}%)\n")
            f.write("\n")
            
            # Anomaly Analysis
            f.write("ANOMALY ANALYSIS\n")
            f.write("-" * 20 + "\n")
            anomaly_info = ai_report['anomaly_analysis']
            if anomaly_info.get('analysis_performed', False):
                f.write(f"Data Points Analyzed: {anomaly_info.get('data_points_analyzed', 0)}\n")
                results = anomaly_info.get('results', {})
                if isinstance(results, dict) and 'anomaly_count' in results:
                    f.write(f"Anomalies Detected: {results['anomaly_count']}\n")
                elif isinstance(results, list):
                    f.write(f"Anomalies Detected: {len(results)}\n")
            else:
                f.write(f"Analysis Status: Not performed - {anomaly_info.get('reason', 'Unknown reason')}\n")
            f.write("\n")
            
            # SLO Analysis
            f.write("SLO COMPLIANCE ANALYSIS\n")
            f.write("-" * 25 + "\n")
            slo_info = ai_report['slo_analysis']
            if slo_info.get('enabled', False):
                f.write("SLO Tracking: Enabled\n")
                targets = slo_info.get('targets', {})
                for metric, target in targets.items():
                    f.write(f"  • {metric.replace('_', ' ').title()}: {target}%\n")
                
                current_perf = slo_info.get('current_performance', {})
                current_avail = current_perf.get('global_availability', 0)
                f.write(f"\nCurrent Performance:\n")
                f.write(f"  • Global Availability: {current_avail:.2f}%\n")
            else:
                f.write(f"SLO Tracking: Disabled - {slo_info.get('reason', 'Unknown reason')}\n")
            f.write("\n")
            
            # Recommendations
            f.write("RECOMMENDATIONS\n")
            f.write("-" * 15 + "\n")
            for i, rec in enumerate(ai_report['recommendations'], 1):
                f.write(f"{i}. [{rec['priority']}] {rec['title']}\n")
                f.write(f"   Category: {rec['category']}\n")
                f.write(f"   Description: {rec['description']}\n\n")
            
            f.write(f"\nReport generated by Red Hat Status Checker v3.1.0\n")
            f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Display results
        app.presenter.present_message(f"\n✅ AI Analysis Report Generated Successfully!")
        app.presenter.present_message("=" * 50)
        
        json_size = os.path.getsize(json_filename) / 1024
        txt_size = os.path.getsize(txt_filename) / 1024
        
        app.presenter.present_message(f"📄 JSON Report: {json_filename}")
        app.presenter.present_message(f"   Size: {json_size:.1f} KB")
        
        app.presenter.present_message(f"📋 Text Report: {txt_filename}")
        app.presenter.present_message(f"   Size: {txt_size:.1f} KB")
        
        app.presenter.present_message(f"\n📊 Report Summary:")
        app.presenter.present_message(f"   • Services Analyzed: {health_metrics.get('total_services', 0)}")
        app.presenter.present_message(f"   • Health Score: {health_metrics.get('availability_percentage', 0):.1f}%")
        app.presenter.present_message(f"   • Recommendations: {len(recommendations)}")
        app.presenter.present_message(f"   • Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        app.presenter.present_message("\n" + "=" * 50)
        
    except Exception as e:
        app.presenter.present_error(f"Error generating AI report: {e}")
        logging.error(f"AI report generation error: {e}", exc_info=True)

def handle_export_history(app, args):
    """Export historical data to files in various formats"""
    try:
        app.presenter.present_message("📂 HISTORICAL DATA EXPORT")
        app.presenter.present_message("=" * 50)
        
        # Check if database is available for historical data
        if not hasattr(app, 'db_manager') or not app.db_manager:
            app.presenter.present_error("Database not available for historical data export")
            app.presenter.present_message("💡 Enable database features in config.json to collect historical data")
            return
        
        if not hasattr(app.db_manager, 'is_enabled') or not app.db_manager.is_enabled():
            app.presenter.present_error("Database is not enabled for historical data export")
            app.presenter.present_message("💡 Enable database in config.json and run some status checks first")
            return
        
        # Get export format from args
        export_format = getattr(args, 'format', 'json').lower()
        if export_format not in ['json', 'csv', 'txt']:
            export_format = 'json'
        
        # Ensure output directory exists
        output_dir = getattr(args, 'output', '.')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp for file naming
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        app.presenter.present_message(f"\n📊 Collecting historical data...")
        app.presenter.present_message(f"📁 Output directory: {output_dir}")
        app.presenter.present_message(f"📄 Export format: {export_format.upper()}")
        
        # Get historical data
        try:
            # Get comprehensive historical data
            app.presenter.present_message("\n🔍 Fetching status history...")
            status_history = app.db_manager.get_status_history(limit=1000)  # Get up to 1000 records
            
            if not status_history:
                app.presenter.present_message("⚠️ No historical status data found")
                app.presenter.present_message("💡 Run some status checks (quick/simple/full) to collect data first")
                return
            
            app.presenter.present_message(f"✅ Found {len(status_history)} status records")
            
            # Get analytics history if available
            analytics_history = []
            if hasattr(app.db_manager, 'get_analytics_history'):
                try:
                    app.presenter.present_message("🔍 Fetching analytics history...")
                    analytics_history = app.db_manager.get_analytics_history(limit=500)
                    if analytics_history:
                        app.presenter.present_message(f"✅ Found {len(analytics_history)} analytics records")
                    else:
                        app.presenter.present_message("ℹ️ No analytics history available")
                except Exception as e:
                    app.presenter.present_message(f"⚠️ Could not fetch analytics history: {e}")
            
            # Get notification history if available
            notification_history = []
            if hasattr(app.db_manager, 'get_notification_history'):
                try:
                    app.presenter.present_message("🔍 Fetching notification history...")
                    notification_history = app.db_manager.get_notification_history(limit=200)
                    if notification_history:
                        app.presenter.present_message(f"✅ Found {len(notification_history)} notification records")
                    else:
                        app.presenter.present_message("ℹ️ No notification history available")
                except Exception as e:
                    app.presenter.present_message(f"⚠️ Could not fetch notification history: {e}")
            
        except Exception as e:
            app.presenter.present_error(f"Error fetching historical data: {e}")
            return
        
        # Prepare comprehensive export data
        export_data = {
            'metadata': {
                'export_type': 'Historical Data Export',
                'generated_at': datetime.now().isoformat(),
                'version': '3.1.0',
                'format': export_format,
                'total_records': len(status_history) + len(analytics_history) + len(notification_history)
            },
            'status_history': status_history,
            'analytics_history': analytics_history,
            'notification_history': notification_history,
            'summary': {}
        }
        
        # Generate summary statistics
        app.presenter.present_message("\n📈 Generating export summary...")
        
        summary = {
            'data_overview': {
                'status_records': len(status_history),
                'analytics_records': len(analytics_history),
                'notification_records': len(notification_history),
                'date_range': {},
                'availability_stats': {}
            },
            'trends': {},
            'service_statistics': {}
        }
        
        # Calculate date range
        if status_history:
            timestamps = [record.get('timestamp') for record in status_history if record.get('timestamp')]
            if timestamps:
                # Handle both string and datetime timestamps
                parsed_timestamps = []
                for ts in timestamps:
                    try:
                        if isinstance(ts, str):
                            parsed_ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        else:
                            parsed_ts = ts
                        parsed_timestamps.append(parsed_ts)
                    except:
                        continue
                
                if parsed_timestamps:
                    earliest = min(parsed_timestamps)
                    latest = max(parsed_timestamps)
                    summary['data_overview']['date_range'] = {
                        'earliest': earliest.isoformat(),
                        'latest': latest.isoformat(),
                        'span_days': (latest - earliest).days
                    }
        
        # Calculate availability statistics
        if status_history:
            availabilities = [record.get('availability_percentage', 0) for record in status_history]
            if availabilities:
                summary['data_overview']['availability_stats'] = {
                    'average': sum(availabilities) / len(availabilities),
                    'minimum': min(availabilities),
                    'maximum': max(availabilities),
                    'latest': availabilities[0] if availabilities else 0
                }
        
        # Calculate service statistics
        service_counts = {}
        issue_counts = {}
        for record in status_history:
            total_services = record.get('total_services', 0)
            services_with_issues = record.get('services_with_issues', 0)
            
            if total_services > 0:
                if total_services not in service_counts:
                    service_counts[total_services] = 0
                service_counts[total_services] += 1
            
            if services_with_issues > 0:
                if services_with_issues not in issue_counts:
                    issue_counts[services_with_issues] = 0
                issue_counts[services_with_issues] += 1
        
        summary['service_statistics'] = {
            'most_common_service_count': max(service_counts.items(), key=lambda x: x[1])[0] if service_counts else 0,
            'total_issue_occurrences': sum(issue_counts.values()),
            'max_concurrent_issues': max(issue_counts.keys()) if issue_counts else 0
        }
        
        export_data['summary'] = summary
        
        # Export in the requested format
        app.presenter.present_message(f"\n💾 Exporting data in {export_format.upper()} format...")
        
        if export_format == 'json':
            # Export to JSON
            filename = os.path.join(output_dir, f"redhat_status_history_{timestamp}.json")
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            file_size = os.path.getsize(filename) / 1024
            app.presenter.present_message(f"📄 JSON Export: {filename}")
            app.presenter.present_message(f"   Size: {file_size:.1f} KB")
            
        elif export_format == 'csv':
            # Export to CSV files (separate files for different data types)
            
            # Status history CSV
            status_csv = os.path.join(output_dir, f"redhat_status_history_{timestamp}.csv")
            app.presenter.present_message("📊 Creating status history CSV...")
            
            with open(status_csv, 'w', newline='', encoding='utf-8') as f:
                if status_history:
                    writer = csv.DictWriter(f, fieldnames=status_history[0].keys())
                    writer.writeheader()
                    writer.writerows(status_history)
            
            # Analytics history CSV (if available)
            if analytics_history:
                analytics_csv = os.path.join(output_dir, f"redhat_analytics_history_{timestamp}.csv")
                app.presenter.present_message("📊 Creating analytics history CSV...")
                
                with open(analytics_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=analytics_history[0].keys())
                    writer.writeheader()
                    writer.writerows(analytics_history)
            
            # Notification history CSV (if available)
            if notification_history:
                notification_csv = os.path.join(output_dir, f"redhat_notifications_history_{timestamp}.csv")
                app.presenter.present_message("📊 Creating notification history CSV...")
                
                with open(notification_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=notification_history[0].keys())
                    writer.writeheader()
                    writer.writerows(notification_history)
            
            # Summary CSV
            summary_csv = os.path.join(output_dir, f"redhat_summary_{timestamp}.csv")
            app.presenter.present_message("📊 Creating summary CSV...")
            
            with open(summary_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Metric', 'Value'])
                writer.writerow(['Total Status Records', len(status_history)])
                writer.writerow(['Total Analytics Records', len(analytics_history)])
                writer.writerow(['Total Notification Records', len(notification_history)])
                
                if summary['data_overview']['availability_stats']:
                    stats = summary['data_overview']['availability_stats']
                    writer.writerow(['Average Availability', f"{stats['average']:.2f}%"])
                    writer.writerow(['Minimum Availability', f"{stats['minimum']:.2f}%"])
                    writer.writerow(['Maximum Availability', f"{stats['maximum']:.2f}%"])
                    writer.writerow(['Latest Availability', f"{stats['latest']:.2f}%"])
            
            status_size = os.path.getsize(status_csv) / 1024
            app.presenter.present_message(f"📄 Status CSV: {status_csv} ({status_size:.1f} KB)")
            
            if analytics_history:
                analytics_size = os.path.getsize(analytics_csv) / 1024
                app.presenter.present_message(f"📄 Analytics CSV: {analytics_csv} ({analytics_size:.1f} KB)")
            
            if notification_history:
                notification_size = os.path.getsize(notification_csv) / 1024
                app.presenter.present_message(f"📄 Notifications CSV: {notification_csv} ({notification_size:.1f} KB)")
            
            summary_size = os.path.getsize(summary_csv) / 1024
            app.presenter.present_message(f"📄 Summary CSV: {summary_csv} ({summary_size:.1f} KB)")
            
        elif export_format == 'txt':
            # Export to human-readable text file
            filename = os.path.join(output_dir, f"redhat_status_history_{timestamp}.txt")
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("RED HAT STATUS CHECKER - HISTORICAL DATA EXPORT\n")
                f.write("=" * 60 + "\n\n")
                
                # Metadata
                f.write("EXPORT INFORMATION\n")
                f.write("-" * 20 + "\n")
                f.write(f"Generated: {export_data['metadata']['generated_at']}\n")
                f.write(f"Version: {export_data['metadata']['version']}\n")
                f.write(f"Total Records: {export_data['metadata']['total_records']}\n\n")
                
                # Summary
                f.write("DATA SUMMARY\n")
                f.write("-" * 15 + "\n")
                f.write(f"Status Records: {summary['data_overview']['status_records']}\n")
                f.write(f"Analytics Records: {summary['data_overview']['analytics_records']}\n")
                f.write(f"Notification Records: {summary['data_overview']['notification_records']}\n\n")
                
                # Date range
                if summary['data_overview']['date_range']:
                    date_range = summary['data_overview']['date_range']
                    f.write("DATE RANGE\n")
                    f.write("-" * 10 + "\n")
                    f.write(f"Earliest Record: {date_range['earliest']}\n")
                    f.write(f"Latest Record: {date_range['latest']}\n")
                    f.write(f"Time Span: {date_range['span_days']} days\n\n")
                
                # Availability statistics
                if summary['data_overview']['availability_stats']:
                    stats = summary['data_overview']['availability_stats']
                    f.write("AVAILABILITY STATISTICS\n")
                    f.write("-" * 25 + "\n")
                    f.write(f"Average: {stats['average']:.2f}%\n")
                    f.write(f"Minimum: {stats['minimum']:.2f}%\n")
                    f.write(f"Maximum: {stats['maximum']:.2f}%\n")
                    f.write(f"Latest: {stats['latest']:.2f}%\n\n")
                
                # Recent status history (last 20 records)
                f.write("RECENT STATUS HISTORY (Last 20 Records)\n")
                f.write("-" * 45 + "\n")
                for i, record in enumerate(status_history[:20]):
                    timestamp_str = record.get('timestamp', 'Unknown')
                    availability = record.get('availability_percentage', 0)
                    total_services = record.get('total_services', 0)
                    operational = record.get('operational_services', 0)
                    
                    status_emoji = "🟢" if availability >= 99 else "🟡" if availability >= 95 else "🔴"
                    f.write(f"{i+1:2d}. {status_emoji} {timestamp_str}: {availability:.1f}% ({operational}/{total_services})\n")
                
                if len(status_history) > 20:
                    f.write(f"\n... and {len(status_history) - 20} more records\n")
                
                f.write(f"\nExport completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            file_size = os.path.getsize(filename) / 1024
            app.presenter.present_message(f"📄 Text Export: {filename}")
            app.presenter.present_message(f"   Size: {file_size:.1f} KB")
        
        # Display export summary
        app.presenter.present_message("\n✅ EXPORT COMPLETED SUCCESSFULLY!")
        app.presenter.present_message("=" * 50)
        
        app.presenter.present_message(f"📊 Export Summary:")
        app.presenter.present_message(f"   • Status Records: {len(status_history)}")
        if analytics_history:
            app.presenter.present_message(f"   • Analytics Records: {len(analytics_history)}")
        if notification_history:
            app.presenter.present_message(f"   • Notification Records: {len(notification_history)}")
        
        if summary['data_overview']['date_range']:
            date_range = summary['data_overview']['date_range']
            app.presenter.present_message(f"   • Data Span: {date_range['span_days']} days")
        
        if summary['data_overview']['availability_stats']:
            stats = summary['data_overview']['availability_stats']
            app.presenter.present_message(f"   • Average Availability: {stats['average']:.1f}%")
        
        app.presenter.present_message(f"   • Export Format: {export_format.upper()}")
        app.presenter.present_message(f"   • Output Directory: {output_dir}")
        app.presenter.present_message(f"   • Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Provide usage recommendations
        app.presenter.present_message(f"\n💡 USAGE RECOMMENDATIONS:")
        app.presenter.present_message("   • Use JSON format for programmatic analysis")
        app.presenter.present_message("   • Use CSV format for spreadsheet analysis")
        app.presenter.present_message("   • Use TXT format for human-readable reports")
        app.presenter.present_message("   • Consider archiving old exports to save space")
        
        app.presenter.present_message("\n" + "=" * 50)
        
    except Exception as e:
        app.presenter.present_error(f"Error exporting historical data: {e}")
        logging.error(f"Historical data export error: {e}", exc_info=True)

def handle_watch(app, args):
    app.presenter.present_message(f"👁️  LIVE MONITORING MODE (refresh every {args.watch}s)")
    app.presenter.present_message("Press Ctrl+C to stop...")
    try:
        while True:
            # In watch mode, we perform a quiet quick check.
            # This will also update the exporter if it's enabled.
            os.system('clear' if os.name == 'posix' else 'cls')
            app.presenter.present_message(f"🔄 Live Monitor - {datetime.now().strftime('%H:%M:%S')}")
            app.presenter.present_message("=" * 40)
            app.quick_status_check(quiet_mode=True)
            time.sleep(args.watch)
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped")

def handle_notify(app, args):
    """Send notifications for current service status"""
    try:
        app.presenter.present_message("📢 NOTIFICATION SYSTEM")
        app.presenter.present_message("=" * 40)
        
        # Check if notification system is available
        if not app.notification_manager:
            app.presenter.present_error("Notification system not available (enterprise feature disabled)")
            app.presenter.present_message("💡 Enable notifications in config.json to use this feature")
            return
        
        # Get current status data
        app.presenter.present_message("\n📊 Fetching current service status...")
        api_response = fetch_status_data(app.api_client)
        
        if not api_response.success or not api_response.data:
            app.presenter.present_error("Failed to fetch status data for notifications")
            return
        
        status_data = api_response.data
        health_metrics = app.api_client.get_service_health_metrics(status_data)
        
        # Analyze status for notification urgency
        app.presenter.present_message("🔍 Analyzing status for notification urgency...")
        
        availability = health_metrics.get('availability_percentage', 0)
        services_with_issues = health_metrics.get('services_with_issues', 0)
        total_services = health_metrics.get('total_services', 0)
        overall_status = health_metrics.get('overall_status', 'unknown')
        
        # Determine notification priority and content
        if availability < 90:
            priority = "critical"
            urgency = "🚨 CRITICAL"
            status_emoji = "🔴"
        elif availability < 95:
            priority = "high"
            urgency = "⚠️ HIGH"
            status_emoji = "🟡"
        elif availability < 99:
            priority = "medium" 
            urgency = "📋 MEDIUM"
            status_emoji = "🟡"
        else:
            priority = "low"
            urgency = "✅ LOW"
            status_emoji = "🟢"
        
        app.presenter.present_message(f"📊 Status Analysis Complete:")
        app.presenter.present_message(f"   • Overall Availability: {availability:.1f}%")
        app.presenter.present_message(f"   • Services with Issues: {services_with_issues}/{total_services}")
        app.presenter.present_message(f"   • Notification Priority: {urgency}")
        
        # Prepare notification content
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Create subject line
        subject = f"Red Hat Services Status Alert - {urgency.split()[1]} Priority"
        
        # Create detailed message body
        message_lines = [
            f"🎯 Red Hat Services Status Report",
            f"⏰ Generated: {timestamp}",
            f"",
            f"📊 SUMMARY:",
            f"{status_emoji} Overall Availability: {availability:.1f}%",
            f"📋 Total Services: {total_services}",
            f"✅ Operational Services: {health_metrics.get('operational_services', 0)}",
            f"⚠️ Services with Issues: {services_with_issues}",
            f"🏷️ Overall Status: {overall_status}",
            f"",
            f"🔍 DETAILS:",
        ]
        
        # Add service-specific details
        components = status_data.get('components', [])
        issue_services = [c for c in components if c.get('status') != 'operational']
        
        if issue_services:
            message_lines.append(f"⚠️ Services with Issues ({len(issue_services)}):")
            for service in issue_services[:10]:  # Limit to first 10 issues
                service_name = service.get('name', 'Unknown Service')
                service_status = service.get('status', 'unknown')
                status_icon = "🔴" if 'major' in service_status else "🟡" if 'degraded' in service_status else "⚠️"
                message_lines.append(f"   {status_icon} {service_name}: {service_status}")
            
            if len(issue_services) > 10:
                message_lines.append(f"   ... and {len(issue_services) - 10} more services")
        else:
            message_lines.append("✅ All services are operational")
        
        # Add trending information if available
        if hasattr(app, 'db_manager') and app.db_manager and hasattr(app.db_manager, 'is_enabled') and app.db_manager.is_enabled():
            try:
                recent_snapshots = app.db_manager.get_status_history(limit=5)
                if len(recent_snapshots) >= 2:
                    latest_avail = recent_snapshots[0].get('availability_percentage', 0)
                    previous_avail = recent_snapshots[1].get('availability_percentage', 0)
                    trend = latest_avail - previous_avail
                    
                    message_lines.append("")
                    message_lines.append("📈 TREND ANALYSIS:")
                    if abs(trend) < 0.1:
                        message_lines.append("➡️ Status: Stable (no significant change)")
                    elif trend > 0:
                        message_lines.append(f"📈 Status: Improving (+{trend:.1f}% availability)")
                    else:
                        message_lines.append(f"📉 Status: Declining ({trend:.1f}% availability)")
            except Exception as e:
                message_lines.append("")
                message_lines.append(f"⚠️ Trend analysis unavailable: {e}")
        
        # Add recommendations based on status
        message_lines.append("")
        message_lines.append("💡 RECOMMENDATIONS:")
        
        if availability < 95:
            message_lines.append("   • Immediate attention required for service issues")
            message_lines.append("   • Review affected services and escalate if needed")
            message_lines.append("   • Monitor closely for further degradation")
        elif availability < 99:
            message_lines.append("   • Monitor affected services for resolution")
            message_lines.append("   • Consider preventive measures")
        else:
            message_lines.append("   • Continue normal monitoring")
            message_lines.append("   • All systems operating within normal parameters")
        
        message_lines.append("")
        message_lines.append("🔗 For more details, check: https://status.redhat.com/")
        message_lines.append("")
        message_lines.append("Generated by Red Hat Status Checker v3.1.0")
        
        message_body = "\n".join(message_lines)
        
        # Prepare notification data
        notification_data = {
            'subject': subject,
            'message': message_body,
            'priority': priority,
            'urgency': urgency,
            'availability': availability,
            'services_with_issues': services_with_issues,
            'total_services': total_services,
            'timestamp': timestamp,
            'status_data': {
                'overall_status': overall_status,
                'page_name': health_metrics.get('page_name', 'Red Hat Status'),
                'last_updated': health_metrics.get('last_updated', 'Unknown')
            }
        }
        
        # Send notifications through all enabled channels
        app.presenter.present_message("\n📤 Sending notifications...")
        
        try:
            # Get notification configuration
            if hasattr(app.config, 'config') and isinstance(app.config.config, dict):
                notification_config = app.config.config.get('notifications', {})
            elif isinstance(app.config, dict):
                notification_config = app.config.get('notifications', {})
            else:
                notification_config = {}
            
            # Track results
            sent_notifications = []
            failed_notifications = []
            
            # Send email notifications
            email_config = notification_config.get('email', {})
            if email_config.get('enabled', False):
                app.presenter.present_message("   📧 Sending email notification...")
                try:
                    email_result = app.notification_manager.send_email(
                        subject=subject,
                        message=message_body,
                        priority=priority
                    )
                    if email_result:
                        sent_notifications.append("Email")
                        app.presenter.present_message("      ✅ Email sent successfully")
                    else:
                        failed_notifications.append("Email")
                        app.presenter.present_message("      ❌ Email failed to send")
                except Exception as e:
                    failed_notifications.append("Email")
                    app.presenter.present_message(f"      ❌ Email error: {e}")
            else:
                app.presenter.present_message("   📧 Email notifications disabled")
            
            # Send webhook notifications
            webhook_config = notification_config.get('webhooks', {})
            if webhook_config.get('enabled', False):
                app.presenter.present_message("   🔗 Sending webhook notification...")
                try:
                    webhook_result = app.notification_manager.send_webhook(notification_data)
                    if webhook_result:
                        sent_notifications.append("Webhook")
                        app.presenter.present_message("      ✅ Webhook sent successfully")
                    else:
                        failed_notifications.append("Webhook")
                        app.presenter.present_message("      ❌ Webhook failed to send")
                except Exception as e:
                    failed_notifications.append("Webhook")
                    app.presenter.present_message(f"      ❌ Webhook error: {e}")
            else:
                app.presenter.present_message("   🔗 Webhook notifications disabled")
            
            # Send Slack notifications
            slack_config = notification_config.get('slack', {})
            if slack_config.get('enabled', False):
                app.presenter.present_message("   💬 Sending Slack notification...")
                try:
                    slack_result = app.notification_manager.send_slack(
                        message=message_body,
                        priority=priority
                    )
                    if slack_result:
                        sent_notifications.append("Slack")
                        app.presenter.present_message("      ✅ Slack sent successfully")
                    else:
                        failed_notifications.append("Slack")
                        app.presenter.present_message("      ❌ Slack failed to send")
                except Exception as e:
                    failed_notifications.append("Slack")
                    app.presenter.present_message(f"      ❌ Slack error: {e}")
            else:
                app.presenter.present_message("   💬 Slack notifications disabled")
            
            # Display summary
            app.presenter.present_message("\n📊 NOTIFICATION SUMMARY")
            app.presenter.present_message("-" * 30)
            
            if sent_notifications:
                app.presenter.present_message(f"✅ Successfully sent: {', '.join(sent_notifications)}")
            
            if failed_notifications:
                app.presenter.present_message(f"❌ Failed to send: {', '.join(failed_notifications)}")
            
            if not sent_notifications and not failed_notifications:
                app.presenter.present_message("ℹ️ No notification channels enabled")
                app.presenter.present_message("💡 Enable email, webhook, or Slack in config.json")
            
            # Store notification in database if available
            if hasattr(app, 'db_manager') and app.db_manager and hasattr(app.db_manager, 'is_enabled') and app.db_manager.is_enabled():
                try:
                    app.db_manager.log_notification(
                        priority=priority,
                        channels_sent=sent_notifications,
                        channels_failed=failed_notifications,
                        availability=availability,
                        services_affected=services_with_issues
                    )
                    app.presenter.present_message("💾 Notification logged to database")
                except Exception as e:
                    app.presenter.present_message(f"⚠️ Failed to log notification: {e}")
            
        except Exception as e:
            app.presenter.present_error(f"Error during notification sending: {e}")
        
        app.presenter.present_message("\n" + "=" * 40)
        app.presenter.present_message(f"📢 Notification process completed at {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        app.presenter.present_error(f"Error in notification handler: {e}")
        logging.error(f"Notification handler error: {e}", exc_info=True)

def handle_benchmark(app, args):
    """Run performance benchmark tests"""
    app.presenter.present_message("\n🏁 PERFORMANCE BENCHMARK")
    app.presenter.present_message("=" * 40)
    
    try:
        import time
        
        # Test API response time
        app.presenter.present_message("\n🌐 API Response Time Test:")
        
        for i in range(3):
            start_time = time.time()
            response = fetch_status_data()
            duration = time.time() - start_time
            
            if response.success:
                status_emoji = "✅"
                result = f"Success ({duration:.3f}s)"
            else:
                status_emoji = "❌"
                result = f"Failed ({duration:.3f}s)"
            
            app.presenter.present_message(f"  Test {i+1}: {status_emoji} {result}")
        
        # Test database operations if available
        if hasattr(app, 'db_manager') and app.db_manager.is_enabled():
            app.presenter.present_message("\n💾 Database Performance Test:")
            
            # Test write operation
            start_time = time.time()
            try:
                test_data = {
                    'page_name': 'Benchmark Test',
                    'overall_status': 'test',
                    'total_services': 0,
                    'operational_services': 0,
                    'availability_percentage': 100.0
                }
                app.db_manager.save_service_snapshot(test_data, [])
                write_time = time.time() - start_time
                app.presenter.present_message(f"  Write Test: ✅ Success ({write_time:.3f}s)")
            except Exception as e:
                write_time = time.time() - start_time
                app.presenter.present_message(f"  Write Test: ❌ Failed ({write_time:.3f}s) - {e}")
            
            # Test read operation
            start_time = time.time()
            try:
                snapshots = app.db_manager.get_status_history(limit=5)
                read_time = time.time() - start_time
                app.presenter.present_message(f"  Read Test: ✅ Success ({read_time:.3f}s) - {len(snapshots)} records")
            except Exception as e:
                read_time = time.time() - start_time
                app.presenter.present_message(f"  Read Test: ❌ Failed ({read_time:.3f}s) - {e}")
        
        # Test module imports
        app.presenter.present_message("\n📦 Module Import Test:")
        modules_to_test = [
            'redhat_status.core.api_client',
            'redhat_status.analytics.ai_analytics',
            'redhat_status.notifications.notification_manager',
            'redhat_status.presentation.presenter'
        ]
        
        for module_name in modules_to_test:
            start_time = time.time()
            try:
                __import__(module_name)
                import_time = time.time() - start_time
                app.presenter.present_message(f"  {module_name}: ✅ Success ({import_time:.3f}s)")
            except Exception as e:
                import_time = time.time() - start_time
                app.presenter.present_message(f"  {module_name}: ❌ Failed ({import_time:.3f}s) - {e}")
        
    except Exception as e:
        app.presenter.present_error(f"Error running benchmark: {e}")

def handle_setup(app, args):
    """Interactive configuration setup wizard"""
    try:
        app.presenter.present_message("⚙️ RED HAT STATUS CHECKER SETUP WIZARD")
        app.presenter.present_message("=" * 60)
        app.presenter.present_message("Welcome to the configuration setup wizard!")
        app.presenter.present_message("This will help you configure the application settings.")
        app.presenter.present_message("")
        
        # Load current configuration
        config_path = Path(__file__).parent.parent / "config.json"
        
        try:
            with open(config_path, 'r') as f:
                current_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            app.presenter.present_message(f"⚠️  Could not load existing config: {e}")
            app.presenter.present_message("Creating a new configuration...")
            current_config = {}
        
        # Create configuration sections
        new_config = {}
        
        # 1. API Configuration
        app.presenter.present_message("📡 API CONFIGURATION")
        app.presenter.present_message("-" * 30)
        
        current_api = current_config.get('api', {})
        
        app.presenter.present_message(f"Current API URL: {current_api.get('base_url', 'https://status.redhat.com/api/v2/summary.json')}")
        api_url = input("Enter API URL (or press Enter to keep current): ").strip()
        if not api_url:
            api_url = current_api.get('base_url', 'https://status.redhat.com/api/v2/summary.json')
        
        app.presenter.present_message(f"Current timeout: {current_api.get('timeout', 30)} seconds")
        timeout_input = input("Enter timeout in seconds (or press Enter to keep current): ").strip()
        timeout = int(timeout_input) if timeout_input.isdigit() else current_api.get('timeout', 30)
        
        app.presenter.present_message(f"Current max retries: {current_api.get('max_retries', 3)}")
        retries_input = input("Enter max retries (or press Enter to keep current): ").strip()
        max_retries = int(retries_input) if retries_input.isdigit() else current_api.get('max_retries', 3)
        
        new_config['api'] = {
            'base_url': api_url,
            'timeout': timeout,
            'max_retries': max_retries
        }
        
        # 2. Cache Configuration
        app.presenter.present_message("\n💾 CACHE CONFIGURATION")
        app.presenter.present_message("-" * 30)
        
        current_cache = current_config.get('cache', {})
        
        app.presenter.present_message(f"Current cache enabled: {current_cache.get('enabled', True)}")
        cache_enabled_input = input("Enable caching? (y/n, or press Enter to keep current): ").strip().lower()
        if cache_enabled_input in ['y', 'yes']:
            cache_enabled = True
        elif cache_enabled_input in ['n', 'no']:
            cache_enabled = False
        else:
            cache_enabled = current_cache.get('enabled', True)
        
        if cache_enabled:
            app.presenter.present_message(f"Current cache duration: {current_cache.get('duration_minutes', 5)} minutes")
            cache_duration_input = input("Enter cache duration in minutes (or press Enter to keep current): ").strip()
            cache_duration = int(cache_duration_input) if cache_duration_input.isdigit() else current_cache.get('duration_minutes', 5)
            
            app.presenter.present_message(f"Current cache directory: {current_cache.get('directory', '.cache')}")
            cache_dir = input("Enter cache directory (or press Enter to keep current): ").strip()
            if not cache_dir:
                cache_dir = current_cache.get('directory', '.cache')
        else:
            cache_duration = 5
            cache_dir = '.cache'
        
        new_config['cache'] = {
            'enabled': cache_enabled,
            'duration_minutes': cache_duration,
            'directory': cache_dir,
            'max_size_mb': current_cache.get('max_size_mb', 100),
            'auto_cleanup': current_cache.get('auto_cleanup', True)
        }
        
        # 3. AI Analytics Configuration
        app.presenter.present_message("\n🤖 AI ANALYTICS CONFIGURATION")
        app.presenter.present_message("-" * 40)
        
        current_ai = current_config.get('ai_analytics', {})
        
        app.presenter.present_message(f"Current AI analytics enabled: {current_ai.get('enabled', True)}")
        ai_enabled_input = input("Enable AI analytics? (y/n, or press Enter to keep current): ").strip().lower()
        if ai_enabled_input in ['y', 'yes']:
            ai_enabled = True
        elif ai_enabled_input in ['n', 'no']:
            ai_enabled = False
        else:
            ai_enabled = current_ai.get('enabled', True)
        
        if ai_enabled:
            app.presenter.present_message(f"Current anomaly detection: {current_ai.get('anomaly_detection', True)}")
            anomaly_input = input("Enable anomaly detection? (y/n, or press Enter to keep current): ").strip().lower()
            if anomaly_input in ['y', 'yes']:
                anomaly_detection = True
            elif anomaly_input in ['n', 'no']:
                anomaly_detection = False
            else:
                anomaly_detection = current_ai.get('anomaly_detection', True)
            
            app.presenter.present_message(f"Current predictive analysis: {current_ai.get('predictive_analysis', True)}")
            predictive_input = input("Enable predictive analysis? (y/n, or press Enter to keep current): ").strip().lower()
            if predictive_input in ['y', 'yes']:
                predictive_analysis = True
            elif predictive_input in ['n', 'no']:
                predictive_analysis = False
            else:
                predictive_analysis = current_ai.get('predictive_analysis', True)
        else:
            anomaly_detection = False
            predictive_analysis = False
        
        new_config['ai_analytics'] = {
            'enabled': ai_enabled,
            'anomaly_detection': anomaly_detection,
            'predictive_analysis': predictive_analysis,
            'learning_window': current_ai.get('learning_window', 50),
            'anomaly_threshold': current_ai.get('anomaly_threshold', 2.0),
            'min_confidence': current_ai.get('min_confidence', 0.7)
        }
        
        # 4. Database Configuration
        app.presenter.present_message("\n💾 DATABASE CONFIGURATION")
        app.presenter.present_message("-" * 35)
        
        current_db = current_config.get('database', {})
        
        app.presenter.present_message(f"Current database enabled: {current_db.get('enabled', True)}")
        db_enabled_input = input("Enable database storage? (y/n, or press Enter to keep current): ").strip().lower()
        if db_enabled_input in ['y', 'yes']:
            db_enabled = True
        elif db_enabled_input in ['n', 'no']:
            db_enabled = False
        else:
            db_enabled = current_db.get('enabled', True)
        
        if db_enabled:
            app.presenter.present_message(f"Current database path: {current_db.get('path', 'redhat_monitoring.db')}")
            db_path = input("Enter database file path (or press Enter to keep current): ").strip()
            if not db_path:
                db_path = current_db.get('path', 'redhat_monitoring.db')
            
            app.presenter.present_message(f"Current retention: {current_db.get('retention_days', 30)} days")
            retention_input = input("Enter data retention in days (or press Enter to keep current): ").strip()
            retention_days = int(retention_input) if retention_input.isdigit() else current_db.get('retention_days', 30)
        else:
            db_path = 'redhat_monitoring.db'
            retention_days = 30
        
        new_config['database'] = {
            'enabled': db_enabled,
            'path': db_path,
            'retention_days': retention_days,
            'auto_cleanup': current_db.get('auto_cleanup', True)
        }
        
        # 5. SLO Configuration
        app.presenter.present_message("\n🎯 SLO CONFIGURATION")
        app.presenter.present_message("-" * 25)
        
        current_slo = current_config.get('slo', {})
        
        app.presenter.present_message(f"Current SLO tracking enabled: {current_slo.get('enabled', True)}")
        slo_enabled_input = input("Enable SLO tracking? (y/n, or press Enter to keep current): ").strip().lower()
        if slo_enabled_input in ['y', 'yes']:
            slo_enabled = True
        elif slo_enabled_input in ['n', 'no']:
            slo_enabled = False
        else:
            slo_enabled = current_slo.get('enabled', True)
        
        if slo_enabled:
            current_targets = current_slo.get('targets', {})
            
            app.presenter.present_message(f"Current global availability target: {current_targets.get('global_availability', 99.9)}%")
            avail_input = input("Enter global availability target % (or press Enter to keep current): ").strip()
            global_availability = float(avail_input) if avail_input.replace('.', '').isdigit() else current_targets.get('global_availability', 99.9)
            
            app.presenter.present_message(f"Current response time target: {current_targets.get('response_time', 2.0)}s")
            response_input = input("Enter response time target in seconds (or press Enter to keep current): ").strip()
            response_time = float(response_input) if response_input.replace('.', '').isdigit() else current_targets.get('response_time', 2.0)
            
            targets = {
                'global_availability': global_availability,
                'response_time': response_time,
                'uptime_monthly': current_targets.get('uptime_monthly', 99.5)
            }
        else:
            targets = current_slo.get('targets', {})
        
        new_config['slo'] = {
            'enabled': slo_enabled,
            'targets': targets,
            'tracking_period': current_slo.get('tracking_period', 'monthly'),
            'alert_on_breach': current_slo.get('alert_on_breach', True)
        }
        
        # 6. Notifications Configuration (simplified)
        app.presenter.present_message("\n📧 NOTIFICATIONS CONFIGURATION")
        app.presenter.present_message("-" * 40)
        
        current_notifications = current_config.get('notifications', {})
        
        app.presenter.present_message("Email notifications:")
        current_email = current_notifications.get('email', {})
        app.presenter.present_message(f"Current email enabled: {current_email.get('enabled', False)}")
        email_enabled_input = input("Enable email notifications? (y/n, or press Enter to keep current): ").strip().lower()
        if email_enabled_input in ['y', 'yes']:
            email_enabled = True
        elif email_enabled_input in ['n', 'no']:
            email_enabled = False
        else:
            email_enabled = current_email.get('enabled', False)
        
        email_config = current_email.copy()
        email_config['enabled'] = email_enabled
        
        # Copy other notification settings from current config
        new_config['notifications'] = {
            'email': email_config,
            'webhooks': current_notifications.get('webhooks', {'enabled': False}),
            'slack': current_notifications.get('slack', {'enabled': False})
        }
        
        # Copy remaining sections from current config
        for section in ['logging', 'output', 'performance']:
            if section in current_config:
                new_config[section] = current_config[section]
        
        # Add default sections if missing
        if 'logging' not in new_config:
            new_config['logging'] = {
                'level': 'INFO',
                'file': 'redhat_status.log',
                'max_size_mb': 10,
                'backup_count': 3
            }
        
        if 'output' not in new_config:
            new_config['output'] = {
                'timestamp_format': '%Y%m%d_%H%M%S',
                'create_summary_report': True
            }
        
        if 'performance' not in new_config:
            new_config['performance'] = {
                'enable_profiling': False,
                'memory_profiling': False,
                'max_concurrent_operations': 5
            }
        
        # Show configuration summary
        app.presenter.present_message("\n📋 CONFIGURATION SUMMARY")
        app.presenter.present_message("=" * 40)
        app.presenter.present_message(f"API URL: {new_config['api']['base_url']}")
        app.presenter.present_message(f"Cache Enabled: {new_config['cache']['enabled']}")
        app.presenter.present_message(f"AI Analytics: {new_config['ai_analytics']['enabled']}")
        app.presenter.present_message(f"Database Storage: {new_config['database']['enabled']}")
        app.presenter.present_message(f"SLO Tracking: {new_config['slo']['enabled']}")
        app.presenter.present_message(f"Email Notifications: {new_config['notifications']['email']['enabled']}")
        
        # Confirm save
        app.presenter.present_message("")
        save_input = input("Save this configuration? (Y/n): ").strip().lower()
        if save_input in ['', 'y', 'yes']:
            # Create backup of existing config
            if config_path.exists():
                backup_path = config_path.with_suffix('.backup')
                import shutil
                shutil.copy2(config_path, backup_path)
                app.presenter.present_message(f"📁 Backup created: {backup_path}")
            
            # Save new configuration
            with open(config_path, 'w') as f:
                json.dump(new_config, f, indent=2)
            
            app.presenter.present_message(f"✅ Configuration saved to: {config_path}")
            app.presenter.present_message("")
            app.presenter.present_message("🔄 Configuration updated successfully!")
            app.presenter.present_message("You may need to restart the application for all changes to take effect.")
            
            # Validate the new configuration
            app.presenter.present_message("\n🔍 Validating configuration...")
            try:
                from redhat_status.config.config_manager import ConfigManager
                config_manager = ConfigManager(str(config_path))
                validation = config_manager.validate()
                
                if validation['valid']:
                    app.presenter.present_message("✅ Configuration validation passed!")
                else:
                    app.presenter.present_message("⚠️  Configuration validation warnings:")
                    for warning in validation.get('warnings', []):
                        app.presenter.present_message(f"  • {warning}")
                    for error in validation.get('errors', []):
                        app.presenter.present_message(f"  ❌ {error}")
            except Exception as e:
                app.presenter.present_message(f"⚠️  Could not validate configuration: {e}")
        else:
            app.presenter.present_message("❌ Configuration not saved.")
        
        app.presenter.present_message("\n" + "=" * 60)
        app.presenter.present_message("Setup wizard completed!")
        
    except KeyboardInterrupt:
        app.presenter.present_message("\n\n⏹️  Setup wizard cancelled by user.")
    except Exception as e:
        app.presenter.present_error(f"Error in setup wizard: {e}")
        logging.error(f"Setup wizard error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
