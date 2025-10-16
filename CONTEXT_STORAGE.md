# Context Storage System

## Overview

The Context Storage System automatically captures and stores data from all API endpoints (Datadog, GitHub, Azure DevOps, and Figma) to provide rich context to the AI chatbot. This ensures the chatbot can provide intelligent, data-driven insights based on your actual analytics data rather than generic responses.

## How It Works

### 1. Automatic Data Capture
- **Datadog**: Metrics and system performance data
- **GitHub**: Pull requests, repositories, and development analytics
- **Azure DevOps**: Work items, pull requests, and project management data
- **Figma**: Design files, projects, and collaboration metrics

### 2. Context Storage
- Data is stored in `context_data/api_context.json`
- Each data source maintains its own section with:
  - Raw data from APIs
  - Last fetch timestamp
  - Status (fetched/not_fetched)
  - Summary statistics

### 3. Smart Context Retrieval
- The chatbot automatically retrieves relevant context based on the data source selected
- Context is formatted for optimal LLM consumption
- Includes both stored data and any additional context provided

## API Endpoints

### Context Management
- `GET /api/chatbot/context/status` - Get current context storage status
- `POST /api/chatbot/context/clear` - Clear all stored context data

### Data Sources (Auto-Store Context)
- `GET /api/analytics` - Datadog metrics (stores context automatically)
- `GET /api/github/prs` - GitHub pull requests (stores context automatically)
- `GET /api/azuredevops/analytics` - Azure DevOps work items (stores context automatically)
- `GET /api/figma/analytics` - Figma design data (stores context automatically)

## Context Structure

```json
{
  "last_updated": "2025-10-16T13:31:49.143240",
  "data_sources": {
    "datadog": {
      "metrics": {...},
      "charts": {...},
      "last_fetch": "2025-10-16T13:30:00",
      "status": "fetched"
    },
    "github": {
      "pull_requests": [...],
      "repositories": [...],
      "analytics": {...},
      "last_fetch": "2025-10-16T13:25:00",
      "status": "fetched"
    },
    "azuredevops": {
      "work_items": [...],
      "pull_requests": [...],
      "analytics": {...},
      "last_fetch": "2025-10-16T13:20:00",
      "status": "fetched"
    },
    "figma": {
      "files": [...],
      "projects": [...],
      "analytics": {...},
      "last_fetch": "2025-10-16T13:15:00",
      "status": "fetched"
    }
  },
  "summary": {
    "total_work_items": 19,
    "total_pull_requests": 24,
    "total_repositories": 5,
    "total_metrics": 12,
    "last_activity": "2025-10-16T13:30:00"
  }
}
```

## Benefits

### 1. Data-Driven Responses
- Chatbot responses are based on actual data from your systems
- No more generic or outdated information
- Real-time insights based on current metrics

### 2. Cross-Platform Analysis
- Correlate data across different platforms
- Identify patterns between development, design, and operations
- Comprehensive view of your entire workflow

### 3. Intelligent Context Selection
- Automatically selects relevant data based on the question
- Combines stored context with additional provided context
- Optimized for LLM consumption

### 4. Persistent Storage
- Context persists across chatbot sessions
- Data is automatically refreshed when APIs are called
- Historical context for trend analysis

## Usage Examples

### General Analytics Question
```
Question: "What's our current development activity?"
Context: All stored data from GitHub, Azure DevOps, Datadog, and Figma
Response: Cross-platform analysis of development trends
```

### Platform-Specific Question
```
Question: "How are our GitHub pull requests performing?"
Context: GitHub-specific data (PRs, repositories, analytics)
Response: Focused insights on GitHub development metrics
```

### Performance Analysis
```
Question: "Are there any performance issues?"
Context: Datadog metrics and system performance data
Response: Analysis of system health and performance trends
```

## Configuration

The context storage system works automatically once the application is running. No additional configuration is required. The system will:

1. Capture data whenever API endpoints are called
2. Store context in the `context_data/` directory
3. Provide rich context to the chatbot for intelligent responses
4. Maintain data freshness with automatic updates

## File Structure

```
context_data/
├── api_context.json          # Main context storage file
└── (additional context files as needed)
```

## Monitoring

Use the context status endpoint to monitor:
- Which data sources have been fetched
- Last fetch timestamps
- Summary statistics
- Overall system health

This ensures your chatbot always has the most relevant and up-to-date information to provide intelligent, data-driven insights.
