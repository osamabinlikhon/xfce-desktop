#!/usr/bin/env python3
"""
Xfce Desktop Environment for HuggingFace Spaces
Main Flask Application
"""

import os
import sys
import subprocess
import signal
import time
import threading
from flask import Flask, render_template, redirect, url_for, jsonify, send_from_directory

# Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'huggingface-spaces-secret-key')

# Environment variables with defaults
VNC_PASSWORD = os.environ.get('VNC_PASSWORD', 'huggingface')
RESOLUTION = os.environ.get('RESOLUTION', '1280x720')
VNC_PORT = os.environ.get('VNC_PORT', '5900')

# Global process references
xvfb_process = None
x11vnc_process = None
xfce_process = None
websockify_process = None


def log_message(message):
    """Log message with timestamp"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)


def run_command(command, wait=True, shell=False):
    """Execute a command and return the process"""
    try:
        if shell:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
        else:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preprocess=os.setsid
            )
        
        if wait:
            process.wait()
            return process.returncode == 0
        return process
    except Exception as e:
        log_message(f"Error running command: {e}")
        return False


def start_xvfb():
    """Start virtual framebuffer"""
    global xvfb_process
    log_message("Starting Xvfb...")
    
    # Kill any existing Xvfb processes
    run_command("pkill -9 Xvfb", wait=False, shell=True)
    time.sleep(1)
    
    # Start Xvfb on display :1
    xvfb_process = subprocess.Popen(
        ["Xvfb", ":1", "-screen", "0", f"{RESOLUTION}x24", "-ac", "+extension", "GLX"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    time.sleep(2)
    log_message(f"Xvfb started on display :1")
    return True


def start_xfce():
    """Start Xfce4 desktop environment"""
    global xfce_process
    log_message("Starting Xfce4...")
    
    # Set display environment variable
    env = os.environ.copy()
    env['DISPLAY'] = ':1'
    
    # Start Xfce4
    xfce_process = subprocess.Popen(
        ["startxfce4"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        preexec_fn=os.setsid
    )
    
    time.sleep(3)
    log_message("Xfce4 started")
    return True


def start_vnc_server():
    """Start x11vnc server"""
    global x11vnc_process
    log_message("Starting x11vnc server...")
    
    # Create VNC password file
    password_file = "/tmp/vnc_passwd"
    try:
        with open(password_file, 'w') as f:
            f.write(VNC_PASSWORD + "\n")
        os.chmod(password_file, 0o600)
    except Exception as e:
        log_message(f"Error creating password file: {e}")
    
    # Kill any existing x11vnc processes
    run_command("pkill -9 x11vnc", wait=False, shell=True)
    time.sleep(1)
    
    # Start x11vnc
    x11vnc_process = subprocess.Popen(
        [
            "x11vnc",
            "-display", ":1",
            "-localhost",
            "-forever",
            "-shared",
            "-rfbport", VNC_PORT,
            "-rfbauth", password_file,
            "-o", "/tmp/x11vnc.log",
            "-bg"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    time.sleep(2)
    log_message(f"x11vnc started on port {VNC_PORT}")
    return True


def start_websockify():
    """Start websockify for noVNC"""
    global websockify_process
    log_message("Starting websockify...")
    
    # Kill any existing websockify processes
    run_command("pkill -9 websockify", wait=False, shell=True)
    time.sleep(1)
    
    # Start websockify
    websockify_process = subprocess.Popen(
        ["websockify", "--web", "/home/user/novnc", "6080", "localhost:5900"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    time.sleep(2)
    log_message("websockify started on port 6080")
    return True


def start_desktop_environment():
    """Initialize the complete desktop environment"""
    log_message("Initializing desktop environment...")
    
    # Start components in order
    start_xvfb()
    start_xfce()
    start_vnc_server()
    start_websockify()
    
    log_message("Desktop environment ready!")
    return True


def check_desktop_status():
    """Check if desktop environment is running"""
    try:
        # Check if Xvfb is running
        result = subprocess.run(
            ["pgrep", "-f", "Xvfb"],
            capture_output=True,
            text=True
        )
        xvfb_running = result.returncode == 0
        
        # Check if x11vnc is running
        result = subprocess.run(
            ["pgrep", "-f", "x11vnc"],
            capture_output=True,
            text=True
        )
        vnc_running = result.returncode == 0
        
        # Check if websockify is running
        result = subprocess.run(
            ["pgrep", "-f", "websockify"],
            capture_output=True,
            text=True
        )
        ws_running = result.returncode == 0
        
        return {
            "xvfb": xvfb_running,
            "vnc": vnc_running,
            "websockify": ws_running,
            "ready": xvfb_running and vnc_running and ws_running
        }
    except Exception as e:
        log_message(f"Error checking status: {e}")
        return {"error": str(e)}


# Flask routes
@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html',
                           vnc_password=VNC_PASSWORD,
                           resolution=RESOLUTION)


@app.route('/desktop')
def desktop():
    """Desktop interface via noVNC"""
    return render_template('desktop.html')


@app.route('/terminal')
def terminal():
    """Terminal interface"""
    return render_template('terminal.html')


@app.route('/terminal.html')
def terminal_html():
    """Terminal HTML page with xterm.js"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terminal - HuggingFace Spaces</title>
    <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.min.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: #1a1a1a; 
            height: 100vh; 
            display: flex;
            flex-direction: column;
        }
        #terminal { 
            flex: 1; 
            padding: 10px; 
            background: #000;
        }
        .toolbar {
            background: linear-gradient(90deg, #1a1a2e, #16213e);
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #333;
        }
        .toolbar-title { color: #fff; font-size: 1.1em; }
        .toolbar-links a {
            color: #00d4ff;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 6px;
            background: rgba(0, 212, 255, 0.1);
        }
    </style>
</head>
<body>
    <div class="toolbar">
        <div class="toolbar-title">Terminal - HuggingFace Spaces</div>
        <div class="toolbar-links">
            <a href="/">Home</a>
            <a href="/desktop">Desktop</a>
        </div>
    </div>
    <div id="terminal"></div>
    <script>
        const term = new Terminal({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: 'Menlo, Monaco, "Courier New", monospace',
            theme: {
                background: '#1a1a1a',
                foreground: '#ffffff'
            }
        });
        const fitAddon = new FitAddon.FitAddon();
        term.loadAddon(fitAddon);
        term.open(document.getElementById('terminal'));
        fitAddon.fit();
        
        // Simple WebSocket terminal connection
        const ws = new WebSocket(`ws://${location.host}/ws`);
        ws.onopen = () => {
            term.write('\\r\\nConnected to terminal\\r\\n\\r\\n$ ');
        };
        ws.onmessage = (event) => {
            term.write(event.data);
        };
        ws.onclose = () => {
            term.write('\\r\\nConnection closed\\r\\n');
        };
        term.onData((data) => {
            ws.send(data);
        });
        
        window.addEventListener('resize', () => fitAddon.fit());
    </script>
</body>
</html>
'''


@app.route('/api/status')
def api_status():
    """API endpoint for desktop status"""
    status = check_desktop_status()
    return jsonify(status)


@app.route('/novnc/<path:filename>')
def novnc_files(filename):
    """Serve noVNC static files"""
    return send_from_directory('/home/user/novnc', filename)


@app.route('/vnc.html')
def vnc_client():
    """Redirect to noVNC client"""
    return render_template('vnc.html')


def create_template_files():
    """Create template directory and files"""
    os.makedirs('/workspace/app/templates', exist_ok=True)
    
    # Create index.html template
    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HuggingFace Spaces - Xfce Desktop</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        header {
            text-align: center;
            margin-bottom: 60px;
        }
        
        h1 {
            font-size: 3em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            color: #a0a0a0;
            font-size: 1.2em;
        }
        
        .status-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 40px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.1em;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #00ff88;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 40px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 40px 30px;
            text-align: center;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
            cursor: pointer;
            text-decoration: none;
            color: inherit;
        }
        
        .card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.1);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        
        .card-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        
        .card h2 {
            font-size: 1.5em;
            margin-bottom: 15px;
        }
        
        .card p {
            color: #a0a0a0;
            line-height: 1.6;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .info-item {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }
        
        .info-label {
            color: #a0a0a0;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        
        .info-value {
            font-size: 1.2em;
            font-weight: bold;
            color: #00d4ff;
        }
        
        footer {
            text-align: center;
            margin-top: 60px;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Xfce Desktop Environment</h1>
            <p class="subtitle">HuggingFace Spaces - Browser-based Linux Desktop</p>
        </header>
        
        <div class="status-card">
            <div class="status-indicator">
                <div class="status-dot"></div>
                <span>Desktop Environment Ready</span>
            </div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Resolution</div>
                    <div class="info-value">{{ resolution }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">VNC Port</div>
                    <div class="info-value">5900</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Web Interface</div>
                    <div class="info-value">Port 6080</div>
                </div>
            </div>
        </div>
        
        <div class="cards">
            <a href="/desktop" class="card">
                <div class="card-icon">🖥️</div>
                <h2>Launch Xfce Desktop</h2>
                <p>Access the full Xfce4 desktop environment in your browser. Includes file manager, terminal, and more.</p>
            </a>
            
            <a href="/terminal" class="card">
                <div class="card-icon">⌨️</div>
                <h2>Launch Terminal</h2>
                <p>Use the web-based terminal for command-line access to your Linux environment.</p>
            </a>
        </div>
        
        <footer>
            <p>Powered by HuggingFace Spaces | Xfce4 Desktop Environment</p>
        </footer>
    </div>
    
    <script>
        // Check desktop status periodically
        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                console.log('Desktop status:', data);
            } catch (error) {
                console.error('Status check failed:', error);
            }
        }
        
        // Check status every 30 seconds
        setInterval(checkStatus, 30000);
        checkStatus();
    </script>
</body>
</html>
'''
    
    with open('/workspace/app/templates/index.html', 'w') as f:
        f.write(index_html)
    
    # Create desktop.html template
    desktop_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Xfce Desktop - HuggingFace Spaces</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            overflow: hidden;
        }
        
        .toolbar {
            background: linear-gradient(90deg, #1a1a2e, #16213e);
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #333;
        }
        
        .toolbar-title {
            color: #fff;
            font-size: 1.1em;
        }
        
        .toolbar-links {
            display: flex;
            gap: 15px;
        }
        
        .toolbar-links a {
            color: #00d4ff;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 6px;
            background: rgba(0, 212, 255, 0.1);
            transition: all 0.3s;
        }
        
        .toolbar-links a:hover {
            background: rgba(0, 212, 255, 0.2);
        }
        
        .vnc-container {
            width: 100vw;
            height: calc(100vh - 50px);
            background: #000;
        }
        
        .vnc-container iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
        
        .loading {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #fff;
            font-size: 1.5em;
            text-align: center;
        }
        
        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-left-color: #00d4ff;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .controls {
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            z-index: 1000;
        }
        
        .control-btn {
            background: rgba(0, 212, 255, 0.9);
            color: #000;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        
        .control-btn:hover {
            background: #00d4ff;
            transform: scale(1.05);
        }
        
        .status-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(0, 0, 0, 0.8);
            color: #00ff88;
            padding: 8px 20px;
            font-size: 0.9em;
            display: flex;
            justify-content: space-between;
        }
    </style>
</head>
<body>
    <div class="toolbar">
        <div class="toolbar-title">🖥️ Xfce Desktop Environment</div>
        <div class="toolbar-links">
            <a href="/">← Back to Home</a>
            <a href="/terminal">Terminal</a>
        </div>
    </div>
    
    <div class="vnc-container">
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Connecting to desktop...</p>
        </div>
        <iframe id="vnc-frame" style="display: none;" src="/novnc/vnc.html?host=localhost&port=6080"></iframe>
    </div>
    
    <div class="controls">
        <button class="control-btn" onclick="toggleFullscreen()">⛶ Fullscreen</button>
        <button class="control-btn" onclick="reloadDesktop()">↻ Reload</button>
    </div>
    
    <div class="status-bar">
        <span id="connection-status">Connecting...</span>
        <span>Xfce4 Desktop | HuggingFace Spaces</span>
    </div>
    
    <script>
        const vncFrame = document.getElementById('vnc-frame');
        const loading = document.getElementById('loading');
        const status = document.getElementById('connection-status');
        
        // Show iframe when loaded
        vncFrame.onload = function() {
            loading.style.display = 'none';
            vncFrame.style.display = 'block';
            status.textContent = 'Connected';
        };
        
        // Handle connection errors
        vncFrame.onerror = function() {
            status.textContent = 'Connection failed';
            loading.innerHTML = '<p>Failed to connect. Please refresh.</p>';
        };
        
        function toggleFullscreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        }
        
        function reloadDesktop() {
            vncFrame.src = vncFrame.src;
            loading.style.display = 'block';
            vncFrame.style.display = 'none';
        }
        
        // Auto-reload on disconnect
        setTimeout(() => {
            if (loading.style.display !== 'none') {
                status.textContent = 'Retrying connection...';
            }
        }, 10000);
    </script>
</body>
</html>
'''
    
    with open('/workspace/app/templates/desktop.html', 'w') as f:
        f.write(desktop_html)
    
    # Create terminal.html template
    terminal_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terminal - HuggingFace Spaces</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .toolbar {
            background: linear-gradient(90deg, #1a1a2e, #16213e);
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #333;
        }
        
        .toolbar-title {
            color: #fff;
            font-size: 1.1em;
        }
        
        .toolbar-links a {
            color: #00d4ff;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 6px;
            background: rgba(0, 212, 255, 0.1);
            transition: all 0.3s;
        }
        
        .toolbar-links a:hover {
            background: rgba(0, 212, 255, 0.2);
        }
        
        .terminal-container {
            flex: 1;
            background: #000;
            padding: 20px;
            overflow: auto;
        }
        
        .terminal-container iframe {
            width: 100%;
            height: 100%;
            border: none;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="toolbar">
        <div class="toolbar-title">⌨️ Web Terminal</div>
        <div class="toolbar-links">
            <a href="/">← Back to Home</a>
            <a href="/desktop">Desktop</a>
        </div>
    </div>
    
    <div class="terminal-container">
        <iframe src="/terminal.html"></iframe>
    </div>
</body>
</html>
'''
    
    with open('/workspace/app/templates/terminal.html', 'w') as f:
        f.write(terminal_html)


if __name__ == '__main__':
    log_message("Starting Xfce Desktop Environment for HuggingFace Spaces...")
    
    # Create template files
    create_template_files()
    
    # Start desktop environment in background thread
    desktop_thread = threading.Thread(target=start_desktop_environment, daemon=True)
    desktop_thread.start()
    
    # Wait a bit for desktop to initialize
    time.sleep(5)
    
    # Run Flask app
    log_message("Starting Flask web server...")
    app.run(host='0.0.0.0', port=7860, debug=False, threaded=True)
