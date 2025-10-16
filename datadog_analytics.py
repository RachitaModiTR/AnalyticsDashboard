"""
Datadog Analytics Module
Handles Datadog logs functionality only
"""

import json
from datetime import datetime, timedelta
import requests
from config import Config


class DatadogApplicationKeyAnalytics:
    def __init__(self):
        self.api_key = Config.DD_API_KEY
        self.application_key = Config.DD_APPLICATION_KEY
        self.site = Config.DD_SITE
        self.base_url = f"https://api.{self.site}"
        
        # Simple cache for services list (cache for 10 minutes)
        self._services_cache = None
        self._services_cache_time = None
        self._services_cache_duration = 600  # 10 minutes in seconds
        
    def get_logs(self, query='*', from_time=None, to_time=None, limit=100, service=None, level=None, hours_back=24):
        """Fetch logs from Datadog using application key authentication"""
        # Calculate time range if not provided
        if not from_time:
            from_time = int((datetime.now() - timedelta(hours=hours_back)).timestamp())
        if not to_time:
            to_time = int(datetime.now().timestamp())
        
        try:
            # Use the correct API endpoint as per Datadog documentation
            url = f"{self.base_url}/api/v2/logs/events"
            
            # Build search query according to Datadog syntax
            search_query = query
            if service:
                search_query = f"service:{service} {search_query}"
            if level:
                search_query = f"status:{level.lower()} {search_query}"
            
            # Parameters as per Datadog API documentation
            params = {
                'filter[query]': search_query,
                'filter[from]': from_time * 1000,  # Convert to milliseconds
                'filter[to]': to_time * 1000,      # Convert to milliseconds
                'page[limit]': limit,
                'sort': '-timestamp'  # Sort by timestamp descending (newest first)
            }
            
            # Headers as per Datadog API documentation
            headers = {
                'DD-API-KEY': self.api_key,
                'DD-APPLICATION-KEY': self.application_key,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            print(f"Fetching logs from Datadog API: {url}")
            print(f"Query: {search_query}")
            print(f"Time range: {from_time} to {to_time}")
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"Successfully fetched {len(data.get('data', []))} logs")
                return self._process_logs_data(data)
            else:
                print(f"API Error fetching logs: {response.status_code} - {response.text}")
                # Return sample data if API fails for testing
                return self._generate_sample_logs(limit, service)
                
        except Exception as e:
            print(f"Error fetching logs: {e}")
            # Return sample data if API fails for testing
            return self._generate_sample_logs(limit, service)
    
    def _process_logs_data(self, api_response):
        """Process the raw API response and format it for the frontend with deduplication"""
        try:
            logs_data = api_response.get('data', [])
            processed_logs = []
            seen_logs = set()  # Track unique log combinations
            
            for log_entry in logs_data:
                # Extract attributes from the log entry
                attributes = log_entry.get('attributes', {})
                
                # Extract log level from various possible locations
                level = 'INFO'  # Default fallback
                if 'level' in attributes:
                    level = attributes.get('level', 'INFO')
                elif 'status' in attributes:
                    level = attributes.get('status', 'INFO').upper()
                elif 'attributes' in attributes and isinstance(attributes.get('attributes'), dict):
                    inner_attrs = attributes.get('attributes', {})
                    if '@l' in inner_attrs:
                        level = inner_attrs.get('@l', 'INFO').upper()
                    elif 'level' in inner_attrs:
                        level = inner_attrs.get('level', 'INFO').upper()
                
                processed_log = {
                    'id': log_entry.get('id'),
                    'timestamp': attributes.get('timestamp'),
                    'message': attributes.get('message', ''),
                    'service': attributes.get('service', ''),
                    'level': level,
                    'source': attributes.get('source', ''),
                    'host': attributes.get('host', ''),
                    'status': attributes.get('status', ''),
                    'tags': attributes.get('tags', []),
                    'attributes': attributes
                }
                
                # Create a unique key for deduplication
                # First try using the log ID (most reliable)
                if processed_log['id']:
                    unique_key = processed_log['id']
                else:
                    # For content-based deduplication, create a normalized message
                    # Remove dynamic parts like ClientMainId to group similar logs
                    message = processed_log['message']
                    if message:
                        # Remove UUIDs and dynamic IDs from the message for grouping
                        import re
                        # Remove UUIDs (like b2d71429-9a93-4ba2-b0ae-2da3eb243dcf)
                        normalized_message = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 'UUID', message)
                        # Remove other dynamic IDs (like ClientMainId: UUID)
                        normalized_message = re.sub(r'ClientMainId:\s*UUID', 'ClientMainId: UUID', normalized_message)
                        # Remove timestamps and other dynamic values
                        normalized_message = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', normalized_message)
                        normalized_message = re.sub(r'\d{2}:\d{2}:\d{2}', 'TIME', normalized_message)
                    else:
                        normalized_message = message
                    
                    # Normalize timestamp to group logs within the same minute
                    timestamp = processed_log['timestamp']
                    if timestamp:
                        # Parse timestamp and round to the nearest minute for grouping
                        from datetime import datetime
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            # Round to the nearest minute
                            rounded_timestamp = dt.replace(second=0, microsecond=0).isoformat()
                        except:
                            rounded_timestamp = timestamp
                    else:
                        rounded_timestamp = timestamp
                    
                    # Create unique key based on normalized content and rounded timestamp
                    unique_key = (
                        normalized_message,
                        processed_log['service'],
                        processed_log['level'],
                        rounded_timestamp
                    )
                
                # Only add if we haven't seen this exact log before
                if unique_key not in seen_logs:
                    seen_logs.add(unique_key)
                    processed_logs.append(processed_log)
            
            duplicates_removed = len(logs_data) - len(processed_logs)
            if duplicates_removed > 0:
                print(f"Processed {len(processed_logs)} unique logs from {len(logs_data)} total logs (removed {duplicates_removed} duplicates)")
            else:
                print(f"Processed {len(processed_logs)} unique logs from {len(logs_data)} total logs (no duplicates found)")
            return processed_logs
            
        except Exception as e:
            print(f"Error processing logs data: {e}")
            return []
    
    def get_log_statistics(self, query='*', service=None, level=None, hours_back=24):
        """Get log statistics for the specified time period"""
        try:
            # Get logs first to calculate statistics
            logs = self.get_logs(query=query, service=service, level=level, hours_back=hours_back, limit=1000)
            
            if not logs:
                return {
                    'total_logs': 0,
                    'unique_services': 0,
                    'error_count': 0,
                    'warning_count': 0,
                    'info_count': 0,
                    'services': []
                }
            
            # Calculate statistics
            total_logs = len(logs)
            services = {}
            error_count = 0
            warning_count = 0
            info_count = 0
            
            for log in logs:
                # Count by service
                service_name = log.get('service', 'unknown')
                services[service_name] = services.get(service_name, 0) + 1
                
                # Count by level
                level = log.get('level', '').upper()
                if level == 'ERROR':
                    error_count += 1
                elif level == 'WARN':
                    warning_count += 1
                elif level == 'INFO':
                    info_count += 1
            
            # Format services data
            services_list = [{'name': name, 'count': count} for name, count in services.items()]
            services_list.sort(key=lambda x: x['count'], reverse=True)
            
            return {
                'total_logs': total_logs,
                'unique_services': len(services),
                'error_count': error_count,
                'warning_count': warning_count,
                'info_count': info_count,
                'services': services_list
            }
            
        except Exception as e:
            print(f"Error calculating log statistics: {e}")
            return {
                'total_logs': 0,
                'unique_services': 0,
                'error_count': 0,
                'warning_count': 0,
                'info_count': 0,
                'services': []
            }
    
    def get_available_services(self, hours_back=24):
        """Get fixed list of specific services for consistent dropdown"""
        try:
            # Return fixed list of specific services
            fixed_services = [
                'ultrataxapiservices',
                'ultrataxclientservices', 
                'taxassistantservices'
            ]
            
            print(f"Returning fixed services list: {fixed_services}")
            return fixed_services
            
        except Exception as e:
            print(f"Error returning fixed services: {e}")
            return []
    
    def get_logs_summary(self, hours=24):
        """Get logs summary for the specified time period"""
        try:
            from_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
            to_time = int(datetime.now().timestamp())
            
            # Get logs data
            logs_data = self.get_logs('*', from_time, to_time, limit=1000)
            
            if logs_data and 'data' in logs_data:
                logs = logs_data['data']
                
                # Analyze logs
                summary = {
                    'total_logs': len(logs),
                    'time_range': {
                        'from': from_time,
                        'to': to_time,
                        'hours': hours
                    },
                    'logs_by_level': {},
                    'logs_by_service': {},
                    'recent_logs': []
                }
                
                # Count by level and service
                for log in logs:
                    attributes = log.get('attributes', {})
                    level = attributes.get('level', 'unknown')
                    service = attributes.get('service', 'unknown')
                    
                    summary['logs_by_level'][level] = summary['logs_by_level'].get(level, 0) + 1
                    summary['logs_by_service'][service] = summary['logs_by_service'].get(service, 0) + 1
                
                # Get recent logs (last 10)
                summary['recent_logs'] = logs[:10]
                
                return summary
            else:
                # Return sample summary if no data
                return self._generate_sample_logs_summary(hours)
                
        except Exception as e:
            print(f"Error generating logs summary: {e}")
            return self._generate_sample_logs_summary(hours)
    
    def send_log_to_datadog(self, message, level='info', service='analytics-dashboard', host=None, tags=None):
        """Send a log entry to Datadog"""
        try:
            url = f"{self.base_url}/api/v1/logs"
            
            # Prepare log data
            log_data = {
                'message': message,
                'level': level,
                'service': service,
                'timestamp': int(datetime.now().timestamp() * 1000),  # Convert to milliseconds
                'host': host or 'localhost',
                'tags': tags or []
            }
            
            headers = {
                'DD-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=log_data, headers=headers)
            
            if response.status_code == 202:
                return True
            else:
                print(f"Error sending log: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending log: {e}")
            return False
    
    def _generate_sample_logs(self, limit=100, services=None):
        """Generate sample logs data for demonstration"""
        if services is None:
            services = ['web-app', 'api-server', 'database', 'cache']
        
        levels = ['info', 'warn', 'error', 'debug']
        sample_logs = []
        
        for i in range(min(limit, 50)):  # Limit to 50 sample logs
            service = services[i % len(services)]
            level = levels[i % len(levels)]
            
            log_entry = {
                'id': f'sample-log-{i}',
                'type': 'log',
                'attributes': {
                    'timestamp': int((datetime.now() - timedelta(minutes=i)).timestamp() * 1000),
                    'message': f'Sample log message {i} from {service}',
                    'level': level,
                    'service': service,
                    'host': 'sample-host',
                    'tags': [f'tag{i % 3}', 'sample']
                }
            }
            sample_logs.append(log_entry)
        
        return {
            'data': sample_logs,
            'meta': {
                'page': {'total_count': len(sample_logs)},
                'status': 'sample_data'
            }
        }
    
    def _generate_sample_logs_summary(self, hours=24):
        """Generate sample logs summary for demonstration"""
        return {
            'total_logs': 150,
            'time_range': {
                'from': int((datetime.now() - timedelta(hours=hours)).timestamp()),
                'to': int(datetime.now().timestamp()),
                'hours': hours
            },
            'logs_by_level': {
                'info': 80,
                'warn': 40,
                'error': 20,
                'debug': 10
            },
            'logs_by_service': {
                'web-app': 60,
                'api-server': 45,
                'database': 30,
                'cache': 15
            },
            'recent_logs': [
                {
                    'id': 'sample-1',
                    'message': 'Sample recent log message 1',
                        'level': 'info',
                    'service': 'web-app',
                    'timestamp': int(datetime.now().timestamp() * 1000)
                },
                {
                    'id': 'sample-2', 
                    'message': 'Sample recent log message 2',
                    'level': 'warn',
                    'service': 'api-server',
                    'timestamp': int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000)
                }
            ],
            'status': 'sample_data'
        }
