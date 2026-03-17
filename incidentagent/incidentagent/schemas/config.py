"""
Configuration Schema

Application configuration using pydantic-settings.
"""

from typing import Dict, List, Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class InvestigationConfig(BaseSettings):
    """Investigation-specific configuration"""
    
    confidence_threshold: float = Field(
        default=0.85,
        description="Confidence threshold to stop investigation"
    )
    max_agents_per_investigation: int = Field(
        default=6,
        description="Maximum agents to call per investigation"
    )
    timeout_seconds: int = Field(
        default=300,
        description="Investigation timeout"
    )
    early_stop_enabled: bool = Field(
        default=True,
        description="Allow early stopping on high confidence"
    )


class ElasticsearchConfig(BaseSettings):
    """Elasticsearch configuration"""
    
    url: str = Field(
        default="http://localhost:9200",
        description="Elasticsearch URL"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication"
    )
    index_pattern: str = Field(
        default="logs-*",
        description="Index pattern for log search"
    )
    timeout_seconds: int = Field(default=30)
    
    model_config = SettingsConfigDict(
        env_prefix="ELASTICSEARCH_"
    )


class PrometheusConfig(BaseSettings):
    """Prometheus configuration"""
    
    url: str = Field(
        default="http://localhost:9090",
        description="Prometheus URL"
    )
    timeout_seconds: int = Field(default=30)
    
    model_config = SettingsConfigDict(
        env_prefix="PROMETHEUS_"
    )


class KubernetesConfig(BaseSettings):
    """Kubernetes configuration"""
    
    config_path: Optional[str] = Field(
        default=None,
        description="Path to kubeconfig"
    )
    namespace: str = Field(
        default="default",
        description="Default namespace"
    )
    in_cluster: bool = Field(
        default=False,
        description="Running inside cluster?"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="KUBERNETES_"
    )


class GradientConfig(BaseSettings):
    """DigitalOcean Gradient configuration"""
    
    api_token: Optional[str] = Field(
        default=None,
        description="DigitalOcean API token"
    )
    model_access_key: Optional[str] = Field(
        default=None,
        description="Gradient model access key"
    )
    
    # Knowledge bases
    runbooks_kb_id: str = Field(
        default="kb_runbooks",
        description="Runbooks knowledge base ID"
    )
    incidents_kb_id: str = Field(
        default="kb_incidents",
        description="Past incidents knowledge base ID"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="GRADIENT_"
    )


class LLMConfig(BaseSettings):
    """LLM configuration"""
    
    provider: Literal["gradient", "anthropic", "openai"] = Field(
        default="gradient",
        description="LLM provider"
    )
    model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Model to use"
    )
    temperature: float = Field(default=0.0)
    max_tokens: int = Field(default=4096)
    
    # API keys (only if not using Gradient)
    anthropic_api_key: Optional[str] = Field(default=None)
    openai_api_key: Optional[str] = Field(default=None)
    
    model_config = SettingsConfigDict(
        env_prefix="LLM_"
    )


class DashboardConfig(BaseSettings):
    """Dashboard configuration"""
    
    enabled: bool = Field(default=True)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8501)
    title: str = Field(default="IncidentAgent Dashboard")
    
    model_config = SettingsConfigDict(
        env_prefix="DASHBOARD_"
    )


class IntegrationsConfig(BaseSettings):
    """External integrations configuration"""
    
    # PagerDuty
    pagerduty_enabled: bool = Field(default=False)
    pagerduty_api_key: Optional[str] = Field(default=None)
    pagerduty_write_back: bool = Field(default=True)
    
    # Slack
    slack_enabled: bool = Field(default=False)
    slack_webhook_url: Optional[str] = Field(default=None)
    slack_bot_token: Optional[str] = Field(default=None)
    slack_channel: str = Field(default="#incidents")
    
    model_config = SettingsConfigDict(
        env_prefix="INTEGRATION_"
    )


class TrainingConfig(BaseSettings):
    """Model training configuration"""
    
    enabled: bool = Field(default=True)
    threshold: int = Field(
        default=100,
        description="Train after N verified incidents"
    )
    benchmark_improvement: float = Field(
        default=0.02,
        description="Required improvement to promote model"
    )
    gpu_droplet_size: str = Field(default="gpu-h100x1-80gb")
    max_training_hours: int = Field(default=4)
    
    model_config = SettingsConfigDict(
        env_prefix="TRAINING_"
    )


class Settings(BaseSettings):
    """
    Main application settings.
    
    Loads from environment variables and .env file.
    """
    
    # App info
    app_name: str = Field(default="incidentagent")
    version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    demo_mode: bool = Field(
        default=True,
        description="Use mock data for all data sources"
    )
    
    # Sub-configs
    investigation: InvestigationConfig = Field(
        default_factory=InvestigationConfig
    )
    elasticsearch: ElasticsearchConfig = Field(
        default_factory=ElasticsearchConfig
    )
    prometheus: PrometheusConfig = Field(
        default_factory=PrometheusConfig
    )
    kubernetes: KubernetesConfig = Field(
        default_factory=KubernetesConfig
    )
    gradient: GradientConfig = Field(
        default_factory=GradientConfig
    )
    llm: LLMConfig = Field(
        default_factory=LLMConfig
    )
    dashboard: DashboardConfig = Field(
        default_factory=DashboardConfig
    )
    integrations: IntegrationsConfig = Field(
        default_factory=IntegrationsConfig
    )
    training: TrainingConfig = Field(
        default_factory=TrainingConfig
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (cached)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
