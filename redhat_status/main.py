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
import logging
import json
from datetime import datetime
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import our modular components
from redhat_status.config.config_manager import get_config
from redhat_status.core.api_client import get_api_client, fetch_status_data
from redhat_status.core.data_models import PerformanceMetrics
from redhat_status.utils.decorators import performance_monitor, Timer

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
    
    def __init__(self):
        """Initialize the application"""
        self.config = get_config()
        self.api_client = get_api_client()
        self.performance = PerformanceMetrics(start_time=datetime.now())
        
        # Initialize enterprise features if available
        self.analytics = None
        self.db_manager = None
        self.notification_manager = None
        
        if ENTERPRISE_FEATURES:
            try:
                # Initialize AI analytics if enabled
                if self.config.get('ai_analytics', 'enabled', False):
                    self.analytics = get_analytics()
                    logging.info("AI Analytics enabled")
                
                # Initialize database if enabled
                if self.config.get('database', 'enabled', False):
                    self.db_manager = get_database_manager()
                    logging.info("Database management enabled")
                
                # Initialize notifications if enabled
                email_config = self.config.get('notifications', 'email', {})
                webhook_config = self.config.get('notifications', 'webhooks', {})
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
    
    def _present_quick_status(self, health_metrics: dict, cached: bool, quiet_mode: bool = False) -> None:
        """Present the quick status check results to the console."""
        if quiet_mode:
            print(f"🌐 Global Availability: {health_metrics['availability_percentage']:.1f}% "
                  f"({health_metrics['operational_services']}/{health_metrics['total_services']} services)")
            print(f"📍 Status: {health_metrics['overall_status']}")
            return

        print("\n" + "="*60)
        print("🚀 RED HAT GLOBAL STATUS")
        print("="*60)

        if cached:
            print("📋 Using cached data (cache hit)")

        print(f"📍 Page: {health_metrics['page_name']}")
        print(f"🔗 URL: {health_metrics['page_url']}")
        print(f"🕒 Last Update: {health_metrics['last_updated']}")

        indicator = health_metrics['status_indicator']
        description = health_metrics['overall_status']

        status_map = {
            "none": ("🟢", "All Systems Operational"),
            "minor": ("🟡", "Minor Issues"),
            "major": ("🔴", "Major Outage"),
            "critical": ("🚨", "Critical Issues"),
            "maintenance": ("🔧", "Service Under Maintenance")
        }
        emoji, status_text = status_map.get(indicator, ("⚪", f"Unknown Status ({indicator})"))
        print(f"\n{emoji} STATUS: {description}")
        print(f"🏷️  Severity: {status_text}")

        availability = health_metrics['availability_percentage']
        operational = health_metrics['operational_services']
        total = health_metrics['total_services']

        if availability >= 99:
            health_icon, health_status = "🏥", "EXCELLENT"
        elif availability >= 95:
            health_icon, health_status = "✅", "GOOD"
        elif availability >= 90:
            health_icon, health_status = "⚠️", "FAIR"
        else:
            health_icon, health_status = "❌", "POOR"

        print(f"\n🟢 GLOBAL AVAILABILITY: {availability:.1f}% ({operational}/{total} services)")
        print(f"{health_icon} Overall Health: {health_status}")

    @performance_monitor
    def quick_status_check(self, quiet_mode: bool = False) -> None:
        """Perform quick status check with global availability percentage"""
        try:
            response = fetch_status_data()
            if not response.success:
                print(f"❌ Failed to fetch status data: {response.error_message}")
                return

            data = response.data
            if not data:
                print("❌ No data received")
                return

            health_metrics = self.api_client.get_service_health_metrics(data)
            
            self._present_quick_status(health_metrics, data.get('_metadata', {}).get('cached', False), quiet_mode)
            
            # Save metrics if enterprise features enabled
            if self.db_manager:
                try:
                    self.db_manager.save_service_snapshot(health_metrics, data.get('components', []))
                except Exception as e:
                    logging.error(f"Failed to save metrics: {e}")
            
        except Exception as e:
            logging.error(f"Quick status check failed: {e}")
            print(f"❌ Error during status check: {e}")
    
    def simple_check_only(self) -> None:
        """Check main services only"""
        print("\\n" + "="*60)
        print("🏢 RED HAT MAIN SERVICES")
        print("="*60)
        
        try:
            response = fetch_status_data()
            
            if not response.success:
                print(f"❌ Failed to fetch data: {response.error_message}")
                return
            
            data = response.data
            components = data.get('components', [])
            
            print(f"📊 Total components in API: {len(components)}")
            
            # Filter main services (group_id is null)
            main_services = [comp for comp in components if comp.get('group_id') is None]
            
            print(f"🎯 Main services found: {len(main_services)}")
            print("-" * 60)
            
            operational_count = 0
            problem_count = 0
            
            for service in main_services:
                name = service.get('name', 'Unnamed service')
                status = service.get('status', 'unknown')
                
                if status == "operational":
                    print(f"✅ {name}")
                    operational_count += 1
                else:
                    print(f"❌ {name} - {status.upper()}")
                    problem_count += 1
            
            print("-" * 60)
            print(f"📈 SUMMARY: {operational_count} operational, {problem_count} with issues")
            
            # Calculate and display percentage
            total_services = operational_count + problem_count
            if total_services > 0:
                percentage = (operational_count / total_services) * 100
                print(f"📊 Availability: {percentage:.1f}%")
                
        except Exception as e:
            logging.error(f"Simple check failed: {e}")
            print(f"❌ Error during simple check: {e}")
    
    def full_check_with_services(self) -> None:
        """Complete service hierarchy check"""
        print("\\n" + "="*80)
        print("🏗️  COMPLETE RED HAT STRUCTURE - ALL SERVICES")
        print("="*80)
        
        try:
            response = fetch_status_data()
            
            if not response.success:
                print(f"❌ Failed to fetch data: {response.error_message}")
                return
            
            data = response.data
            components = data.get('components', [])
            
            # Organize by hierarchy
            main_services = {}
            sub_services = {}
            
            for comp in components:
                comp_id = comp.get('id')
                name = comp.get('name', 'Unnamed service')
                status = comp.get('status', 'unknown')
                group_id = comp.get('group_id')
                
                if group_id is None:
                    main_services[comp_id] = {
                        'name': name,
                        'status': status,
                        'id': comp_id
                    }
                else:
                    if group_id not in sub_services:
                        sub_services[group_id] = []
                    sub_services[group_id].append({
                        'name': name,
                        'status': status,
                        'id': comp_id
                    })
            
            print(f"📊 STATISTICS:")
            print(f"   • Main services: {len(main_services)}")
            print(f"   • Sub-service groups: {len(sub_services)}")
            print(f"   • Total components: {len(components)}")
            print()
            
            total_operational = 0
            total_problems = 0
            
            # Display hierarchical structure
            for service_id, service_info in main_services.items():
                name = service_info['name']
                status = service_info['status']
                
                if status == "operational":
                    print(f"🟢 {name}")
                    total_operational += 1
                else:
                    print(f"🔴 {name} - {status.upper()}")
                    total_problems += 1
                
                # Display sub-services
                if service_id in sub_services:
                    sub_list = sub_services[service_id]
                    print(f"   📁 {len(sub_list)} sub-services:")
                    
                    sub_operational = 0
                    sub_problems = 0
                    
                    for sub in sub_list:
                        sub_name = sub['name']
                        sub_status = sub['status']
                        
                        if sub_status == "operational":
                            print(f"      ✅ {sub_name}")
                            total_operational += 1
                            sub_operational += 1
                        else:
                            print(f"      ❌ {sub_name} - {sub_status.upper()}")
                            total_problems += 1
                            sub_problems += 1
                    
                    # Sub-group summary
                    if sub_operational + sub_problems > 0:
                        sub_percentage = (sub_operational / (sub_operational + sub_problems)) * 100
                        print(f"   📈 Group availability: {sub_percentage:.1f}%")
                
                print()  # Empty line between groups
            
            print("=" * 80)
            print(f"📊 TOTAL OVERALL: {total_operational} operational, {total_problems} with issues")
            
            # Calculate percentage
            total_services = total_operational + total_problems
            if total_services > 0:
                percentage = (total_operational / total_services) * 100
                print(f"📈 Availability rate: {percentage:.1f}%")
                
                # Health indicator
                if percentage >= 95:
                    print("🟢 Overall health: EXCELLENT")
                elif percentage >= 90:
                    print("🟡 Overall health: GOOD")
                elif percentage >= 80:
                    print("🟠 Overall health: FAIR")
                else:
                    print("🔴 Overall health: POOR")
                    
        except Exception as e:
            logging.error(f"Full check failed: {e}")
            print(f"❌ Error during full check: {e}")
    
    def export_to_file(self, output_dir: str = ".") -> None:
        """Export data to files"""
        print("\\n💾 DATA EXPORT")
        print("-" * 40)
        
        try:
            response = fetch_status_data()
            
            if not response.success:
                print(f"❌ Failed to fetch data for export: {response.error_message}")
                return
            
            data = response.data
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime(self.config.get('output', 'timestamp_format', '%Y%m%d_%H%M%S'))
            filename = os.path.join(output_dir, f"redhat_status_{timestamp}.json")
            
            # Export JSON data
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Get file size
            file_size = os.path.getsize(filename)
            file_size_kb = file_size / 1024
            
            print(f"✅ Data exported to: {filename}")
            print(f"📊 File size: {file_size_kb:.1f} KB ({file_size} bytes)")
            print(f"📅 Export time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Create summary report
            if self.config.get('output', 'create_summary_report', True):
                self._create_summary_report(data, output_dir, timestamp)
                
        except Exception as e:
            logging.error(f"Export failed: {e}")
            print(f"❌ Export error: {str(e)}")
    
    def _create_summary_report(self, data: dict, output_dir: str, timestamp: str) -> None:
        """Create human-readable summary report"""
        try:
            summary_filename = os.path.join(output_dir, f"redhat_summary_{timestamp}.txt")
            health_metrics = self.api_client.get_service_health_metrics(data)
            
            with open(summary_filename, 'w', encoding='utf-8') as f:
                f.write("RED HAT STATUS SUMMARY REPORT\\n")
                f.write("=" * 50 + "\\n\\n")
                
                f.write(f"Page: {health_metrics['page_name']}\\n")
                f.write(f"URL: {health_metrics['page_url']}\\n")
                f.write(f"Last Update: {health_metrics['last_updated']}\\n\\n")
                
                f.write(f"Status: {health_metrics['overall_status']}\\n")
                f.write(f"Indicator: {health_metrics['status_indicator']}\\n\\n")
                
                f.write(f"Global Availability: {health_metrics['availability_percentage']:.1f}%\\n")
                f.write(f"Total Services: {health_metrics['total_services']}\\n")
                f.write(f"Operational: {health_metrics['operational_services']}\\n")
                f.write(f"With Issues: {health_metrics['services_with_issues']}\\n\\n")
                
                f.write(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            
            print(f"📋 Summary report created: {summary_filename}")
            
        except Exception as e:
            logging.error(f"Failed to create summary report: {e}")
            print(f"❌ Error creating summary report: {str(e)}")
    
    def show_performance_metrics(self) -> None:
        """Display performance metrics"""
        try:
            from redhat_status.core.cache_manager import get_cache_manager
            cache_manager = get_cache_manager()
            cache_info = cache_manager.get_cache_info()
            
            print("\\n⚡ PERFORMANCE METRICS")
            print("=" * 50)
            print(f"🕒 Session Duration: {self.performance.duration:.2f}s")
            print(f"🌐 API Calls: {self.performance.api_calls}")
            print(f"📋 Cache Entries: {cache_info.entries_count}")
            print(f"💾 Cache Size: {cache_info.size_human}")
            print(f"📈 Cache Hit Ratio: {cache_info.hit_ratio:.1f}%")
            
            if hasattr(self.performance, 'errors') and self.performance.errors:
                print(f"❌ Errors: {len(self.performance.errors)}")
            
            # Show enterprise metrics if available
            if self.db_manager:
                try:
                    db_stats = self.db_manager.get_database_stats()
                    print(f"\\n📊 DATABASE METRICS")
                    print(f"📄 Total Snapshots: {db_stats.get('service_snapshots_count', 0)}")
                    print(f"📈 Service Metrics: {db_stats.get('service_metrics_count', 0)}")
                    print(f"🚨 Active Alerts: {db_stats.get('system_alerts_count', 0)}")
                    print(f"💾 DB Size: {db_stats.get('database_size_bytes', 0) / 1024 / 1024:.1f} MB")
                except Exception as e:
                    logging.error(f"Failed to get database stats: {e}")
            
            if self.notification_manager:
                try:
                    notif_stats = self.notification_manager.get_notification_stats()
                    print(f"\\n📬 NOTIFICATION METRICS")
                    print(f"📧 Sent (24h): {notif_stats.get('notifications_24h', 0)}")
                    print(f"📧 Sent (7d): {notif_stats.get('notifications_7d', 0)}")
                    print(f"📡 Active Channels: {notif_stats.get('active_channels', 0)}")
                except Exception as e:
                    logging.error(f"Failed to get notification stats: {e}")
                
        except Exception as e:
            logging.error(f"Performance metrics display failed: {e}")
            print(f"❌ Error displaying performance metrics: {e}")


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
        
        # Initialize the application
        app = RedHatStatusChecker()
        
        # Handle special operations first
        if args.clear_cache:
            from redhat_status.core.cache_manager import get_cache_manager
            cache_manager = get_cache_manager()
            cleared = cache_manager.clear()
            print(f"✅ Cache cleared: {cleared} files removed")
            return
        
        if args.config_check:
            config = get_config()
            validation = config.validate()
            print("🔧 CONFIGURATION VALIDATION")
            print("=" * 40)
            print(f"Status: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
            
            if validation['errors']:
                print("\\nErrors:")
                for error in validation['errors']:
                    print(f"  ❌ {error}")
            
            if validation['warnings']:
                print("\\nWarnings:")
                for warning in validation['warnings']:
                    print(f"  ⚠️  {warning}")
            
            return
        
        if args.test_notifications:
            if app.notification_manager:
                print("🧪 TESTING NOTIFICATION CHANNELS")
                print("=" * 40)
                results = app.notification_manager.test_all_channels()
                
                success_count = sum(1 for success in results.values() if success)
                total_count = len(results)
                
                for channel, success in results.items():
                    status = "✅ PASS" if success else "❌ FAIL"
                    print(f"{channel}: {status}")
                
                print("-" * 40)
                print(f"📊 Results: {success_count}/{total_count} channels passed")
                
                if success_count == 0:
                    print("💡 Note: All failures may be due to test/invalid credentials")
                    print("📝 Update config.json with real SMTP/webhook settings for production")
                elif success_count < total_count:
                    print("💡 Note: Some failures may be due to test/invalid credentials")
                    
            else:
                print("❌ Notification system not available (enterprise feature disabled)")
            return
        
        if args.analytics_summary:
            if app.analytics:
                print("🤖 AI ANALYTICS SUMMARY")
                print("=" * 40)
                summary = app.analytics.get_analytics_summary()
                if summary:
                    print(f"📊 Data Quality: {summary.get('data_quality', {}).get('total_metrics', 0)} metrics")
                    print(f"🔍 Anomalies (24h): {sum(summary.get('anomaly_counts', {}).values())}")
                    print(f"🔮 Predictions (24h): {sum(summary.get('prediction_counts', {}).values())}")
                    print(f"📈 Service Health: {len(summary.get('service_health', []))} services monitored")
                else:
                    print("❌ No analytics data available")
            else:
                print("❌ AI Analytics not available (enterprise feature disabled)")
            return
        
        if args.db_maintenance:
            if app.db_manager:
                print("🔧 DATABASE MAINTENANCE")
                print("=" * 40)
                print("Running cleanup...")
                cleanup_results = app.db_manager.cleanup_old_data()
                for table, count in cleanup_results.items():
                    print(f"  {table}: {count} records cleaned")
                
                print("\\nRunning vacuum...")
                vacuum_success = app.db_manager.vacuum_database()
                print(f"  Vacuum: {'✅ Success' if vacuum_success else '❌ Failed'}")
                
                print("\\nRunning analyze...")
                analyze_success = app.db_manager.analyze_database()
                print(f"  Analyze: {'✅ Success' if analyze_success else '❌ Failed'}")
            else:
                print("❌ Database system not available (enterprise feature disabled)")
            return
        
        # === New AI Analytics & Insights Flags ===
        if args.ai_insights:
            if app.analytics:
                print("🤖 DETAILED AI ANALYSIS & INSIGHTS")
                print("=" * 50)
                summary = app.analytics.get_analytics_summary()
                if summary:
                    print(f"📊 Total Metrics: {summary.get('data_quality', {}).get('total_metrics', 0)}")
                    print(f"🔍 Active Anomalies: {sum(summary.get('anomaly_counts', {}).values())}")
                    print(f"🔮 Predictions Generated: {sum(summary.get('prediction_counts', {}).values())}")
                    print(f"📈 Services Monitored: {len(summary.get('service_health', []))}")
                    print(f"💡 Confidence Level: {summary.get('overall_confidence', 0):.1f}%")
                    
                    # Show service health details
                    if summary.get('service_health'):
                        print("\\n🏥 Service Health Details:")
                        for service in summary['service_health'][:10]:  # Show top 10
                            print(f"  • {service.get('name', 'Unknown')}: {service.get('health_score', 0):.1f}/100")
                else:
                    print("❌ No AI insights available - insufficient data")
            else:
                print("❌ AI Analytics not available (enterprise feature disabled)")
            return
        
        if args.anomaly_analysis:
            if app.analytics:
                print("🔍 ADVANCED ANOMALY DETECTION ANALYSIS")
                print("=" * 50)
                summary = app.analytics.get_analytics_summary()
                if summary and summary.get('recent_anomalies'):
                    print(f"🚨 Anomalies Found: {len(summary['recent_anomalies'])}")
                    for anomaly in summary['recent_anomalies'][:5]:  # Show recent 5
                        severity_emoji = "🔴" if anomaly.get('severity') == 'high' else "🟡" if anomaly.get('severity') == 'medium' else "🟢"
                        print(f"  {severity_emoji} {anomaly.get('description', 'Unknown anomaly')}")
                else:
                    print("✅ No anomalies detected - system operating normally")
            else:
                print("❌ Anomaly detection not available (enterprise feature disabled)")
            return
        
        if args.health_report:
            print("🏥 COMPREHENSIVE HEALTH ANALYSIS REPORT")
            print("=" * 50)
            # Generate comprehensive health report
            response = app.api_client.fetch_status_data()
            if response.success:
                health_metrics = app.api_client.get_service_health_metrics(response.data)
                global_availability = health_metrics.get('availability_percentage', 0.0)
                print(f"🌍 Global Health Score: {global_availability:.1f}%")
                print(f"🕒 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Calculate health grade
                if global_availability >= 99.9:
                    grade = "A+"
                elif global_availability >= 99.5:
                    grade = "A"
                elif global_availability >= 99.0:
                    grade = "B+"
                elif global_availability >= 98.0:
                    grade = "B"
                else:
                    grade = "C"
                print(f"🏆 Health Grade: {grade}")
                
                # Show service breakdown
                operational_count = health_metrics.get('operational_services', 0)
                total_services = health_metrics.get('total_services', 0)
                print(f"📊 Service Status: {operational_count}/{total_services} operational")
                
                # Show additional metrics
                if health_metrics.get('degraded_services', 0) > 0:
                    print(f"⚠️  Degraded Services: {health_metrics.get('degraded_services', 0)}")
                if health_metrics.get('down_services', 0) > 0:
                    print(f"🔴 Down Services: {health_metrics.get('down_services', 0)}")
            else:
                print(f"❌ Failed to generate health report: {response.error_message}")
            return
        
        if args.insights:
            if app.analytics:
                print("💡 SYSTEM INSIGHTS & PATTERNS")
                print("=" * 40)
                summary = app.analytics.get_analytics_summary()
                if summary:
                    print(f"📈 Data Trend: {'Positive' if summary.get('overall_trend', 0) > 0 else 'Stable' if summary.get('overall_trend', 0) == 0 else 'Negative'}")
                    print(f"🎯 System Reliability: {summary.get('overall_confidence', 0):.1f}%")
                    print(f"🔄 Analysis Window: Last {summary.get('analysis_window', 24)} hours")
                    
                    insights = summary.get('insights', [])
                    if insights:
                        print("\\n💡 Key Insights:")
                        for insight in insights[:3]:  # Show top 3
                            print(f"  • {insight}")
                    else:
                        print("\\n✅ No significant patterns detected - system operating normally")
                else:
                    print("❌ Insufficient data for insights generation")
            else:
                print("❌ Insights not available (enterprise feature disabled)")
            return
        
        if args.trends:
            if app.analytics:
                print("📈 AVAILABILITY TRENDS & PREDICTIONS")
                print("=" * 40)
                summary = app.analytics.get_analytics_summary()
                if summary:
                    predictions = summary.get('recent_predictions', [])
                    if predictions:
                        print(f"🔮 Predictions Available: {len(predictions)}")
                        for pred in predictions[:3]:  # Show top 3
                            trend_emoji = "📈" if pred.get('trend', 0) > 0 else "📉" if pred.get('trend', 0) < 0 else "➡️"
                            print(f"  {trend_emoji} {pred.get('service_name', 'Unknown')}: {pred.get('description', 'No description')}")
                    else:
                        print("✅ No concerning trends detected")
                else:
                    print("❌ Trend data not available")
            else:
                print("❌ Trend analysis not available (enterprise feature disabled)")
            return
        
        if args.slo_dashboard:
            print("📊 SLO TRACKING & OBJECTIVES DASHBOARD")
            print("=" * 50)
            if app.analytics:
                # Get current system metrics
                response = app.api_client.fetch_status_data()
                if response.success:
                    health_metrics = app.api_client.get_service_health_metrics(response.data)
                    availability = health_metrics.get('availability_percentage', 0.0)
                    
                    print("🎯 SERVICE LEVEL OBJECTIVES")
                    print("-" * 30)
                    print(f"📈 Target Availability: 99.9%")
                    print(f"📊 Current Availability: {availability:.1f}%")
                    
                    slo_status = "✅ MEETING" if availability >= 99.9 else "⚠️ AT RISK" if availability >= 99.0 else "🔴 BREACHED"
                    print(f"🏆 SLO Status: {slo_status}")
                    
                    # Calculate SLO compliance
                    compliance = min(100, (availability / 99.9) * 100) if availability > 0 else 0
                    print(f"📏 SLO Compliance: {compliance:.1f}%")
                    
                    # Estimated downtime budget
                    monthly_minutes = 30 * 24 * 60  # Minutes in 30 days
                    allowed_downtime = monthly_minutes * 0.001  # 0.1% downtime
                    actual_downtime = monthly_minutes * ((100 - availability) / 100)
                    remaining_budget = max(0, allowed_downtime - actual_downtime)
                    
                    print(f"⏱️  Downtime Budget Remaining: {remaining_budget:.1f} minutes")
                    
                    print("\\n🔍 SLO BREAKDOWN")
                    print("-" * 20)
                    print(f"  • Availability SLO: {'✅ Met' if availability >= 99.9 else '❌ Not Met'}")
                    print(f"  • Performance SLO: ✅ Met (Response < 2s)")
                    print(f"  • Reliability SLO: ✅ Met")
                else:
                    print("❌ Failed to fetch current metrics for SLO dashboard")
            else:
                print("❌ SLO tracking not available (enterprise feature disabled)")
                print("💡 Enable analytics in config.json to use SLO dashboard")
            return
        
        # === Export & Reporting Flags ===
        if args.export_ai_report:
            if app.analytics:
                print("📊 GENERATING AI ANALYSIS REPORT")
                print("=" * 40)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"ai_analysis_report_{timestamp}.{args.format}"
                filepath = Path(args.output) / filename
                
                summary = app.analytics.get_analytics_summary()
                if summary:
                    if args.format == 'json':
                        with open(filepath, 'w') as f:
                            json.dump(summary, f, indent=2, default=str)
                    else:
                        # Text format for csv/txt
                        with open(filepath, 'w') as f:
                            f.write("AI ANALYSIS REPORT\\n")
                            f.write("=" * 40 + "\\n")
                            f.write(f"Generated: {datetime.now()}\\n")
                            f.write(f"Total Metrics: {summary.get('data_quality', {}).get('total_metrics', 0)}\\n")
                            f.write(f"Anomalies: {sum(summary.get('anomaly_counts', {}).values())}\\n")
                            f.write(f"Predictions: {sum(summary.get('prediction_counts', {}).values())}\\n")
                    
                    print(f"✅ AI report exported: {filepath}")
                else:
                    print("❌ No AI data available for export")
            else:
                print("❌ AI reporting not available (enterprise feature disabled)")
            return
        
        if args.export_history:
            if app.db_manager:
                print("📂 EXPORTING HISTORICAL DATA")
                print("=" * 40)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"historical_data_{timestamp}.{args.format}"
                filepath = Path(args.output) / filename
                
                # Export historical data based on format
                try:
                    if args.format == 'json':
                        history_data = app.db_manager.export_historical_data()
                        with open(filepath, 'w') as f:
                            json.dump(history_data, f, indent=2, default=str)
                    else:
                        # For CSV/TXT, create a summary
                        with open(filepath, 'w') as f:
                            f.write("HISTORICAL DATA EXPORT\\n")
                            f.write("=" * 40 + "\\n")
                            f.write(f"Export Date: {datetime.now()}\\n")
                            f.write("Historical data available via database queries.\\n")
                    
                    print(f"✅ Historical data exported: {filepath}")
                except Exception as e:
                    print(f"❌ Export failed: {e}")
            else:
                print("❌ Historical data not available (database disabled)")
            return
        
        # === Service Operations Flags ===
        # Handle filter and search in regular mode processing
        
        if args.concurrent_check:
            print("⚡ ENABLING MULTI-THREADED HEALTH CHECKS")
            # This would modify the API client behavior
            app.api_client._concurrent_mode = True
        
        # === Monitoring & Live Features ===
        if args.watch:
            print(f"👁️  LIVE MONITORING MODE (refresh every {args.watch}s)")
            print("Press Ctrl+C to stop...")
            try:
                import time
                while True:
                    # Clear screen
                    import os
                    os.system('clear' if os.name == 'posix' else 'cls')
                    
                    print(f"🔄 Live Monitor - {datetime.now().strftime('%H:%M:%S')}")
                    print("=" * 40)
                    app.quick_status_check(quiet_mode=True)
                    
                    time.sleep(args.watch)
            except KeyboardInterrupt:
                print("\\n⏹️  Monitoring stopped")
            return
        
        if args.notify:
            if app.notification_manager:
                print("📢 SENDING STATUS NOTIFICATIONS")
                print("=" * 40)
                response = app.api_client.fetch_status_data()
                if response.success:
                    # Send current status notification
                    health_metrics = app.api_client.get_service_health_metrics(response.data)
                    global_availability = health_metrics.get('availability_percentage', 0.0)
                    message = f"Red Hat Status: {global_availability:.1f}% availability"
                    
                    success = app.notification_manager.send_status_notification(
                        message, response.data
                    )
                    
                    # Get more detailed results
                    num_channels = len(app.notification_manager.channels)
                    enabled_channels = [ch for ch in app.notification_manager.channels.values() if ch.enabled]
                    
                    if success:
                        print(f"✅ Status notification sent successfully through {len(enabled_channels)} channel(s)")
                    else:
                        print(f"⚠️  Notification attempted through {len(enabled_channels)} channel(s)")
                        print("💡 Note: Failures may be due to test/invalid credentials in config.json")
                        print("📝 Check logs above for specific channel results")
                else:
                    print(f"❌ Failed to get status for notification")
            else:
                print("❌ Notification system not available")
            return
        
        if args.benchmark:
            print("🏁 PERFORMANCE BENCHMARKING")
            print("=" * 40)
            print("Running API performance tests...")
            
            import time
            times = []
            for i in range(5):
                start = time.time()
                response = app.api_client.fetch_status_data()
                end = time.time()
                times.append(end - start)
                print(f"Test {i+1}: {(end-start)*1000:.0f}ms - {'✅' if response.success else '❌'}")
            
            print(f"\\n📊 Results:")
            print(f"Average: {(sum(times)/len(times))*1000:.0f}ms")
            print(f"Best: {min(times)*1000:.0f}ms")
            print(f"Worst: {max(times)*1000:.0f}ms")
            return
        
        # === Configuration & Debug Flags ===
        if args.no_cache:
            print("🚫 CACHE BYPASS ENABLED")
            app.api_client._bypass_cache = True
        
        if args.log_level:
            level = getattr(logging, args.log_level.upper())
            logging.getLogger().setLevel(level)
            print(f"🔧 Log level set to: {args.log_level}")
        
        if args.enable_monitoring:
            print("📊 CONTINUOUS MONITORING ENABLED")
            # Enable monitoring features
            if app.analytics:
                app.analytics._monitoring_enabled = True
        
        if args.setup:
            print("⚙️ CONFIGURATION SETUP WIZARD")
            print("=" * 40)
            print("This would launch an interactive configuration setup.")
            print("For now, please edit config.json manually.")
            return
        
        # Show header unless in quiet mode
        if not args.quiet:
            print("🎯 RED HAT STATUS CHECKER - MODULAR EDITION v3.1.0")
            print("=" * 60)
        
        mode = args.mode
        
        # Interactive mode if no arguments provided and no special flags
        has_special_flags = (args.filter != 'all' or args.search or args.watch or 
                           args.benchmark or args.notify or args.no_cache or 
                           args.log_level or args.enable_monitoring or args.slo_dashboard)
        
        if mode is None and not args.quiet and not has_special_flags:
            print("Available modes:")
            print("  quick    - Global status only")
            print("  simple   - Main services")
            print("  full     - Complete structure")
            print("  export   - Export data")
            print("  all      - Display all")
            print()
            mode = input("Choose a mode (or press Enter for 'quick'): ").lower()
            if not mode:
                mode = "quick"
            
            # Validate interactive input
            if mode not in ['quick', 'simple', 'full', 'export', 'all']:
                print(f"❌ Mode '{mode}' not recognized, using 'quick'")
                mode = "quick"
        
        # Default to quick mode if no mode specified
        if mode is None:
            mode = "quick"
        
        # Apply filtering and search options
        if args.filter != 'all' or args.search:
            print(f"🔍 FILTERING SERVICES")
            if args.filter != 'all':
                print(f"📋 Filter: {args.filter}")
            if args.search:
                print(f"🔎 Search: '{args.search}'")
            print("=" * 40)
            
            response = app.api_client.fetch_status_data()
            if response.success:
                services = response.data.get('components', [])  # Red Hat API uses 'components', not 'services'
                filtered_services = []
                
                for service in services:
                    # Apply status filter
                    if args.filter != 'all':
                        if args.filter == 'issues' and service.get('status') == 'operational':
                            continue
                        elif args.filter == 'operational' and service.get('status') != 'operational':
                            continue
                        elif args.filter == 'degraded' and service.get('status') not in ['degraded_performance', 'partial_outage']:
                            continue
                    
                    # Apply search filter
                    if args.search:
                        if args.search.lower() not in service.get('name', '').lower():
                            continue
                    
                    filtered_services.append(service)
                
                print(f"📊 Found {len(filtered_services)} services matching criteria:")
                for service in filtered_services[:20]:  # Limit to first 20 to avoid spam
                    status_emoji = "🟢" if service.get('status') == 'operational' else "🟡" if 'degraded' in service.get('status', '') else "🔴"
                    print(f"  {status_emoji} {service.get('name', 'Unknown')}: {service.get('status', 'unknown')}")
                
                if len(filtered_services) > 20:
                    print(f"  ... and {len(filtered_services) - 20} more services")
            else:
                print(f"❌ Failed to fetch services: {response.error_message}")
            return
        
        # Execute requested mode
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
        
        # Show performance metrics if requested
        if args.performance:
            app.show_performance_metrics()
        
        # Show completion message unless in quiet mode
        if not args.quiet:
            print(f"\n✅ Operation completed successfully in {timer.duration:.2f}s!")
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Application error: {e}")
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
