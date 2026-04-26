"""
Analytics API Endpoints
Provides network graphs, heatmaps, predictive models, and word clouds
"""
from flask import Blueprint, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from typing import List, Dict
import json

# Import analytics services
from src.services.analytics import (
    NetworkGraphBuilder,
    HeatmapCalendarBuilder,
    PredictiveEscalationModel,
    WordCloudAnalyzer,
    TimeOfDayAnalyzer
)

bp = Blueprint('analytics', __name__)
CORS(bp)

# Initialize services
escalation_model = PredictiveEscalationModel()
word_cloud = WordCloudAnalyzer()
time_analyzer = TimeOfDayAnalyzer()

# ── Analytics API Endpoints ────────────────────────────────────────────────────

@bp.route('/analytics/network-graph/<user_id>', methods=['POST'])
def get_network_graph(user_id):
    """
    Generate network graph showing connections between abusers, platforms, and victims
    POST /api/v1/analytics/network-graph/{user_id}
    Body: { evidence_data: [...] }
    """
    try:
        data = request.get_json()
        evidence_list = data.get('evidence_data', [])
        
        # Build network graph
        builder = NetworkGraphBuilder.from_evidence_list(evidence_list)
        graph = builder.get_graph_json()
        
        return jsonify({
            'user_id': user_id,
            'network_graph': graph,
            'generated_at': datetime.now().isoformat(),
            'description': 'Network visualization showing connections between abusers, platforms, and victims'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/analytics/heatmap-calendar/<user_id>', methods=['POST'])
def get_heatmap_calendar(user_id):
    """
    Generate GitHub-style heatmap calendar of incident frequency
    POST /api/v1/analytics/heatmap-calendar/{user_id}
    Body: { incidents: [{ date: YYYY-MM-DD, count: N }, ...] }
    """
    try:
        data = request.get_json()
        incidents = data.get('incidents', [])
        days_back = data.get('days_back', 365)
        
        # Build heatmap
        heatmap = HeatmapCalendarBuilder(days_back=days_back)
        
        for incident in incidents:
            date_str = incident.get('date')
            count = incident.get('count', 1)
            if date_str:
                heatmap.add_incident(date_str, count)
        
        calendar = heatmap.get_calendar_json()
        
        return jsonify({
            'user_id': user_id,
            'heatmap_calendar': calendar,
            'generated_at': datetime.now().isoformat(),
            'description': 'Heatmap showing incident frequency over time'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/analytics/predictive-escalation/<user_id>', methods=['POST'])
def get_predictive_escalation(user_id):
    """
    Predict escalation risk for abusers based on historical data
    POST /api/v1/analytics/predictive-escalation/{user_id}
    Body: { abuser_profiles: [{ abuser_id, incident_frequency, severity_trend, days_since_last_incident }, ...] }
    """
    try:
        data = request.get_json()
        abuser_profiles = data.get('abuser_profiles', [])
        
        # Calculate risk scores
        predictions = escalation_model.predict_multiple(abuser_profiles)
        
        return jsonify({
            'user_id': user_id,
            'predictions': predictions,
            'high_risk_count': len([p for p in predictions if p['risk_level'] in ['HIGH', 'CRITICAL']]),
            'critical_count': len([p for p in predictions if p['risk_level'] == 'CRITICAL']),
            'generated_at': datetime.now().isoformat(),
            'model_version': 'v1'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/analytics/single-risk-score', methods=['POST'])
def get_single_risk_score():
    """
    Calculate risk score for a single abuser profile
    POST /api/v1/analytics/single-risk-score
    Body: { incident_frequency, severity_trend, days_since_last_incident, avg_message_intensity }
    """
    try:
        profile = request.get_json()
        
        score = escalation_model.calculate_risk_score(profile)
        risk_level = escalation_model._get_risk_level(score)
        recommendation = escalation_model._get_recommendation(risk_level)
        
        return jsonify({
            'risk_score': round(score, 3),
            'risk_level': risk_level,
            'recommendation': recommendation,
            'factors': {
                'frequency': profile.get('incident_frequency', 0),
                'trend': profile.get('severity_trend', 'stable'),
                'recency': profile.get('days_since_last_incident', 0),
                'intensity': profile.get('avg_message_intensity', 0)
            },
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/analytics/word-cloud/<user_id>', methods=['POST'])
def get_word_cloud(user_id):
    """
    Generate word cloud from toxic content
    POST /api/v1/analytics/word-cloud/{user_id}
    Body: { content_items: [{ text, toxicity_score }, ...], limit: 100 }
    """
    try:
        data = request.get_json()
        content_items = data.get('content_items', [])
        limit = data.get('limit', 100)
        
        # Create fresh analyzer for this user
        analyzer = WordCloudAnalyzer()
        
        for item in content_items:
            text = item.get('text', '')
            toxicity = item.get('toxicity_score', 0.0)
            analyzer.process_text(text, toxicity)
        
        cloud_data = analyzer.get_word_cloud_data(limit=limit)
        
        return jsonify({
            'user_id': user_id,
            'word_cloud': cloud_data,
            'total_words': len(analyzer.word_frequency),
            'toxic_words': len(analyzer.toxic_words),
            'generated_at': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/analytics/time-pattern-analysis/<user_id>', methods=['POST'])
def get_time_pattern_analysis(user_id):
    """
    Analyze incident patterns by time and day
    POST /api/v1/analytics/time-pattern-analysis/{user_id}
    Body: { incidents: [{ timestamp: ISO8601, severity: 0-1 }, ...] }
    """
    try:
        data = request.get_json()
        incidents = data.get('incidents', [])
        
        # Create analyzer
        analyzer = TimeOfDayAnalyzer()
        
        for incident in incidents:
            timestamp_str = incident.get('timestamp')
            severity = incident.get('severity', 0.5)
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                analyzer.add_incident(timestamp, severity)
            except:
                continue
        
        analysis = analyzer.get_combined_analysis()
        
        return jsonify({
            'user_id': user_id,
            'analysis': analysis,
            'insights': {
                'peak_hour_range': f"{analysis['hourly']['peak_hours'][0][0]:02d}:00-{analysis['hourly']['peak_hours'][0][0]:02d}:59" if analysis['hourly']['peak_hours'] else 'N/A',
                'peak_day': analysis['daily']['peak_days'][0][0] if analysis['daily']['peak_days'] else 'N/A',
                'weekend_incidents': analysis['daily']['weekend_incidents'],
                'weekday_incidents': analysis['daily']['weekday_incidents']
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/analytics/comprehensive-dashboard/<user_id>', methods=['POST'])
def get_comprehensive_dashboard(user_id):
    """
    Get all analytics in one comprehensive dashboard
    POST /api/v1/analytics/comprehensive-dashboard/{user_id}
    Body: { evidence_data, incidents, abuser_profiles, content_items }
    """
    try:
        data = request.get_json()
        
        # Collect all analytics
        dashboard = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'sections': {}
        }
        
        # Network graph
        if 'evidence_data' in data:
            builder = NetworkGraphBuilder.from_evidence_list(data['evidence_data'])
            dashboard['sections']['network_graph'] = builder.get_graph_json()
        
        # Heatmap
        if 'incidents' in data:
            heatmap = HeatmapCalendarBuilder()
            for incident in data['incidents']:
                if 'date' in incident:
                    heatmap.add_incident(incident['date'], incident.get('count', 1))
            dashboard['sections']['heatmap'] = heatmap.get_calendar_json()
        
        # Escalation predictions
        if 'abuser_profiles' in data:
            predictions = escalation_model.predict_multiple(data['abuser_profiles'])
            dashboard['sections']['escalation_predictions'] = {
                'predictions': predictions,
                'summary': {
                    'total': len(predictions),
                    'critical': len([p for p in predictions if p['risk_level'] == 'CRITICAL']),
                    'high': len([p for p in predictions if p['risk_level'] == 'HIGH']),
                    'medium': len([p for p in predictions if p['risk_level'] == 'MEDIUM']),
                    'low': len([p for p in predictions if p['risk_level'] == 'LOW'])
                }
            }
        
        # Word cloud
        if 'content_items' in data:
            analyzer = WordCloudAnalyzer()
            for item in data['content_items']:
                analyzer.process_text(item.get('text', ''), item.get('toxicity_score', 0.0))
            dashboard['sections']['word_cloud'] = analyzer.get_word_cloud_data(limit=100)
        
        # Time analysis
        if 'incidents' in data:
            analyzer = TimeOfDayAnalyzer()
            for incident in data['incidents']:
                if 'timestamp' in incident:
                    try:
                        ts = datetime.fromisoformat(incident['timestamp'].replace('Z', '+00:00'))
                        analyzer.add_incident(ts, incident.get('severity', 0.5))
                    except:
                        pass
            dashboard['sections']['time_analysis'] = analyzer.get_combined_analysis()
        
        return jsonify(dashboard), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/analytics/export/<user_id>/<format>', methods=['POST'])
def export_analytics(user_id, format):
    """
    Export analytics in different formats (JSON, CSV)
    POST /api/v1/analytics/export/{user_id}/{format}
    """
    try:
        data = request.get_json()
        
        if format == 'json':
            return jsonify({
                'user_id': user_id,
                'format': 'json',
                'data': data,
                'exported_at': datetime.now().isoformat()
            }), 200
        
        elif format == 'csv':
            # TODO: Implement CSV export
            return jsonify({'error': 'CSV export not yet implemented'}), 501
        
        else:
            return jsonify({'error': 'Unsupported format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
