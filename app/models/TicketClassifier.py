import openai
from openai.openai_object import OpenAIObject

from data.constants import OPENAI_API_KEY, CATEGORIES, DELIMITER

openai.api_key = OPENAI_API_KEY


class TicketClassifier:
    delimiter = DELIMITER
    categories = CATEGORIES

    def __init__(self):
        self.messages = [
            {
                "role": "system",
                "content": self.get_system_message()
            }
        ]

    def get_system_message(self) -> str:
        return f"""
        I want you to act as an IT tickets classification machine.
        I will provide you with the user request in the ticket and you will act as a classification machine.
        The user message should be delimited with {self.delimiter} characters.
        The ticket MUST necessarily be classified into one of the following categories: {self.categories}.
        Provide the output in JSON format with the key: category.
        """
    
    def add_user_message(self, message):
        self.messages.append({
            "role": "user",
            "content": f"{self.delimiter}{message}{self.delimiter}"
        })

    def get_completion(self, model="gpt-3.5-turbo", temperature=0, max_tokens=250) -> str | None:
        response = openai.ChatCompletion.create(
            model=model,
            messages=self.messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if isinstance(response, OpenAIObject):
            return response.choices[0].message["content"]
        else:
            return None
    

    def classify_ticket(self, message) -> str | None:
        self.add_user_message(message)
        response = self.get_completion()
        return response
