# Multi-Platform Analytics Dashboard

**AI Nexus Hackathon 2025** 🏆

A comprehensive Python Flask application that provides analytics dashboards for multiple platforms including Datadog, GitHub, Azure DevOps, and Figma.

## 🚀 Features

### 📊 **Multi-Platform Integration**
- **Datadog Analytics**: Metrics, logs, and dashboard integration
- **GitHub Analytics**: Multi-repository PR analysis with summary tables  
- **Azure DevOps Analytics**: Work items, PRs, and repository tracking
- **Figma Analytics**: Design file and team collaboration metrics

### ⚡ **Performance Optimizations**
- **97% faster loading** for Azure DevOps (1.4s vs 1+ min)
- **Fast Mode**: Quick analysis (1-2 seconds)
- **Detailed Mode**: Comprehensive analysis (1 minute)
- **Smart caching** and optimized queries

### 📈 **Advanced Analytics**
- **6 Chart Types**: Overview, by Type, State, Assignee, PR Status, Repository Breakdown
- **Interactive Plotly Charts**: Professional visualizations
- **Real-time Data**: Live updates from all platforms
- **Multi-repository Support**: Analyze across multiple GitHub repos

### 🎨 **Modern UI/UX**
- **Bootstrap 5**: Responsive, modern design
- **Loading Indicators**: Smart progress feedback
- **Error Handling**: Graceful failure management
- **Mobile Friendly**: Works on all devices

## 🛠️ Prerequisites

- Python 3.7 or higher
- API access to desired platforms:
  - Datadog account with API/Application keys
  - GitHub Personal Access Token
  - Azure DevOps Personal Access Token
  - Figma Personal Access Token (optional)

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/RachitaModiTR/AnalyticsDashboard.git
   cd AnalyticsDashboard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your API tokens:
   ```env
   # Datadog Configuration
   DD_API_KEY=your_datadog_api_key
   DD_APPLICATION_KEY=your_datadog_app_key
   DD_SITE=datadoghq.com
   
   # GitHub Configuration  
   GITHUB_TOKEN=your_github_token
   
   # Azure DevOps Configuration
   AZURE_DEVOPS_PAT=your_azure_devops_token
   
   # Figma Configuration (Optional)
   FIGMA_TOKEN=your_figma_token
   
   # Flask Configuration
   SECRET_KEY=your_secret_key
   FLASK_ENV=development
   ```

## 🚀 Usage

1. **Start the application**
   ```bash
   python run.py
   ```

2. **Open your browser**
   Navigate to `http://localhost:5002`

3. **Configure each platform**
   - **Datadog**: Automatically configured via environment variables
   - **GitHub**: Add repositories dynamically in the UI
   - **Azure DevOps**: Configure organization, project, and area path
   - **Figma**: Set team ID in configuration

## 🎯 Azure DevOps Features

### **Performance Modes**
- **🚀 Fast Mode**: Work items analysis (1-2 seconds)
- **🔍 Detailed Mode**: Full PR/repository analysis (~1 minute)

### **Chart Types**
- **📊 Activity Overview**: Work Items, PRs, Repositories
- **🏷️ Work Items by Type**: Bug, Task, User Story breakdown
- **📋 Work Items by State**: Active, Resolved, Closed status
- **👤 Work Items by Assignee**: Workload distribution
- **🔀 Pull Requests by Status**: PR status analysis
- **📁 Repository Breakdown**: PRs/commits by repository

### **Smart Filtering**
- **Area Path Filtering**: Focus on specific project areas
- **Date Range Selection**: 7, 30, or 90 days
- **Dynamic Configuration**: Organization/project selection

## 🐙 GitHub Features

### **Multi-Repository Support**
- Add/remove repositories dynamically
- Cross-repository PR analysis
- Repository summary tables
- Comprehensive analytics across multiple repos

### **Analytics**
- Pull request metrics and trends
- Repository activity comparison
- Developer contribution analysis
- Time-based filtering

## 📊 API Endpoints

### **Datadog**
- `GET /api/datadog/analytics` - Datadog metrics summary
- `GET /api/datadog/charts/<metric>` - Chart data for specific metric

### **GitHub** 
- `GET /api/github/prs` - Pull request analytics
- `GET /api/github/prs/chart` - PR chart data

### **Azure DevOps**
- `GET /api/azuredevops/analytics` - Fast analytics
- `GET /api/azuredevops/analytics-detailed` - Detailed analytics
- `GET /api/azuredevops/chart` - Chart data
- `GET /api/azuredevops/workitems` - Work items data

### **Figma**
- `GET /api/figma/analytics` - Figma team analytics

## ⚙️ Configuration Options

### **Environment Variables**

| Variable | Description | Required |
|----------|-------------|----------|
| `DD_API_KEY` | Datadog API key | ✅ |
| `DD_APPLICATION_KEY` | Datadog application key | ✅ |
| `GITHUB_TOKEN` | GitHub personal access token | ❌ |
| `AZURE_DEVOPS_PAT` | Azure DevOps personal access token | ❌ |
| `FIGMA_TOKEN` | Figma personal access token | ❌ |

### **Dynamic Configuration**
- GitHub repositories: Configure via UI
- Azure DevOps: Organization/project/area path via UI
- Time ranges: Selectable in dashboard
- Chart types: Multiple visualization options

## 🔧 Technical Architecture

### **Backend**
- **Flask**: Web framework
- **Plotly**: Interactive charts
- **Requests**: API integrations
- **Python-dotenv**: Environment management

### **Frontend**
- **Bootstrap 5**: UI framework
- **JavaScript**: Dynamic interactions
- **Plotly.js**: Chart rendering
- **Responsive Design**: Mobile-first approach

### **Performance Optimizations**
- **Streamlined Analytics**: Fast work item retrieval
- **Batch Processing**: Efficient API calls
- **Smart Caching**: Reduced redundant requests
- **Conditional Loading**: Load data only when needed

## 🚨 Troubleshooting

### **Common Issues**

1. **Authentication Errors**
   - Verify API tokens are correct and active
   - Check token permissions and scopes
   - Ensure environment variables are loaded

2. **Performance Issues**
   - Use Fast Mode for quick analysis
   - Reduce time range for faster loading
   - Check network connectivity

3. **Data Not Loading**
   - Verify API endpoints are accessible
   - Check organization/project names
   - Ensure area paths are correct

4. **Chart Display Issues**
   - Check browser console for JavaScript errors
   - Verify Plotly.js is loading correctly
   - Try refreshing the page

## 🌟 Performance Highlights

- **Azure DevOps**: 97% performance improvement
- **GitHub**: Multi-repo analysis in seconds
- **Datadog**: Real-time metrics display
- **UI**: Responsive design with smart loading

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 🏆 AI Nexus Hackathon 2025

This project was developed for the AI Nexus Hackathon 2025, showcasing advanced analytics capabilities across multiple platforms with performance optimizations and modern UI/UX design.

## 📞 Support

For issues and questions:
- Open an issue in this repository
- Check the troubleshooting section above
- Review platform-specific API documentation
