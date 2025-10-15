# Datadog Analytics Dashboard (Client Token Version)

A Python Flask application that connects to your Datadog account using client tokens to create custom analytics and dashboards.

## Features

- 🔗 **Client Token Authentication**: Connect to your Datadog account using client tokens (no API keys required)
- 📊 **Interactive Dashboards**: Create custom dashboards with real-time metrics
- 📈 **Multiple Chart Types**: Line charts, bar charts, and more
- ⏰ **Flexible Time Ranges**: View data from 1 hour to 7 days
- 🎯 **Metric Selection**: Choose from available Datadog metrics or add custom ones
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🔄 **Auto-refresh**: Automatic dashboard updates every 5 minutes
- ➕ **Custom Metrics**: Add your own metric names to the dashboard

## Prerequisites

- Python 3.7 or higher
- Datadog account with client token access
- pip (Python package installer)

## Installation

1. **Clone or download this project**
   ```bash
   git clone <your-repo-url>
   cd datadog-analytics-app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your Datadog client token:
   ```
   DD_CLIENT_TOKEN=your_datadog_client_token_here
   DD_SITE=datadoghq.com
   SECRET_KEY=your_secret_key_here
   ```

## Getting Datadog Client Token

1. Log in to your Datadog account
2. Go to **Integrations** → **APIs**
3. Create a new **Client Token**:
   - Client tokens are used for browser-based applications
   - They have limited permissions compared to API keys
   - They're perfect for read-only operations like viewing metrics
4. Copy the client token to your `.env` file

## Usage

1. **Start the application**
   ```bash
   python run.py
   ```

2. **Open your browser**
   Navigate to `http://localhost:5000`

3. **Configure your dashboard**
   - Select metrics from the sidebar
   - Add custom metrics using the "Custom Metric" field
   - Choose time range (1 hour to 7 days)
   - Select chart type (line or bar)
   - Click "Update Dashboard"

## Available Metrics

The application supports common Datadog metrics including:
- `system.cpu.user` - CPU usage
- `system.mem.used` - Memory usage
- `system.disk.used` - Disk usage
- `system.load.1` - System load
- `aws.ec2.cpuutilization` - AWS EC2 CPU utilization
- `docker.cpu.usage` - Docker container CPU usage
- `docker.mem.usage` - Docker container memory usage

### Adding Custom Metrics

You can add any metric name that exists in your Datadog account:
1. Enter the metric name in the "Custom Metric" field
2. Click "Add Metric"
3. The metric will be added to your dashboard

## API Endpoints

- `GET /` - Main dashboard page
- `GET /api/metrics` - List available metrics
- `GET /api/metrics/<metric_name>` - Get specific metric data
- `GET /api/analytics` - Get analytics summary
- `GET /api/charts/<metric_name>` - Get chart data for a metric
- `GET /api/dashboard/<dashboard_id>` - Get dashboard data (if dashboard ID is known)

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DD_CLIENT_TOKEN` | Datadog client token | - | ✅ **Yes** |
| `DD_SITE` | Datadog site (datadoghq.com, datadoghq.eu, etc.) | datadoghq.com | No |
| `DD_APPLICATION_ID` | Datadog application ID (for RUM features) | - | ❌ **No** |
| `SECRET_KEY` | Flask secret key | dev-secret-key | No |
| `FLASK_ENV` | Flask environment | development | No |
| `FLASK_DEBUG` | Enable debug mode | True | No |

### Getting DD_APPLICATION_ID (Optional)

The `DD_APPLICATION_ID` is **only needed if you want RUM (Real User Monitoring) features**. For basic analytics dashboards, you don't need it.

**To get it (if needed):**
1. Go to **UX Monitoring** → **RUM Applications**
2. Create a new **Browser Application**
3. Copy the **Application ID** from the setup code

**For this analytics dashboard, you can skip this step entirely.**

### Customization

You can customize the application by:
- Adding new metrics in the HTML template
- Modifying the dashboard layout in `templates/index.html`
- Adding new chart types in the chart generation code
- Extending the analytics calculations

## Troubleshooting

### Common Issues

1. **"Failed to fetch metric data"**
   - Check your client token is correct
   - Verify the metric name exists in your Datadog account
   - Ensure your Datadog account has data for the selected time range
   - Client tokens have limited permissions - some metrics might not be accessible

2. **"No data available for chart"**
   - The metric might not have data for the selected time range
   - Try selecting a different time range
   - Check if the metric is actively being collected
   - Verify the metric name is correct (case-sensitive)

3. **Connection errors**
   - Verify your internet connection
   - Check if your Datadog site URL is correct
   - Ensure your client token is valid and not expired

4. **Authentication errors**
   - Client tokens are different from API keys
   - Make sure you're using a client token, not an API key
   - Client tokens have limited scope - they can only read certain data

### Debug Mode

Enable debug mode by setting `FLASK_DEBUG=True` in your `.env` file to see detailed error messages.

## Client Token vs API Key

| Feature | Client Token | API Key |
|---------|--------------|---------|
| **Authentication** | Browser-based | Server-based |
| **Permissions** | Limited (read-only) | Full access |
| **Use Case** | Frontend applications | Backend applications |
| **Security** | Less sensitive | More sensitive |
| **Access** | Public metrics | All metrics and operations |

## Production Deployment

For production deployment:

1. **Set production environment variables**
   ```
   FLASK_ENV=production
   FLASK_DEBUG=False
   SECRET_KEY=your-secure-secret-key
   ```

2. **Use a production WSGI server**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **Set up reverse proxy** (nginx, Apache, etc.)

4. **Enable HTTPS** for secure connections

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review Datadog client token documentation
- Open an issue in the project repository

## Changelog

### Version 2.0 (Client Token Support)
- ✅ Added client token authentication
- ✅ Removed dependency on API keys
- ✅ Added custom metric input
- ✅ Improved error handling
- ✅ Updated UI to show authentication method
- ✅ Made DD_APPLICATION_ID optional
