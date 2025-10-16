import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import threading
import time

class ContextStorage:
    """Context storage system for capturing and managing API data for chatbot context"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, storage_dir="context_data"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ContextStorage, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, storage_dir="context_data"):
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        
        self.storage_dir = storage_dir
        self.context_file = os.path.join(storage_dir, "api_context.json")
        self.lock = threading.Lock()
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize context structure
        self.context = {
            "last_updated": None,
            "data_sources": {
                "datadog": {
                    "metrics": {},
                    "charts": {},
                    "logs": {},
                    "last_fetch": None,
                    "status": "not_fetched"
                },
                "github": {
                    "pull_requests": [],
                    "repositories": [],
                    "analytics": {},
                    "last_fetch": None,
                    "status": "not_fetched"
                },
                "azuredevops": {
                    "work_items": [],
                    "pull_requests": [],
                    "analytics": {},
                    "last_fetch": None,
                    "status": "not_fetched"
                },
                "figma": {
                    "files": [],
                    "projects": [],
                    "analytics": {},
                    "last_fetch": None,
                    "status": "not_fetched"
                }
            },
            "summary": {
                "total_work_items": 0,
                "total_pull_requests": 0,
                "total_repositories": 0,
                "total_metrics": 0,
                "last_activity": None
            }
        }
        
        # Load existing context
        self.load_context()
        
        # Mark as initialized
        self._initialized = True
    
    def load_context(self):
        """Load existing context from file"""
        try:
            if os.path.exists(self.context_file):
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    self.context = json.load(f)
                print(f"📁 Loaded context from {self.context_file}")
            else:
                print(f"📁 Created new context file at {self.context_file}")
        except Exception as e:
            print(f"❌ Error loading context: {e}")
    
    def save_context(self):
        """Save context to file"""
        try:
            with self.lock:
                self.context["last_updated"] = datetime.now().isoformat()
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.context_file), exist_ok=True)
                with open(self.context_file, 'w', encoding='utf-8') as f:
                    json.dump(self.context, f, indent=2, ensure_ascii=False)
                print(f"💾 Context saved to {self.context_file}")
        except Exception as e:
            print(f"❌ Error saving context: {e}")
            import traceback
            traceback.print_exc()
    
    def update_datadog_context(self, metrics_data: Dict, charts_data: Dict = None):
        """Update Datadog context with new data"""
        try:
            with self.lock:
                self.context["data_sources"]["datadog"]["metrics"] = metrics_data
                if charts_data:
                    self.context["data_sources"]["datadog"]["charts"] = charts_data
                self.context["data_sources"]["datadog"]["last_fetch"] = datetime.now().isoformat()
                self.context["data_sources"]["datadog"]["status"] = "fetched"
                
                # Update summary
                if metrics_data and "metrics" in metrics_data:
                    self.context["summary"]["total_metrics"] = len(metrics_data["metrics"])
                
                self.save_context()
                print("📊 Datadog context updated")
        except Exception as e:
            print(f"❌ Error updating Datadog context: {e}")
    
    def update_datadog_logs_context(self, logs_data: Dict):
        """Update Datadog logs context with new data"""
        try:
            with self.lock:
                self.context["data_sources"]["datadog"]["logs"] = logs_data
                self.context["data_sources"]["datadog"]["last_fetch"] = datetime.now().isoformat()
                self.context["data_sources"]["datadog"]["status"] = "fetched"
                self.save_context()
                print("📋 Datadog logs context updated")
        except Exception as e:
            print(f"❌ Error updating Datadog logs context: {e}")
    
    def update_github_context(self, analytics_data: Dict):
        """Update GitHub context with new data"""
        try:
            with self.lock:
                if "data" in analytics_data:
                    data = analytics_data["data"]
                    self.context["data_sources"]["github"]["analytics"] = data
                    
                    # Extract pull requests and repositories
                    if "recent_pull_requests" in data:
                        self.context["data_sources"]["github"]["pull_requests"] = data["recent_pull_requests"]
                    if "repositories" in data:
                        self.context["data_sources"]["github"]["repositories"] = data["repositories"]
                    
                    # Update summary
                    if "total_pull_requests" in data:
                        self.context["summary"]["total_pull_requests"] += data["total_pull_requests"]
                    if "total_repositories" in data:
                        self.context["summary"]["total_repositories"] += data["total_repositories"]
                
                self.context["data_sources"]["github"]["last_fetch"] = datetime.now().isoformat()
                self.context["data_sources"]["github"]["status"] = "fetched"
                self.save_context()
                print("🐙 GitHub context updated")
        except Exception as e:
            print(f"❌ Error updating GitHub context: {e}")
    
    def update_azuredevops_context(self, analytics_data: Dict):
        """Update Azure DevOps context with new data"""
        try:
            print(f"🔧 DEBUG: Updating Azure DevOps context with data: {analytics_data.get('status', 'unknown')}")
            with self.lock:
                if "data" in analytics_data:
                    data = analytics_data["data"]
                    self.context["data_sources"]["azuredevops"]["analytics"] = data
                    
                    # Extract work items and pull requests
                    if "recent_work_items" in data:
                        self.context["data_sources"]["azuredevops"]["work_items"] = data["recent_work_items"]
                        print(f"🔧 DEBUG: Stored {len(data['recent_work_items'])} work items")
                    if "recent_pull_requests" in data:
                        self.context["data_sources"]["azuredevops"]["pull_requests"] = data["recent_pull_requests"]
                        print(f"🔧 DEBUG: Stored {len(data['recent_pull_requests'])} pull requests")
                    
                    # Update summary
                    if "total_work_items" in data:
                        self.context["summary"]["total_work_items"] = data["total_work_items"]
                        print(f"🔧 DEBUG: Total work items: {data['total_work_items']}")
                    if "total_pull_requests" in data:
                        self.context["summary"]["total_pull_requests"] += data["total_pull_requests"]
                    if "total_repositories" in data:
                        self.context["summary"]["total_repositories"] += data["total_repositories"]
                else:
                    print(f"🔧 DEBUG: No 'data' key found in analytics_data")
                
                self.context["data_sources"]["azuredevops"]["last_fetch"] = datetime.now().isoformat()
                self.context["data_sources"]["azuredevops"]["status"] = "fetched"
                self.save_context()
                print("🔷 Azure DevOps context updated successfully")
        except Exception as e:
            print(f"❌ Error updating Azure DevOps context: {e}")
            import traceback
            traceback.print_exc()
    
    def update_figma_context(self, analytics_data: Dict):
        """Update Figma context with new data"""
        try:
            with self.lock:
                if "data" in analytics_data:
                    data = analytics_data["data"]
                    self.context["data_sources"]["figma"]["analytics"] = data
                    
                    # Extract files and projects
                    if "files" in data:
                        self.context["data_sources"]["figma"]["files"] = data["files"]
                    if "projects" in data:
                        self.context["data_sources"]["figma"]["projects"] = data["projects"]
                
                self.context["data_sources"]["figma"]["last_fetch"] = datetime.now().isoformat()
                self.context["data_sources"]["figma"]["status"] = "fetched"
                self.save_context()
                print("🎨 Figma context updated")
        except Exception as e:
            print(f"❌ Error updating Figma context: {e}")
    
    def get_context_for_llm(self, data_source: str = "all") -> str:
        """Get formatted context for LLM based on data source"""
        try:
            print(f"🔧 DEBUG: Getting context for data_source: {data_source}")
            context_parts = []
            
            # Add general summary
            summary = self.context.get("summary", {})
            if summary:
                context_parts.append("=== ANALYTICS DASHBOARD SUMMARY ===")
                context_parts.append(f"Total Work Items: {summary.get('total_work_items', 0)}")
                context_parts.append(f"Total Pull Requests: {summary.get('total_pull_requests', 0)}")
                context_parts.append(f"Total Repositories: {summary.get('total_repositories', 0)}")
                context_parts.append(f"Total Metrics: {summary.get('total_metrics', 0)}")
                context_parts.append(f"Last Updated: {self.context.get('last_updated', 'Never')}")
                context_parts.append("")
            
            # Add data source specific context
            if data_source == "all" or data_source == "datadog":
                datadog_data = self.context["data_sources"]["datadog"]
                if datadog_data["status"] == "fetched":
                    context_parts.append("=== DATADOG METRICS ===")
                    if datadog_data["metrics"]:
                        metrics = datadog_data["metrics"].get("metrics", [])
                        for metric in metrics[:10]:  # Limit to first 10 metrics
                            context_parts.append(f"- {metric.get('name', 'Unknown')}: {metric.get('value', 'N/A')} {metric.get('unit', '')}")
                    
                    # Add Datadog logs
                    if datadog_data.get("logs"):
                        context_parts.append("=== DATADOG LOGS ===")
                        logs = datadog_data["logs"]
                        if logs.get("logs"):
                            context_parts.append(f"Total Logs: {logs.get('total_logs', 0)}")
                            context_parts.append(f"Services: {', '.join(logs.get('services', []))}")
                            
                            # Add recent log entries
                            recent_logs = logs.get("logs", [])[:5]  # Limit to 5 recent logs
                            if recent_logs:
                                context_parts.append("Recent Log Entries:")
                                for log in recent_logs:
                                    context_parts.append(f"- {log.get('message', 'No message')[:100]}...")
                    
                    context_parts.append(f"Last Fetch: {datadog_data.get('last_fetch', 'Never')}")
                    context_parts.append("")
            
            if data_source == "all" or data_source == "github":
                github_data = self.context["data_sources"]["github"]
                if github_data["status"] == "fetched":
                    context_parts.append("=== GITHUB ANALYTICS ===")
                    analytics = github_data.get("analytics", {})
                    if analytics:
                        context_parts.append(f"Total PRs: {analytics.get('total_pull_requests', 0)}")
                        context_parts.append(f"Total Repositories: {analytics.get('total_repositories', 0)}")
                        context_parts.append(f"Total Commits: {analytics.get('total_commits', 0)}")
                        
                        # Add recent PRs
                        recent_prs = github_data.get("pull_requests", [])
                        if recent_prs:
                            context_parts.append("Recent Pull Requests:")
                            for pr in recent_prs[:5]:  # Limit to 5 recent PRs
                                context_parts.append(f"- {pr.get('title', 'Unknown')} (State: {pr.get('state', 'Unknown')})")
                    context_parts.append(f"Last Fetch: {github_data.get('last_fetch', 'Never')}")
                    context_parts.append("")
            
            if data_source == "all" or data_source == "azuredevops":
                azure_data = self.context["data_sources"]["azuredevops"]
                print(f"🔧 DEBUG: Azure DevOps status: {azure_data['status']}")
                if azure_data["status"] == "fetched":
                    context_parts.append("=== AZURE DEVOPS ANALYTICS ===")
                    analytics = azure_data.get("analytics", {})
                    print(f"🔧 DEBUG: Azure DevOps analytics keys: {list(analytics.keys()) if analytics else 'None'}")
                    if analytics:
                        context_parts.append(f"Total Work Items: {analytics.get('total_work_items', 0)}")
                        context_parts.append(f"Total PRs: {analytics.get('total_pull_requests', 0)}")
                        context_parts.append(f"Total Repositories: {analytics.get('total_repositories', 0)}")
                        
                        # Add work items by type
                        work_items_by_type = analytics.get("work_items_by_type", {})
                        if work_items_by_type:
                            context_parts.append("Work Items by Type:")
                            for item_type, count in work_items_by_type.items():
                                context_parts.append(f"- {item_type}: {count}")
                        
                        # Add work items by state
                        work_items_by_state = analytics.get("work_items_by_state", {})
                        if work_items_by_state:
                            context_parts.append("Work Items by State:")
                            for state, count in work_items_by_state.items():
                                context_parts.append(f"- {state}: {count}")
                    context_parts.append(f"Last Fetch: {azure_data.get('last_fetch', 'Never')}")
                    context_parts.append("")
            
            if data_source == "all" or data_source == "figma":
                figma_data = self.context["data_sources"]["figma"]
                if figma_data["status"] == "fetched":
                    context_parts.append("=== FIGMA ANALYTICS ===")
                    analytics = figma_data.get("analytics", {})
                    if analytics:
                        context_parts.append(f"Total Files: {analytics.get('total_files', 0)}")
                        context_parts.append(f"Total Projects: {analytics.get('total_projects', 0)}")
                        
                        # Add recent files
                        recent_files = figma_data.get("files", [])
                        if recent_files:
                            context_parts.append("Recent Files:")
                            for file in recent_files[:5]:  # Limit to 5 recent files
                                context_parts.append(f"- {file.get('name', 'Unknown')} (Last Modified: {file.get('last_modified', 'Unknown')})")
                    context_parts.append(f"Last Fetch: {figma_data.get('last_fetch', 'Never')}")
                    context_parts.append("")
            
            context_result = "\n".join(context_parts)
            print(f"🔧 DEBUG: Final context length: {len(context_result)} characters")
            print(f"🔧 DEBUG: Context preview: {context_result[:500]}...")
            return context_result
            
        except Exception as e:
            print(f"❌ Error getting context for LLM: {e}")
            return "Error retrieving context data."
    
    def get_context_summary(self) -> Dict:
        """Get a summary of current context status"""
        return {
            "last_updated": self.context.get("last_updated"),
            "data_sources": {
                source: {
                    "status": data["status"],
                    "last_fetch": data["last_fetch"]
                }
                for source, data in self.context["data_sources"].items()
            },
            "summary": self.context.get("summary", {})
        }
    
    def clear_context(self):
        """Clear all context data"""
        try:
            with self.lock:
                self.context = {
                    "last_updated": None,
                    "data_sources": {
                        "datadog": {"metrics": {}, "charts": {}, "last_fetch": None, "status": "not_fetched"},
                        "github": {"pull_requests": [], "repositories": [], "analytics": {}, "last_fetch": None, "status": "not_fetched"},
                        "azuredevops": {"work_items": [], "pull_requests": [], "analytics": {}, "last_fetch": None, "status": "not_fetched"},
                        "figma": {"files": [], "projects": [], "analytics": {}, "last_fetch": None, "status": "not_fetched"}
                    },
                    "summary": {"total_work_items": 0, "total_pull_requests": 0, "total_repositories": 0, "total_metrics": 0, "last_activity": None}
                }
                self.save_context()
                print("🗑️ Context cleared")
        except Exception as e:
            print(f"❌ Error clearing context: {e}")

# Global context storage instance
context_storage = ContextStorage()
