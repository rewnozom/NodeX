import os
import json
import traceback
from typing import Dict, Any, Optional
from log.logger import logger

# Konstanter för tjänster som inte kräver API-nycklar
LMSTUDIO_API_KEY = None
OLLAMA_API_ENDPOINT = "http://localhost:11434"

# Sökvägar och mappar
CHAT_HISTORY_FOLDER = "./Workspace/chat_history"
MEMORY_FILE_PATH = "./Workspace/memory.json"
SYSTEM_PROMPT_PATH = "./Workspace/system_prompt.txt"
DEFAULT_SYSTEM_PROMPT_PATH = "./ai/System_Prompts/Original.md"
SAVED_MODULES_DIR = "./Workspace/savedmodules"
DATAMEMORY_DIR = "./Workspace/datamemory"
GROQ_OUTPUT_DIR_TEMPLATE = "./Workspace/groq/output/{version}/"

# Ange ett separat filnamn för agentinställningar
AGENT_SETTINGS_FILE = "./ai_agent/config/agent_settings.json"

class Config:
    """
    Denna klass kombinerar generella inställningar (API-nycklar, modeller, UI m.m.)
    med agentrelaterade inställningar som sparas persistently i filen "agent_settings.json".
    
    Om filen inte finns används en hårdkodad standardkonfiguration (fallback).
    Alla uppdateringar av agentinställningar sparas direkt i agent_settings.json.
    """

    def __init__(self):
        # Generella inställningar
        self._config = {
            # Allmänna inställningar
            'disable_color': os.getenv('DISABLE_COLOR_PRINTING', 'False').lower() in ('true', '1', 't'),
            'debug': os.getenv('DEBUG', 'False').lower() in ('true', '1', 't'),
            'log_directory': os.getenv('LOG_DIR', "./logs"),
            'logging_rest_api': os.getenv('LOGGING_REST_API', 'False').lower() in ('true', '1', 't'),

            # API-nycklar
            'OPENAI_API_KEY': os.getenv("OPENAI_API_KEY", "your_openai_api_key_here"),
            'API_KEY_ANTHROPIC': os.getenv("API_KEY_ANTHROPIC", "your_anthropic_api_key_here"),
            'API_KEY_GROQ': os.getenv("API_KEY_GROQ", "your_groq_api_key_here"),
            'MISTRAL_API_KEY': os.getenv("MISTRAL_API_KEY", "your_mistral_api_key_here"),

            # Modellinställningar
            'CHAT_MODEL': os.getenv("CHAT_MODEL", "LM Studio Model"),
            'CHAT_TEMPERATURE': float(os.getenv("CHAT_TEMPERATURE", 0.65)),
            'UTILITY_MODEL': os.getenv("UTILITY_MODEL", "LM Studio Model"),
            'UTILITY_TEMPERATURE': float(os.getenv("UTILITY_TEMPERATURE", 0.65)),
            'EMBEDDING_MODEL': os.getenv("EMBEDDING_MODEL", "HuggingFace Embeddings"),

            # Chat-specifika inställningar
            'MAX_TOKENS': int(os.getenv("MAX_TOKENS", 49152)),
            'ENABLE_HISTORY': os.getenv("ENABLE_HISTORY", "False").lower() in ('true', '1', 't'),
            'ENABLE_MEMORY': os.getenv("ENABLE_MEMORY", "True").lower() in ('true', '1', 't'),

            # Filvägar
            'MEMORY_FILE': MEMORY_FILE_PATH,
            'SYSTEM_PROMPT_FILE': SYSTEM_PROMPT_PATH,
            'DATA_MEMORY_FOLDER': DATAMEMORY_DIR,
            'SAVED_MODULES_FOLDER': SAVED_MODULES_DIR,

            # UI-specifika inställningar
            'theme': 'light',
            'enable_phone_layout': False,
        }

        self.DEFAULT_CHAT_SETTINGS = {
            'temperature': self._config['CHAT_TEMPERATURE'],
            'max_tokens': self._config['MAX_TOKENS'],
            'model': self._config['CHAT_MODEL'],
            'system_prompt': 'default',
            'autog': False,
            'prefix_states': [(False, True)] * 6
        }

        self.DEFAULT_LEFT_MENU_STATE = {
            'current_tab': 0,
            'input_directory': '',
            'output_directory': '',
            'system_prompt': '',
            'selected_chat': None,
            'progress_visible': False,
            'progress_value': 0,
            'log_visible': False,
            'log_content': ''
        }

        # Ladda agentrelaterade inställningar (från fil, eller använd default)
        self._agent_config = self._load_agent_config()

    # --- Agent-relaterad logik ---
    def _default_agent_config(self) -> Dict[str, Any]:
        """Returnerar den hårdkodade standard-agentkonfigurationen (fallback)."""
        return {
            'AGENT_ENABLED': False,
            'CURRENT_AGENT': 'chat',
            'AGENT_CONFIG': {},
            'AGENT_PROFILES': {
                'chat': {
                    'name': 'Standard Chat',
                    'description': 'Basic chat interaction',
                    'enabled': True,
                    'temperature': 0.7
                },
                'developer': {
                    'name': 'Developer Agent',
                    'description': 'Multi-agent system for software development',
                    'enabled': True,
                    'config': {
                        'max_team_size': 3,
                        'process_type': 'sequential',
                        'verbose': True,
                        'tools': {
                            'code_analysis': True,
                            'dependency_tracking': True,
                            'impact_analysis': True,
                            'documentation_generation': True
                        },
                        'workflows': {
                            'troubleshoot': {
                                'enabled': True,
                                'name': 'Problem Solving',
                                'description': 'Debug and fix issues',
                                'steps': [
                                    "problem_analysis",
                                    "context_gathering",
                                    "error_diagnosis",
                                    "solution_design",
                                    "implementation",
                                    "verification"
                                ],
                                'roles': {
                                    'architect': "Analyze system impact and dependencies",
                                    'debugger': "Diagnose and fix issues",
                                    'tester': "Verify solutions"
                                }
                            },
                            'improve': {
                                'enabled': True,
                                'name': 'Code Enhancement',
                                'description': 'Improve code quality and structure',
                                'steps': [
                                    "code_review",
                                    "quality_analysis",
                                    "pattern_recognition",
                                    "reusability_check",
                                    "improvement_planning",
                                    "refactoring",
                                    "validation"
                                ],
                                'roles': {
                                    'analyst': "Review and analyze code",
                                    'architect': "Design improvements",
                                    'developer': "Implement changes"
                                }
                            },
                            'develop': {
                                'enabled': True,
                                'name': 'New Development',
                                'description': 'Develop new features with dependency management',
                                'steps': [
                                    "requirement_analysis",
                                    "dependency_check",
                                    "impact_analysis",
                                    "design_planning",
                                    "implementation",
                                    "integration",
                                    "dependency_updates",
                                    "testing"
                                ],
                                'roles': {
                                    'architect': "Design and plan",
                                    'developer': "Implement features",
                                    'integrator': "Handle dependencies"
                                }
                            },
                            'document': {
                                'enabled': True,
                                'name': 'Documentation',
                                'description': 'Create professional documentation',
                                'steps': [
                                    "scope_analysis",
                                    "content_assessment",
                                    "structure_planning",
                                    "content_creation",
                                    "review_and_refine",
                                    "validation"
                                ],
                                'roles': {
                                    'analyst': "Analyze and plan documentation",
                                    'writer': "Create and refine content",
                                    'reviewer': "Review and validate"
                                }
                            }
                        },
                        'roles': {
                            'architect': {
                                'enabled': True,
                                'temperature': 0.3,
                                'description': 'System design and architecture',
                                'responsibilities': [
                                    "System design",
                                    "Dependency management",
                                    "Architecture decisions",
                                    "Impact analysis"
                                ]
                            },
                            'developer': {
                                'enabled': True,
                                'temperature': 0.5,
                                'description': 'Implementation and problem-solving',
                                'responsibilities': [
                                    "Code implementation",
                                    "Bug fixing",
                                    "Feature development",
                                    "Testing"
                                ]
                            },
                            'analyst': {
                                'enabled': True,
                                'temperature': 0.4,
                                'description': 'Analysis and documentation',
                                'responsibilities': [
                                    "Code analysis",
                                    "Pattern recognition",
                                    "Documentation",
                                    "Quality assessment"
                                ]
                            },
                            'integrator': {
                                'enabled': True,
                                'temperature': 0.4,
                                'description': 'Integration and dependencies',
                                'responsibilities': [
                                    "Dependency management",
                                    "System integration",
                                    "Compatibility checks",
                                    "Version control"
                                ]
                            }
                        }
                    }
                }
            }
        }

    def _load_agent_config(self) -> Dict[str, Any]:
        """
        Försök läsa in sparade agentinställningar från AGENT_SETTINGS_FILE.
        Om filen inte finns eller ett fel uppstår returneras en kopia av den standardiserade agentkonfigurationen.
        """
        if os.path.exists(AGENT_SETTINGS_FILE):
            try:
                with open(AGENT_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info("Agent configuration loaded from agent_settings.json")
                    return data
            except Exception as e:
                logger.error(f"Error loading agent configuration: {e}")
        logger.debug("No valid agent_settings.json found; using default agent configuration.")
        return self._default_agent_config().copy()

    def _save_agent_config(self):
        """
        Spara den aktuella agentkonfigurationen (_agent_config) till AGENT_SETTINGS_FILE.
        Skapar mappar om de inte existerar.
        """
        try:
            os.makedirs(os.path.dirname(AGENT_SETTINGS_FILE), exist_ok=True)
            with open(AGENT_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._agent_config, f, indent=4)
            logger.info("Agent configuration saved to agent_settings.json")
        except Exception as e:
            logger.error(f"Error saving agent configuration: {e}")

    def get_agent_config(self, agent_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Returnera aktuella inställningar för en given agenttyp.
        Om agent_type inte anges används värdet från CURRENT_AGENT.
        Returnerad dictionary innehåller:
          {
            'enabled': bool,
            'current_agent': str,
            'profile': dict,
            'config': dict
          }
        """
        if agent_type is None:
            agent_type = self._agent_config.get('CURRENT_AGENT', 'chat')
        return {
            'enabled': self._agent_config.get('AGENT_ENABLED', False),
            'current_agent': agent_type,
            'profile': self._agent_config.get('AGENT_PROFILES', {}).get(agent_type, {}),
            'config': self._agent_config.get('AGENT_CONFIG', {})
        }

    def update_agent_config(self, settings: Dict[str, Any]):
        """
        Uppdatera agentkonfigurationen med de värden som ges i "settings" och spara ändringarna.

        Exempel:
          {
            'enabled': True,
            'current_agent': 'developer',
            'config': { ... },
            'profile': { ... }
          }

        Efter uppdatering sparas konfigurationen till AGENT_SETTINGS_FILE.
        """
        logger.info(f"[update_agent_config] Called with {settings}")
        logger.info("Stack trace for update_agent_config:\n" + "".join(traceback.format_stack()))

        old_enabled = self._agent_config.get('AGENT_ENABLED', False)
        old_agent = self._agent_config.get('CURRENT_AGENT', 'chat')

        self._agent_config['AGENT_ENABLED'] = settings.get('enabled', old_enabled)
        self._agent_config['CURRENT_AGENT'] = settings.get('current_agent', old_agent)

        if 'config' in settings:
            self._agent_config.setdefault('AGENT_CONFIG', {}).update(settings['config'])
        if 'profile' in settings:
            agent_type = self._agent_config.get('CURRENT_AGENT', 'chat')
            if agent_type in self._agent_config.get('AGENT_PROFILES', {}):
                self._agent_config['AGENT_PROFILES'][agent_type].update(settings['profile'])

        logger.info(f"Agent configuration updated: {settings}")
        self._save_agent_config()

    def get_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        Returnera alla agentprofiler som definieras under AGENT_PROFILES.
        """
        return self._agent_config.get('AGENT_PROFILES', {})

    def get_agent_profile(self, agent_type: str) -> Dict[str, Any]:
        """
        Returnera den specifika agentprofilen för "agent_type" (ex. "chat" eller "developer").
        Om agenttypen inte finns returneras en tom dictionary.
        """
        return self._agent_config.get('AGENT_PROFILES', {}).get(agent_type, {})

    def get_role_config(self, role_name: str) -> Dict[str, Any]:
        """
        Exempelmetod för att hämta konfigurationen för en specifik roll från developer-agenten.
        Exempel: get_role_config('architect') returnerar konfigurationen för 'architect'.
        """
        dev_config = self._agent_config.get('AGENT_PROFILES', {}).get('developer', {}).get('config', {})
        return dev_config.get('roles', {}).get(role_name, {})

    # --- Generella inställningar-metoder ---
    def get(self, key, default=None):
        return self._config.get(key, default)

    def __getattr__(self, name):
        return self.get(name)
