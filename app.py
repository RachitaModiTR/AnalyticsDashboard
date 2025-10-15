from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import requests
from config import Config
from datadog_analytics import DatadogApplicationKeyAnalytics
from github_analytics import GitHubPullRequestAnalytics
from azuredevops_analytics import AzureDevOpsAnalytics
from figma_analytics import FigmaAnalytics

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Initialize analytics clients
datadog_analytics = DatadogApplicationKeyAnalytics()
github_analytics = GitHubPullRequestAnalytics()
azuredevops_analytics = AzureDevOpsAnalytics()
figma_analytics = FigmaAnalytics()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html',
                         api_key=Config.DD_API_KEY,
                         application_key=Config.DD_APPLICATION_KEY,
                         site=Config.DD_SITE)

@app.route('/api/metrics')
def get_metrics():
    """API endpoint to get available metrics"""
    metrics = datadog_analytics.get_available_metrics()
    return jsonify(metrics)

@app.route('/api/metrics/<metric_name>')
def get_metric_data(metric_name):
    """API endpoint to get specific metric data"""
    hours = request.args.get('hours', 24, type=int)
    tags = request.args.get('tags', '')
    
    from_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
    to_time = int(datetime.now().timestamp())
    
    tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else None
    
    data = datadog_analytics.get_metrics_data(metric_name, from_time, to_time, tag_list)
    
    if data:
        return jsonify({
            'status': 'success',
            'data': data
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch metric data'
        }), 500

@app.route('/api/analytics')
def get_analytics():
    """API endpoint to get analytics dashboard data"""
    metric_names = request.args.getlist('metrics')
    hours = request.args.get('hours', 24, type=int)
    
    if not metric_names:
        return jsonify({
            'status': 'error',
            'message': 'No metrics specified'
        }), 400
    
    from_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
    to_time = int(datetime.now().timestamp())
    
    all_metrics_data = []
    for metric_name in metric_names:
        data = datadog_analytics.get_metrics_data(metric_name, from_time, to_time)
        if data and 'series' in data:
            all_metrics_data.extend(data['series'])
    
    # Create a combined metrics data structure
    combined_data = {
        'series': all_metrics_data,
        'from': from_time,
        'to': to_time
    }
    
    analytics_data = datadog_analytics.create_analytics_dashboard(combined_data)
    
    # If no real data available, generate sample data for demonstration
    if not analytics_data or not analytics_data.get('metrics_summary'):
        analytics_data = datadog_analytics._generate_sample_data(metric_names, hours)
    
    if analytics_data:
        return jsonify({
            'status': 'success',
            'data': analytics_data
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to create analytics data'
        }), 500

@app.route('/api/charts/<metric_name>')
def get_chart_data(metric_name):
    """API endpoint to get chart data for a specific metric"""
    hours = request.args.get('hours', 24, type=int)
    chart_type = request.args.get('type', 'line')
    
    chart_data = datadog_analytics.get_chart_data(metric_name, hours, chart_type)
    
    # If no real data available, generate sample chart data for demonstration
    if not chart_data:
        chart_data = datadog_analytics._generate_sample_chart_data(metric_name, hours, chart_type)
    
    if chart_data:
        return jsonify({
            'status': 'success',
            'chart': chart_data
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'No data available for chart'
        }), 404

@app.route('/api/datadog/dashboards')
def get_all_dashboards():
    """API endpoint to get all Datadog dashboards"""
    data = datadog_analytics.get_all_dashboards()
    
    if data:
        return jsonify({
            'status': 'success',
            'data': data
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch dashboards'
        }), 500

@app.route('/api/datadog/dashboards/<dashboard_id>')
def get_dashboard_by_id(dashboard_id):
    """API endpoint to get specific dashboard data by ID"""
    data = datadog_analytics.get_dashboard_by_id(dashboard_id)
    
    if data:
        return jsonify({
            'status': 'success',
            'data': data
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch dashboard data'
        }), 500

@app.route('/api/dashboard/<dashboard_id>')
def get_dashboard(dashboard_id):
    """API endpoint to get dashboard data (legacy endpoint)"""
    data = datadog_analytics.get_dashboard_data(dashboard_id)
    
    if data:
        return jsonify({
            'status': 'success',
            'data': data
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch dashboard data'
        }), 500

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

# Datadog Logs API Routes
@app.route('/api/datadog/logs')
def get_datadog_logs():
    """API endpoint to get Datadog logs"""
    query = request.args.get('query', '*')
    hours = request.args.get('hours', 24, type=int)
    limit = request.args.get('limit', 100, type=int)
    service = request.args.get('service', None)
    
    from_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
    to_time = int(datetime.now().timestamp())
    
    logs_data = datadog_analytics.get_logs(query, from_time, to_time, limit, service)
    
    if logs_data:
        return jsonify({
            'status': 'success',
            'data': logs_data
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch logs'
        }), 500

@app.route('/api/datadog/logs/summary')
def get_datadog_logs_summary():
    """API endpoint to get Datadog logs summary"""
    hours = request.args.get('hours', 24, type=int)
    
    summary = datadog_analytics.get_logs_summary(hours)
    
    if summary:
        return jsonify({
            'status': 'success',
            'data': summary
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch logs summary'
        }), 500

@app.route('/api/datadog/logs/search')
def search_datadog_logs():
    """API endpoint to search Datadog logs"""
    query = request.args.get('q', '*')
    hours = request.args.get('hours', 24, type=int)
    limit = request.args.get('limit', 50, type=int)
    service = request.args.get('service', None)
    level = request.args.get('level', None)
    
    # Build search query
    search_query = query
    if service:
        search_query = f"service:{service} {search_query}"
    if level:
        search_query = f"level:{level} {search_query}"
    
    from_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
    to_time = int(datetime.now().timestamp())
    
    logs_data = datadog_analytics.get_logs(search_query, from_time, to_time, limit)
    
    if logs_data:
        return jsonify({
            'status': 'success',
            'data': logs_data
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to search logs'
        }), 500

@app.route('/api/datadog/services')
def get_datadog_services():
    """API endpoint to get available services from Datadog"""
    services = datadog_analytics.get_available_services()
    
    return jsonify({
        'status': 'success',
        'data': services
    })

@app.route('/api/datadog/logs/send', methods=['POST'])
def send_log_to_datadog():
    """API endpoint to send a log entry to Datadog"""
    try:
        data = request.get_json()
        
        message = data.get('message', '')
        level = data.get('level', 'info')
        service = data.get('service', 'analytics-dashboard')
        host = data.get('host', None)
        tags = data.get('tags', None)
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'Message is required'
            }), 400
        
        success = datadog_analytics.send_log_to_datadog(message, level, service, host, tags)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Log sent successfully to Datadog'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send log to Datadog'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error sending log: {str(e)}'
        }), 500

# Datadog Dashboards API Routes
@app.route('/api/datadog/dashboards')
def get_datadog_dashboards():
    """API endpoint to get all Datadog dashboards"""
    dashboards = datadog_analytics.get_all_dashboards()
    
    return jsonify({
        'status': 'success',
        'data': dashboards
    })

@app.route('/api/datadog/dashboards/summary')
def get_datadog_dashboards_summary():
    """API endpoint to get Datadog dashboards summary"""
    summary = datadog_analytics.get_dashboard_summary()
    
    return jsonify({
        'status': 'success',
        'data': summary
    })

@app.route('/api/datadog/dashboards/<dashboard_id>')
def get_datadog_dashboard(dashboard_id):
    """API endpoint to get a specific dashboard by ID"""
    dashboard = datadog_analytics.get_dashboard_by_id(dashboard_id)
    
    if dashboard:
        return jsonify({
            'status': 'success',
            'data': dashboard
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Dashboard not found or failed to fetch'
        }), 404

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
