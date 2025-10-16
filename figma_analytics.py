"""
Figma Analytics Module
Handles all Figma-related functionality including file analytics, team collaboration, and design metrics
"""

import json
import base64
from datetime import datetime, timedelta
import requests
import plotly.graph_objs as go
import plotly
from config import Config


class FigmaAnalytics:
    def __init__(self):
        self.figma_token = Config.FIGMA_TOKEN
        self.team_id = Config.FIGMA_TEAM_ID
        self.base_url = "https://api.figma.com/v1"
        
    def _get_headers(self):
        """Get authentication headers for Figma API"""
        if not self.figma_token:
            return None
        
        return {
            'X-Figma-Token': self.figma_token,
            'Content-Type': 'application/json'
        }
    
    def get_team_projects(self, team_id: str = None):
        """Fetch projects from Figma team"""
        effective_team_id = team_id or self.team_id
        if not self.figma_token or not effective_team_id:
            return None
            
        try:
            url = f"{self.base_url}/teams/{effective_team_id}/projects"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Figma API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error fetching team projects: {e}")
            return None
    
    def get_project_files(self, project_id, team_id: str = None):
        """Fetch files from a specific project"""
        if not self.figma_token:
            return None
            
        try:
            # Figma API uses /projects/{project_id}/files (team_id not required)
            url = f"{self.base_url}/projects/{project_id}/files"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Figma API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error fetching project files: {e}")
            return None
    
    def get_file_info(self, file_key):
        """Get detailed information about a specific file"""
        if not self.figma_token:
            return None
            
        try:
            url = f"{self.base_url}/files/{file_key}"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Figma API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error fetching file info: {e}")
            return None
    
    def get_file_comments(self, file_key):
        """Get comments for a specific file"""
        if not self.figma_token:
            return None
            
        try:
            url = f"{self.base_url}/files/{file_key}/comments"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Figma API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error fetching file comments: {e}")
            return None
    
    def get_team_analytics(self, days=30, team_id: str = None):
        """Get comprehensive team analytics"""
        effective_team_id = team_id or self.team_id
        if not self.figma_token or not effective_team_id:
            return {
                'status': 'error',
                'message': 'Figma configuration not provided'
            }
            
        try:
            # Get team projects
            projects_data = self.get_team_projects(effective_team_id)
            if not projects_data:
                return {
                    'status': 'error',
                    'message': 'Failed to fetch team projects'
                }
            
            analytics = {
                'total_projects': len(projects_data.get('projects', [])),
                'total_files': 0,
                'total_comments': 0,
                'files_by_project': {},
                'recent_files': [],
                'active_collaborators': set(),
                'project_breakdown': []
            }
            
            # Analyze each project
            for project in projects_data.get('projects', []):
                project_id = project['id']
                project_name = project['name']
                
                # Get files for this project
                files_data = self.get_project_files(project_id, effective_team_id)
                if files_data:
                    files = files_data.get('files', [])
                    analytics['total_files'] += len(files)
                    analytics['files_by_project'][project_name] = len(files)
                    
                    # Analyze recent files
                    for file in files[:5]:  # Get first 5 files for analysis
                        file_key = file['key']
                        file_info = self.get_file_info(file_key)
                        
                        if file_info:
                            # Get file metadata
                            file_data = {
                                'name': file_info.get('name', 'Unknown'),
                                'key': file_key,
                                'last_modified': file_info.get('lastModified', ''),
                                'version': file_info.get('version', ''),
                                'thumbnail_url': file_info.get('thumbnailUrl', ''),
                                'link_access': file_info.get('linkAccess', ''),
                                'comments_count': 0
                            }
                            
                            # Get comments for this file
                            comments_data = self.get_file_comments(file_key)
                            if comments_data:
                                comments = comments_data.get('comments', [])
                                file_data['comments_count'] = len(comments)
                                analytics['total_comments'] += len(comments)
                                
                                # Track active collaborators
                                for comment in comments:
                                    if 'user' in comment:
                                        analytics['active_collaborators'].add(comment['user'].get('handle', 'Unknown'))
                            
                            analytics['recent_files'].append(file_data)
                    
                    # Add project breakdown
                    analytics['project_breakdown'].append({
                        'name': project_name,
                        'id': project_id,
                        'files_count': len(files),
                        'description': project.get('description', '')
                    })
            
            # Convert set to list for JSON serialization
            analytics['active_collaborators'] = list(analytics['active_collaborators'])
            
            # Sort recent files by last modified
            analytics['recent_files'].sort(
                key=lambda x: x.get('last_modified', ''), 
                reverse=True
            )
            
            return {
                'status': 'success',
                'data': analytics
            }
            
        except Exception as e:
            print(f"Error calculating Figma analytics: {e}")
            return {
                'status': 'error',
                'message': f'Error calculating analytics: {str(e)}'
            }
    
    def get_chart_data(self, chart_type='files_by_project', days=30, team_id: str = None):
        """Get chart data for Figma analytics"""
        result = self.get_team_analytics(days, team_id)
        
        if result['status'] != 'success':
            return None
        
        data = result['data']
        
        # Prepare chart data based on type
        if chart_type == 'files_by_project':
            projects = list(data['files_by_project'].keys())
            values = list(data['files_by_project'].values())
            
            fig = go.Figure(data=go.Pie(
                labels=projects,
                values=values,
                name='Files by Project'
            ))
            
            fig.update_layout(
                title=f'Files by Project - Last {days} days'
            )
            
        elif chart_type == 'collaboration_activity':
            # Create a simple collaboration activity chart
            collaborators = data['active_collaborators']
            values = [1] * len(collaborators)  # Simple representation
            
            fig = go.Figure(data=go.Bar(
                x=collaborators,
                y=values,
                name='Active Collaborators'
            ))
            
            fig.update_layout(
                title=f'Active Collaborators - Last {days} days',
                xaxis_title='Collaborator',
                yaxis_title='Activity',
                hovermode='x unified'
            )
            
        elif chart_type == 'project_overview':
            projects = [p['name'] for p in data['project_breakdown']]
            files_counts = [p['files_count'] for p in data['project_breakdown']]
            
            fig = go.Figure(data=go.Bar(
                x=projects,
                y=files_counts,
                name='Project Overview'
            ))
            
            fig.update_layout(
                title=f'Project Overview - Last {days} days',
                xaxis_title='Project',
                yaxis_title='Number of Files',
                hovermode='x unified'
            )
            
        else:  # Default to team overview
            categories = ['Projects', 'Files', 'Comments', 'Collaborators']
            values = [
                data['total_projects'],
                data['total_files'],
                data['total_comments'],
                len(data['active_collaborators'])
            ]
            
            fig = go.Figure(data=go.Bar(
                x=categories,
                y=values,
                name='Team Overview'
            ))
            
            fig.update_layout(
                title=f'Figma Team Overview - Last {days} days',
                xaxis_title='Category',
                yaxis_title='Count',
                hovermode='x unified'
            )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    def search_files(self, query, team_id: str = None):
        """Search for files by name or content"""
        effective_team_id = team_id or self.team_id
        if not self.figma_token or not effective_team_id:
            return None
            
        try:
            # Get all projects and search through files
            projects_data = self.get_team_projects(effective_team_id)
            if not projects_data:
                return []
            
            matching_files = []
            
            for project in projects_data.get('projects', []):
                project_id = project['id']
                files_data = self.get_project_files(project_id, effective_team_id)
                
                if files_data:
                    for file in files_data.get('files', []):
                        if query.lower() in file.get('name', '').lower():
                            matching_files.append({
                                'name': file['name'],
                                'key': file['key'],
                                'project': project['name'],
                                'last_modified': file.get('lastModified', ''),
                                'thumbnail_url': file.get('thumbnailUrl', '')
                            })
            
            return matching_files
            
        except Exception as e:
            print(f"Error searching files: {e}")
            return None


