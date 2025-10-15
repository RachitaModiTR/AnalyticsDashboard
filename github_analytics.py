"""
GitHub Analytics Module
Handles all GitHub-related functionality including pull request analytics
"""

import json
from datetime import datetime, timedelta
import requests
import plotly.graph_objs as go
import plotly
from config import Config


class GitHubPullRequestAnalytics:
    def __init__(self):
        self.github_token = Config.GITHUB_TOKEN
        self.owner = Config.GITHUB_OWNER
        self.repo = Config.GITHUB_REPO
        self.base_url = "https://api.github.com"
        
    def get_pull_requests(self, state='all', per_page=100):
        """Fetch pull requests from GitHub repository"""
        if not self.github_token or not self.owner or not self.repo:
            return None
            
        try:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            params = {
                'state': state,
                'per_page': per_page,
                'sort': 'updated',
                'direction': 'desc'
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"GitHub API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error fetching pull requests: {e}")
            return None
    
    def get_pull_request_analytics(self, days=30):
        """Get analytics data for pull requests"""
        if not self.github_token or not self.owner or not self.repo:
            return {
                'status': 'error',
                'message': 'GitHub configuration not provided'
            }
            
        try:
            # Get all pull requests
            all_prs = self.get_pull_requests(state='all')
            if all_prs is None:
                return {
                    'status': 'error',
                    'message': 'Failed to fetch pull requests'
                }
            
            # Filter PRs from last N days
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_prs = []
            
            for pr in all_prs:
                created_at = datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                if created_at >= cutoff_date:
                    recent_prs.append(pr)
            
            # Calculate analytics
            analytics = {
                'total_prs': len(recent_prs),
                'open_prs': len([pr for pr in recent_prs if pr['state'] == 'open']),
                'closed_prs': len([pr for pr in recent_prs if pr['state'] == 'closed']),
                'merged_prs': len([pr for pr in recent_prs if pr['merged_at'] is not None]),
                'average_commits': 0,
                'average_additions': 0,
                'average_deletions': 0,
                'average_changed_files': 0,
                'prs_by_author': {},
                'prs_by_day': {},
                'recent_prs': []
            }
            
            if recent_prs:
                # Calculate averages
                total_commits = sum(pr.get('commits', 0) for pr in recent_prs)
                total_additions = sum(pr.get('additions', 0) for pr in recent_prs)
                total_deletions = sum(pr.get('deletions', 0) for pr in recent_prs)
                total_changed_files = sum(pr.get('changed_files', 0) for pr in recent_prs)
                
                analytics['average_commits'] = total_commits / len(recent_prs)
                analytics['average_additions'] = total_additions / len(recent_prs)
                analytics['average_deletions'] = total_deletions / len(recent_prs)
                analytics['average_changed_files'] = total_changed_files / len(recent_prs)
                
                # Group by author
                for pr in recent_prs:
                    author = pr['user']['login']
                    if author not in analytics['prs_by_author']:
                        analytics['prs_by_author'][author] = 0
                    analytics['prs_by_author'][author] += 1
                
                # Group by day
                for pr in recent_prs:
                    day = pr['created_at'][:10]  # YYYY-MM-DD
                    if day not in analytics['prs_by_day']:
                        analytics['prs_by_day'][day] = 0
                    analytics['prs_by_day'][day] += 1
                
                # Get recent PRs (last 10)
                analytics['recent_prs'] = recent_prs[:10]
            
            return {
                'status': 'success',
                'data': analytics
            }
            
        except Exception as e:
            print(f"Error calculating PR analytics: {e}")
            return {
                'status': 'error',
                'message': f'Error calculating analytics: {str(e)}'
            }
    
    def get_pull_request_details(self, pr_number):
        """Get detailed information about a specific pull request"""
        if not self.github_token or not self.owner or not self.repo:
            return None
            
        try:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls/{pr_number}"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"GitHub API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error fetching PR details: {e}")
            return None

    def get_chart_data(self, days=30, chart_type='overview'):
        """Get chart data for GitHub pull requests"""
        result = self.get_pull_request_analytics(days)
        
        if result['status'] != 'success':
            return None
        
        data = result['data']
        
        # Prepare chart data based on type
        if chart_type == 'prs_by_day':
            dates = sorted(data['prs_by_day'].keys())
            values = [data['prs_by_day'][date] for date in dates]
            
            fig = go.Figure(data=go.Scatter(
                x=dates,
                y=values,
                mode='lines+markers',
                name='Pull Requests',
                line=dict(width=2)
            ))
            
            fig.update_layout(
                title=f'Pull Requests Created - Last {days} days',
                xaxis_title='Date',
                yaxis_title='Number of PRs',
                hovermode='x unified'
            )
            
        elif chart_type == 'prs_by_author':
            authors = list(data['prs_by_author'].keys())
            values = list(data['prs_by_author'].values())
            
            fig = go.Figure(data=go.Bar(
                x=authors,
                y=values,
                name='Pull Requests by Author'
            ))
            
            fig.update_layout(
                title=f'Pull Requests by Author - Last {days} days',
                xaxis_title='Author',
                yaxis_title='Number of PRs',
                hovermode='x unified'
            )
            
        else:  # Default to PR status overview
            labels = ['Open', 'Closed', 'Merged']
            values = [data['open_prs'], data['closed_prs'], data['merged_prs']]
            
            fig = go.Figure(data=go.Pie(
                labels=labels,
                values=values,
                name='PR Status'
            ))
            
            fig.update_layout(
                title=f'Pull Request Status Overview - Last {days} days'
            )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    def _create_chart_from_data(self, data, chart_type='overview'):
        """Create chart data from pre-computed analytics data"""
        # Prepare chart data based on type
        if chart_type == 'prs_by_day':
            dates = sorted(data['prs_by_day'].keys())
            values = [data['prs_by_day'][date] for date in dates]
            
            fig = go.Figure(data=go.Scatter(
                x=dates,
                y=values,
                mode='lines+markers',
                name='Pull Requests',
                line=dict(width=2)
            ))
            
            fig.update_layout(
                title=f'Pull Requests Created - Multi-Repository',
                xaxis_title='Date',
                yaxis_title='Number of PRs',
                hovermode='x unified'
            )
            
        elif chart_type == 'prs_by_author':
            authors = list(data['prs_by_author'].keys())
            values = list(data['prs_by_author'].values())
            
            fig = go.Figure(data=go.Bar(
                x=authors,
                y=values,
                name='Pull Requests by Author'
            ))
            
            fig.update_layout(
                title=f'Pull Requests by Author - Multi-Repository',
                xaxis_title='Author',
                yaxis_title='Number of PRs',
                hovermode='x unified'
            )
            
        else:  # Default to PR status overview
            labels = ['Open', 'Closed', 'Merged']
            values = [data['open_prs'], data['closed_prs'], data['merged_prs']]
            
            fig = go.Figure(data=go.Pie(
                labels=labels,
                values=values,
                name='PR Status'
            ))
            
            fig.update_layout(
                title=f'Pull Request Status Overview - Multi-Repository'
            )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


