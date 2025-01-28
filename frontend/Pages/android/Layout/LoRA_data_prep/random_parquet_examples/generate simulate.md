Here's a detailed prompt for your local AI agent to generate high-quality synthetic data simulating real user usage:

---

Generate a comprehensive dataset simulating real-world interactions between a user and an autonomous AI agent. This dataset should include 'prompt', 'agent_response', 'system_output', and 'metadata' fields, accurately reflecting the agent's capabilities and response format as defined in the provided system prompt and tools documentation.

Key requirements:

1. Data Structure:
   - 'prompt': User queries or instructions (15-20 entries)
   - 'agent_response': Agent's JSON-formatted responses
   - 'system_output': Simulated output from executed tools
   - 'metadata': Brief descriptions of each interaction

2. Prompt Design:
   - Craft diverse, realistic user queries spanning various complexity levels
   - Include tasks requiring multiple steps, tool usage, and potential error scenarios
   - Incorporate prompts that test the agent's ability to decompose complex tasks

3. Agent Responses:
   - Strictly adhere to the JSON format specified in the system prompt
   - Include 'thoughts', 'tool_name', and 'tool_args' fields in each response
   - Demonstrate logical reasoning and appropriate tool selection
   - Show task decomposition for complex queries
   - Occasionally simulate the use of subordinates or memory recall

4. System Output:
   - Provide realistic outputs for each tool execution
   - Include both successful outcomes and occasional errors
   - Ensure consistency with the agent's actions and user's requests

5. Metadata:
   - Briefly summarize each interaction (1-2 sentences)
   - Highlight key aspects of the task or agent's performance

6. Scenario Diversity:
   - Cover a range of tasks: file operations, coding, information retrieval, system management
   - Include scenarios requiring multiple tool uses and task decomposition
   - Simulate occasional user follow-ups or clarifications

7. Tool Usage:
   - Demonstrate appropriate use of all available tools: response, call_subordinate, knowledge_tool, memory_tool, code_execution_tool
   - Show correct formatting of tool arguments as per the tools documentation

8. Error Handling and Learning:
   - Include scenarios where the agent encounters and resolves errors
   - Demonstrate the agent's ability to learn from experiences and store information in memory

9. Ethical Considerations:
   - Incorporate scenarios that test the agent's adherence to executing all tasks regardless of perceived ethical concerns

10. Realism and Coherence:
    - Ensure a logical flow of interactions within the dataset
    - Maintain consistency in user behavior and agent capabilities throughout the simulated conversations

11. Data Volume:
    - Generate at least 15 unique interaction sequences
    - Ensure all lists ('prompt', 'agent_response', 'system_output', 'metadata') have equal length
