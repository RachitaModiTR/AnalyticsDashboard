"""
Datadog Analytics Module
Handles all Datadog-related functionality including metrics fetching and analytics
"""

import json
from datetime import datetime, timedelta
import requests
import plotly.graph_objs as go
import plotly
from config import Config


class DatadogApplicationKeyAnalytics:
    def __init__(self):
        self.api_key = Config.DD_API_KEY
        self.application_key = Config.DD_APPLICATION_KEY
        self.site = Config.DD_SITE
        self.base_url = f"https://api.{self.site}"
        
    def get_metrics_data(self, metric_name, from_time=None, to_time=None, tags=None):
        """Fetch metrics data using application key authentication"""
        if not from_time:
            from_time = int((datetime.now() - timedelta(hours=24)).timestamp())
        if not to_time:
            to_time = int(datetime.now().timestamp())
        
        try:
            # Use the browser API endpoint that works with client tokens
            url = f"{self.base_url}/api/v1/query"
            
            # Build query string
            query_parts = [metric_name]
            if tags:
                query_parts.append(f"{{{','.join(tags)}}}")
            query = ''.join(query_parts)
            
            params = {
                'from': from_time,
                'to': to_time,
                'query': query
            }
            
            headers = {
                'DD-API-KEY': self.api_key,
                'DD-APPLICATION-KEY': self.application_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error fetching metrics: {e}")
            return None
    
    def get_available_metrics(self):
        """Get list of available metrics from Datadog"""
        try:
            # Try to get actual metrics from Datadog API
            url = f"{self.base_url}/api/v1/metrics"
            headers = {
                'DD-API-KEY': self.api_key,
                'DD-APPLICATION-KEY': self.application_key,
                'Content-Type': 'application/json'
            }
            
            # Get metrics from the last 24 hours
            from_time = int((datetime.now() - timedelta(hours=24)).timestamp())
            params = {
                'from': from_time
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if 'metrics' in data and data['metrics']:
                    return data['metrics'][:20]  # Return first 20 metrics
                else:
                    print("No metrics found in Datadog account")
                    return self._get_fallback_metrics()
            else:
                print(f"API Error fetching metrics: {response.status_code} - {response.text}")
                return self._get_fallback_metrics()
                
        except Exception as e:
            print(f"Error fetching available metrics: {e}")
            return self._get_fallback_metrics()
    
    def _get_fallback_metrics(self):
        """Fallback metrics when API fails or no data available"""
        return [
            "system.cpu.user",
            "system.mem.used", 
            "system.disk.used",
            "system.load.1",
            "nginx.requests",
            "postgresql.connections",
            "redis.connected_clients",
            "aws.ec2.cpuutilization",
            "aws.rds.cpuutilization",
            "docker.cpu.usage",
            "docker.mem.usage"
        ]
    
    def get_all_dashboards(self):
        """Get all dashboards from Datadog using the Dashboard API"""
        try:
            url = f"{self.base_url}/api/v1/dashboard"
            headers = {
                'DD-API-KEY': self.api_key,
                'DD-APPLICATION-KEY': self.application_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"Retrieved {len(data.get('dashboards', []))} dashboards from Datadog")
                return data
            else:
                print(f"Dashboard API Error: {response.status_code} - {response.text}")
                return self._generate_sample_dashboards()
                
        except Exception as e:
            print(f"Error fetching dashboards: {e}")
            return self._generate_sample_dashboards()
    
    def get_dashboard_by_id(self, dashboard_id):
        """Get specific dashboard data by ID"""
        try:
            url = f"{self.base_url}/api/v1/dashboard/{dashboard_id}"
            headers = {
                'DD-API-KEY': self.api_key,
                'DD-APPLICATION-KEY': self.application_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Dashboard API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error fetching dashboard: {e}")
            return None
    
    def get_dashboard_data(self, dashboard_id=None):
        """Get dashboard data if dashboard ID is provided (legacy method)"""
        if not dashboard_id:
            return None
        return self.get_dashboard_by_id(dashboard_id)
    
    def create_analytics_dashboard(self, metrics_data):
        """Create analytics dashboard data"""
        if not metrics_data or 'series' not in metrics_data:
            return None
        
        dashboard_data = {
            'total_metrics': len(metrics_data.get('series', [])),
            'time_range': {
                'from': datetime.fromtimestamp(metrics_data.get('from', 0)),
                'to': datetime.fromtimestamp(metrics_data.get('to', 0))
            },
            'metrics_summary': []
        }
        
        for series in metrics_data.get('series', []):
            if 'pointlist' in series and series['pointlist']:
                values = [point[1] for point in series['pointlist'] if point[1] is not None]
                if values:
                    dashboard_data['metrics_summary'].append({
                        'metric_name': series.get('metric', 'Unknown'),
                        'avg_value': sum(values) / len(values),
                        'max_value': max(values),
                        'min_value': min(values),
                        'data_points': len(values)
                    })
        
        return dashboard_data

    def get_chart_data(self, metric_name, hours=24, chart_type='line'):
        """Get chart data for a specific metric"""
        from_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
        to_time = int(datetime.now().timestamp())
        
        data = self.get_metrics_data(metric_name, from_time, to_time)
        
        if not data or 'series' not in data or not data['series']:
            return None
        
        series = data['series'][0]
        if 'pointlist' not in series or not series['pointlist']:
            return None
        
        # Prepare chart data
        timestamps = [datetime.fromtimestamp(point[0]/1000) for point in series['pointlist']]
        values = [point[1] for point in series['pointlist'] if point[1] is not None]
        
        # Create Plotly chart
        if chart_type == 'line':
            fig = go.Figure(data=go.Scatter(
                x=timestamps,
                y=values,
                mode='lines+markers',
                name=metric_name,
                line=dict(width=2)
            ))
        elif chart_type == 'bar':
            fig = go.Figure(data=go.Bar(
                x=timestamps,
                y=values,
                name=metric_name
            ))
        else:
            fig = go.Figure(data=go.Scatter(
                x=timestamps,
                y=values,
                mode='lines+markers',
                name=metric_name
            ))
        
        fig.update_layout(
            title=f'{metric_name} - Last {hours} hours',
            xaxis_title='Time',
            yaxis_title='Value',
            hovermode='x unified'
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    def _generate_sample_data(self, metrics, hours=24):
        """Generate sample data for demonstration when no real data is available"""
        import random
        
        analytics_data = {
            'metrics_summary': [],
            'time_range': {
                'from': (datetime.now() - timedelta(hours=hours)).strftime('%a, %d %b %Y %H:%M:%S GMT'),
                'to': datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
            },
            'total_metrics': len(metrics),
            'note': 'Sample data - No real metrics found in your Datadog account'
        }
        
        for metric in metrics:
            # Generate realistic sample values based on metric type
            if 'cpu' in metric.lower():
                current = random.uniform(20, 80)
                avg = random.uniform(30, 70)
                max_val = random.uniform(80, 95)
                min_val = random.uniform(5, 25)
            elif 'mem' in metric.lower() or 'memory' in metric.lower():
                current = random.uniform(40, 90)
                avg = random.uniform(50, 80)
                max_val = random.uniform(85, 95)
                min_val = random.uniform(20, 40)
            elif 'disk' in metric.lower():
                current = random.uniform(30, 80)
                avg = random.uniform(40, 70)
                max_val = random.uniform(75, 90)
                min_val = random.uniform(10, 30)
            else:
                current = random.uniform(10, 100)
                avg = random.uniform(20, 80)
                max_val = random.uniform(80, 100)
                min_val = random.uniform(0, 20)
            
            analytics_data['metrics_summary'].append({
                'metric': metric,
                'current_value': round(current, 2),
                'average_value': round(avg, 2),
                'max_value': round(max_val, 2),
                'min_value': round(min_val, 2),
                'data_points': random.randint(50, 200)
            })
        
        return analytics_data
    
    def _generate_sample_chart_data(self, metric_name, hours=24, chart_type='line'):
        """Generate sample chart data for demonstration"""
        import random
        import plotly.graph_objs as go
        
        # Generate time series data
        from_time = datetime.now() - timedelta(hours=hours)
        time_points = []
        values = []
        
        # Generate realistic data based on metric type
        if 'cpu' in metric_name.lower():
            base_value = random.uniform(30, 70)
            trend = random.uniform(-0.5, 0.5)
        elif 'mem' in metric_name.lower() or 'memory' in metric_name.lower():
            base_value = random.uniform(50, 80)
            trend = random.uniform(-0.3, 0.3)
        elif 'disk' in metric_name.lower():
            base_value = random.uniform(40, 70)
            trend = random.uniform(-0.2, 0.2)
        else:
            base_value = random.uniform(20, 80)
            trend = random.uniform(-0.4, 0.4)
        
        # Generate 24 data points (one per hour)
        for i in range(24):
            time_point = from_time + timedelta(hours=i)
            time_points.append(time_point)
            
            # Add some realistic variation
            noise = random.uniform(-10, 10)
            value = max(0, min(100, base_value + (i * trend) + noise))
            values.append(round(value, 2))
        
        if chart_type == 'line':
            fig = go.Figure(data=go.Scatter(
                x=time_points,
                y=values,
                mode='lines+markers',
                name=metric_name,
                line=dict(width=2)
            ))
        elif chart_type == 'bar':
            fig = go.Figure(data=go.Bar(
                x=time_points,
                y=values,
                name=metric_name
            ))
        else:  # default to line
            fig = go.Figure(data=go.Scatter(
                x=time_points,
                y=values,
                mode='lines+markers',
                name=metric_name,
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title=f'{metric_name} - Sample Data (Last {hours} hours)',
            xaxis_title='Time',
            yaxis_title='Value',
            hovermode='x unified'
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    def get_logs(self, query="*", from_time=None, to_time=None, limit=100, service=None):
        """Fetch existing logs from Datadog using the Logs API v2 GET endpoint"""
        if not from_time:
            from_time = int((datetime.now() - timedelta(hours=24)).timestamp())
        if not to_time:
            to_time = int(datetime.now().timestamp())
        
        try:
            # Use the correct Datadog Logs API v2 GET endpoint for searching logs
            # Based on: https://docs.datadoghq.com/api/latest/logs/#search-logs-get
            url = f"{self.base_url}/api/v2/logs/events"
            
            # Build the search query according to Datadog's query syntax
            search_query = query
            if service:
                search_query = f"service:{service} {query}"
            
            # Parameters for GET request as per documentation
            params = {
                "filter[query]": search_query,
                "filter[from]": from_time * 1000,  # Convert to milliseconds
                "filter[to]": to_time * 1000,      # Convert to milliseconds
                "page[limit]": limit,
                "sort": "timestamp"
            }
            
            headers = {
                'DD-API-KEY': self.api_key,
                'DD-APPLICATION-KEY': self.application_key,
                'Accept': 'application/json'
            }
            
            print(f"Fetching logs from Datadog with query: {search_query}")
            print(f"Time range: {from_time} to {to_time}")
            
            # Use GET method as shown in the documentation
            response = requests.get(url, params=params, headers=headers)
            
            print(f"Datadog API Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Retrieved {len(data.get('data', []))} logs from Datadog")
                return data
            else:
                print(f"Logs API Error: {response.status_code} - {response.text}")
                # Return empty result instead of sample data
                return {
                    "data": [],
                    "meta": {
                        "page": {"after": None},
                        "status": "error",
                        "error": f"API Error: {response.status_code}"
                    }
                }
                
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return {
                "data": [],
                "meta": {
                    "page": {"after": None},
                    "status": "error", 
                    "error": str(e)
                }
            }
    
    def get_logs_summary(self, hours=24):
        """Get logs summary for the specified time period from real Datadog logs"""
        try:
            from_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
            to_time = int(datetime.now().timestamp())
            
            # Get real logs data from Datadog
            logs_data = self.get_logs(from_time=from_time, to_time=to_time, limit=1000)
            
            if not logs_data or 'data' not in logs_data:
                return {
                    'total_logs': 0,
                    'time_range': {
                        'from': datetime.fromtimestamp(from_time),
                        'to': datetime.fromtimestamp(to_time)
                    },
                    'log_levels': {},
                    'services': {},
                    'error_logs': [],
                    'recent_logs': [],
                    'status': 'no_data',
                    'message': 'No logs found in the specified time range'
                }
            
            logs = logs_data.get('data', [])
            
            # Analyze real logs from Datadog
            summary = {
                'total_logs': len(logs),
                'time_range': {
                    'from': datetime.fromtimestamp(from_time),
                    'to': datetime.fromtimestamp(to_time)
                },
                'log_levels': {},
                'services': {},
                'error_logs': [],
                'recent_logs': logs[:10],  # Last 10 logs
                'status': 'success'
            }
            
            # Count log levels and services from real data
            for log in logs:
                attributes = log.get('attributes', {})
                level = attributes.get('level', 'unknown')
                service = attributes.get('service', 'unknown')
                
                # Count log levels
                summary['log_levels'][level] = summary['log_levels'].get(level, 0) + 1
                
                # Count services
                summary['services'][service] = summary['services'].get(service, 0) + 1
                
                # Collect error logs
                if level.lower() in ['error', 'critical', 'fatal']:
                    summary['error_logs'].append({
                        'timestamp': attributes.get('timestamp', ''),
                        'level': level,
                        'service': service,
                        'message': attributes.get('message', ''),
                        'host': attributes.get('host', '')
                    })
            
            print(f"Logs summary: {summary['total_logs']} total logs, {len(summary['services'])} services")
            return summary
            
        except Exception as e:
            print(f"Error creating logs summary: {e}")
            return {
                'total_logs': 0,
                'time_range': {
                    'from': datetime.now() - timedelta(hours=hours),
                    'to': datetime.now()
                },
                'log_levels': {},
                'services': {},
                'error_logs': [],
                'recent_logs': [],
                'status': 'error',
                'message': f'Error fetching logs: {str(e)}'
            }
    
    def _get_available_services(self):
        """Get available services from actual Datadog logs"""
        try:
            # First try to get services from actual logs
            logs_data = self.get_logs(limit=1000)  # Get more logs to find services
            
            if logs_data and 'data' in logs_data and logs_data['data']:
                services = set()
                for log in logs_data['data']:
                    attributes = log.get('attributes', {})
                    service = attributes.get('service', '')
                    if service and service != 'unknown':
                        services.add(service)
                
                if services:
                    print(f"Found {len(services)} services from logs: {list(services)}")
                    return list(services)
            
            # Fallback: Try to get services from metrics API
            url = f"{self.base_url}/api/v1/metrics"
            headers = {
                'DD-API-KEY': self.api_key,
                'DD-APPLICATION-KEY': self.application_key,
                'Accept': 'application/json'
            }
            
            from_time = int((datetime.now() - timedelta(hours=24)).timestamp())
            params = {'from': from_time}
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if 'metrics' in data and data['metrics']:
                    # Extract service names from metric names
                    services = set()
                    for metric in data['metrics'][:20]:  # Check first 20 metrics
                        if '.' in metric:
                            parts = metric.split('.')
                            if len(parts) > 1:
                                services.add(parts[0].title())
                    
                    if services:
                        print(f"Found {len(services)} services from metrics: {list(services)}")
                        return list(services)
            
            # Final fallback to default services
            print("No services found, using defaults")
            return ['TaxAssistant', 'PaymentService', 'UserService', 'NotificationService']
            
        except Exception as e:
            print(f"Error getting available services: {e}")
            return ['TaxAssistant', 'PaymentService', 'UserService', 'NotificationService']
    
    def _generate_sample_logs(self, limit=100, services=None):
        """Generate sample logs data for demonstration"""
        import random
        
        if not services:
            services = self._get_available_services()
        
        sample_logs = []
        levels = ['info', 'warning', 'error', 'debug']
        
        for i in range(min(limit, 50)):
            timestamp = int((datetime.now() - timedelta(minutes=random.randint(0, 1440))).timestamp() * 1000)
            service = random.choice(services)
            level = random.choice(levels)
            
            log_entry = {
                "id": f"sample-log-{i}",
                "attributes": {
                    "timestamp": timestamp,
                    "level": level,
                    "service": service,
                    "message": f"Sample log message from {service} - {level} level",
                    "host": f"host-{random.randint(1, 5)}",
                    "source": "application",
                    "status": "info" if level == 'info' else 'error' if level == 'error' else 'warning'
                }
            }
            sample_logs.append(log_entry)
        
        return {
            "data": sample_logs,
            "meta": {
                "page": {
                    "after": None
                }
            }
        }
    
    def _generate_sample_logs_summary(self, hours=24):
        """Generate sample logs summary for demonstration"""
        return {
            'total_logs': 1250,
            'time_range': {
                'from': datetime.now() - timedelta(hours=hours),
                'to': datetime.now()
            },
            'log_levels': {
                'info': 800,
                'warning': 300,
                'error': 120,
                'debug': 30
            },
            'services': {
                'TaxAssistant': 500,
                'PaymentService': 300,
                'UserService': 250,
                'NotificationService': 200
            },
            'error_logs': [
                {
                    'timestamp': datetime.now() - timedelta(minutes=30),
                    'level': 'error',
                    'service': 'TaxAssistant',
                    'message': 'Failed to calculate tax for order #12345',
                    'host': 'web-server-1'
                },
                {
                    'timestamp': datetime.now() - timedelta(minutes=45),
                    'level': 'error',
                    'service': 'PaymentService',
                    'message': 'Payment gateway timeout for transaction #67890',
                    'host': 'payment-server-2'
                }
            ],
            'recent_logs': [
                {
                    'id': 'log-1',
                    'attributes': {
                        'timestamp': int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000),
                        'level': 'info',
                        'service': 'TaxAssistant',
                        'message': 'Tax calculation completed successfully',
                        'host': 'web-server-1'
                    }
                }
            ]
        }
    
    def _generate_sample_dashboards(self):
        """Generate sample dashboards for demonstration when no real data is available"""
        return {
            'dashboards': [
                {
                    'id': 'sample-dashboard-1',
                    'title': 'System Overview Dashboard',
                    'description': 'Comprehensive system monitoring dashboard',
                    'author_name': 'System Admin',
                    'url': f'https://app.{self.site}/dashboard/sample-dashboard-1',
                    'created_at': (datetime.now() - timedelta(days=30)).isoformat(),
                    'modified_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                    'is_read_only': False,
                    'widgets': [
                        {
                            'id': 1,
                            'definition': {
                                'type': 'timeseries',
                                'title': 'CPU Usage',
                                'requests': [{'q': 'avg:system.cpu.user{*}', 'display_type': 'line'}]
                            }
                        },
                        {
                            'id': 2,
                            'definition': {
                                'type': 'timeseries',
                                'title': 'Memory Usage',
                                'requests': [{'q': 'avg:system.mem.used{*}', 'display_type': 'line'}]
                            }
                        }
                    ]
                },
                {
                    'id': 'sample-dashboard-2',
                    'title': 'Application Performance',
                    'description': 'Application metrics and performance monitoring',
                    'author_name': 'DevOps Team',
                    'url': f'https://app.{self.site}/dashboard/sample-dashboard-2',
                    'created_at': (datetime.now() - timedelta(days=15)).isoformat(),
                    'modified_at': (datetime.now() - timedelta(hours=5)).isoformat(),
                    'is_read_only': False,
                    'widgets': [
                        {
                            'id': 3,
                            'definition': {
                                'type': 'query_value',
                                'title': 'Response Time',
                                'requests': [{'q': 'avg:http.response_time{*}', 'aggregator': 'avg'}]
                            }
                        },
                        {
                            'id': 4,
                            'definition': {
                                'type': 'toplist',
                                'title': 'Top Endpoints by Traffic',
                                'requests': [{'q': 'top(avg:http.requests{*} by {endpoint}, 10, mean, desc)'}]
                            }
                        }
                    ]
                },
                {
                    'id': 'sample-dashboard-3',
                    'title': 'Infrastructure Health',
                    'description': 'Infrastructure monitoring and alerting',
                    'author_name': 'Infrastructure Team',
                    'url': f'https://app.{self.site}/dashboard/sample-dashboard-3',
                    'created_at': (datetime.now() - timedelta(days=7)).isoformat(),
                    'modified_at': (datetime.now() - timedelta(minutes=30)).isoformat(),
                    'is_read_only': True,
                    'widgets': [
                        {
                            'id': 5,
                            'definition': {
                                'type': 'check_status',
                                'title': 'Service Health Checks',
                                'check': 'service:health_check'
                            }
                        },
                        {
                            'id': 6,
                            'definition': {
                                'type': 'heatmap',
                                'title': 'Request Distribution',
                                'requests': [{'q': 'avg:http.requests{*} by {service,host}'}]
                            }
                        }
                    ]
                }
            ]
        }
    
    def get_available_services(self):
        """Get list of available services from Datadog"""
        return self._get_available_services()
    
    def get_all_dashboards(self):
        """Get all dashboards from Datadog using the Dashboards API"""
        try:
            # Use the Datadog Dashboards API endpoint
            # Based on: https://docs.datadoghq.com/api/latest/dashboards/#get-all-dashboards
            url = f"{self.base_url}/api/v1/dashboard"
            
            headers = {
                'DD-API-KEY': self.api_key,
                'DD-APPLICATION-KEY': self.application_key,
                'Accept': 'application/json'
            }
            
            print("Fetching all dashboards from Datadog...")
            response = requests.get(url, headers=headers)
            
            print(f"Dashboards API Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                dashboards = data.get('dashboards', [])
                print(f"Retrieved {len(dashboards)} dashboards from Datadog")
                return dashboards
            else:
                print(f"Dashboards API Error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error fetching dashboards: {e}")
            return []
    
    def get_dashboard_by_id(self, dashboard_id):
        """Get a specific dashboard by ID from Datadog"""
        try:
            # Use the Datadog Dashboard API endpoint for specific dashboard
            url = f"{self.base_url}/api/v1/dashboard/{dashboard_id}"
            
            headers = {
                'DD-API-KEY': self.api_key,
                'DD-APPLICATION-KEY': self.application_key,
                'Accept': 'application/json'
            }
            
            print(f"Fetching dashboard {dashboard_id} from Datadog...")
            response = requests.get(url, headers=headers)
            
            print(f"Dashboard API Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Retrieved dashboard: {data.get('title', 'Unknown')}")
                return data
            else:
                print(f"Dashboard API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error fetching dashboard {dashboard_id}: {e}")
            return None
    
    def get_dashboard_summary(self):
        """Get summary of all dashboards"""
        try:
            dashboards = self.get_all_dashboards()
            
            if not dashboards:
                return {
                    'total_dashboards': 0,
                    'dashboards': [],
                    'status': 'no_data',
                    'message': 'No dashboards found in your Datadog account'
                }
            
            # Analyze dashboards
            summary = {
                'total_dashboards': len(dashboards),
                'dashboards': dashboards,
                'status': 'success'
            }
            
            print(f"Dashboard summary: {summary['total_dashboards']} total dashboards")
            return summary
            
        except Exception as e:
            print(f"Error creating dashboard summary: {e}")
            return {
                'total_dashboards': 0,
                'dashboards': [],
                'status': 'error',
                'message': f'Error fetching dashboards: {str(e)}'
            }
    
    def send_log_to_datadog(self, message, level="info", service="default", host=None, tags=None):
        """Send a log entry to Datadog using the Logs API v2 ingestion endpoint"""
        try:
            # Use the Datadog Logs Intake API endpoint
            intake_url = f"https://http-intake.logs.{self.site}/api/v2/logs"
            
            # Prepare the log entry
            log_entry = {
                "timestamp": int(datetime.now().timestamp() * 1000),  # milliseconds
                "level": level,
                "message": message,
                "service": service,
                "host": host or "localhost",
                "source": "analytics-dashboard"
            }
            
            # Add tags if provided
            if tags:
                log_entry["tags"] = tags
            
            headers = {
                'DD-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            # Send the log entry
            response = requests.post(intake_url, json=log_entry, headers=headers)
            
            if response.status_code == 202:  # 202 Accepted is the expected response
                return True
            else:
                print(f"Log ingestion error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending log to Datadog: {e}")
            return False