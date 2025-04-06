# Food Calorie Estimation System

This system uses Google's Gemini AI to estimate calories from both image and text inputs. It provides real-time feedback on daily calorie goals and maintains a log of food entries.

## Features

- Image-based food recognition and calorie estimation
- Text-based food description and calorie estimation
- Daily calorie tracking and goal monitoring
- SQLite database for persistent storage
- User-specific calorie goals

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root and add your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

You can get a free API key from the Google AI Studio (https://makersuite.google.com/app/apikey).

## Usage

```python
from calorie_estimator import CalorieEstimator
from database import Database

# Initialize the system
estimator = CalorieEstimator()
db = Database()

# Create a new user
user_id = db.add_user("username", daily_calorie_goal=2000)

# Estimate calories from an image
result = estimator.estimate_from_image("path/to/food_image.jpg")
if result:
    estimator.log_calories(result, user_id)

# Estimate calories from text
result = estimator.estimate_from_text("2 cups of rice")
if result:
    estimator.log_calories(result, user_id)

# Get daily summary
summary = estimator.get_daily_summary(user_id)
print(f"Total calories today: {summary['total_calories']}")
```

## Notes

- The system uses Gemini Pro for text analysis and Gemini Pro Vision for image analysis
- Free tier limits apply to the Google API
- Images should be clear and well-lit for best results
- The system stores data in a SQLite database (`calories.db`)

## Error Handling

- If image recognition fails, the system will return None
- Invalid text inputs will be handled gracefully
- Database operations are wrapped in try-except blocks

## Contributing

Feel free to submit issues and enhancement requests! 