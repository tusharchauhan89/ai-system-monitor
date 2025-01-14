import psutil
import time
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template
import plotly.express as px
from sklearn.ensemble import IsolationForest
import numpy as np
import requests

# Set thresholds for alerts
CPU_THRESHOLD = 80
MEMORY_THRESHOLD = 75
DISK_THRESHOLD = 85

# Set up logging
logging.basicConfig(filename='system_metrics.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Email function to send alerts
def send_email_alert(message):
    sender_email = "your_email@gmail.com"  # Your Gmail address
    receiver_email = "recipient_email@example.com"  # Recipient's email address
    password = "your_generated_app_password"  # Your Gmail App password

    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = 'System Alert'

    # Add the message body
    msg.attach(MIMEText(message, 'plain'))

    try:
        # Connect to Gmail's SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
            print("Email sent successfully")
    except Exception as e:
        print(f"Error: {e}")

# Slack notification function
def send_slack_alert(message):
    webhook_url = 'your_slack_webhook_url'  # Replace with your actual Slack webhook URL
    slack_data = {'text': message}
    response = requests.post(webhook_url, json=slack_data)
    if response.status_code != 200:
        print(f"Error sending Slack message: {response.status_code}")

# Function to get system metrics
def get_system_metrics():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return cpu_usage, memory.percent, disk.percent

# Function to monitor the system
def monitor_system():
    # Sample data for anomaly detection (normally this would be collected over time)
    data = np.array([[50], [60], [70], [80], [90], [100], [110]])

    # Train the anomaly detection model
    model = IsolationForest(contamination=0.1)
    model.fit(data)

    while True:
        cpu_usage, memory_usage, disk_usage = get_system_metrics()

        # Log system metrics
        logging.info(f"CPU Usage: {cpu_usage}% | Memory Usage: {memory_usage}% | Disk Usage: {disk_usage}%")

        # Anomaly detection for CPU usage
        new_data = np.array([[cpu_usage]])
        prediction = model.predict(new_data)
        if prediction == -1:
            send_email_alert(f"Anomaly detected in CPU usage: {cpu_usage}%")
            send_slack_alert(f"Anomaly detected in CPU usage: {cpu_usage}%")

        # Send email alerts if thresholds are exceeded
        if cpu_usage > CPU_THRESHOLD:
            send_email_alert(f"Alert: CPU usage is {cpu_usage}% (Exceeds threshold of {CPU_THRESHOLD}%)")
            send_slack_alert(f"Alert: CPU usage is {cpu_usage}% (Exceeds threshold of {CPU_THRESHOLD}%)")
        if memory_usage > MEMORY_THRESHOLD:
            send_email_alert(f"Alert: Memory usage is {memory_usage}% (Exceeds threshold of {MEMORY_THRESHOLD}%)")
            send_slack_alert(f"Alert: Memory usage is {memory_usage}% (Exceeds threshold of {MEMORY_THRESHOLD}%)")
        if disk_usage > DISK_THRESHOLD:
            send_email_alert(f"Alert: Disk usage is {disk_usage}% (Exceeds threshold of {DISK_THRESHOLD}%)")
            send_slack_alert(f"Alert: Disk usage is {disk_usage}% (Exceeds threshold of {DISK_THRESHOLD}%)")

        # Sleep for 5 seconds before the next check
        time.sleep(5)

# Flask app for real-time dashboard
app = Flask(__name__)

@app.route('/')
def dashboard():
    cpu_usage, memory_usage, disk_usage = get_system_metrics()

    # Create a Plotly bar chart
    fig = px.bar(x=['CPU Usage', 'Memory Usage', 'Disk Usage'], y=[cpu_usage, memory_usage, disk_usage], 
                 labels={'x': 'Metric', 'y': 'Usage (%)'})
    fig.update_layout(title='System Resource Usage')

    # Convert Plotly figure to HTML
    graph_html = fig.to_html(full_html=False)

    return render_template('dashboard.html', graph_html=graph_html)

# Main entry point for the Flask app
if __name__ == "__main__":
    # Run the system monitor in a separate thread or process
    import threading
    monitor_thread = threading.Thread(target=monitor_system)
    monitor_thread.daemon = True
    monitor_thread.start()

    # Start Flask web server for dashboard
    app.run(debug=True, use_reloader=False)  # use_reloader=False to prevent the Flask app from restarting the thread

