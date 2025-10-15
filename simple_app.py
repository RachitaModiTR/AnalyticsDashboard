from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Datadog Analytics Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row">
            <div class="col-12">
                <h1>🚀 Datadog Analytics Dashboard</h1>
                <div class="alert alert-info">
                    <h4>Setup Required</h4>
                    <p>To use this dashboard, you need to:</p>
                    <ol>
                        <li>Get your Datadog Client Token from: <strong>Integrations → APIs → Client Tokens</strong></li>
                        <li>Edit the <code>.env</code> file and replace <code>your_datadog_client_token_here</code> with your actual token</li>
                        <li>Restart the application</li>
                    </ol>
                    <p><strong>Current Status:</strong> Waiting for client token configuration</p>
                </div>
                <div class="alert alert-warning">
                    <h5>Note:</h5>
                    <p>This application is running on port <strong>5001</strong> to avoid conflicts with macOS AirPlay on port 5000.</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''')

if __name__ == '__main__':
    print("🚀 Simple test server starting...")
    print("📊 Open: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
