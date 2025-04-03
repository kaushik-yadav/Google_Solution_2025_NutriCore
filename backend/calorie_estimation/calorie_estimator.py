import os
import requests
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
from database import Database
import re


class CalorieEstimator:
    def __init__(self):
        load_dotenv()
        self.genai_api_key = os.getenv("GEMINI_API_KEY")
        self.logmeal_api_key = os.getenv("IMAGE_API_KEY")
        print(self.logmeal_api_key)
        if not self.genai_api_key:
            raise ValueError("Please set GEMINI_API_KEY in your .env file")
        if not self.logmeal_api_key:
            raise ValueError("Please set IMAGE_API_KEY in your .env file")

        genai.configure(api_key=self.genai_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-pro")
        self.db = Database()

    def analyze_food_image(self, image_path):
        """Use LogMeal API to detect food items in an image."""
        img = "food.jpg"
        api_user_token = self.logmeal_api_key
        headers = {"Authorization": "Bearer " + api_user_token}
        api_url = "https://api.logmeal.com/v2"
        endpoint = "/image/segmentation/complete"
        response = requests.post(
            api_url + endpoint, files={"image": open(img, "rb")}, headers=headers
        )
        print(response.json())
        for i in response.json()["segmentation_results"]:
            food_item = i["recognition_results"][0]["name"]
            break
        return food_item

    def estimate_from_image(self, image_path):
        """Estimate calories from an image input using LogMeal + Gemini."""
        food_item = self.analyze_food_image(image_path)
        if not food_item:
            return None

        portion_size = input(
            f"Detected food: {food_item}. Enter portion size (e.g., '1 cup', '200g'): "
        )
        food_description = f"{portion_size} of {food_item}"
        return self.estimate_from_text(food_description)

    def estimate_from_text(self, text_input):
        """Estimate calories from text input using Gemini."""
        prompt = f"""
        Given this food description: "{text_input}", provide:
        - Estimated Protein (g)
        - Estimated Fat (g)
        - Estimated Carbohydrates (g)
        - Estimated Calories (kcal)
        - Estimated Sugars (g)
        - Estimated Fiber (g)
        
        Output format:
        food: [name], portion: [portion], calories: [number], protein: [number], carbohydrates: [number], fat: [number], sugars: [number], fiber: [number]
        """
        response = self.model.generate_content(prompt)
        return self._parse_response(response.text)

    def _parse_response(self, response_text):
        """Parse the AI response into structured data using regex."""
        try:
            pattern = (
                r"food:\s*(.*?),\s*portion:\s*(.*?),\s*calories:\s*(\d+),\s*"
                r"protein:\s*(\d+),\s*carbohydrates:\s*(\d+),\s*fat:\s*(\d+),\s*"
                r"sugars:\s*(\d+),\s*fiber:\s*(\d+)"
            )
            match = re.search(pattern, response_text)
            if not match:
                print("Failed to parse response correctly.")
                return None

            return {
                "food": match.group(1),
                "portion": match.group(2),
                "calories": int(match.group(3)),
                "protein": int(match.group(4)),
                "carbohydrates": int(match.group(5)),
                "fat": int(match.group(6)),
                "sugars": int(match.group(7)),
                "fiber": int(match.group(8)),
            }
        except Exception as e:
            print(f"Error parsing response: {str(e)}")
            return None

    def log_calories(self, food_data, user_id):
        """Log calories to database."""
        if food_data:
            self.db.add_calorie_entry(
                user_id=user_id,
                food_data=food_data,
                timestamp=datetime.now(),
            )
            return True
        return False

    def get_daily_summary(self, user_id):
        """Get daily calorie summary."""
        today = datetime.now().date()
        entries = self.db.get_calories_for_date(user_id, today)
        total_calories = sum(entry.calories for entry in entries)
        return {"total_calories": total_calories, "entries": entries}
