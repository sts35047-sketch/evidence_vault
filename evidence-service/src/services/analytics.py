"""
Advanced Analytics Services
- Network graph visualization
- Heatmap calendar data
- Predictive escalation modeling
- Word cloud analysis
- Time-of-day pattern analysis
"""
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import json
import math

class NetworkGraphBuilder:
    """Build network graph of connections between abusers, platforms, and victims"""
    
    def __init__(self):
        self.nodes = []
        self.links = []
        self.node_index = {}
    
    def add_node(self, node_id: str, node_type: str, label: str, 
                metadata: Dict = None) -> int:
        """Add a node to the network"""
        if node_id in self.node_index:
            return self.node_index[node_id]
        
        idx = len(self.nodes)
        self.node_index[node_id] = idx
        
        node = {
            'id': node_id,
            'type': node_type,  # 'abuser', 'platform', 'victim'
            'label': label,
            'index': idx,
            'metadata': metadata or {}
        }
        self.nodes.append(node)
        return idx
    
    def add_link(self, source_id: str, target_id: str, connection_type: str,
                weight: int = 1, metadata: Dict = None):
        """Add a connection between two nodes"""
        source_idx = self.node_index.get(source_id)
        target_idx = self.node_index.get(target_id)
        
        if source_idx is None or target_idx is None:
            return
        
        link = {
            'source': source_idx,
            'target': target_idx,
            'type': connection_type,
            'weight': weight,
            'metadata': metadata or {}
        }
        self.links.append(link)
    
    def get_graph_json(self) -> Dict:
        """Return D3.js compatible network graph"""
        return {
            'nodes': self.nodes,
            'links': self.links,
            'stats': {
                'node_count': len(self.nodes),
                'link_count': len(self.links),
                'abuser_count': len([n for n in self.nodes if n['type'] == 'abuser']),
                'victim_count': len([n for n in self.nodes if n['type'] == 'victim']),
                'platform_count': len([n for n in self.nodes if n['type'] == 'platform'])
            }
        }
    
    @staticmethod
    def from_evidence_list(evidence_list: List[Dict]) -> 'NetworkGraphBuilder':
        """Build graph from evidence data"""
        builder = NetworkGraphBuilder()
        
        for evidence in evidence_list:
            # Add abuser node
            abuser_id = evidence.get('abuser_id', 'unknown_abuser')
            builder.add_node(abuser_id, 'abuser', 
                           evidence.get('abuser_name', abuser_id),
                           {'incidents': evidence.get('count', 1)})
            
            # Add victim node
            victim_id = evidence.get('victim_id', 'unknown_victim')
            builder.add_node(victim_id, 'victim',
                           evidence.get('victim_name', victim_id),
                           {'reports': evidence.get('report_count', 1)})
            
            # Add platform node
            platform = evidence.get('platform', 'unknown_platform')
            builder.add_node(platform, 'platform', platform)
            
            # Add connections
            builder.add_link(abuser_id, platform, 'abuses_on',
                           weight=evidence.get('count', 1))
            builder.add_link(platform, victim_id, 'targets',
                           weight=evidence.get('count', 1))
            builder.add_link(abuser_id, victim_id, 'targets',
                           weight=evidence.get('count', 1),
                           metadata={'platforms': [platform]})
        
        return builder

class HeatmapCalendarBuilder:
    """Generate GitHub-style heatmap calendar for incident frequency"""
    
    def __init__(self, days_back: int = 365):
        self.days_back = days_back
        self.data = defaultdict(int)
    
    def add_incident(self, date: str, count: int = 1):
        """Add incident to specific date (YYYY-MM-DD)"""
        self.data[date] += count
    
    def get_week_data(self) -> List[List[Dict]]:
        """Generate heatmap data grouped by week"""
        heatmap = []
        current_date = datetime.now()
        end_date = current_date - timedelta(days=self.days_back)
        
        weeks = defaultdict(list)
        
        while current_date > end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            week_num = current_date.isocalendar()[1]
            
            count = self.data.get(date_str, 0)
            
            weeks[week_num].append({
                'date': date_str,
                'day': current_date.strftime('%A'),
                'count': count,
                'intensity': self._get_intensity(count)
            })
            
            current_date -= timedelta(days=1)
        
        # Convert to list of weeks
        for week_num in sorted(weeks.keys()):
            heatmap.append(weeks[week_num])
        
        return heatmap
    
    def _get_intensity(self, count: int) -> str:
        """Map count to intensity level"""
        if count == 0:
            return 'none'
        elif count < 3:
            return 'low'
        elif count < 7:
            return 'medium'
        elif count < 15:
            return 'high'
        else:
            return 'very_high'
    
    def get_calendar_json(self) -> Dict:
        """Return calendar heatmap as JSON"""
        return {
            'weeks': self.get_week_data(),
            'total_incidents': sum(self.data.values()),
            'coverage_days': len(self.data),
            'average_per_day': sum(self.data.values()) / max(len(self.data), 1),
            'peak_date': max(self.data, key=self.data.get) if self.data else None,
            'peak_count': max(self.data.values()) if self.data else 0
        }

class PredictiveEscalationModel:
    """Simple ML model for predicting abuser escalation risk"""
    
    def __init__(self):
        self.feature_weights = {
            'incident_frequency': 0.4,
            'severity_trend': 0.3,
            'time_since_last_incident': 0.15,
            'message_intensity': 0.15
        }
    
    def calculate_risk_score(self, abuser_profile: Dict) -> float:
        """Calculate escalation risk score (0.0 - 1.0)"""
        
        # Extract features
        incident_frequency = min(abuser_profile.get('incident_frequency', 0) / 100, 1.0)
        severity_trend = self._normalize_trend(abuser_profile.get('severity_trend', 'stable'))
        time_since_last = self._normalize_time(abuser_profile.get('days_since_last_incident', 30))
        message_intensity = min(abuser_profile.get('avg_message_intensity', 0) / 100, 1.0)
        
        # Calculate weighted score
        risk_score = (
            incident_frequency * self.feature_weights['incident_frequency'] +
            severity_trend * self.feature_weights['severity_trend'] +
            time_since_last * self.feature_weights['time_since_last_incident'] +
            message_intensity * self.feature_weights['message_intensity']
        )
        
        return min(max(risk_score, 0.0), 1.0)
    
    def _normalize_trend(self, trend: str) -> float:
        """Normalize trend to 0.0-1.0"""
        trends = {'decreasing': 0.2, 'stable': 0.5, 'increasing': 0.9}
        return trends.get(trend, 0.5)
    
    def _normalize_time(self, days: int) -> float:
        """Normalize time since last incident (recency factor)"""
        # Closer to now = higher risk
        if days <= 1:
            return 1.0
        elif days <= 7:
            return 0.8
        elif days <= 30:
            return 0.5
        elif days <= 90:
            return 0.2
        else:
            return 0.0
    
    def predict_multiple(self, abuser_profiles: List[Dict]) -> List[Dict]:
        """Predict risk for multiple abusers"""
        predictions = []
        for profile in abuser_profiles:
            risk_score = self.calculate_risk_score(profile)
            risk_level = self._get_risk_level(risk_score)
            
            predictions.append({
                'abuser_id': profile.get('abuser_id'),
                'risk_score': round(risk_score, 3),
                'risk_level': risk_level,
                'recommendation': self._get_recommendation(risk_level),
                'factors': {
                    'frequency': profile.get('incident_frequency', 0),
                    'trend': profile.get('severity_trend', 'stable'),
                    'recency': profile.get('days_since_last_incident', 0)
                }
            })
        
        # Sort by risk score descending
        predictions.sort(key=lambda x: x['risk_score'], reverse=True)
        return predictions
    
    def _get_risk_level(self, score: float) -> str:
        """Categorize risk level"""
        if score < 0.3:
            return 'LOW'
        elif score < 0.6:
            return 'MEDIUM'
        elif score < 0.8:
            return 'HIGH'
        else:
            return 'CRITICAL'
    
    def _get_recommendation(self, risk_level: str) -> str:
        """Get action recommendation"""
        recommendations = {
            'LOW': 'Monitor but no immediate action needed',
            'MEDIUM': 'Increase monitoring frequency',
            'HIGH': 'Prepare documentation for escalation',
            'CRITICAL': 'Escalate to authorities immediately'
        }
        return recommendations.get(risk_level, 'Monitor situation')

class WordCloudAnalyzer:
    """Analyze content to generate word clouds from toxic content"""
    
    # Common stop words
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'is', 'was', 'are', 'be', 'been', 'being', 'have', 'has',
        'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
        'might', 'can', 'it', 'that', 'this', 'these', 'those', 'i', 'you',
        'he', 'she', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why'
    }
    
    def __init__(self):
        self.word_frequency = Counter()
        self.toxic_words = Counter()
    
    def process_text(self, text: str, toxicity_score: float = 0.0):
        """Process text and extract important words"""
        # Simple tokenization
        words = text.lower().split()
        
        for word in words:
            # Remove punctuation
            word = ''.join(c for c in word if c.isalnum())
            
            # Skip short words and stop words
            if len(word) > 3 and word not in self.STOP_WORDS:
                self.word_frequency[word] += 1
                
                # Track toxic words separately
                if toxicity_score > 0.5:
                    self.toxic_words[word] += 1
    
    def get_word_cloud_data(self, limit: int = 100) -> List[Dict]:
        """Generate word cloud data"""
        cloud_data = []
        
        for word, count in self.word_frequency.most_common(limit):
            toxicity = self.toxic_words.get(word, 0) / max(count, 1)
            
            cloud_data.append({
                'word': word,
                'frequency': count,
                'toxicity_ratio': round(toxicity, 2),
                'size': self._calculate_size(count)
            })
        
        return cloud_data
    
    def _calculate_size(self, count: int) -> str:
        """Calculate word size based on frequency"""
        if count < 5:
            return 'xs'
        elif count < 10:
            return 'sm'
        elif count < 20:
            return 'md'
        elif count < 50:
            return 'lg'
        else:
            return 'xl'

class TimeOfDayAnalyzer:
    """Analyze incident patterns by time and day"""
    
    def __init__(self):
        self.hourly_data = defaultdict(int)
        self.daily_data = defaultdict(int)
        self.incidents = []
    
    def add_incident(self, timestamp: datetime, severity: float = 0.5):
        """Log an incident with timestamp and severity"""
        hour = timestamp.hour
        day = timestamp.strftime('%A')
        
        self.hourly_data[hour] += 1
        self.daily_data[day] += 1
        self.incidents.append({
            'timestamp': timestamp.isoformat(),
            'hour': hour,
            'day': day,
            'severity': severity
        })
    
    def get_hourly_pattern(self) -> Dict:
        """Get incidents per hour"""
        pattern = {}
        for hour in range(24):
            pattern[str(hour).zfill(2)] = self.hourly_data[hour]
        
        return {
            'hourly_pattern': pattern,
            'peak_hours': sorted(self.hourly_data.items(), 
                                key=lambda x: x[1], reverse=True)[:5],
            'average_per_hour': sum(self.hourly_data.values()) / 24 if self.hourly_data else 0
        }
    
    def get_daily_pattern(self) -> Dict:
        """Get incidents per day of week"""
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pattern = {day: self.daily_data[day] for day in days_order}
        
        return {
            'daily_pattern': pattern,
            'peak_days': sorted(self.daily_data.items(),
                              key=lambda x: x[1], reverse=True),
            'average_per_day': sum(self.daily_data.values()) / 7 if self.daily_data else 0,
            'weekend_incidents': self.daily_data['Saturday'] + self.daily_data['Sunday'],
            'weekday_incidents': sum(self.daily_data[day] for day in days_order[:5])
        }
    
    def get_combined_analysis(self) -> Dict:
        """Get combined time analysis"""
        return {
            'hourly': self.get_hourly_pattern(),
            'daily': self.get_daily_pattern(),
            'total_incidents': len(self.incidents),
            'timestamp': datetime.now().isoformat()
        }
