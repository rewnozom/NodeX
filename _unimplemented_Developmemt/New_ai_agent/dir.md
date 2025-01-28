# Enhanced Project Structure

```
ai_agent/
├── core/
│   ├── models/
│   │   ├── registry.py
│   │   ├── base.py
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── openai.py
│   │       ├── anthropic.py
│   │       ├── lmstudio.py
│   │       └── groq.py
│   ├── agents/
│   │   ├── base.py
│   │   ├── registry.py
│   │   └── state.py
│   └── workflow/
│       ├── manager.py
│       └── steps.py
├── agents/
│   ├── judge.py
│   ├── architect.py
│   ├── developer.py
│   └── reviewer.py
├── testing/
│   ├── runner.py
│   ├── validators.py
│   └── executors/
│       ├── __init__.py
│       ├── base.py 
│       ├── terminal.py
│       ├── python.py
│       └── docker.py
├── extensions/
│   ├── message_loop_end/
│   │   ├── __init__.py
│   │   ├── organize_history.py
│   │   └── save_chat.py
│   ├── message_loop_prompts/
│   │   ├── __init__.py
│   │   ├── recall_memories.py
│   │   └── recall_solutions.py
│   ├── message_loop_start/
│   │   ├── __init__.py
│   │   └── iteration_no.py
│   ├── monologue_end/
│   │   ├── __init__.py
│   │   ├── memorize_fragments.py
│   │   └── memorize_solutions.py
│   ├── monologue_start/
│   │   ├── __init__.py
│   │   └── behaviour_update.py
│   └── system_prompt/
│       ├── __init__.py
│       ├── system_prompt.py
│       └── behaviour_prompt.py
├── plugins/
│   ├── loader.py
│   └── registry.py
└── utils/
    ├── logging.py
    ├── monitoring.py 
    ├── tokens.py
    ├── rate_limiter.py
    ├── defer.py
    ├── shell.py
    ├── docker.py
    └── messages.py
```