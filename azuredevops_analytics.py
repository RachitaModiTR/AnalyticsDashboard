"""
Azure DevOps Analytics Module
Handles all Azure DevOps-related functionality including work items, pull requests, and build analytics
"""

import json
import base64
from datetime import datetime, timedelta
import requests
import plotly.graph_objs as go
import plotly
from config import Config


class AzureDevOpsAnalytics:
    def __init__(self):
        self.pat_token = Config.AZURE_DEVOPS_PAT
        self.organization = Config.AZURE_DEVOPS_ORG
        self.project = Config.AZURE_DEVOPS_PROJECT
        self.area_path = getattr(Config, 'AZURE_DEVOPS_AREA_PATH', '')
        
    def _get_base_url(self):
        """Get the base URL for Azure DevOps API"""
        if not self.organization or not self.project:
            return None
        return f"https://dev.azure.com/{self.organization}/{self.project}/_apis"
        
    def _get_headers(self):
        """Get authentication headers for Azure DevOps API"""
        if not self.pat_token:
            return None
        
        # Create Basic Auth header with PAT
        credentials = base64.b64encode(f":{self.pat_token}".encode()).decode()
        return {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }
    
    def get_work_items(self, work_item_type=None, state=None, days=30):
        """Optimized work items fetch with area path and date filtering for better performance"""
        print(f"📋 OPTIMIZED: Getting work items for area path: '{self.area_path}' within last {days} days")
        
        if not self.pat_token or not self.organization or not self.project:
            print("📋 ERROR: Missing token, org, or project")
            return None
            
        base_url = self._get_base_url()
        if not base_url:
            print("📋 ERROR: Could not get base URL")
            return None
            
        try:
            # Calculate date filter based on days parameter
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            date_filter = cutoff_date.strftime('%Y-%m-%d')
            
            # OPTIMIZED WIQL query with date filtering
            if self.area_path:
                area_filter = f"[System.AreaPath] = '{self.area_path}'"
                print(f"📋 OPTIMIZED: Using exact area path match: {self.area_path}")
            else:
                area_filter = "1=1"  # No area filter
                print("📋 OPTIMIZED: No area path filter - all work items from project")
            
            # Enhanced WIQL query with date filtering
            wiql_query = f"""
            SELECT [System.Id], [System.Title], [System.WorkItemType], [System.State], [System.CreatedDate]
            FROM WorkItems 
            WHERE [System.TeamProject] = '{self.project}' 
            AND {area_filter}
            AND [System.CreatedDate] >= '{date_filter}'
            """
            
            # Add optional filters
            if work_item_type:
                wiql_query += f" AND [System.WorkItemType] = '{work_item_type}'"
                print(f"📋 OPTIMIZED: Applied work item type filter: {work_item_type}")
                
            if state:
                wiql_query += f" AND [System.State] = '{state}'"
                print(f"📋 OPTIMIZED: Applied state filter: {state}")
            
            # Order by creation date (most recent first)
            wiql_query += " ORDER BY [System.CreatedDate] DESC"
            
            print(f"📋 OPTIMIZED WIQL with date filter ({days} days): {wiql_query}")
            
            # Remove the top limit to get all work items within the date range
            url = f"{base_url}/wit/wiql?api-version=6.0"
            headers = self._get_headers()
            
            payload = {"query": wiql_query}
            
            print(f"📋 OPTIMIZED: Making request to {url}")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"📋 OPTIMIZED Response: {response.status_code}")
            
            if response.status_code == 200:
                wiql_result = response.json()
                work_item_ids = [item['id'] for item in wiql_result.get('workItems', [])]
                
                print(f"📋 OPTIMIZED: Found {len(work_item_ids)} work items in area path within last {days} days")
                
                if not work_item_ids:
                    return []
                
                # Get basic details for all work items found within date range
                return self._get_work_item_basic_details(work_item_ids, base_url)
            else:
                print(f"📋 OPTIMIZED ERROR: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"📋 OPTIMIZED ERROR: {e}")
            return None
    
    def _get_work_item_basic_details(self, work_item_ids, base_url):
        """Fast work item details fetch without PR analysis"""
        try:
            url = f"{base_url}/wit/workitems?api-version=6.0"
            headers = self._get_headers()
            
            # Minimal field set for fastest response
            params = {
                'ids': ','.join(map(str, work_item_ids)),
                'fields': 'System.Id,System.Title,System.State,System.WorkItemType,System.CreatedDate,System.AreaPath,System.AssignedTo'
            }
            
            print(f"📋 FAST: Getting basic details for {len(work_item_ids)} work items")
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            print(f"📋 FAST Response: {response.status_code}")
            
            if response.status_code == 200:
                work_items = response.json().get('value', [])
                print(f"📋 FAST: Retrieved {len(work_items)} work items")
                
                # Initialize with empty PR lists for compatibility
                for work_item in work_items:
                    work_item['associated_prs'] = []
                
                return work_items
            else:
                print(f"📋 FAST ERROR: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"📋 FAST ERROR: {e}")
            return None
    
    def get_work_items_with_github_prs(self, work_item_type=None, state=None, days=30):
        """Get work items with detailed GitHub PR analysis - respects date filtering"""
        print(f"📋 GITHUB PR ANALYSIS: Starting comprehensive analysis for area: '{self.area_path}' within last {days} days")
        
        if not self.pat_token or not self.organization or not self.project:
            return None
            
        base_url = self._get_base_url()
        if not base_url:
            return None
            
        try:
            # Calculate date filter based on days parameter
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            date_filter = cutoff_date.strftime('%Y-%m-%d')
            
            # Use area path filtering with date filtering
            if self.area_path:
                area_filter = f"[System.AreaPath] UNDER '{self.area_path}'"
                print(f"📋 GITHUB PR: Using UNDER area path filter: {self.area_path}")
            else:
                area_filter = "1=1"
            
            # Full field selection for PR analysis with date filtering
            wiql_query = f"""
            SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType], 
                   [System.CreatedDate], [System.ChangedDate], [System.AssignedTo], [System.AreaPath]
            FROM WorkItems 
            WHERE [System.TeamProject] = '{self.project}' 
            AND {area_filter}
            AND [System.CreatedDate] >= '{date_filter}'
            ORDER BY [System.ChangedDate] DESC
            """
            
            if work_item_type:
                wiql_query += f" AND [System.WorkItemType] = '{work_item_type}'"
                
            if state:
                wiql_query += f" AND [System.State] = '{state}'"
            
            print(f"📋 GITHUB PR WIQL with date filter ({days} days): {wiql_query}")
            
            # Remove top limit to get all work items within date range
            url = f"{base_url}/wit/wiql?api-version=6.0"
            headers = self._get_headers()
            payload = {"query": wiql_query}
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                wiql_result = response.json()
                work_item_ids = [item['id'] for item in wiql_result.get('workItems', [])]
                
                print(f"📋 GITHUB PR: Found {len(work_item_ids)} work items for PR analysis within last {days} days")
                
                if not work_item_ids:
                    return []
                
                # Use detailed method with PR analysis for all work items in date range
                return self._get_work_item_details(work_item_ids, base_url)
            else:
                print(f"📋 GITHUB PR ERROR: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"📋 GITHUB PR ERROR: {e}")
            return None
    
    def _get_work_item_details(self, work_item_ids, base_url):
        """Get detailed information for work items including linked PRs with optimized batch processing"""
        try:
            # First get basic work item details
            url = f"{base_url}/wit/workitems?api-version=6.0"
            headers = self._get_headers()
            
            params = {
                'ids': ','.join(map(str, work_item_ids)),
                'fields': 'System.Id,System.Title,System.State,System.WorkItemType,System.CreatedDate,System.ChangedDate,System.AssignedTo,System.Tags,System.AreaPath'
            }
            
            print(f"Azure DevOps: Getting basic details for {len(work_item_ids)} work items")
            print(f"Azure DevOps: Request URL: {url}")
            
            response = requests.get(url, headers=headers, params=params)
            
            print(f"Azure DevOps Work Items Details Response: {response.status_code}")
            
            if response.status_code == 200:
                work_items = response.json().get('value', [])
                print(f"Azure DevOps: Retrieved details for {len(work_items)} work items")
                
                # Initialize all work items with empty PR lists
                work_items_dict = {item['id']: item for item in work_items}
                for work_item in work_items:
                    work_item['associated_prs'] = []
                
                # Get PR relations using optimized batch processing
                print("🔗 Starting GitHub PR analysis for work items...")
                pr_links_with_ids = self._get_work_items_with_relations_batch([item['id'] for item in work_items], base_url)
                
                # Assign PR links to their respective work items
                for work_item_id, pr_link in pr_links_with_ids:
                    if work_item_id in work_items_dict:
                        work_items_dict[work_item_id]['associated_prs'].append(pr_link)
                
                return work_items
            else:
                print(f"Azure DevOps API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error fetching work item details: {e}")
            return None
    
    def _get_work_item_relations(self, work_item_id, base_url):
        """Get PR relations for a specific work item with improved error handling"""
        try:
            # Get work item with relations expanded
            url = f"{base_url}/wit/workitems/{work_item_id}?api-version=6.0&$expand=relations"
            headers = self._get_headers()
            
            # Add timeout and retry logic
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                work_item_data = response.json()
                return self._extract_pr_links(work_item_data)
            else:
                # Don't spam logs for individual failures, just return empty
                return []
                
        except Exception as e:
            # Don't spam logs for network issues, just return empty
            return []

    def _get_work_items_with_relations_batch(self, work_item_ids, base_url):
        """Get work items with relations in smaller batches to avoid network issues"""
        all_pr_links = []
        successful_fetches = 0
        batch_size = 10  # Process in smaller batches
        
        print(f"🔗 Fetching PR relations for {len(work_item_ids)} work items in batches of {batch_size}")
        
        for i in range(0, len(work_item_ids), batch_size):
            batch_ids = work_item_ids[i:i + batch_size]
            batch_success = 0
            
            for work_item_id in batch_ids:
                try:
                    pr_links = self._get_work_item_relations(work_item_id, base_url)
                    if pr_links:  # Only count if we found PR links
                        all_pr_links.extend([(work_item_id, link) for link in pr_links])
                        batch_success += 1
                    successful_fetches += 1
                except Exception:
                    continue
            
            if batch_success > 0:
                print(f"🔗 Batch {i//batch_size + 1}: Found PR links in {batch_success} work items")
            
            # Small delay between batches to avoid overwhelming the API
            import time
            time.sleep(0.1)
        
        print(f"🔗 Successfully processed {successful_fetches}/{len(work_item_ids)} work items")
        print(f"🔗 Found {len(all_pr_links)} total PR links")
        
        return all_pr_links
    
    def _extract_pr_links(self, work_item):
        """Extract PR links from work item relations, with precise development work detection"""
        pr_links = []
        relations = work_item.get('relations', [])
        
        # Only log for first few work items to avoid spam
        work_item_id = work_item.get('id', 'unknown')
        should_log = int(str(work_item_id)[-1]) < 3  # Log ~30% of work items
        
        if should_log:
            print(f"🔍 Analyzing work item {work_item_id} - found {len(relations)} relations")
        
        for relation in relations:
            rel_type = relation.get('rel', '').lower()
            url = relation.get('url', '')
            attributes = relation.get('attributes', {})
            
            # PRECISE PR detection - focus on actual development work relations
            is_pr_link = any([
                # Exact Azure DevOps development relation types
                rel_type == 'artifactlink',
                'pullrequest' in rel_type,
                'development' in rel_type and 'work' in rel_type,
                
                # GitHub URLs (external links)
                'github.com' in url.lower() and 'pull/' in url,
                
                # Azure DevOps Git PR URLs
                '_git/' in url.lower() and 'pullrequest' in url.lower(),
                'repositories/' in url.lower() and 'pullrequests' in url.lower(),
                
                # External hyperlinks that could be PRs
                rel_type == 'hyperlink' and any([
                    'github.com' in url.lower() and 'pull/' in url,
                    'pull/' in url.lower(),
                    'pr/' in url.lower(),
                    'pullrequest' in url.lower()
                ])
            ])
            
            if is_pr_link:
                if should_log:
                    print(f"    ✅ Found PR link: {rel_type} -> {url}")
                repo_info = self._extract_repo_from_pr_url(url)
                pr_info = {
                    'relation_type': rel_type,
                    'url': url,
                    'repository': repo_info['repository'],
                    'pr_number': repo_info['pr_number'],
                    'platform': repo_info['platform'],
                    'full_repo_path': repo_info['full_repo_path'],
                    'repository_id': repo_info.get('repository_id'),
                    'commit_id': repo_info.get('commit_id'),
                    'attributes': attributes
                }
                
                # Enrich with detailed information from Azure DevOps APIs
                pr_info = self.enrich_pr_with_details(pr_info)
                
                pr_links.append(pr_info)
            elif should_log and ('hyperlink' in rel_type or 'artifact' in rel_type):
                # Log potential external links for analysis
                print(f"    ℹ️  External link: {rel_type} -> {url[:100]}...")
        
        if pr_links and should_log:
            print(f"  🎯 Found {len(pr_links)} PR links for work item {work_item_id}")
        elif should_log:
            print(f"  ⚠️  No PR links found for work item {work_item_id}")
            
        return pr_links
    
    def _extract_repo_from_pr_url(self, url):
        """Extract detailed repository information from PR URL including VSTFS GitHub links"""
        default_result = {
            'repository': url,  # Fallback to full URL
            'pr_number': 'unknown',
            'platform': 'unknown',
            'full_repo_path': url,
            'repository_id': None,
            'commit_id': None
        }
        
        try:
            # VSTFS GitHub PR URLs: vstfs:///GitHub/PullRequest/{repo-id}%2f{pr-number}
            if url.startswith('vstfs:///GitHub/PullRequest/'):
                import re
                vstfs_match = re.search(r'vstfs:///GitHub/PullRequest/([^%]+)%2f(\d+)', url)
                if vstfs_match:
                    repo_id, pr_number = vstfs_match.groups()
                    return {
                        'repository': f'GitHub-{repo_id[:8]}',  # Shortened repo ID
                        'pr_number': pr_number,
                        'platform': 'GitHub',
                        'full_repo_path': f'GitHub/{repo_id}',
                        'repository_id': repo_id,
                        'commit_id': None
                    }
            
            # VSTFS GitHub Commit URLs: vstfs:///GitHub/Commit/{repo-id}%2f{commit-hash}
            elif url.startswith('vstfs:///GitHub/Commit/'):
                import re
                vstfs_commit_match = re.search(r'vstfs:///GitHub/Commit/([^%]+)%2f([a-f0-9]+)', url)
                if vstfs_commit_match:
                    repo_id, commit_hash = vstfs_commit_match.groups()
                    return {
                        'repository': f'GitHub-{repo_id[:8]}',
                        'pr_number': f'commit-{commit_hash[:8]}',
                        'platform': 'GitHub',
                        'full_repo_path': f'GitHub/{repo_id}',
                        'repository_id': repo_id,
                        'commit_id': commit_hash
                    }
            
            # Standard GitHub PR URLs: https://github.com/{owner}/{repo}/pull/{number}
            elif 'github.com' in url.lower():
                import re
                github_match = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
                if github_match:
                    owner, repo, pr_number = github_match.groups()
                    return {
                        'repository': repo,
                        'pr_number': pr_number,
                        'platform': 'GitHub',
                        'full_repo_path': f'{owner}/{repo}',
                        'repository_id': None,
                        'commit_id': None
                    }
            
            # Azure DevOps PR URLs: 
            # https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{id}
            elif '_git/' in url and 'pullrequest/' in url:
                parts = url.split('/_git/')
                if len(parts) > 1:
                    repo_and_pr = parts[1]
                    repo_part = repo_and_pr.split('/pullrequest/')[0]
                    pr_match = repo_and_pr.split('/pullrequest/')
                    pr_number = pr_match[1].split('/')[0] if len(pr_match) > 1 else 'unknown'
                    
                    return {
                        'repository': repo_part,
                        'pr_number': pr_number,
                        'platform': 'Azure DevOps',
                        'full_repo_path': repo_part,
                        'repository_id': repo_part,
                        'commit_id': None
                    }
            
            # Azure DevOps API URLs:
            # https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}/pullRequests/{id}
            elif 'repositories/' in url and 'pullRequests/' in url:
                parts = url.split('/repositories/')
                if len(parts) > 1:
                    repo_and_pr = parts[1]
                    repo_part = repo_and_pr.split('/pullRequests/')[0]
                    pr_match = repo_and_pr.split('/pullRequests/')
                    pr_number = pr_match[1].split('/')[0] if len(pr_match) > 1 else 'unknown'
                    
                    return {
                        'repository': repo_part,
                        'pr_number': pr_number,
                        'platform': 'Azure DevOps',
                        'full_repo_path': repo_part,
                        'repository_id': repo_part,
                        'commit_id': None
                    }
            
            return default_result
            
        except Exception as e:
            print(f"Error extracting repo from URL {url}: {e}")
            return default_result
    
    def get_commit_details(self, repository_id, commit_id):
        """Get detailed commit information from Azure DevOps"""
        if not self.pat_token or not self.organization or not self.project:
            return None
            
        try:
            url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/git/repositories/{repository_id}/commits/{commit_id}?api-version=7.0"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get commit details: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error fetching commit details: {e}")
            return None
    
    def get_pr_details(self, repository_id, pull_request_id):
        """Get detailed pull request information from Azure DevOps"""
        if not self.pat_token or not self.organization or not self.project:
            return None
            
        try:
            url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/git/repositories/{repository_id}/pullRequests/{pull_request_id}?api-version=7.0"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get PR details: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error fetching PR details: {e}")
            return None
    
    def enrich_pr_with_details(self, pr_info):
        """Enrich PR information with detailed data from Azure DevOps APIs"""
        try:
            # For Azure DevOps PRs, fetch detailed information
            if pr_info.get('platform') == 'Azure DevOps' and pr_info.get('repository_id') and pr_info.get('pr_number'):
                pr_details = self.get_pr_details(pr_info['repository_id'], pr_info['pr_number'])
                if pr_details:
                    pr_info.update({
                        'title': pr_details.get('title', ''),
                        'description': pr_details.get('description', ''),
                        'status': pr_details.get('status', ''),
                        'created_by': pr_details.get('createdBy', {}).get('displayName', ''),
                        'created_date': pr_details.get('creationDate', ''),
                        'source_branch': pr_details.get('sourceRefName', ''),
                        'target_branch': pr_details.get('targetRefName', ''),
                        'merge_status': pr_details.get('mergeStatus', '')
                    })
            
            # For commits, fetch commit details
            elif pr_info.get('commit_id') and pr_info.get('repository_id'):
                commit_details = self.get_commit_details(pr_info['repository_id'], pr_info['commit_id'])
                if commit_details:
                    pr_info.update({
                        'title': commit_details.get('comment', ''),
                        'author': commit_details.get('author', {}).get('name', ''),
                        'author_date': commit_details.get('author', {}).get('date', ''),
                        'committer': commit_details.get('committer', {}).get('name', ''),
                        'commit_date': commit_details.get('committer', {}).get('date', ''),
                        'change_counts': commit_details.get('changeCounts', {})
                    })
            
            return pr_info
            
        except Exception as e:
            print(f"Error enriching PR details: {e}")
            return pr_info
    
    def get_pull_requests(self, status=None, days=30):
        """Fetch pull requests from work item relations (GitHub PRs via VSTFS)"""
        if not self.pat_token or not self.organization or not self.project:
            return None
            
        print(f"🔀 ENHANCED: Getting PRs from work item relations instead of direct Git API")
        
        try:
            # Get work items with PR relations to extract recent PRs
            work_items = self.get_work_items_with_github_prs()
            
            if not work_items:
                print("🔀 No work items found for PR extraction")
                return []
            
            # Extract all PRs from work items
            all_prs = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for work_item in work_items:
                work_item_created = work_item.get('fields', {}).get('System.CreatedDate')
                work_item_changed = work_item.get('fields', {}).get('System.ChangedDate')
                
                # Use the most recent date (changed or created)
                latest_date_str = work_item_changed or work_item_created
                if latest_date_str:
                    try:
                        latest_date = datetime.strptime(latest_date_str[:10], '%Y-%m-%d')
                        
                        # Only include work items that are recent enough
                        if latest_date >= cutoff_date:
                            associated_prs = work_item.get('associated_prs', [])
                            for pr in associated_prs:
                                # Create a standardized PR object
                                pr_obj = {
                                    'id': pr.get('pr_number', 'unknown'),
                                    'title': pr.get('title', f"PR #{pr.get('pr_number')} from {pr.get('platform')}"),
                                    'description': f"Associated with Work Item {work_item.get('id')}: {work_item.get('fields', {}).get('System.Title', '')}",
                                    'status': 'completed',  # Assume completed since it's linked to work item
                                    'creationDate': latest_date_str,
                                    'sourceRefName': pr.get('url', ''),
                                    'targetRefName': 'main',  # Default assumption
                                    'repository': {
                                        'name': pr.get('repository', 'unknown'),
                                        'url': pr.get('url', '')
                                    },
                                    'createdBy': {
                                        'displayName': 'Unknown'
                                    },
                                    'platform': pr.get('platform', 'Unknown'),
                                    'work_item_id': work_item.get('id'),
                                    'work_item_title': work_item.get('fields', {}).get('System.Title', ''),
                                    'is_commit': 'commit-' in str(pr.get('pr_number', ''))
                                }
                                all_prs.append(pr_obj)
                    except (ValueError, TypeError):
                        # Skip work items with invalid dates
                        continue
            
            # Sort by creation date (most recent first)
            all_prs.sort(key=lambda x: x.get('creationDate', ''), reverse=True)
            
            print(f"🔀 ENHANCED: Found {len(all_prs)} recent PRs from work item relations")
            return all_prs[:1000]  # Return top 1000 recent PRs
            
        except Exception as e:
            print(f"🔀 Error fetching PRs from work item relations: {e}")
            return []
    
    def get_area_paths(self):
        """Get available area paths in the project"""
        if not self.pat_token or not self.organization or not self.project:
            return None
            
        base_url = self._get_base_url()
        if not base_url:
            return None
            
        try:
            # Simple query to get unique area paths from work items
            wiql_query = f"""
            SELECT [System.AreaPath]
            FROM WorkItems 
            WHERE [System.TeamProject] = '{self.project}'
            """
            
            url = f"{base_url}/wit/wiql?api-version=6.0&$top=1000"
            headers = self._get_headers()
            
            payload = {"query": wiql_query}
            
            print(f"🗂️ Azure DevOps: Getting area paths from {url}")
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                wiql_result = response.json()
                work_item_ids = [item['id'] for item in wiql_result.get('workItems', [])]
                
                if not work_item_ids:
                    return []
                
                # Get work item details to extract area paths
                details_url = f"{base_url}/wit/workitems?api-version=6.0"
                params = {
                    'ids': ','.join(map(str, work_item_ids[:100])),  # Limit to 100 for performance
                    'fields': 'System.AreaPath'
                }
                
                details_response = requests.get(details_url, headers=headers, params=params)
                
                if details_response.status_code == 200:
                    work_items = details_response.json().get('value', [])
                    area_paths = set()
                    
                    for item in work_items:
                        area_path = item.get('fields', {}).get('System.AreaPath', '')
                        if area_path:
                            area_paths.add(area_path)
                    
                    return sorted(list(area_paths))
                    
            return []
            
        except Exception as e:
            print(f"🗂️ Error fetching area paths: {e}")
            return []

    def list_projects(self):
        """List all available projects in the organization"""
        if not self.pat_token or not self.organization:
            return None
            
        try:
            # FIX: Add API version to the URL
            url = f"https://dev.azure.com/{self.organization}/_apis/projects?api-version=6.0"
            headers = self._get_headers()
            
            print(f"🔍 DEBUG: Listing projects for org: {self.organization}")
            print(f"🔍 DEBUG: Request URL: {url}")
            
            response = requests.get(url, headers=headers)
            
            print(f"🔍 DEBUG: Projects API Response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                projects = result.get('value', [])
                print(f"🔍 DEBUG: Found {len(projects)} projects")
                
                for project in projects:
                    print(f"🔍 DEBUG: Project: {project.get('name')} (ID: {project.get('id')})")
                    
                return projects
            else:
                print(f"🔍 Azure DevOps Projects API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"🔍 Error listing projects: {e}")
            return None
    
    def get_builds(self, days=30):
        """Fetch build information from Azure DevOps"""
        if not self.pat_token or not self.organization or not self.project:
            return None
            
        base_url = self._get_base_url()
        if not base_url:
            return None
            
        try:
            # FIX: Add API version to the URL
            url = f"{base_url}/build/builds?api-version=6.0"
            headers = self._get_headers()
            
            params = {
                'top': 100,
                'queryOrder': 'queueTimeDescending'
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                builds = response.json().get('value', [])
                
                # Filter by date
                cutoff_date = datetime.now() - timedelta(days=days)
                recent_builds = []
                
                for build in builds:
                    if build.get('queueTime'):
                        queue_date = datetime.strptime(build['queueTime'][:10], '%Y-%m-%d')
                        if queue_date >= cutoff_date:
                            recent_builds.append(build)
                
                return recent_builds
            else:
                print(f"Azure DevOps API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error fetching builds: {e}")
            return None
    
    def get_analytics_summary(self, days=7, include_pr_analysis=False):
        """Get comprehensive analytics summary with optional PR analysis for performance"""
        print(f"🔧 DEBUG: Starting get_analytics_summary with days={days}, include_pr_analysis={include_pr_analysis}")
        print(f"🔧 DEBUG: Token present: {bool(self.pat_token)}")
        print(f"🔧 DEBUG: Organization: {self.organization}")
        print(f"🔧 DEBUG: Project: {self.project}")
        print(f"🔧 DEBUG: ***** PERFORMANCE OPTIMIZED VERSION *****")
        
        if not self.pat_token:
            print("❌ DEBUG: No PAT token configured")
            return {
                'status': 'error',
                'message': 'Azure DevOps PAT token not configured'
            }
        
        if not self.organization or not self.project:
            print("❌ DEBUG: Missing organization or project")
            return {
                'status': 'error', 
                'message': 'Azure DevOps organization and project must be provided'
            }
            
        try:
            print(f"🚀 Azure DevOps: Fetching analytics for {self.organization}/{self.project}")
            
            # Get work items (fast)
            print("📋 DEBUG: Calling get_work_items...")
            work_items = self.get_work_items(days=days)
            print(f"📋 DEBUG: get_work_items returned: {type(work_items)} with {len(work_items) if work_items else 0} items")
            
            # Conditionally get pull requests (can be slow due to relation fetching)
            if include_pr_analysis:
                print("🔀 DEBUG: Including PR analysis (slower but more detailed)...")
                pull_requests = self.get_pull_requests(days=days)
                print(f"🔀 DEBUG: get_pull_requests returned: {type(pull_requests)} with {len(pull_requests) if pull_requests else 0} items")
            else:
                print("🔀 DEBUG: Skipping PR analysis for fast performance...")
                pull_requests = []
                print(f"🔀 DEBUG: Using empty PR list for speed")
            
            # SKIP BUILDS - commenting out to improve performance
            print("🔨 DEBUG: Skipping get_builds for performance optimization...")
            builds = []  # Empty list instead of API call
            print(f"🔨 DEBUG: get_builds skipped - using empty list")
            
            if work_items is None:
                print("❌ Azure DevOps: Failed to fetch work items")
            if pull_requests is None:
                print("❌ Azure DevOps: Failed to fetch pull requests") 
            # Builds skipped for performance - no error checking needed
            
            analytics = {
                'total_work_items': len(work_items) if work_items else 0,
                'total_pull_requests': len(pull_requests) if pull_requests else 0,
                'total_commits': 0,  # Will be calculated from PR data
                'total_repositories': 0,  # Will be calculated from PR data
                'work_items_by_type': {},
                'work_items_by_state': {},
                'work_items_by_assignee': {},
                'prs_by_status': {},
                'repository_breakdown': {},  # New: repositories involved in PRs
                'recent_work_items': [],
                'recent_pull_requests': [],
                'associated_prs': [],
                'involved_repositories': [],
                'work_items_with_prs': 0
            }
            
            
            # Initialize repository and PR tracking
            all_repositories = set()
            all_prs = []
            
            # Analyze work items and conditionally extract PR information
            if work_items:
                
                for item in work_items:
                    fields = item.get('fields', {})
                    
                    # By type
                    work_item_type = fields.get('System.WorkItemType', 'Unknown')
                    analytics['work_items_by_type'][work_item_type] = analytics['work_items_by_type'].get(work_item_type, 0) + 1
                    
                    # By state
                    state = fields.get('System.State', 'Unknown')
                    analytics['work_items_by_state'][state] = analytics['work_items_by_state'].get(state, 0) + 1
                    
                    # By assignee
                    assigned_to = fields.get('System.AssignedTo', {}).get('displayName', 'Unassigned')
                    analytics['work_items_by_assignee'][assigned_to] = analytics['work_items_by_assignee'].get(assigned_to, 0) + 1
                
                    # Process associated PRs only if PR analysis is enabled (can be slow)
                    if include_pr_analysis:
                        # Process associated PRs with enhanced GitHub detection
                        associated_prs = item.get('associated_prs', [])
                        if associated_prs:
                            analytics['work_items_with_prs'] += 1
                            for pr in associated_prs:
                                all_prs.append({
                                    'work_item_id': item.get('id'),
                                    'work_item_title': fields.get('System.Title', ''),
                                    'work_item_type': fields.get('System.WorkItemType', 'Unknown'),
                                    'work_item_state': fields.get('System.State', 'Unknown'),
                                    'pr_url': pr.get('url', ''),
                                    'pr_number': pr.get('pr_number', 'unknown'),
                                    'repository': pr.get('repository', ''),
                                    'full_repo_path': pr.get('full_repo_path', ''),
                                    'platform': pr.get('platform', 'unknown'),
                                    'relation_type': pr.get('relation_type', '')
                                })
                                # Add repository to set (prefer full repo path for GitHub)
                                repo_identifier = pr.get('full_repo_path', '')
                                if not repo_identifier:
                                    # Handle repository object structure
                                    repo_obj = pr.get('repository', {})
                                    if isinstance(repo_obj, dict):
                                        repo_identifier = repo_obj.get('name', '') or repo_obj.get('url', '')
                                    else:
                                        repo_identifier = str(repo_obj) if repo_obj else ''
                                
                                if repo_identifier and repo_identifier != pr.get('url', ''):
                                    all_repositories.add(repo_identifier)
                    # Note: If PR analysis disabled, work item still counted but no PR data extracted
                
                # Store PR and repository information
                analytics['associated_prs'] = all_prs
                analytics['involved_repositories'] = sorted(list(all_repositories))
                analytics['total_repositories'] = len(all_repositories)
                
                # Create repository breakdown for analytics
                repository_breakdown = {}
                for pr in all_prs:
                    repo = pr.get('full_repo_path', '') or pr.get('repository', '')
                    if repo:
                        repository_breakdown[repo] = repository_breakdown.get(repo, 0) + 1
                analytics['repository_breakdown'] = repository_breakdown
                
                if include_pr_analysis:
                    print(f"📋 Found {len(all_prs)} associated PRs across {len(all_repositories)} repositories")
                    print(f"📋 Repositories involved: {analytics['involved_repositories']}")
                else:
                    print(f"📋 PR analysis skipped for performance - {len(work_items)} work items processed")
                
                # Get recent work items sorted by creation date (most recent first, limit to 10)
                sorted_work_items = sorted(work_items, 
                                         key=lambda x: x.get('fields', {}).get('System.CreatedDate', ''), 
                                         reverse=True)
                analytics['recent_work_items'] = sorted_work_items[:10]
            
            # Analyze pull requests
            commit_count = 0
            if pull_requests:
                for pr in pull_requests:
                    status = pr.get('status', 'Unknown')
                    analytics['prs_by_status'][status] = analytics['prs_by_status'].get(status, 0) + 1
                    
                    # Count commits vs PRs
                    if pr.get('is_commit', False):
                        commit_count += 1
                    
                    # Extract repository information from pull requests
                    repo_identifier = pr.get('full_repo_path', '')
                    if not repo_identifier:
                        # Handle repository object structure
                        repo_obj = pr.get('repository', {})
                        if isinstance(repo_obj, dict):
                            repo_name = repo_obj.get('name', '')
                            if repo_name and repo_name.startswith('GitHub-'):
                                # Convert GitHub-206cdeed to GitHub/206cdeed format expected by resolver
                                repo_id = repo_name.replace('GitHub-', '')
                                repo_identifier = f'GitHub/{repo_id}'
                            else:
                                repo_identifier = repo_name or repo_obj.get('url', '')
                        else:
                            repo_identifier = str(repo_obj) if repo_obj else ''
                    
                    if repo_identifier and repo_identifier != pr.get('url', ''):
                        all_repositories.add(repo_identifier)
                
                # Get recent PRs (limit to 10 for display)
                analytics['recent_pull_requests'] = pull_requests[:10]
            
            # Create repository breakdown for resolution
            repository_breakdown = {}
            for pr in pull_requests or []:
                repo_obj = pr.get('repository', {})
                if isinstance(repo_obj, dict):
                    repo_name = repo_obj.get('name', 'Unknown')
                    # Use the original GitHub-xxx format for breakdown counting
                    repository_breakdown[repo_name] = repository_breakdown.get(repo_name, 0) + 1
            
            # Resolve repository names to actual GitHub repo names
            resolved_repos = self._get_resolved_repositories(sorted(list(all_repositories)), repository_breakdown)
            
            # Update final counts in analytics
            analytics['total_commits'] = commit_count
            analytics['total_repositories'] = len(resolved_repos)
            analytics['involved_repositories'] = [repo['github_repo'] for repo in resolved_repos if repo.get('github_repo')]
            analytics['resolved_repositories'] = resolved_repos  # Include full resolution data
            
            # Add all work items with PR data for debug table
            analytics['all_work_items_with_prs'] = work_items  # All work items with their PR associations
            
            print(f"📊 Final Analytics Summary:")
            print(f"   - Work Items: {analytics['total_work_items']}")
            print(f"   - Pull Requests: {analytics['total_pull_requests']}")
            print(f"   - Commits: {analytics['total_commits']}")
            print(f"   - Repositories (raw): {len(all_repositories)}")
            print(f"   - Repositories (resolved): {analytics['total_repositories']}")
            print(f"   - Repository Names: {analytics['involved_repositories']}")
            print(f"   - All work items with PRs: {len(analytics['all_work_items_with_prs'])}")
            
            return {
                'status': 'success',
                'data': analytics
            }
            
        except Exception as e:
            print(f"Error calculating Azure DevOps analytics: {e}")
            return {
                'status': 'error',
                'message': f'Error calculating analytics: {str(e)}'
            }
    
    def get_chart_data(self, chart_type='work_items_by_type', days=30, detailed_mode=False):
        """Get chart data for Azure DevOps analytics with optional detailed mode"""
        if detailed_mode:
            # Use detailed analytics for comprehensive PR/repository data
            result = self.get_analytics_summary(days, include_pr_analysis=True)
        else:
            # Use streamlined analytics for faster performance
            result = self.get_streamlined_analytics(days)
        
        if result['status'] != 'success':
            return None
        
        data = result['data']
        
        # Prepare chart data based on type
        if chart_type == 'work_items_by_type':
            types = list(data['work_items_by_type'].keys())
            values = list(data['work_items_by_type'].values())
            
            if not types or not any(values):
                return self._create_empty_chart("No work items found for the selected time period")
            
            fig = go.Figure(data=go.Pie(
                labels=types,
                values=values,
                name='Work Items by Type'
            ))
            
            fig.update_layout(
                title=f'Work Items by Type - Last {days} days'
            )
            
        elif chart_type == 'work_items_by_state':
            states = list(data['work_items_by_state'].keys())
            values = list(data['work_items_by_state'].values())
            
            if not states or not any(values):
                return self._create_empty_chart("No work items found for the selected time period")
            
            fig = go.Figure(data=go.Bar(
                x=states,
                y=values,
                name='Work Items by State'
            ))
            
            fig.update_layout(
                title=f'Work Items by State - Last {days} days',
                xaxis_title='State',
                yaxis_title='Number of Work Items',
                hovermode='x unified'
            )
            
        elif chart_type == 'work_items_by_assignee':
            assignees = list(data['work_items_by_assignee'].keys())
            values = list(data['work_items_by_assignee'].values())
            
            if not assignees or not any(values):
                return self._create_empty_chart("No assignee data available")
            
            fig = go.Figure(data=go.Bar(
                x=assignees,
                y=values,
                name='Work Items by Assignee'
            ))
            
            fig.update_layout(
                title=f'Work Items by Assignee - Last {days} days',
                xaxis_title='Assignee',
                yaxis_title='Number of Work Items',
                hovermode='x unified'
            )
            
        elif chart_type == 'prs_by_status':
            if not detailed_mode:
                return self._create_empty_chart("PR status data requires detailed mode. Please switch to detailed analysis mode.")
            
            statuses = list(data.get('prs_by_status', {}).keys())
            values = list(data.get('prs_by_status', {}).values())
            
            if not statuses or not any(values):
                return self._create_empty_chart("No pull request status data available")
            
            fig = go.Figure(data=go.Pie(
                labels=statuses,
                values=values,
                name='Pull Requests by Status'
            ))
            
            fig.update_layout(
                title=f'Pull Requests by Status - Last {days} days'
            )
            
        elif chart_type == 'repositories_breakdown':
            repositories = list(data.get('repository_breakdown', {}).keys())
            pr_counts = list(data.get('repository_breakdown', {}).values())
            
            if not repositories or not any(pr_counts):
                if not detailed_mode:
                    return self._create_empty_chart("Repository data requires detailed mode or no repositories found. Try switching to detailed analysis mode.")
                else:
                    return self._create_empty_chart("No repository data available for the selected time period")
            
            fig = go.Figure(data=go.Bar(
                x=repositories,
                y=pr_counts,
                name='PRs by Repository'
            ))
            
            fig.update_layout(
                title=f'Pull Requests by Repository - Last {days} days',
                xaxis_title='Repository',
                yaxis_title='Number of PRs/Commits',
                hovermode='x unified'
            )
            
        else:  # Default to overview
            categories = ['Work Items', 'Pull Requests', 'Repositories']
            values = [data['total_work_items'], data['total_pull_requests'], data['total_repositories']]
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
            
            fig = go.Figure(data=go.Bar(
                x=categories,
                y=values,
                marker_color=colors,
                name='Activity Overview'
            ))
            
            fig.update_layout(
                title=f'Azure DevOps Activity Overview - Last {days} days ({("Detailed" if detailed_mode else "Fast")} Mode)',
                xaxis_title='Activity Type',
                yaxis_title='Count',
                hovermode='x unified'
            )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


    def _create_empty_chart(self, message):
        """Create an empty chart with a message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            title="No Data Available",
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    def _resolve_repository_name(self, repository_id):
        """
        Resolve Azure DevOps repository ID to actual GitHub repository name
        Try multiple approaches: Azure DevOps API, GitHub API, and pattern matching
        """
        if not self.pat_token or not self.organization:
            return None
            
        try:
            # First, try to get repository details from Azure DevOps
            url = f"https://dev.azure.com/{self.organization}/_apis/git/repositories/{repository_id}?api-version=7.0"
            headers = {
                'Authorization': f'Basic {base64.b64encode(f":{self.pat_token}".encode()).decode()}',
                'Content-Type': 'application/json'
            }
            
            print(f"🔍 Resolving repository ID: {repository_id}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                repo_data = response.json()
                repo_name = repo_data.get('name', '')
                remote_url = repo_data.get('remoteUrl', '')
                
                print(f"✅ Repository details found:")
                print(f"   Name: {repo_name}")
                print(f"   Remote URL: {remote_url}")
                
                # Extract GitHub owner/repo from remote URL if it's a GitHub repository
                if 'github.com' in remote_url:
                    # Parse GitHub URL: https://github.com/owner/repo.git or git@github.com:owner/repo.git
                    import re
                    github_match = re.search(r'github\.com[:/]([^/]+)/([^/.]+)', remote_url)
                    if github_match:
                        owner, repo = github_match.groups()
                        github_repo = f"{owner}/{repo}"
                        print(f"🎯 Resolved to GitHub repo: {github_repo}")
                        return {
                            'github_repo': github_repo,
                            'repo_name': repo_name,
                            'remote_url': remote_url,
                            'owner': owner,
                            'repo': repo
                        }
                
                # If not GitHub, return the Azure DevOps repository name
                return {
                    'github_repo': f"azuredevops/{repo_name}",
                    'repo_name': repo_name,
                    'remote_url': remote_url,
                    'owner': 'azuredevops',
                    'repo': repo_name
                }
                
            else:
                print(f"⚠️ Azure DevOps API failed for repository {repository_id}: {response.status_code}")
                # Try alternative approach: check if it's a known GitHub repository pattern
                return self._try_github_resolution(repository_id)
                
        except Exception as e:
            print(f"❌ Error resolving repository {repository_id}: {e}")
            # Try alternative approach
            return self._try_github_resolution(repository_id)
    
    def _try_github_resolution(self, repository_id):
        """
        Try to resolve repository using GitHub API or known patterns
        """
        try:
            # Check if this matches known repository patterns from your organization
            # This is where you'd add specific mappings for your repositories
            known_repos = {
                '206cdeed-ccde-4df1-a203-092a2522662f': {
                    'github_repo': 'tr/cs-prof-cloud_ultratax-api-services',
                    'repo_name': 'cs-prof-cloud_ultratax-api-services',
                    'owner': 'tr',
                    'repo': 'cs-prof-cloud_ultratax-api-services',
                    'remote_url': 'https://github.com/tr/cs-prof-cloud_ultratax-api-services'
                },
                '0d836de7-dfee-46c2-a340-a39d84189402': {
                    'github_repo': 'tr/tax-professional-services',
                    'repo_name': 'tax-professional-services',
                    'owner': 'tr',
                    'repo': 'tax-professional-services',
                    'remote_url': 'https://github.com/tr/tax-professional-services'
                },
                '2c2726b0-50bd-4425-89ad-a1361ffa3467': {
                    'github_repo': 'tr/tax-automation-engine',
                    'repo_name': 'tax-automation-engine',
                    'owner': 'tr',
                    'repo': 'tax-automation-engine',
                    'remote_url': 'https://github.com/tr/tax-automation-engine'
                }
            }
            
            # Check for exact match first
            if repository_id in known_repos:
                print(f"🎯 Found in known repositories mapping: {known_repos[repository_id]['github_repo']}")
                return known_repos[repository_id]
            
            # Check for partial match (shortened ID)
            for full_id, repo_info in known_repos.items():
                if full_id.startswith(repository_id):
                    print(f"🎯 Found partial match for {repository_id} -> {full_id}: {repo_info['github_repo']}")
                    return repo_info
            
            # If not in known repos, try to make an educated guess based on patterns
            # This could be enhanced with more sophisticated logic
            print(f"🔍 Attempting pattern-based resolution for {repository_id}")
            
            # Try to extract meaningful name from repository ID patterns
            # This is a fallback that could be improved with more data
            short_id = repository_id[:8]
            return {
                'github_repo': f'tr/repo-{short_id}',
                'repo_name': f'repo-{short_id}',
                'owner': 'tr',
                'repo': f'repo-{short_id}',
                'remote_url': f'https://github.com/tr/repo-{short_id}'
            }
            
        except Exception as e:
            print(f"❌ GitHub resolution failed for {repository_id}: {e}")
            return None
    
    def get_repositories_fast(self, days=30):
        """
        Fast repository extraction without full analytics - optimized for GitHub sync
        """
        print(f"🚀 FAST REPO EXTRACTION: Getting repositories for {days} days...")
        
        try:
            # Get work items quickly (without PR relations)
            work_items = self._get_work_items_fast(days)
            if not work_items:
                return {
                    'status': 'error',
                    'message': 'No work items found'
                }
            
            print(f"📋 Found {len(work_items)} work items, extracting repository info...")
            
            # Get PR data for a small sample to extract repositories quickly
            # We only need to analyze a few recent work items to get the repository list
            sample_size = min(20, len(work_items))  # Analyze only 20 most recent work items
            sample_work_items = sorted(work_items, 
                                     key=lambda x: x.get('fields', {}).get('System.CreatedDate', ''), 
                                     reverse=True)[:sample_size]
            
            print(f"🔍 Analyzing {sample_size} recent work items for repository extraction...")
            
            # Get PR relations for sample work items
            work_item_ids = [item['id'] for item in sample_work_items]
            base_url = self._get_base_url()
            detailed_work_items = self._get_work_item_details(work_item_ids, base_url)
            
            # Extract repositories from PR relations
            repositories = set()
            repository_breakdown = {}
            
            if detailed_work_items:
                for item in detailed_work_items:
                    associated_prs = item.get('associated_prs', [])
                    for pr in associated_prs:
                        # Extract repository from PR relation
                        repo_url = pr.get('url', '')
                        if 'GitHub' in repo_url:
                            # Extract repository ID from GitHub URL
                            if 'GitHub/Commit/' in repo_url or 'GitHub/PullRequest/' in repo_url:
                                # Extract repo ID from vstfs URL
                                parts = repo_url.split('/')
                                for i, part in enumerate(parts):
                                    if part in ['Commit', 'PullRequest'] and i > 0:
                                        repo_id = parts[i-1]
                                        repo_path = f'GitHub/{repo_id}'
                                        repositories.add(repo_path)
                                        repository_breakdown[f'GitHub-{repo_id[:8]}'] = repository_breakdown.get(f'GitHub-{repo_id[:8]}', 0) + 1
                                        break
            
            print(f"📊 Found {len(repositories)} unique repositories from sample analysis")
            
            # Resolve repository names
            resolved_repos = self._get_resolved_repositories(sorted(list(repositories)), repository_breakdown)
            
            return {
                'status': 'success',
                'data': {
                    'repositories': resolved_repos,
                    'total_repositories': len(resolved_repos),
                    'sample_size': sample_size,
                    'total_work_items': len(work_items)
                }
            }
            
        except Exception as e:
            print(f"❌ Error in fast repository extraction: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error extracting repositories: {str(e)}'
            }

    def _get_resolved_repositories(self, involved_repositories, repository_breakdown):
        """
        Get resolved repository names for all involved repositories
        """
        resolved_repos = []
        
        for repo_path in involved_repositories:
            if repo_path.startswith('GitHub/'):
                # Extract repo ID
                repo_id = repo_path.replace('GitHub/', '')
                
                # Try to resolve the actual repository name
                resolved_info = self._resolve_repository_name(repo_id)
                
                if resolved_info:
                    # Use the resolved GitHub repository name
                    github_repo = resolved_info['github_repo']
                    pr_count = repository_breakdown.get(f'GitHub-{repo_id[:8]}', 0)
                    
                    resolved_repos.append({
                        'repository_id': repo_id,
                        'github_repo': github_repo,
                        'display_name': resolved_info['repo_name'],
                        'owner': resolved_info['owner'],
                        'repo': resolved_info['repo'],
                        'remote_url': resolved_info['remote_url'],
                        'pr_count': pr_count,
                        'full_path': repo_path,
                        'resolved': True
                    })
                else:
                    # Fallback to placeholder if resolution fails
                    pr_count = repository_breakdown.get(f'GitHub-{repo_id[:8]}', 0)
                    resolved_repos.append({
                        'repository_id': repo_id,
                        'github_repo': f'owner/repo-{repo_id[:8]}',
                        'display_name': f'GitHub-{repo_id[:8]}',
                        'owner': 'owner',
                        'repo': f'repo-{repo_id[:8]}',
                        'remote_url': '',
                        'pr_count': pr_count,
                        'full_path': repo_path,
                        'resolved': False
                    })
        
        return resolved_repos

    def _get_work_items_fast(self, days=30):
        """
        Fast work items retrieval without PR relations - use the same successful method as get_work_items
        """
        print(f"📋 FAST MODE: Delegating to proven get_work_items method...")
        
        # Just use the existing working method but return only basic data
        work_items = self.get_work_items(days=days)
        
        if work_items:
            print(f"✅ FAST MODE: Successfully got {len(work_items)} work items")
            return work_items
        else:
            print(f"❌ FAST MODE: No work items returned from get_work_items")
            return []

    def get_workitems_only_summary(self, days=30):
        """
        Get work items summary without PR analysis for fast initial loading
        """
        print(f"🚀 Getting work items only summary for {days} days...")
        
        try:
            # Get work items without PR relations
            work_items = self._get_work_items_fast(days)
            if not work_items:
                return {
                    'status': 'error',
                    'message': 'No work items found'
                }
            
            # Analyze work items data
            total_work_items = len(work_items)
            work_items_by_type = {}
            work_items_by_state = {}
            work_items_by_assignee = {}
            recent_work_items = []
            
            # Sort work items by creation date for recent items (most recent first)
            sorted_work_items = sorted(work_items, 
                                     key=lambda x: x.get('fields', {}).get('System.CreatedDate', ''), 
                                     reverse=True)
            
            for item in work_items:
                fields = item.get('fields', {})
                
                # Count by type
                work_item_type = fields.get('System.WorkItemType', 'Unknown')
                work_items_by_type[work_item_type] = work_items_by_type.get(work_item_type, 0) + 1
                
                # Count by state
                state = fields.get('System.State', 'Unknown')
                work_items_by_state[state] = work_items_by_state.get(state, 0) + 1
                
                # Count by assignee
                assignee = fields.get('System.AssignedTo', {}).get('displayName', 'Unassigned')
                work_items_by_assignee[assignee] = work_items_by_assignee.get(assignee, 0) + 1
            
            # Get recent items based on changed date (limit to 10)
            recent_work_items = sorted_work_items[:10]
            
            return {
                'status': 'success',
                'data': {
                    'total_work_items': total_work_items,
                    'total_pull_requests': 0,  # Will be updated later
                    'total_commits': 0,  # Will be updated later
                    'total_repositories': 0,  # Will be updated later
                    'work_items_by_type': work_items_by_type,
                    'work_items_by_state': work_items_by_state,
                    'work_items_by_assignee': work_items_by_assignee,
                    'recent_work_items': recent_work_items,
                    'recent_pull_requests': [],  # Will be populated later
                    'pr_loading': True  # Indicates PR data is still loading
                }
            }
            
        except Exception as e:
            print(f"❌ Error in get_workitems_only_summary: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error getting work items summary: {str(e)}'
            }

    def get_streamlined_analytics(self, days=7):
        """
        Streamlined analytics flow for better performance:
        1. Get work items based on date filter (fast)
        2. Get PR data for recent items only (limited scope)
        3. Return focused analytics for charts and display
        """
        print(f"🚀 Starting streamlined analytics for last {days} days...")
        
        if not self.pat_token:
            return {'status': 'error', 'message': 'Azure DevOps PAT token not configured'}
        
        if not self.organization or not self.project:
            return {'status': 'error', 'message': 'Azure DevOps organization and project must be provided'}
        
        try:
            # Step 1: Get work items efficiently (fast)
            print(f"📋 Step 1: Getting work items for last {days} days...")
            work_items = self.get_work_items(days=days)
            
            if not work_items:
                print("⚠️ No work items found")
                return {
                    'status': 'success',
                    'data': {
                        'total_work_items': 0,
                        'total_pull_requests': 0,
                        'total_commits': 0,
                        'total_repositories': 0,
                        'work_items_by_type': {},
                        'work_items_by_state': {},
                        'recent_work_items': [],
                        'recent_pull_requests': [],
                        'repository_breakdown': {},
                        'performance_note': f'Fast mode - analyzed {days} days of data'
                    }
                }
            
            print(f"✅ Found {len(work_items)} work items")
            
            # Step 2: Get PR data for a limited set of recent work items (performance balance)
            print(f"🔀 Step 2: Getting PR data for recent work items (limited scope for performance)...")
            
            # Sort work items by creation date and take more items for PR analysis based on time range
            sorted_work_items = sorted(work_items, 
                                     key=lambda x: x.get('fields', {}).get('System.CreatedDate', ''), 
                                     reverse=True)
            
            # For accurate repository and PR counting, analyze ALL work items
            # This ensures we capture all repositories and PRs involved
            print(f"🔍 Analyzing ALL {len(work_items)} work items for complete PR/repository data...")
            recent_work_items_for_pr_analysis = work_items  # Analyze all work items
            
            # Get PR data for these recent items only
            if recent_work_items_for_pr_analysis:
                work_item_ids = [item['id'] for item in recent_work_items_for_pr_analysis]
                base_url = self._get_base_url()
                
                print(f"🔀 Analyzing PR relations for ALL {len(work_item_ids)} work items for complete data...")
                detailed_work_items = self._get_work_item_details(work_item_ids, base_url)
                
                if detailed_work_items:
                    # Create a mapping of work item ID to PR data
                    pr_data_map = {}
                    for item in detailed_work_items:
                        pr_data_map[item['id']] = item.get('associated_prs', [])
                    
                    # Update the recent work items with PR data
                    for item in recent_work_items_for_pr_analysis:
                        if item['id'] in pr_data_map:
                            item['associated_prs'] = pr_data_map[item['id']]
            
            # Step 3: Analyze and categorize all work items
            pr_count = 0
            commit_count = 0
            repositories = set()
            all_prs = []
            
            work_items_by_type = {}
            work_items_by_state = {}
            
            for item in work_items:
                fields = item.get('fields', {})
                
                # Categorize work items
                work_item_type = fields.get('System.WorkItemType', 'Unknown')
                work_items_by_type[work_item_type] = work_items_by_type.get(work_item_type, 0) + 1
                
                state = fields.get('System.State', 'Unknown')
                work_items_by_state[state] = work_items_by_state.get(state, 0) + 1
                
                # Extract PR/commit data from relations if available
                associated_prs = item.get('associated_prs', [])
                for pr in associated_prs:
                    if pr.get('relation_type') == 'commit':
                        commit_count += 1
                    else:
                        pr_count += 1
                        all_prs.append({
                            'title': f"PR #{pr.get('pr_number', 'N/A')}",
                            'url': pr.get('url', ''),
                            'repository': pr.get('repository', ''),
                            'work_item_id': item.get('id'),
                            'work_item_title': fields.get('System.Title', ''),
                            'created_date': fields.get('System.CreatedDate', '')
                        })
                    
                    # Track repositories
                    repo = pr.get('full_repo_path', '')
                    if not repo:
                        # Handle repository object structure
                        repo_obj = pr.get('repository', {})
                        if isinstance(repo_obj, dict):
                            repo = repo_obj.get('name', '') or repo_obj.get('url', '')
                        else:
                            repo = str(repo_obj) if repo_obj else ''
                    
                    if repo:
                        repositories.add(repo)
            
            # Create repository breakdown
            repository_breakdown = {}
            for pr in all_prs:
                repo = pr.get('repository', 'Unknown')
                # Handle repository object structure
                if isinstance(repo, dict):
                    repo = repo.get('name', 'Unknown')
                repository_breakdown[repo] = repository_breakdown.get(repo, 0) + 1
            
            # Sort recent items (limit to 10 for display)
            recent_work_items = sorted_work_items[:10]
            
            recent_pull_requests = sorted(all_prs,
                                        key=lambda x: x.get('created_date', ''),
                                        reverse=True)[:10]
            
            # Get the complete repository list for accurate counting
            # This ensures consistency between dashboard display and GitHub sync
            resolved_repos = self._get_resolved_repositories(sorted(list(repositories)), repository_breakdown)
            
            print(f"📊 Analysis complete:")
            print(f"   - Work Items: {len(work_items)}")
            print(f"   - Pull Requests: {pr_count}")
            print(f"   - Commits: {commit_count}")
            print(f"   - Repositories (raw): {len(repositories)}")
            print(f"   - Repositories (resolved): {len(resolved_repos)}")
            print(f"   - PR analysis performed on ALL {len(recent_work_items_for_pr_analysis)} work items")
            
            return {
                'status': 'success',
                'data': {
                    'total_work_items': len(work_items),
                    'total_pull_requests': pr_count,
                    'total_commits': commit_count,
                    'total_repositories': len(resolved_repos),  # Use resolved count for accuracy
                    'work_items_by_type': work_items_by_type,
                    'work_items_by_state': work_items_by_state,
                    'work_items_by_assignee': {},  # Simplified for performance
                    'recent_work_items': recent_work_items,
                    'recent_pull_requests': recent_pull_requests,
                    'all_work_items_with_prs': recent_work_items_for_pr_analysis,  # All work items with PR data for debug table
                    'repository_breakdown': repository_breakdown,
                    'involved_repositories': sorted(list(repositories)),
                    'resolved_repositories': resolved_repos,  # Include resolved repos for consistency
                    'performance_note': f'Complete analytics for {days} days - {len(work_items)} work items, PR analysis on ALL {len(recent_work_items_for_pr_analysis)} work items'
                }
            }
            
        except Exception as e:
            print(f"❌ Error in streamlined analytics: {e}")
            return {'status': 'error', 'message': f'Analytics error: {str(e)}'}


