"""
Real-time toxicity detection and WebSocket endpoints for live monitoring
"""
from flask import Blueprint, request, jsonify, Response
from flask_cors import CORS
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Callable
import queue

# Import toxicity detection
try:
    from detoxify import Detoxify
    DETOXIFY_AVAILABLE = True
except ImportError:
    DETOXIFY_AVAILABLE = False

bp = Blueprint('realtime', __name__)
CORS(bp)

# ── Real-time Client Management ────────────────────────────────────────────────
class RealtimeMonitor:
    """Manages real-time monitoring sessions and client connections"""
    
    def __init__(self):
        self.clients: Dict[str, queue.Queue] = {}
        self.sessions: Dict[str, Dict] = {}
        self.toxicity_detector = None
        if DETOXIFY_AVAILABLE:
            self.toxicity_detector = Detoxify("multilingual")
    
    def register_client(self, session_id: str) -> queue.Queue:
        """Register a new real-time client"""
        self.clients[session_id] = queue.Queue()
        self.sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "alerts": []
        }
        return self.clients[session_id]
    
    def unregister_client(self, session_id: str):
        """Unregister a real-time client"""
        if session_id in self.clients:
            del self.clients[session_id]
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def detect_toxicity(self, text: str) -> Dict:
        """Analyze text for toxic content"""
        if not self.toxicity_detector:
            return {"error": "Detoxify not available"}
        
        try:
            results = self.toxicity_detector.predict(text)
            return {
                "text": text,
                "timestamp": datetime.now().isoformat(),
                "scores": results,
                "is_toxic": max(results.values()) > 0.5,
                "max_toxicity": max(results.values())
            }
        except Exception as e:
            return {"error": str(e)}
    
    def broadcast_alert(self, session_id: str, alert_data: Dict):
        """Send alert to specific client"""
        if session_id in self.clients:
            self.clients[session_id].put(alert_data)
            if session_id in self.sessions:
                self.sessions[session_id]["message_count"] += 1
                self.sessions[session_id]["alerts"].append(alert_data)

monitor = RealtimeMonitor()

# ── Real-time API Endpoints ────────────────────────────────────────────────────

@bp.route('/realtime/analyze', methods=['POST'])
def analyze_realtime():
    """
    Analyze content in real-time for toxic patterns
    POST /api/v1/realtime/analyze
    """
    data = request.get_json()
    content = data.get('content', '')
    session_id = data.get('session_id', '')
    
    if not content:
        return jsonify({'error': 'Content required'}), 400
    
    analysis = monitor.detect_toxicity(content)
    
    if session_id:
        analysis['session_id'] = session_id
        monitor.broadcast_alert(session_id, analysis)
    
    return jsonify(analysis), 200

@bp.route('/realtime/stream/<session_id>')
def stream_realtime(session_id):
    """
    Server-Sent Events (SSE) endpoint for real-time monitoring
    GET /api/v1/realtime/stream/{session_id}
    """
    client_queue = monitor.register_client(session_id)
    
    def event_stream():
        try:
            while True:
                try:
                    alert = client_queue.get(timeout=30)  # 30 second timeout
                    yield f'data: {json.dumps(alert)}\n\n'
                except queue.Empty:
                    # Send heartbeat
                    yield f'data: {json.dumps({"type": "heartbeat", "timestamp": datetime.now().isoformat()})}\n\n'
        except GeneratorExit:
            monitor.unregister_client(session_id)
    
    return Response(event_stream(), mimetype='text/event-stream')

@bp.route('/realtime/status/<session_id>', methods=['GET'])
def get_session_status(session_id):
    """Get status of a real-time monitoring session"""
    if session_id not in monitor.sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = monitor.sessions[session_id]
    return jsonify({
        'session_id': session_id,
        'created_at': session['created_at'],
        'message_count': session['message_count'],
        'recent_alerts': session['alerts'][-10:],  # Last 10 alerts
        'is_active': session_id in monitor.clients
    }), 200

@bp.route('/realtime/screenshot-monitor', methods=['POST'])
def process_screenshot():
    """
    Process screenshots submitted in real-time
    POST /api/v1/realtime/screenshot-monitor
    """
    if 'screenshot' not in request.files:
        return jsonify({'error': 'No screenshot provided'}), 400
    
    screenshot = request.files['screenshot']
    session_id = request.form.get('session_id', '')
    platform = request.form.get('platform', 'unknown')
    url = request.form.get('url', '')
    
    try:
        # Save screenshot temporarily
        import os
        from PIL import Image
        import io
        
        img = Image.open(screenshot.stream)
        filename = f"screenshot_{int(time.time())}.png"
        filepath = os.path.join('/tmp', filename)
        img.save(filepath)
        
        alert_data = {
            'type': 'screenshot_captured',
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'url': url,
            'filename': filename,
            'session_id': session_id
        }
        
        if session_id:
            monitor.broadcast_alert(session_id, alert_data)
        
        return jsonify({
            'message': 'Screenshot processed',
            'filename': filename,
            'alert': alert_data
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/realtime/highlight-toxic', methods=['POST'])
def highlight_toxic_content():
    """
    Return toxic content highlights for browser extension
    POST /api/v1/realtime/highlight-toxic
    """
    data = request.get_json()
    page_content = data.get('page_content', '')
    
    if not page_content:
        return jsonify({'error': 'Page content required'}), 400
    
    # Extract text nodes and analyze
    toxic_items = []
    sentences = page_content.split('.')
    
    for idx, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if len(sentence) > 10:
            analysis = monitor.detect_toxicity(sentence)
            if analysis.get('is_toxic'):
                toxic_items.append({
                    'text': sentence,
                    'index': idx,
                    'scores': analysis.get('scores', {}),
                    'toxicity_level': analysis.get('max_toxicity', 0)
                })
    
    return jsonify({
        'total_sentences': len(sentences),
        'toxic_count': len(toxic_items),
        'highlights': toxic_items,
        'timestamp': datetime.now().isoformat()
    }), 200
