"""
Red Hat Status Checker - Web UI (Flask App)

This module contains a simple Flask web application to display
the Red Hat status on a web page.
"""

from flask import Flask, render_template_string
from ..core.api_client import fetch_status_data, get_api_client

# It's better to create the app in a function to allow for configuration
# but for this simple stub, a global app is fine.
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Red Hat Status</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 2rem auto; padding: 0 1rem; background-color: #f8f9fa; }
        .container { background-color: #fff; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1, h2 { color: #c00; } /* Red Hat Red */
        .status-banner { padding: 1rem; margin-bottom: 1.5rem; border-radius: 5px; color: #fff; text-align: center; font-size: 1.2rem; }
        .status-operational { background-color: #28a745; }
        .status-issue { background-color: #dc3545; }
        .status-degraded { background-color: #ffc107; color: #333; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 2rem; }
        .metric { background-color: #f1f1f1; padding: 1rem; border-radius: 5px; text-align: center; }
        .metric h3 { margin-top: 0; color: #555; }
        .metric p { font-size: 2rem; font-weight: bold; margin-bottom: 0; color: #c00; }
        .footer { text-align: center; margin-top: 2rem; color: #666; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Red Hat Service Status</h1>

        {% if error %}
            <div class="status-banner status-issue">
                <h2>Error</h2>
                <p>{{ error }}</p>
            </div>
        {% else %}
            <div class="status-banner {{ status_class }}">
                <h2>{{ health.overall_status }}</h2>
            </div>
            <p><strong>Last Updated:</strong> {{ health.last_updated }}</p>

            <div class="metrics">
                <div class="metric">
                    <h3>Global Availability</h3>
                    <p>{{ '%.1f'|format(health.availability_percentage) }}%</p>
                </div>
                <div class="metric">
                    <h3>Operational Services</h3>
                    <p>{{ health.operational_services }} / {{ health.total_services }}</p>
                </div>
                <div class="metric">
                    <h3>Services with Issues</h3>
                    <p>{{ health.services_with_issues }}</p>
                </div>
            </div>
        {% endif %}

        <div class="footer">
            <p>Red Hat Status Checker | Last refresh: {{ refresh_time }}</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """
    Main route that fetches status and renders the HTML page.
    """
    api_client = get_api_client()
    response = fetch_status_data()

    if not response.success:
        return render_template_string(
            HTML_TEMPLATE,
            error=response.error_message,
            refresh_time=get_current_time()
        )

    health_metrics = api_client.get_service_health_metrics(response.data)

    status_class = 'status-operational'
    if health_metrics['status_indicator'] in ['major', 'critical']:
        status_class = 'status-issue'
    elif health_metrics['status_indicator'] in ['minor', 'maintenance']:
        status_class = 'status-degraded'

    return render_template_string(
        HTML_TEMPLATE,
        health=health_metrics,
        status_class=status_class,
        error=None,
        refresh_time=get_current_time()
    )

def get_current_time():
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def run_web_server(port=5000, debug=False):
    """
    Runs the Flask web server.
    """
    print(f"🌍 Starting web server on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
