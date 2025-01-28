import json
import re

def markdown_to_question_answer(markdown_text, user_prompt):
    prompt_pattern = re.compile(r'# User-Prompt\n(.*?)\n\n#', re.DOTALL)
    markdown_pattern = re.compile(r'(?s)(.*?)\n{2,}(?=^#|$)', re.MULTILINE)

    prompt_match = prompt_pattern.search(markdown_text)
    markdown_match = markdown_pattern.findall(markdown_text)

    question_answer_pairs = []
    for markdown in markdown_match:
        question_answer_pairs.append({
            "question": user_prompt,
            "answer": markdown.strip()
        })

    return json.dumps(question_answer_pairs, indent=4)

# Example Markdown content with the specific format
user_prompt = "What is the main feature of this application?"
LLM_answer = """
**Key Features:**
- **Interactive Terminal:** Integrated directly within the GUI, allowing for real-time command execution and output viewing.
- **Path and Command Management:** Enables users to dynamically choose execution paths and toggle between various command interpreters like Cmd, WSL, or Git Bash.
- **Customizable Interface:** Users can toggle the visibility of the terminal and modify the interface through a series of button-driven commands.


```python

class App(ctk.CTk):
    def __init__(self):
        super().__init__()  # Always call the superclass initializer first

        self._configure_app()
        self._setup_frames()  # This must be called before setup_ui
        self.button_config = ButtonConfig(self, self.colors, SCALE)  # Pass self.colors and SCALE directly here
        self.command_manager = CommandManager(self.button_config, self)
        self._setup_command_controls()

        # Setup key bindings

        # Setup UI
        self.setup_ui()  # This should be called after all frame setup is done
        
```
**Setup:**

### Create new folder for the application `Terminal-hub`
- 1. Create a new directory for your project and add the files `main.py`, `backends.py`.
- 2. Run `python main.py` to start the application.
- 3. The application will launch with a grayish design, and you can interact with the buttons and entries.

"""

json_output = markdown_to_question_answer(LLM_answer, user_prompt)
print(json_output)