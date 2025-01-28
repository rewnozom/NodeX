"""
ai_agent/core/models/registry.py - Model registry and factory
"""

from typing import Dict, Type, Optional
from .base import BaseModel, ModelConfig, ModelType

class ModelRegistry:
    _models: Dict[str, Dict[str, Type[BaseModel]]] = {}
    _instances: Dict[str, BaseModel] = {}
    
    @classmethod
    def register(cls, provider: str, model_type: ModelType, model_class: Type[BaseModel]):
        """Register a model implementation"""
        if provider not in cls._models:
            cls._models[provider] = {}
        cls._models[provider][model_type.value] = model_class

    @classmethod
    def get_model(cls, config: ModelConfig, model_type: ModelType) -> BaseModel:
        """Get or create model instance"""
        key = f"{config.provider}:{config.model_name}:{model_type.value}"
        
        if key not in cls._instances:
            if config.provider not in cls._models:
                raise ValueError(f"Unknown provider: {config.provider}")
            if model_type.value not in cls._models[config.provider]:
                raise ValueError(f"Model type {model_type} not supported by {config.provider}")
                
            model_class = cls._models[config.provider][model_type.value]
            cls._instances[key] = model_class(config)
            
        return cls._instances[key]

    @classmethod
    def unregister_model(cls, provider: str, model_type: ModelType):
        """Unregister a model implementation"""
        if provider in cls._models and model_type.value in cls._models[provider]:
            del cls._models[provider][model_type.value]

    @classmethod
    def clear_instances(cls):
        """Clear cached model instances"""
        cls._instances.clear()