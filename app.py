from datetime import datetime
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import requests
from config import Config
from github_analytics import GitHubPullRequestAnalytics
from azuredevops_analytics import AzureDevOpsAnalytics
from figma_analytics import FigmaAnalytics
from chatbot_analytics import ChatbotAnalytics
from datadog_analytics import DatadogApplicationKeyAnalytics

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Initialize analytics clients
github_analytics = GitHubPullRequestAnalytics()
azuredevops_analytics = AzureDevOpsAnalytics()
figma_analytics = FigmaAnalytics()
datadog_analytics = DatadogApplicationKeyAnalytics()
chatbot_analytics = ChatbotAnalytics()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')





# GitHub Pull Request API Routes
@app.route('/api/github/prs')
def get_github_pull_requests():
    """API endpoint to get GitHub pull request analytics for multiple repositories"""
    days = request.args.get('days', 30, type=int)
    repos = request.args.getlist('repos')  # Get list of repositories from URL parameters
    
    # If no repos specified in request, fall back to config (for backward compatibility)
    if not repos:
        if Config.GITHUB_OWNER and Config.GITHUB_REPO:
            repos = [f"{Config.GITHUB_OWNER}/{Config.GITHUB_REPO}"]
    
    if not repos:
        return jsonify({
            'status': 'error',
            'message': 'No repositories specified. Please provide repos parameter.'
        }), 400
    
    # Get analytics for multiple repositories
    combined_analytics = get_multi_repo_analytics(repos, days)
    return jsonify(combined_analytics)

@app.route('/api/github/prs/<int:pr_number>')
def get_github_pull_request_details(pr_number):
    """API endpoint to get specific pull request details"""
    data = github_analytics.get_pull_request_details(pr_number)
    
    if data:
        return jsonify({
            'status': 'success',
            'data': data
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch pull request details'
        }), 500

@app.route('/api/github/prs/chart')
def get_github_pr_chart():
    """API endpoint to get GitHub PR chart data for multiple repositories"""
    days = request.args.get('days', 30, type=int)
    chart_type = request.args.get('type', 'overview')
    repos = request.args.getlist('repos')  # Get list of repositories from URL parameters
    
    # If no repos specified in request, fall back to config (for backward compatibility)
    if not repos:
        if Config.GITHUB_OWNER and Config.GITHUB_REPO:
            repos = [f"{Config.GITHUB_OWNER}/{Config.GITHUB_REPO}"]
    
    if not repos:
        return jsonify({
            'status': 'error',
            'message': 'No repositories specified. Please provide repos parameter.'
        }), 404
    
    # Get chart data for multiple repositories
    chart_data = get_multi_repo_chart_data(repos, days, chart_type)
    
    if chart_data:
        return jsonify({
            'status': 'success',
            'chart': chart_data,
            'chart_type': chart_type  # Include chart type for frontend handling
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'No data available for GitHub chart'
        }), 404

# Azure DevOps API Routes
@app.route('/api/azuredevops/wiql-test')
def test_wiql_direct():
    """Direct test of WIQL query"""
    org = request.args.get('org', 'tr-tax')
    project = request.args.get('project', 'TaxProf')
    
    if not org or not project:
        return jsonify({'error': 'Org and project required'}), 400
    
    # Test with a very simple WIQL query first
    import requests
    import base64
    from config import Config
    
    if not Config.AZURE_DEVOPS_PAT:
        return jsonify({'error': 'No PAT token'}), 400
    
    # Create auth headers
    credentials = base64.b64encode(f":{Config.AZURE_DEVOPS_PAT}".encode()).decode()
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
    
    # Try without date filtering but with TOP limit - fix WIQL syntax
    simple_query = f"""
    SELECT [System.Id], [System.Title], [System.WorkItemType], [System.State], [System.CreatedDate]
    FROM WorkItems 
    WHERE [System.TeamProject] = '{project}'
    ORDER BY [System.CreatedDate] DESC
    """
    
    # FIX: Add API version to the URL and add top parameter
    url = f"https://dev.azure.com/{org}/{project}/_apis/wit/wiql?api-version=6.0&$top=100"
    
    payload = {"query": simple_query}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        result = {
            'query': simple_query,
            'url': url,
            'status_code': response.status_code,
            'response': response.json() if response.status_code == 200 else response.text,
            'headers_sent': 'Authorization' in headers
        }
        
        if response.status_code == 200:
            work_items = response.json().get('workItems', [])
            result['work_item_count'] = len(work_items)
            result['sample_work_items'] = work_items[:5]  # First 5 work items as sample
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/azuredevops/prs-repos')
def get_azuredevops_prs_repos():
    """API endpoint to get PRs and repositories associated with work items"""
    org = request.args.get('org', '')
    project = request.args.get('project', '')
    area_path = request.args.get('area_path', '')
    
    # Validate required parameters
    if not org or not project:
        return jsonify({
            'status': 'error',
            'message': 'Organization and project name are required'
        }), 400
    
    # Update the Azure DevOps analytics instance
    azuredevops_analytics.organization = org
    azuredevops_analytics.project = project
    azuredevops_analytics.area_path = area_path
    
    result = azuredevops_analytics.get_analytics_summary(days=30)
    
    if result.get('status') == 'success':
        data = result['data']
        pr_repo_info = {
            'status': 'success',
            'summary': {
                'total_work_items': data.get('total_work_items', 0),
                'work_items_with_prs': data.get('work_items_with_prs', 0),
                'total_associated_prs': len(data.get('associated_prs', [])),
                'total_repositories': len(data.get('involved_repositories', []))
            },
            'associated_prs': data.get('associated_prs', []),
            'involved_repositories': data.get('involved_repositories', [])
        }
        return jsonify(pr_repo_info)
    else:
        return jsonify(result)

@app.route('/api/azuredevops/workitems-fast')
def get_azuredevops_workitems_fast():
    """API endpoint for optimized fast work items fetch"""
    org = request.args.get('org', '')
    project = request.args.get('project', '')
    area_path = request.args.get('area_path', '')
    work_item_type = request.args.get('type')
    state = request.args.get('state')
    
    # Validate required parameters
    if not org or not project:
        return jsonify({
            'status': 'error',
            'message': 'Organization and project name are required'
        }), 400
    
    # Update the Azure DevOps analytics instance
    azuredevops_analytics.organization = org
    azuredevops_analytics.project = project
    azuredevops_analytics.area_path = area_path
    
    try:
        work_items = azuredevops_analytics.get_work_items(work_item_type=work_item_type, state=state)
        
        if work_items is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch work items'
            }), 500
        
        return jsonify({
            'status': 'success',
            'data': {
                'work_items': work_items,
                'total_count': len(work_items),
                'area_path': area_path,
                'filters': {
                    'type': work_item_type,
                    'state': state
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching work items: {str(e)}'
        }), 500

@app.route('/api/azuredevops/github-prs')
def get_azuredevops_github_prs():
    """API endpoint for detailed GitHub PR analysis of work items"""
    org = request.args.get('org', '')
    project = request.args.get('project', '')
    area_path = request.args.get('area_path', '')
    
    # Validate required parameters
    if not org or not project:
        return jsonify({
            'status': 'error',
            'message': 'Organization and project name are required'
        }), 400
    
    # Update the Azure DevOps analytics instance
    azuredevops_analytics.organization = org
    azuredevops_analytics.project = project
    azuredevops_analytics.area_path = area_path
    
    try:
        work_items = azuredevops_analytics.get_work_items_with_github_prs()
        
        if work_items is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch work items with GitHub PR analysis'
            }), 500
        
        # Extract GitHub PR summary
        github_prs = []
        github_repos = set()
        
        for item in work_items:
            for pr in item.get('associated_prs', []):
                if pr.get('platform') == 'GitHub':
                    github_prs.append({
                        'work_item_id': item.get('id'),
                        'work_item_title': item.get('fields', {}).get('System.Title', ''),
                        'pr_url': pr.get('url'),
                        'pr_number': pr.get('pr_number'),
                        'repository': pr.get('full_repo_path', pr.get('repository')),
                        'platform': pr.get('platform')
                    })
                    repo = pr.get('full_repo_path', '') or pr.get('repository', '')
                    if repo:
                        github_repos.add(repo)
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_work_items': len(work_items),
                'work_items_with_github_prs': len([item for item in work_items if any(pr.get('platform') == 'GitHub' for pr in item.get('associated_prs', []))]),
                'github_prs': github_prs,
                'github_repositories': sorted(list(github_repos)),
                'area_path': area_path
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error analyzing GitHub PRs: {str(e)}'
        }), 500

@app.route('/api/azuredevops/comprehensive-pr-analysis')
def get_comprehensive_pr_analysis():
    """Comprehensive PR analysis endpoint with detailed work item and development work information"""
    org = request.args.get('org', '')
    project = request.args.get('project', '')
    area_path = request.args.get('area_path', '')
    
    # Validate required parameters
    if not org or not project:
        return jsonify({
            'status': 'error',
            'message': 'Organization and project name are required'
        }), 400
    
    # Update the Azure DevOps analytics instance
    azuredevops_analytics.organization = org
    azuredevops_analytics.project = project
    azuredevops_analytics.area_path = area_path
    
    try:
        work_items = azuredevops_analytics.get_work_items_with_github_prs()
        
        if work_items is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch work items with PR analysis'
            }), 500
        
        # Comprehensive analysis
        github_prs = []
        azure_prs = []
        all_repositories = set()
        work_items_with_prs = []
        pr_by_type = {'GitHub': 0, 'Azure DevOps': 0, 'Commits': 0}
        
        for item in work_items:
            item_prs = item.get('associated_prs', [])
            if item_prs:
                work_item_info = {
                    'id': item.get('id'),
                    'title': item.get('fields', {}).get('System.Title', ''),
                    'type': item.get('fields', {}).get('System.WorkItemType', ''),
                    'state': item.get('fields', {}).get('System.State', ''),
                    'area_path': item.get('fields', {}).get('System.AreaPath', ''),
                    'pr_count': len(item_prs),
                    'associated_prs': []
                }
                
                for pr in item_prs:
                    pr_detail = {
                        'platform': pr.get('platform'),
                        'pr_number': pr.get('pr_number'),
                        'repository': pr.get('repository'),
                        'full_repo_path': pr.get('full_repo_path'),
                        'url': pr.get('url'),
                        'title': pr.get('title', ''),
                        'relation_type': pr.get('relation_type'),
                        'is_commit': 'commit-' in str(pr.get('pr_number', ''))
                    }
                    
                    work_item_info['associated_prs'].append(pr_detail)
                    
                    # Categorize PRs
                    if pr.get('platform') == 'GitHub':
                        if pr_detail['is_commit']:
                            pr_by_type['Commits'] += 1
                        else:
                            pr_by_type['GitHub'] += 1
                            github_prs.append(pr_detail)
                    elif pr.get('platform') == 'Azure DevOps':
                        pr_by_type['Azure DevOps'] += 1
                        azure_prs.append(pr_detail)
                    
                    # Add repository
                    repo = pr.get('full_repo_path', '') or pr.get('repository', '')
                    if repo:
                        all_repositories.add(repo)
                
                work_items_with_prs.append(work_item_info)
        
        return jsonify({
            'status': 'success',
            'data': {
                'summary': {
                    'total_work_items_analyzed': len(work_items),
                    'work_items_with_development_work': len(work_items_with_prs),
                    'total_prs_and_commits': sum(pr_by_type.values()),
                    'github_prs': pr_by_type['GitHub'],
                    'azure_devops_prs': pr_by_type['Azure DevOps'],
                    'commits': pr_by_type['Commits'],
                    'total_repositories': len(all_repositories),
                    'area_path': area_path
                },
                'repositories': sorted(list(all_repositories)),
                'work_items_with_development_work': work_items_with_prs,
                'github_prs': github_prs,
                'azure_devops_prs': azure_prs,
                'pr_breakdown_by_type': pr_by_type
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error in comprehensive PR analysis: {str(e)}'
        }), 500

@app.route('/api/azuredevops/debug-workitem/<int:work_item_id>')
def debug_workitem_relations(work_item_id):
    """Debug endpoint to examine a specific work item's relations"""
    org = request.args.get('org', 'tr-tax')
    project = request.args.get('project', 'TaxProf')
    
    # Update the Azure DevOps analytics instance
    azuredevops_analytics.organization = org
    azuredevops_analytics.project = project
    
    try:
        base_url = azuredevops_analytics._get_base_url()
        if not base_url:
            return jsonify({'error': 'Could not construct base URL'}), 500
        
        # Get work item with all relations expanded
        url = f"{base_url}/wit/workitems/{work_item_id}?api-version=6.0&$expand=relations"
        headers = azuredevops_analytics._get_headers()
        
        if not headers:
            return jsonify({'error': 'No authentication headers available'}), 500
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            work_item_data = response.json()
            relations = work_item_data.get('relations', [])
            
            # Analyze relations
            relation_summary = []
            pr_links = []
            
            for relation in relations:
                rel_type = relation.get('rel', '')
                url_val = relation.get('url', '')
                attributes = relation.get('attributes', {})
                
                relation_info = {
                    'relation_type': rel_type,
                    'url': url_val,
                    'attributes': attributes
                }
                relation_summary.append(relation_info)
                
                # Check if this could be a PR link
                is_potential_pr = any([
                    'pullrequest' in rel_type.lower(),
                    'artifactlink' in rel_type.lower(),
                    'development' in rel_type.lower(),
                    'github.com' in url_val.lower(),
                    'pull/' in url_val,
                    '_git/' in url_val.lower(),
                    'dev.azure.com' in url_val.lower()
                ])
                
                if is_potential_pr:
                    pr_links.append(relation_info)
            
            return jsonify({
                'work_item_id': work_item_id,
                'title': work_item_data.get('fields', {}).get('System.Title', 'Unknown'),
                'state': work_item_data.get('fields', {}).get('System.State', 'Unknown'),
                'work_item_type': work_item_data.get('fields', {}).get('System.WorkItemType', 'Unknown'),
                'total_relations': len(relations),
                'potential_pr_relations': len(pr_links),
                'all_relations': relation_summary,
                'potential_prs': pr_links
            })
        else:
            return jsonify({
                'error': f'Failed to fetch work item: {response.status_code}',
                'message': response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({'error': f'Exception: {str(e)}'}), 500

@app.route('/api/azuredevops/test')
def test_azuredevops_connection():
    """Test endpoint to validate Azure DevOps connection"""
    org = request.args.get('org', '')
    project = request.args.get('project', '')
    
    if not org:
        return jsonify({
            'status': 'error',
            'message': 'Organization name is required'
        }), 400
    
    # Update the Azure DevOps analytics instance
    azuredevops_analytics.organization = org
    azuredevops_analytics.project = project
    azuredevops_analytics.area_path = ''
    
    result = {
        'config': {
            'organization': azuredevops_analytics.organization,
            'project': azuredevops_analytics.project,
            'has_token': bool(azuredevops_analytics.pat_token),
            'base_url': azuredevops_analytics._get_base_url() if project else f"https://dev.azure.com/{org}"
        },
        'test_results': {}
    }
    
    # Test listing projects
    try:
        projects = azuredevops_analytics.list_projects()
        result['test_results']['projects'] = {
            'status': 'success' if projects is not None else 'failed',
            'count': len(projects) if projects else 0,
            'projects': [p.get('name') for p in projects] if projects else []
        }
    except Exception as e:
        result['test_results']['projects'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # If project specified, test work items API
    if project:
        try:
            work_items = azuredevops_analytics.get_work_items(days=365)  # Try 1 year to get any work items
            result['test_results']['work_items'] = {
                'status': 'success' if work_items is not None else 'failed',
                'count': len(work_items) if work_items else 0,
                'data_type': type(work_items).__name__
            }
        except Exception as e:
            result['test_results']['work_items'] = {
                'status': 'error',
                'error': str(e)
            }
    
    return jsonify({
        'status': 'success',
        'results': result
    })

@app.route('/api/azuredevops/debug')
def debug_azuredevops():
    """Debug endpoint for Azure DevOps connection"""
    org = request.args.get('org', '')
    project = request.args.get('project', '')
    area_path = request.args.get('area_path', '')
    
    # Validate required parameters
    if not org or not project:
        return jsonify({
            'status': 'error',
            'message': 'Organization and project name are required'
        }), 400
    
    # Update the Azure DevOps analytics instance with user-provided values
    azuredevops_analytics.organization = org
    azuredevops_analytics.project = project
    azuredevops_analytics.area_path = area_path
    
    debug_info = {
        'organization': azuredevops_analytics.organization,
        'project': azuredevops_analytics.project, 
        'area_path': azuredevops_analytics.area_path,
        'base_url': azuredevops_analytics._get_base_url(),
        'has_token': bool(azuredevops_analytics.pat_token),
        'token_length': len(azuredevops_analytics.pat_token) if azuredevops_analytics.pat_token else 0
    }
    
    return jsonify({
        'status': 'success',
        'debug_info': debug_info
    })

@app.route('/api/azuredevops/analytics')
def get_azuredevops_analytics():
    """API endpoint to get Azure DevOps analytics summary"""
    days = request.args.get('days', 30, type=int)
    org = request.args.get('org', '')
    project = request.args.get('project', '')
    area_path = request.args.get('area_path', '')
    
    # Validate required parameters
    if not org or not project:
        return jsonify({
            'status': 'error',
            'message': 'Organization and project name are required'
        }), 400
    
    # Update the Azure DevOps analytics instance with user-provided values
    azuredevops_analytics.organization = org
    azuredevops_analytics.project = project
    azuredevops_analytics.area_path = area_path
    
    # Use streamlined analytics for better performance (7-day default)
    result = azuredevops_analytics.get_streamlined_analytics(days)
    return jsonify(result)

@app.route('/api/azuredevops/analytics-detailed')
def get_azuredevops_analytics_detailed():
    """API endpoint to get detailed Azure DevOps analytics with PR analysis (slower)"""
    days = request.args.get('days', 30, type=int)
    org = request.args.get('org', '')
    project = request.args.get('project', '')
    area_path = request.args.get('area_path', '')
    
    # Validate required parameters
    if not org or not project:
        return jsonify({
            'status': 'error',
            'message': 'Organization and project name are required'
        }), 400
    
    # Update the Azure DevOps analytics instance with user-provided values
    azuredevops_analytics.organization = org
    azuredevops_analytics.project = project
    azuredevops_analytics.area_path = area_path
    
    # Use detailed mode with PR analysis (slower but comprehensive)
    result = azuredevops_analytics.get_analytics_summary(days, include_pr_analysis=True)
    return jsonify(result)

@app.route('/api/azuredevops/workitems')
def get_azuredevops_work_items():
    """API endpoint to get Azure DevOps work items"""
    days = request.args.get('days', 30, type=int)
    work_item_type = request.args.get('type', None)
    state = request.args.get('state', None)
    org = request.args.get('org', '')
    project = request.args.get('project', '')
    area_path = request.args.get('area_path', '')
    
    # Validate required parameters
    if not org or not project:
        return jsonify({
            'status': 'error',
            'message': 'Organization and project name are required'
        }), 400
    
    # Update the Azure DevOps analytics instance with user-provided values
    azuredevops_analytics.organization = org
    azuredevops_analytics.project = project
    azuredevops_analytics.area_path = area_path
    
    work_items = azuredevops_analytics.get_work_items(work_item_type, state, days)
    
    if work_items is not None:
        return jsonify({
            'status': 'success',
            'data': work_items
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch work items'
        }), 500

@app.route('/api/azuredevops/workitems-summary')
def get_azuredevops_workitems_summary():
    """API endpoint to get Azure DevOps work items summary with analytics (no PR data)"""
    days = request.args.get('days', 30, type=int)
    org = request.args.get('org', '')
    project = request.args.get('project', '')
    area_path = request.args.get('area_path', '')
    
    # Validate required parameters
    if not org or not project:
        return jsonify({
            'status': 'error',
            'message': 'Organization and project name are required'
        }), 400
    
    # Update the Azure DevOps analytics instance with user-provided values
    azuredevops_analytics.organization = org
    azuredevops_analytics.project = project
    azuredevops_analytics.area_path = area_path
    
    # Get work items only summary (fast loading)
    result = azuredevops_analytics.get_workitems_only_summary(days)
    return jsonify(result)

@app.route('/api/azuredevops/pullrequests')
def get_azuredevops_pull_requests():
    """API endpoint to get Azure DevOps pull requests"""
    days = request.args.get('days', 30, type=int)
    status = request.args.get('status', None)
    org = request.args.get('org', '')
    project = request.args.get('project', '')
    area_path = request.args.get('area_path', '')
    
    # Validate required parameters
    if not org or not project:
        return jsonify({
            'status': 'error',
            'message': 'Organization and project name are required'
        }), 400
    
    # Update the Azure DevOps analytics instance with user-provided values
    azuredevops_analytics.organization = org
    azuredevops_analytics.project = project
    azuredevops_analytics.area_path = area_path
    
    pull_requests = azuredevops_analytics.get_pull_requests(status, days)
    
    if pull_requests is not None:
        return jsonify({
            'status': 'success',
            'data': pull_requests
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch pull requests'
        }), 500

@app.route('/api/azuredevops/builds')
def get_azuredevops_builds():
    """API endpoint to get Azure DevOps builds"""
    days = request.args.get('days', 30, type=int)
    org = request.args.get('org', '')
    project = request.args.get('project', '')
    area_path = request.args.get('area_path', '')
    
    # Validate required parameters
    if not org or not project:
        return jsonify({
            'status': 'error',
            'message': 'Organization and project name are required'
        }), 400
    
    # Update the Azure DevOps analytics instance with user-provided values
    azuredevops_analytics.organization = org
    azuredevops_analytics.project = project
    azuredevops_analytics.area_path = area_path
    
    builds = azuredevops_analytics.get_builds(days)
    
    if builds is not None:
        return jsonify({
            'status': 'success',
            'data': builds
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch builds'
        }), 500

@app.route('/api/azuredevops/chart')
def get_azuredevops_chart():
    """API endpoint to get Azure DevOps chart data with analysis mode support"""
    days = request.args.get('days', 30, type=int)
    chart_type = request.args.get('type', 'overview')
    org = request.args.get('org', '')
    project = request.args.get('project', '')
    area_path = request.args.get('area_path', '')
    detailed = request.args.get('detailed', 'false').lower() == 'true'
    
    # Validate required parameters
    if not org or not project:
        return jsonify({
            'status': 'error',
            'message': 'Organization and project name are required'
        }), 400
    
    # Update the Azure DevOps analytics instance with user-provided values
    azuredevops_analytics.organization = org
    azuredevops_analytics.project = project
    azuredevops_analytics.area_path = area_path
    
    try:
        chart_data = azuredevops_analytics.get_chart_data(chart_type, days, detailed_mode=detailed)
        
        if chart_data:
            return jsonify({
                'status': 'success',
                'chart': chart_data,
                'chart_type': chart_type,
                'analysis_mode': 'detailed' if detailed else 'fast'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'No data available for {chart_type} chart'
            }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Chart generation error: {str(e)}'
        }), 500

@app.route('/api/azuredevops/repositories')
def get_azuredevops_repositories():
    """Extract GitHub repositories from Azure DevOps work items for GitHub tab integration"""
    days = int(request.args.get('days', 30))
    org = request.args.get('org', azuredevops_analytics.organization)
    project = request.args.get('project', azuredevops_analytics.project)
    area_path = request.args.get('area_path', azuredevops_analytics.area_path)
    
    if org:
        azuredevops_analytics.organization = org
    if project:
        azuredevops_analytics.project = project
    if area_path:
        azuredevops_analytics.area_path = area_path
    
    try:
        # Use the existing streamlined analytics to get repositories (same as Azure DevOps tab)
        # This ensures consistency with what's shown in the Azure DevOps dashboard
        result = azuredevops_analytics.get_streamlined_analytics(days)
        
        if result.get('status') == 'success':
            data = result.get('data', {})
            resolved_repos = data.get('resolved_repositories', [])
            
            # If no resolved repositories, fall back to involved repositories
            if not resolved_repos:
                involved_repos = data.get('involved_repositories', [])
                repository_breakdown = data.get('repository_breakdown', {})
                resolved_repos = azuredevops_analytics._get_resolved_repositories(involved_repos, repository_breakdown)
            
            return jsonify({
                'status': 'success',
                'repositories': resolved_repos,
                'total_repositories': len(resolved_repos),
                'analysis_period': f'{days} days',
                'total_work_items': data.get('total_work_items', 0),
                'total_prs': data.get('total_pull_requests', 0),
                'resolved_count': len([r for r in resolved_repos if r.get('resolved', False)]),
                'note': f'Repositories from Azure DevOps analytics (same as dashboard)'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('message', 'Failed to get Azure DevOps data')
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error extracting repositories: {str(e)}'
        }), 500

# Figma API Routes
@app.route('/api/figma/analytics')
def get_figma_analytics():
    """API endpoint to get Figma team analytics"""
    days = request.args.get('days', 30, type=int)
    
    result = figma_analytics.get_team_analytics(days)
    return jsonify(result)

@app.route('/api/figma/projects')
def get_figma_projects():
    """API endpoint to get Figma team projects"""
    projects = figma_analytics.get_team_projects()
    
    if projects is not None:
        return jsonify({
            'status': 'success',
            'data': projects
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch team projects'
        }), 500

@app.route('/api/figma/projects/<project_id>/files')
def get_figma_project_files(project_id):
    """API endpoint to get files from a specific project"""
    files = figma_analytics.get_project_files(project_id)
    
    if files is not None:
        return jsonify({
            'status': 'success',
            'data': files
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch project files'
        }), 500

@app.route('/api/figma/files/<file_key>')
def get_figma_file_info(file_key):
    """API endpoint to get detailed file information"""
    file_info = figma_analytics.get_file_info(file_key)
    
    if file_info is not None:
        return jsonify({
            'status': 'success',
            'data': file_info
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch file information'
        }), 500

@app.route('/api/figma/files/<file_key>/comments')
def get_figma_file_comments(file_key):
    """API endpoint to get file comments"""
    comments = figma_analytics.get_file_comments(file_key)
    
    if comments is not None:
        return jsonify({
            'status': 'success',
            'data': comments
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch file comments'
        }), 500

@app.route('/api/figma/search')
def search_figma_files():
    """API endpoint to search for files"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({
            'status': 'error',
            'message': 'Search query is required'
        }), 400
    
    results = figma_analytics.search_files(query)
    
    if results is not None:
        return jsonify({
            'status': 'success',
            'data': results
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to search files'
        }), 500

@app.route('/api/figma/chart')
def get_figma_chart():
    """API endpoint to get Figma chart data"""
    days = request.args.get('days', 30, type=int)
    chart_type = request.args.get('type', 'files_by_project')
    
    chart_data = figma_analytics.get_chart_data(chart_type, days)
    
    if chart_data:
        return jsonify({
            'status': 'success',
            'chart': chart_data
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'No data available for Figma chart'
        }), 404

# Datadog API Routes
@app.route('/api/datadog/logs')
def get_datadog_logs():
    """API endpoint to get Datadog logs"""
    query = request.args.get('query', '*')
    service = request.args.get('service', None)
    level = request.args.get('level', None)
    hours = request.args.get('hours', 24, type=int)
    limit = request.args.get('limit', 100, type=int)
    
    try:
        logs = datadog_analytics.get_logs(
            query=query,
            service=service,
            level=level,
            hours_back=hours,
            limit=limit
        )
        
        if logs is not None:
            return jsonify({
                'status': 'success',
                'data': logs
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch logs from Datadog'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching logs: {str(e)}'
        }), 500

@app.route('/api/datadog/logs/stats')
def get_datadog_log_stats():
    """API endpoint to get Datadog log statistics"""
    query = request.args.get('query', '*')
    service = request.args.get('service', None)
    level = request.args.get('level', None)
    hours = request.args.get('hours', 24, type=int)
    
    try:
        stats = datadog_analytics.get_log_statistics(
            query=query,
            service=service,
            level=level,
            hours_back=hours
        )
        
        if stats is not None:
            return jsonify({
                'status': 'success',
                'data': stats
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch log statistics from Datadog'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching log statistics: {str(e)}'
        }), 500

@app.route('/api/datadog/services')
def get_datadog_services():
    """API endpoint to get available services from Datadog logs"""
    hours = request.args.get('hours', 24, type=int)
    
    try:
        services = datadog_analytics.get_available_services(hours_back=hours)
        
        return jsonify({
            'status': 'success',
            'data': services
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching services: {str(e)}'
        }), 500

@app.route('/api/datadog/test')
def test_datadog_connection():
    """Test endpoint to validate Datadog connection"""
    try:
        # Test with a simple query
        test_logs = datadog_analytics.get_logs(query='*', limit=1)
        
        return jsonify({
            'status': 'success',
            'message': 'Datadog connection successful',
            'config': {
                'site': datadog_analytics.site,
                'has_api_key': bool(datadog_analytics.api_key),
                'has_application_key': bool(datadog_analytics.application_key)
            },
            'test_result': {
                'logs_fetched': test_logs is not None,
                'sample_count': len(test_logs) if test_logs else 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Datadog connection failed: {str(e)}'
        }), 500



# Multi-repository GitHub analytics helper functions
def get_multi_repo_analytics(repos, days):
    """Combine analytics from multiple repositories"""
    combined_data = {
        'total_prs': 0,
        'open_prs': 0,
        'closed_prs': 0,
        'merged_prs': 0,
        'average_additions': 0,
        'average_deletions': 0,
        'average_commits': 0,
        'average_changed_files': 0,
        'prs_by_author': {},
        'prs_by_day': {},
        'recent_prs': [],
        'repositories': {}
    }
    
    total_additions = 0
    total_deletions = 0
    total_commits = 0
    total_changed_files = 0
    total_prs_for_avg = 0
    
    for repo in repos:
        try:
            # Parse owner/repo
            parts = repo.split('/')
            if len(parts) != 2:
                continue
                
            owner, repo_name = parts
            
            # Create a temporary GitHub analytics instance for this repo
            temp_analytics = GitHubPullRequestAnalytics()
            temp_analytics.owner = owner
            temp_analytics.repo = repo_name
            temp_analytics.github_token = Config.GITHUB_TOKEN
            
            # Get analytics for this repository
            repo_result = temp_analytics.get_pull_request_analytics(days)
            
            if repo_result.get('status') == 'success':
                repo_data = repo_result['data']
                
                # Combine basic stats
                combined_data['total_prs'] += repo_data.get('total_prs', 0)
                combined_data['open_prs'] += repo_data.get('open_prs', 0) 
                combined_data['closed_prs'] += repo_data.get('closed_prs', 0)
                combined_data['merged_prs'] += repo_data.get('merged_prs', 0)
                
                # Accumulate for averages
                repo_total_prs = repo_data.get('total_prs', 0)
                if repo_total_prs > 0:
                    total_additions += repo_data.get('average_additions', 0) * repo_total_prs
                    total_deletions += repo_data.get('average_deletions', 0) * repo_total_prs
                    total_commits += repo_data.get('average_commits', 0) * repo_total_prs
                    total_changed_files += repo_data.get('average_changed_files', 0) * repo_total_prs
                    total_prs_for_avg += repo_total_prs
                
                # Combine authors (with repo prefix)
                for author, count in repo_data.get('prs_by_author', {}).items():
                    if author in combined_data['prs_by_author']:
                        combined_data['prs_by_author'][author] += count
                    else:
                        combined_data['prs_by_author'][author] = count
                
                # Combine by day
                for day, count in repo_data.get('prs_by_day', {}).items():
                    if day in combined_data['prs_by_day']:
                        combined_data['prs_by_day'][day] += count
                    else:
                        combined_data['prs_by_day'][day] = count
                
                # Add recent PRs (with repo info)
                for pr in repo_data.get('recent_prs', [])[:5]:  # Limit per repo
                    pr_copy = pr.copy()
                    pr_copy['repository'] = repo
                    combined_data['recent_prs'].append(pr_copy)
                
                # Store individual repo stats
                combined_data['repositories'][repo] = {
                    'total_prs': repo_data.get('total_prs', 0),
                    'open_prs': repo_data.get('open_prs', 0),
                    'closed_prs': repo_data.get('closed_prs', 0),
                    'merged_prs': repo_data.get('merged_prs', 0)
                }
                
        except Exception as e:
            print(f"Error processing repository {repo}: {e}")
            continue
    
    # Calculate combined averages
    if total_prs_for_avg > 0:
        combined_data['average_additions'] = total_additions / total_prs_for_avg
        combined_data['average_deletions'] = total_deletions / total_prs_for_avg
        combined_data['average_commits'] = total_commits / total_prs_for_avg
        combined_data['average_changed_files'] = total_changed_files / total_prs_for_avg
    
    # Sort recent PRs by date (newest first)
    combined_data['recent_prs'] = sorted(
        combined_data['recent_prs'], 
        key=lambda x: x.get('created_at', ''), 
        reverse=True
    )[:20]  # Limit to 20 most recent
    
    return {
        'status': 'success',
        'data': combined_data
    }

def get_multi_repo_chart_data(repos, days, chart_type):
    """Generate chart data for multiple repositories"""
    try:
        # Get combined analytics data
        analytics_result = get_multi_repo_analytics(repos, days)
        
        if analytics_result.get('status') != 'success':
            return None
            
        data = analytics_result['data']
        
        # Handle summary table differently
        if chart_type == 'summary':
            return create_repository_summary_table(data, repos)
        
        # Use the first repo's analytics instance to generate chart
        # (the chart generation logic should work with the combined data)
        if repos:
            parts = repos[0].split('/')
            if len(parts) == 2:
                owner, repo_name = parts
                temp_analytics = GitHubPullRequestAnalytics()
                temp_analytics.owner = owner
                temp_analytics.repo = repo_name
                temp_analytics.github_token = Config.GITHUB_TOKEN
                
                # Override the data with our combined data for chart generation
                return temp_analytics._create_chart_from_data(data, chart_type)
                
        return None
        
    except Exception as e:
        print(f"Error generating multi-repo chart data: {e}")
        return None

def create_repository_summary_table(data, repos):
    """Create a summary table for all repositories"""
    try:
        summary_data = {
            'type': 'table',
            'headers': ['Repository', 'Total PRs', 'Open', 'Closed', 'Merged', 'Merge Rate'],
            'rows': []
        }
        
        # Add individual repository data
        repositories_data = data.get('repositories', {})
        
        for repo in repos:
            repo_data = repositories_data.get(repo, {})
            total_prs = repo_data.get('total_prs', 0)
            open_prs = repo_data.get('open_prs', 0)
            closed_prs = repo_data.get('closed_prs', 0)
            merged_prs = repo_data.get('merged_prs', 0)
            
            # Calculate merge rate
            merge_rate = f"{(merged_prs / total_prs * 100):.1f}%" if total_prs > 0 else "0%"
            
            summary_data['rows'].append([
                repo,
                str(total_prs),
                str(open_prs),
                str(closed_prs), 
                str(merged_prs),
                merge_rate
            ])
        
        # Add total row
        total_prs = data.get('total_prs', 0)
        total_open = data.get('open_prs', 0)
        total_closed = data.get('closed_prs', 0)
        total_merged = data.get('merged_prs', 0)
        total_merge_rate = f"{(total_merged / total_prs * 100):.1f}%" if total_prs > 0 else "0%"
        
        summary_data['rows'].append([
            '<strong>TOTAL</strong>',
            f'<strong>{total_prs}</strong>',
            f'<strong>{total_open}</strong>',
            f'<strong>{total_closed}</strong>',
            f'<strong>{total_merged}</strong>',
            f'<strong>{total_merge_rate}</strong>'
        ])
        
        return summary_data
        
    except Exception as e:
        print(f"Error creating repository summary table: {e}")
        return None

# Chatbot API Routes
@app.route('/api/chatbot/analyze', methods=['POST'])
def chatbot_analyze():
    """API endpoint for chatbot analysis"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        data_source = data.get('data_source', 'general')
        context_data = data.get('context_data', {})
        
        if not question:
            return jsonify({
                'status': 'error',
                'message': 'Question is required'
            }), 400
        
        # Route to appropriate analysis method based on data source
        if data_source == 'datadog':
            response = chatbot_analytics.analyze_datadog_metrics(context_data, question)
        elif data_source == 'github':
            response = chatbot_analytics.analyze_github_analytics(context_data, question)
        elif data_source == 'azuredevops':
            response = chatbot_analytics.analyze_azure_devops_data(context_data, question)
        elif data_source == 'figma':
            response = chatbot_analytics.analyze_figma_data(context_data, question)
        else:
            response = chatbot_analytics.get_general_insights(context_data, question)
        
        return jsonify({
            'status': 'success',
            'response': response,
            'data_source': data_source,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Analysis error: {str(e)}'
        }), 500

@app.route('/api/chatbot/summary/<data_source>', methods=['POST'])
def chatbot_summary(data_source):
    """API endpoint for getting data summaries"""
    try:
        data = request.get_json()
        context_data = data.get('context_data', {})
        
        if not context_data:
            return jsonify({
                'status': 'error',
                'message': 'Context data is required'
            }), 400
        
        response = chatbot_analytics.get_data_summary(data_source, context_data)
        
        return jsonify({
            'status': 'success',
            'summary': response,
            'data_source': data_source,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Summary error: {str(e)}'
        }), 500

@app.route('/api/chatbot/suggest-questions/<data_source>', methods=['POST'])
def chatbot_suggest_questions(data_source):
    """API endpoint for getting suggested questions"""
    try:
        data = request.get_json()
        available_data = data.get('available_data', {})
        
        questions = chatbot_analytics.suggest_questions(data_source, available_data)
        
        return jsonify({
            'status': 'success',
            'questions': questions,
            'data_source': data_source,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Question suggestion error: {str(e)}'
        }), 500

@app.route('/api/chatbot/status')
def chatbot_status():
    """API endpoint to check chatbot configuration status"""
    try:
        # For Thomson Reuters integration, we don't need traditional API keys
        thomson_reuters_configured = chatbot_analytics.llm_provider == 'openai'
        
        status = {
            'llm_provider': chatbot_analytics.llm_provider,
            'openai_configured': thomson_reuters_configured,  # Thomson Reuters integration
            'anthropic_configured': bool(chatbot_analytics.anthropic_api_key),
            'azure_configured': bool(chatbot_analytics.azure_openai_endpoint and 
                                   chatbot_analytics.azure_openai_key and 
                                   chatbot_analytics.azure_openai_deployment),
            'thomson_reuters_configured': thomson_reuters_configured,
            'ready': bool(thomson_reuters_configured or 
                         chatbot_analytics.anthropic_api_key or 
                         (chatbot_analytics.azure_openai_endpoint and 
                          chatbot_analytics.azure_openai_key and 
                          chatbot_analytics.azure_openai_deployment))
        }
        
        return jsonify({
            'status': 'success',
            'data': status
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Status check error: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
