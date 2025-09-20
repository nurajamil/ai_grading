# Import from files
from utils.helper_functions import create_grading_prompt, create_feedback_prompt

# Import from libraries
from openai import OpenAI
import json
from dotenv import load_dotenv
import os

load_dotenv()


class GPTModel():
    """GPT model class - GPT5 mini"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_GPT5_API_KEY")
        self.model = "gpt-5-mini"
        

    def format_input (self, system_prompt, user_prompt):
        """Format the input prompt for the model."""

        formatted_input = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return formatted_input
    
    def format_hyperparams(self):
        """Format the hyperparameters for the model."""
        return {
            "max_tokens": 256,
            "temperature": 0,
            "top_p": 0.2,
        }
    
    def create_client(self):
        client = OpenAI(
            api_key=self.api_key
        ) 
        return client
    
    def model_response(self, **kwargs):
        """Call the model and return the response object."""
        completion = kwargs['client'].responses.create(
            model=self.model,
            input=kwargs['formatted_input'],
            store=True
        )

        return completion
    
 
    def parse_response(self, response) -> str:
        """Parse the model's response and return the generated text."""
        return response.output_text
    
    def model_pipeline(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Full pipeline to generate parsed model output from a prompt."""
        
        # Step 1: Format the input prompt
        formatted_input = self.format_input(system_prompt=system_prompt, user_prompt=user_prompt, **kwargs)
        print(f"Formatted input: {formatted_input}")

        # Step 2: Format model hyperparameters
        hyperparams = self.format_hyperparams()
        
        # Step 3: Create the model client
        client = self.create_client()

        # Step 4: Get the model response object
        response = self.model_response(
            client=client, 
            formatted_input=formatted_input, 
            **hyperparams)
        print(f"Response object: {response}")
        
        # Step 5: Parse and return the model's output
        parsed_output = self.parse_response(response)
        print(f"Parse output: {parsed_output}")

        #try:
        #    parsed_output = json.loads(parsed_output)
        #except json.JSONDecodeError as e:
        #    print(f"JSON decoding error: {e}")
        #    parsed_output = {"marks_awarded": 0, "max_marks": 0, "reasoning": "Failed to parse JSON response."}
        #print(f"Parsed output: {parsed_output}")
        
        return parsed_output
    