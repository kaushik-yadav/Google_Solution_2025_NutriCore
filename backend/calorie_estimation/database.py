import os
from datetime import datetime, timedelta
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, joinedload

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    daily_calorie_goal = Column(Integer, default=2000, nullable=False)

    entries = relationship(
        "CalorieEntry", back_populates="user", cascade="all, delete-orphan"
    )


class CalorieEntry(Base):
    __tablename__ = "calorie_entries"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    food_name = Column(String, nullable=False)
    portion = Column(String, nullable=False)
    calories = Column(Integer, nullable=False)
    protein = Column(Integer, nullable=True)
    carbs = Column(Integer, nullable=True)
    fat = Column(Integer, nullable=True)
    sugars = Column(Integer, nullable=True)
    fiber = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)

    user = relationship("User", back_populates="entries")


class Database:
    _instance = None  # Singleton instance

    def __new__(cls):
        """Ensure only one instance of Database is created."""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        """Initialize database connection."""
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DB_PATH = os.path.join(BASE_DIR, "calories.db")

        self.engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
        Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add_user(self, username, daily_calorie_goal=2000):
        """Add a new user or return existing user ID."""
        try:
            existing_user = (
                self.session.query(User).filter_by(username=username).first()
            )
            if existing_user:
                return existing_user.id

            new_user = User(username=username, daily_calorie_goal=daily_calorie_goal)
            self.session.add(new_user)
            self.session.commit()
            return new_user.id
        except IntegrityError:
            self.session.rollback()
            return None

    def add_calorie_entry(self, user_id, food_data, timestamp=None):
        """Add a new calorie entry."""
        try:
            entry = CalorieEntry(
                user_id=user_id,
                food_name=food_data["food"],
                portion=food_data["portion"],
                calories=food_data["calories"],
                protein=food_data.get("protein"),
                carbs=food_data.get("carbohydrates"),
                fat=food_data.get("fat"),
                sugars=food_data.get("sugars"),
                fiber=food_data.get("fiber"),
                timestamp=timestamp or datetime.now(),
            )
            self.session.add(entry)
            self.session.commit()
            return entry.id
        except Exception as e:
            self.session.rollback()
            print(f"Error adding calorie entry: {e}")
            return None

    def get_calories_for_date(self, user_id, date):
        """Retrieve all calorie entries for a specific date."""
        try:
            return (
                self.session.query(CalorieEntry)
                .options(joinedload(CalorieEntry.user))
                .filter(
                    CalorieEntry.user_id == user_id,
                    CalorieEntry.timestamp >= date,
                    CalorieEntry.timestamp < date + timedelta(days=1),
                )
                .all()
            )
        except Exception as e:
            print(f"Error retrieving entries: {e}")
            return []

    def get_user_goal(self, user_id):
        """Retrieve the daily calorie goal of a user."""
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            return user.daily_calorie_goal if user else None
        except Exception as e:
            print(f"Error retrieving user goal: {e}")
            return None

    def update_user_goal(self, user_id, new_goal):
        """Update the daily calorie goal for a user."""
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if user:
                user.daily_calorie_goal = new_goal
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Error updating user goal: {e}")
            return False

    def delete_calorie_entry(self, entry_id):
        """Delete a calorie entry by ID."""
        try:
            entry = (
                self.session.query(CalorieEntry)
                .filter(CalorieEntry.id == entry_id)
                .first()
            )
            if entry:
                self.session.delete(entry)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Error deleting entry: {e}")
            return False
