"""
Red Hat Status Checker - Presentation Module

This module handles all the console output and presentation logic,
keeping the main application logic clean and focused on functionality.

Author: Red Hat Status Checker v3.1.0 - Modular Edition
"""

from typing import Dict, Any, List

class Presenter:
    """Handles all formatted output to the console."""

    def present_quick_status(self, health_metrics: dict, cached: bool, quiet_mode: bool = False) -> None:
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

    def present_simple_check(self, components: List[Dict[str, Any]]) -> None:
        """Presents the status of main services."""
        print("\n" + "="*60)
        print("🏢 RED HAT MAIN SERVICES")
        print("="*60)

        print(f"📊 Total components in API: {len(components)}")

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

        total_services = operational_count + problem_count
        if total_services > 0:
            percentage = (operational_count / total_services) * 100
            print(f"📊 Availability: {percentage:.1f}%")

    def present_full_check(self, components: List[Dict[str, Any]]) -> None:
        """Presents the complete service hierarchy."""
        print("\n" + "="*80)
        print("🏗️  COMPLETE RED HAT STRUCTURE - ALL SERVICES")
        print("="*80)

        main_services = {}
        sub_services = {}

        for comp in components:
            comp_id = comp.get('id')
            name = comp.get('name', 'Unnamed service')
            status = comp.get('status', 'unknown')
            group_id = comp.get('group_id')

            if group_id is None:
                main_services[comp_id] = {'name': name, 'status': status, 'id': comp_id}
            else:
                if group_id not in sub_services:
                    sub_services[group_id] = []
                sub_services[group_id].append({'name': name, 'status': status, 'id': comp_id})

        print(f"📊 STATISTICS:")
        print(f"   • Main services: {len(main_services)}")
        print(f"   • Sub-service groups: {len(sub_services)}")
        print(f"   • Total components: {len(components)}")
        print()

        total_operational = 0
        total_problems = 0

        for service_id, service_info in main_services.items():
            name = service_info['name']
            status = service_info['status']

            if status == "operational":
                print(f"🟢 {name}")
                total_operational += 1
            else:
                print(f"🔴 {name} - {status.upper()}")
                total_problems += 1

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

                if sub_operational + sub_problems > 0:
                    sub_percentage = (sub_operational / (sub_operational + sub_problems)) * 100
                    print(f"   📈 Group availability: {sub_percentage:.1f}%")

            print()

        print("=" * 80)
        print(f"📊 TOTAL OVERALL: {total_operational} operational, {total_problems} with issues")

        total_services = total_operational + total_problems
        if total_services > 0:
            percentage = (total_operational / total_services) * 100
            print(f"📈 Availability rate: {percentage:.1f}%")

            if percentage >= 95:
                print("🟢 Overall health: EXCELLENT")
            elif percentage >= 90:
                print("🟡 Overall health: GOOD")
            elif percentage >= 80:
                print("🟠 Overall health: FAIR")
            else:
                print("🔴 Overall health: POOR")

    def present_performance_metrics(self, performance_metrics, cache_info, db_stats=None, notif_stats=None) -> None:
        """Displays performance metrics."""
        print("\n⚡ PERFORMANCE METRICS")
        print("=" * 50)
        print(f"🕒 Session Duration: {performance_metrics.duration:.2f}s")
        print(f"🌐 API Calls: {performance_metrics.api_calls}")
        print(f"📋 Cache Entries: {cache_info.entries_count}")
        print(f"💾 Cache Size: {cache_info.size_human}")
        print(f"📈 Cache Hit Ratio: {cache_info.hit_ratio:.1f}%")

        if hasattr(performance_metrics, 'errors') and performance_metrics.errors:
            print(f"❌ Errors: {len(performance_metrics.errors)}")

        if db_stats:
            print(f"\n📊 DATABASE METRICS")
            print(f"📄 Total Snapshots: {db_stats.get('service_snapshots_count', 0)}")
            print(f"📈 Service Metrics: {db_stats.get('service_metrics_count', 0)}")
            print(f"🚨 Active Alerts: {db_stats.get('system_alerts_count', 0)}")
            print(f"💾 DB Size: {db_stats.get('database_size_bytes', 0) / 1024 / 1024:.1f} MB")

        if notif_stats:
            print(f"\n📬 NOTIFICATION METRICS")
            print(f"📧 Sent (24h): {notif_stats.get('notifications_24h', 0)}")
            print(f"📧 Sent (7d): {notif_stats.get('notifications_7d', 0)}")
            print(f"📡 Active Channels: {notif_stats.get('active_channels', 0)}")

    def present_error(self, message: str) -> None:
        """Presents an error message."""
        print(f"❌ {message}")

    def present_message(self, message: str) -> None:
        """Presents a generic message."""
        print(message)
