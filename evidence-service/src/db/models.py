from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Evidence(Base):
    __tablename__ = 'evidence'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# ── Webhook Integration Models ──────────────────────────────────────────────────
class WebhookConfig(Base):
    __tablename__ = 'webhook_configs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    platform = Column(String(50), nullable=False)  # 'discord', 'slack', 'twitter', 'telegram'
    webhook_url = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class WebhookEvent(Base):
    __tablename__ = 'webhook_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    webhook_config_id = Column(Integer, ForeignKey('webhook_configs.id'), nullable=False)
    evidence_id = Column(Integer, ForeignKey('evidence.id'), nullable=True)
    event_type = Column(String(50), nullable=False)  # 'submitted', 'verified', 'escalated'
    payload = Column(JSON, nullable=True)
    status = Column(String(20), default='pending')  # 'pending', 'sent', 'failed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ── Analytics Models ────────────────────────────────────────────────────────────
class IncidentMetric(Base):
    __tablename__ = 'incident_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    evidence_id = Column(Integer, ForeignKey('evidence.id'), nullable=False)
    hour_of_day = Column(Integer, nullable=False)  # 0-23
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Monday-Sunday)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD for heatmap
    incident_count = Column(Integer, default=1)
    severity_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class NetworkNode(Base):
    __tablename__ = 'network_nodes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    evidence_id = Column(Integer, ForeignKey('evidence.id'), nullable=False)
    node_type = Column(String(50), nullable=False)  # 'abuser', 'platform', 'victim'
    node_name = Column(String(255), nullable=False)
    node_identifier = Column(String(255), nullable=False)  # Username, URL, handle
    connections = Column(JSON, default={})  # Related nodes
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PredictiveEscalation(Base):
    __tablename__ = 'predictive_escalations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    abuser_identifier = Column(String(255), nullable=False)
    escalation_risk_score = Column(Float, default=0.0)  # 0.0-1.0
    incident_frequency = Column(Integer, default=0)
    severity_trend = Column(String(50))  # 'increasing', 'stable', 'decreasing'
    last_incident = Column(DateTime(timezone=True), nullable=True)
    prediction_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    model_version = Column(String(20), default='v1')

class ContentKeyword(Base):
    __tablename__ = 'content_keywords'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    evidence_id = Column(Integer, ForeignKey('evidence.id'), nullable=False)
    keyword = Column(String(100), nullable=False)
    frequency = Column(Integer, default=1)
    toxicity_level = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BotSubmission(Base):
    __tablename__ = 'bot_submissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_type = Column(String(50), nullable=False)  # 'telegram', 'whatsapp'
    user_id = Column(String(255), nullable=False)  # Bot user ID
    evidence_id = Column(Integer, ForeignKey('evidence.id'), nullable=True)
    source_url = Column(String(500), nullable=True)
    submission_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())