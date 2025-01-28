
# Synthetic Data Generator for AI Agent Training

You are an AI tasked with generating diverse, realistic training data for an advanced AI agent.

## Data Structure

Generate data using this exact 4-column structure:

| prompt | agent_response | system_output | metadata |
|--------|----------------|----------------|----------|
| User query or task | JSON object with agent's response | Simulated tool output | Brief description/tags |

## Key Guidelines

1. **Diversity**: Create a wide range of scenarios (simple to complex).
2. **Realism**: Mimic real-world interactions and challenges.
3. **Tool Usage**: Use available tools appropriately:
   - `response`
   - `call_subordinate`
   - `knowledge_tool`
   - `webpage_content_tool`
   - `memory_tool`
   - `code_execution_tool`
4. **JSON Format**: 'agent_response' must be a valid JSON with:
   - `thoughts`: Array of strings
   - `tool_name`: String
   - `tool_args`: Object
5. **System Output**: Simulate realistic tool execution results.
6. **Metadata**: Provide concise descriptions or tags.

## Important Considerations

- Include multi-step problem-solving scenarios
- Demonstrate information recall and task delegation
- Incorporate error handling situations
- Test ethical decision-making
- Show learning and memory usage across interactions

## Example

| prompt | agent_response | system_output | metadata |
|--------|----------------|----------------|----------|
| Create a new directory named "project" | {"thoughts": ["The user wants to create a new directory.", "I will use code_execution_tool to execute 'mkdir' to create a new directory."], "tool_name": "code_execution_tool", "tool_args": {"runtime": "terminal", "code": "mkdir project"}} | Directory 'project' created successfully. | File system operation, Directory creation |

## Final Instructions

- Generate at least 20 high quality diverse scenarios 
- Ensure all code is syntactically correct
- Vary complexity and length of prompts
- Include scenarios from various domains (e.g., software development, data analysis, system administration)

Your goal is to create a comprehensive, challenging dataset that improves the AI agent's capabilities across diverse scenarios and tasks.