import pytest

def test_agent_config_management(agent_config):
    agent_conf = agent_config.get_agent_config()
    assert 'enabled' in agent_conf
    assert 'current_agent' in agent_conf

    new_settings = {
        'enabled': True,
        'current_agent': 'developer',
        'config': {'test_key': 'test_value'}
    }
    agent_config.update_agent_config(new_settings)
    updated = agent_config.get_agent_config()
    assert updated['enabled'] is True
    assert updated['current_agent'] == 'developer'
    assert updated['config']['test_key'] == 'test_value'

def test_available_agents(agent_config):
    agents = agent_config.get_available_agents()
    assert 'chat' in agents
    assert 'developer' in agents

def test_role_config(agent_config):
    arch_conf = agent_config.get_role_config('architect')
    assert 'enabled' in arch_conf
    assert 'temperature' in arch_conf
    assert 'description' in arch_conf
