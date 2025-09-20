# Import from files
from model_manager.deepseek_model import DeepseekModel
from model_manager.gemini_model import GeminiModel
from model_manager.gpt_model import GPTModel

# Import from library
import time

class ModelFallback():
    def __init__(self):
        self.GM = GeminiModel()
        self.DS = DeepseekModel()
        self.GPT = GPTModel()

    def try_gemini(self, system_prompt, user_prompt):
        response = self.GM.model_pipeline(system_prompt=system_prompt, user_prompt=user_prompt)
        return response
    
    def try_deepseek(self, system_prompt, user_prompt):
        response = self.DS.model_pipeline(system_prompt=system_prompt, user_prompt=user_prompt)
        return response
    
    def try_gpt(self, system_prompt, user_prompt):
        response = self.GPT.model_pipeline(system_prompt=system_prompt, user_prompt=user_prompt)
        print(f"Response from MF: {response}")
        return response
    
    def call_with_fallback(self, system_prompt, user_prompt, max_retries=1, backoffs=(1.5, 3)):
        """Try gemini first then Deepseek"""
    
        attempts = [
            ("gpt", lambda: self.try_gpt(system_prompt, user_prompt))
            ]            
#        ("gemini", self.try_gemini), 
#        ("deepseek", self.try_deepseek)

        for attempt in range(max_retries+1):
            for name, function in attempts:
                try:
                    return function()
                except Exception as e:
                    print(f"Error with {name} model: {e}")
            if attempt < max_retries:
                time.sleep(backoffs[min(attempt, len(backoffs) - 1)])