from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Date,
    ForeignKey,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    daily_calorie_goal = Column(Integer, default=2000)
    entries = relationship("CalorieEntry", back_populates="user")


class CalorieEntry(Base):
    __tablename__ = "calorie_entries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    food_name = Column(String)
    portion = Column(String)
    calories = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="entries")


class Database:
    def __init__(self):
        self.engine = create_engine("sqlite:///backend/calories.db")

        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add_user(self, username, daily_calorie_goal=2000):
        existing_user = self.session.query(User).filter_by(username=username).first()
        if existing_user:
            return (
                existing_user.id
            )  # Return existing user ID instead of inserting again

        new_user = User(username=username, daily_calorie_goal=daily_calorie_goal)
        self.session.add(new_user)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return None  # Handle the error gracefully
        return new_user.id

    def add_calorie_entry(self, user_id, food_name, portion, calories, timestamp):
        entry = CalorieEntry(
            user_id=user_id,
            food_name=food_name,
            portion=portion,
            calories=calories,
            timestamp=timestamp,
        )
        self.session.add(entry)
        self.session.commit()
        return entry.id

    def get_calories_for_date(self, user_id, date):
        return (
            self.session.query(CalorieEntry)
            .filter(
                CalorieEntry.user_id == user_id,
                CalorieEntry.timestamp >= date,
                CalorieEntry.timestamp < date + timedelta(days=1),
            )
            .all()
        )

    def get_user_goal(self, user_id):
        user = self.session.query(User).filter(User.id == user_id).first()
        return user.daily_calorie_goal if user else 2000

    def update_user_goal(self, user_id, new_goal):
        user = self.session.query(User).filter(User.id == user_id).first()
        if user:
            user.daily_calorie_goal = new_goal
            self.session.commit()
            return True
        return False
