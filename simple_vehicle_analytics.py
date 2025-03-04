from flask import Flask, render_template, jsonify
import os
import json
from datetime import datetime, timedelta
from collections import Counter

app = Flask(__name__, template_folder='app/templates')
app.config['SECRET_KEY'] = 'vehicle-analytics-secret-key'

# Sample data for demonstration
vehicle_interests = [
    {
        "id": 1,
        "lead_id": 1,
        "make": "Toyota",
        "model": "Camry",
        "year": 2022,
        "trim": "XLE",
        "body_style": "Sedan",
        "new_or_used": "new",
        "created_at": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    },
    {
        "id": 2,
        "lead_id": 2,
        "make": "Honda",
        "model": "Accord",
        "year": 2021,
        "trim": "Sport",
        "body_style": "Sedan",
        "new_or_used": "new",
        "created_at": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    },
    {
        "id": 3,
        "lead_id": 3,
        "make": "Ford",
        "model": "F-150",
        "year": 2023,
        "trim": "Lariat",
        "body_style": "Truck",
        "new_or_used": "new",
        "created_at": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    },
    {
        "id": 4,
        "lead_id": 4,
        "make": "Toyota",
        "model": "RAV4",
        "year": 2020,
        "trim": "Limited",
        "body_style": "SUV",
        "new_or_used": "used",
        "created_at": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    },
    {
        "id": 5,
        "lead_id": 5,
        "make": "Chevrolet",
        "model": "Silverado",
        "year": 2022,
        "trim": "LT",
        "body_style": "Truck",
        "new_or_used": "new",
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }
]

@app.route('/')
def index():
    return render_template('analytics/index.html', title='Vehicle Interest Analytics')

@app.route('/analytics')
def analytics():
    # Count vehicle interests by make
    make_counts = Counter([vi['make'] for vi in vehicle_interests])
    make_data = [{'name': make, 'count': count} for make, count in make_counts.items()]
    
    # Count vehicle interests by body style
    body_style_counts = Counter([vi['body_style'] for vi in vehicle_interests])
    body_style_data = [{'name': style, 'count': count} for style, count in body_style_counts.items()]
    
    # Count new vs used
    new_used_counts = Counter([vi['new_or_used'] for vi in vehicle_interests])
    new_used_data = [{'name': status, 'count': count} for status, count in new_used_counts.items()]
    
    return render_template('analytics/dashboard.html', 
                           title='Vehicle Interest Analytics',
                           make_data=make_data,
                           body_style_data=body_style_data,
                           new_used_data=new_used_data,
                           vehicle_interests=vehicle_interests)

@app.route('/api/analytics/data')
def analytics_data():
    return jsonify(vehicle_interests)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('app/templates/analytics', exist_ok=True)
    
    # Create a simple dashboard template
    dashboard_html = """
    {% extends 'base.html' %}
    
    {% block content %}
    <div class="container mt-4">
        <h1>Vehicle Interest Analytics Dashboard</h1>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Interest by Make</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="makeChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Interest by Body Style</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="bodyStyleChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>New vs Used</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="newUsedChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Recent Vehicle Interests</h5>
                    </div>
                    <div class="card-body">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Make</th>
                                    <th>Model</th>
                                    <th>Year</th>
                                    <th>Body Style</th>
                                    <th>New/Used</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for vi in vehicle_interests %}
                                <tr>
                                    <td>{{ vi.make }}</td>
                                    <td>{{ vi.model }}</td>
                                    <td>{{ vi.year }}</td>
                                    <td>{{ vi.body_style }}</td>
                                    <td>{{ vi.new_or_used }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Make Chart
        const makeData = {{ make_data|tojson }};
        const makeCtx = document.getElementById('makeChart').getContext('2d');
        const makeChart = new Chart(makeCtx, {
            type: 'bar',
            data: {
                labels: makeData.map(item => item.name),
                datasets: [{
                    label: 'Vehicle Interests by Make',
                    data: makeData.map(item => item.count),
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.5)',
                        'rgba(54, 162, 235, 0.5)',
                        'rgba(255, 206, 86, 0.5)',
                        'rgba(75, 192, 192, 0.5)',
                        'rgba(153, 102, 255, 0.5)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
        
        // Body Style Chart
        const bodyStyleData = {{ body_style_data|tojson }};
        const bodyStyleCtx = document.getElementById('bodyStyleChart').getContext('2d');
        const bodyStyleChart = new Chart(bodyStyleCtx, {
            type: 'pie',
            data: {
                labels: bodyStyleData.map(item => item.name),
                datasets: [{
                    label: 'Vehicle Interests by Body Style',
                    data: bodyStyleData.map(item => item.count),
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.5)',
                        'rgba(54, 162, 235, 0.5)',
                        'rgba(255, 206, 86, 0.5)',
                        'rgba(75, 192, 192, 0.5)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)'
                    ],
                    borderWidth: 1
                }]
            }
        });
        
        // New vs Used Chart
        const newUsedData = {{ new_used_data|tojson }};
        const newUsedCtx = document.getElementById('newUsedChart').getContext('2d');
        const newUsedChart = new Chart(newUsedCtx, {
            type: 'doughnut',
            data: {
                labels: newUsedData.map(item => item.name),
                datasets: [{
                    label: 'New vs Used',
                    data: newUsedData.map(item => item.count),
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.5)',
                        'rgba(255, 99, 132, 0.5)'
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 99, 132, 1)'
                    ],
                    borderWidth: 1
                }]
            }
        });
    </script>
    {% endblock %}
    """
    
    # Create a simple index template
    index_html = """
    {% extends 'base.html' %}
    
    {% block content %}
    <div class="container mt-4">
        <div class="jumbotron">
            <h1 class="display-4">Vehicle Interest Analytics</h1>
            <p class="lead">Track and analyze vehicle interests to make data-driven decisions.</p>
            <hr class="my-4">
            <p>View comprehensive analytics about vehicle interests, trends, and patterns.</p>
            <a class="btn btn-primary btn-lg" href="{{ url_for('analytics') }}" role="button">View Analytics</a>
        </div>
    </div>
    {% endblock %}
    """
    
    # Create a simple base template
    base_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }}</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="{{ url_for('index') }}">BDC Module</a>
                <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('index') }}">Home</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('analytics') }}">Analytics</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        
        {% block content %}{% endblock %}
        
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.3/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    </body>
    </html>
    """
    
    # Write templates to files
    with open('app/templates/base.html', 'w') as f:
        f.write(base_html)
    
    with open('app/templates/analytics/index.html', 'w') as f:
        f.write(index_html)
    
    with open('app/templates/analytics/dashboard.html', 'w') as f:
        f.write(dashboard_html)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
