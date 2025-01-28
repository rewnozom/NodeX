from python.helpers.extension import Extension
from agent import LoopData
from extensions.message_loop_prompts.recall_memories import DATA_NAME_TASK as DATA_NAME_TASK_MEMORIES
from extensions.message_loop_prompts.recall_solutions import DATA_NAME_TASK as DATA_NAME_TASK_SOLUTIONS


class RecallWait(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):

            task = self.agent.get_data(DATA_NAME_TASK_MEMORIES)
            if task and not task.done():
                # self.agent.context.log.set_progress("Recalling memories...")
                await task

            task = self.agent.get_data(DATA_NAME_TASK_SOLUTIONS)
            if task and not task.done():
                # self.agent.context.log.set_progress("Recalling solutions...")
                await task

