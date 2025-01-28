"""
ai_agent/agents/architect.py - System architect agent implementation
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from ..core.agents.base import BaseAgent, AgentConfig, AgentState

@dataclass
class Component:
    name: str
    description: str
    interfaces: List[str]
    dependencies: List[str]
    tests: Optional[str] = None

@dataclass
class Architecture:
    components: List[Component]
    data_flows: List[Dict[str, str]]
    api_specs: Dict[str, Any]

class ArchitectAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.current_design: Optional[Architecture] = None

    async def _process_implementation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Design system architecture"""
        self.set_state(AgentState.ANALYZING)
        
        requirements = input_data.get("requirements", [])
        constraints = input_data.get("constraints", [])
        
        # Analyze requirements
        components = await self._identify_components(requirements)
        
        # Design interfaces
        interfaces = await self._design_interfaces(components)
        
        # Analyze data flows
        data_flows = await self._analyze_data_flows(components, interfaces)
        
        # Generate API specs
        api_specs = await self._generate_api_specs(components, interfaces)
        
        # Create architecture
        self.current_design = Architecture(
            components=components,
            data_flows=data_flows,
            api_specs=api_specs
        )
        
        # Validate design
        issues = await self._validate_design()
        if issues:
            self.set_state(AgentState.ERROR)
            return {"error": issues}
            
        self.set_state(AgentState.IMPLEMENTING)
        return {
            "components": [c.__dict__ for c in components],
            "data_flows": data_flows,
            "api_specs": api_specs
        }

    async def _identify_components(self, requirements: List[str]) -> List[Component]:
        """Identify system components from requirements"""
        prompt = f"""Analyze these requirements and identify key components:
Requirements:
{self._format_list(requirements)}

For each component specify:
- Name
- Description 
- Required interfaces
- Dependencies

Format as JSON list."""

        response = await self._get_model_response(prompt)
        components = self._parse_components(response)
        return components

    async def _design_interfaces(self, components: List[Component]) -> Dict[str, Any]:
        """Design component interfaces"""
        prompt = f"""Design interfaces for these components:
Components:
{self._format_components(components)}

For each interface specify:
- Name
- Methods
- Parameters
- Return types
- Error handling

Format as JSON."""

        response = await self._get_model_response(prompt)
        return self._parse_json(response)

    async def _analyze_data_flows(
        self,
        components: List[Component],
        interfaces: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Analyze data flows between components"""
        prompt = f"""Analyze data flows between components:
Components:
{self._format_components(components)}

Interfaces:
{self._format_dict(interfaces)}

Specify all data flows as source->target pairs with data type.
Format as JSON array."""

        response = await self._get_model_response(prompt)
        return self._parse_json(response)

    async def _generate_api_specs(
        self,
        components: List[Component],
        interfaces: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate OpenAPI specs"""
        prompt = f"""Generate OpenAPI specs for components:
Components:
{self._format_components(components)}

Interfaces:
{self._format_dict(interfaces)}

Format as JSON OpenAPI 3.0."""

        response = await self._get_model_response(prompt)
        return self._parse_json(response)

    async def _validate_design(self) -> List[str]:
        """Validate architecture design"""
        if not self.current_design:
            return ["No design to validate"]

        issues = []
        
        # Check for circular dependencies
        if self._has_circular_dependencies():
            issues.append("Circular dependencies detected")
            
        # Verify interface coverage
        missing = self._find_missing_interfaces()
        if missing:
            issues.append(f"Missing interfaces: {', '.join(missing)}")
            
        # Validate data flows
        invalid = self._validate_data_flows()
        if invalid:
            issues.append(f"Invalid data flows: {', '.join(invalid)}")
            
        return issues

    def _has_circular_dependencies(self) -> bool:
        """Check for circular dependencies"""
        if not self.current_design:
            return False
            
        # Build dependency graph
        graph = {}
        for comp in self.current_design.components:
            graph[comp.name] = comp.dependencies

        # Check for cycles
        visited = set()
        path = []
        
        def has_cycle(node: str) -> bool:
            if node in path:
                return True
            if node in visited:
                return False
                
            visited.add(node)
            path.append(node)
            
            for dep in graph.get(node, []):
                if has_cycle(dep):
                    return True
                    
            path.pop()
            return False

        return any(has_cycle(comp.name) for comp in self.current_design.components)

    def _find_missing_interfaces(self) -> List[str]:
        """Find missing interfaces"""
        if not self.current_design:
            return []
            
        required = set()
        provided = set()
        
        for comp in self.current_design.components:
            required.update(comp.interfaces)
            provided.add(comp.name)
            
        return list(required - provided)

    def _validate_data_flows(self) -> List[str]:
        """Validate data flow consistency"""
        if not self.current_design:
            return []
            
        invalid = []
        components = {c.name for c in self.current_design.components}
        
        for flow in self.current_design.data_flows:
            if flow["source"] not in components:
                invalid.append(f"Invalid source: {flow['source']}")
            if flow["target"] not in components:
                invalid.append(f"Invalid target: {flow['target']}")
                
        return invalid

    def _format_list(self, items: List[str]) -> str:
        return "\n".join(f"- {item}" for item in items)
        
    def _format_components(self, components: List[Component]) -> str:
        return "\n".join(str(c.__dict__) for c in components)
        
    def _format_dict(self, d: Dict) -> str:
        return "\n".join(f"{k}: {v}" for k, v in d.items())