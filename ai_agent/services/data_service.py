# services/data_service.py



from ai_agent.generation_manager.auto_gen import generate_data_and_save_excel as auto_generate_data
from log.logger import logger

class DataService:
    @staticmethod
    def auto_generate_data(response_content):
        try:
            saved_file = auto_generate_data(response_content)
            if saved_file:
                logger.info(f"Data list saved to {saved_file}")
                return saved_file
        except Exception as e:
            logger.error(f"Error in handling data list saving: {e}")
        return None
