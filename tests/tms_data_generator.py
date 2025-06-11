"""
Generate and seed MongoDB with dummy user and time log data.
"""

from datetime import date, timedelta
from typing import List

from faker import Faker
from pydantic import ValidationError
from pymongo.errors import PyMongoError

from time_management_system.database import DBClient
from time_management_system.logger import get_logger
from time_management_system.schemas import TimeLogModel, UserModel


class TMSDataGenerator:
    """
    Class to generate and seed MongoDB with dummy user and time log data using Faker.
    """
    TIMELOGS_PER_USER = 10
    DEPARTMENTS = [
        "Compositing", "Lighting", "Modeling", "Rigging", "Animation", "FX", "Matte Painting", "Layout",
        "Matchmove", "Pipeline", "Editorial", "Production", "IT", "Prodtech", "Asset Management", "Lookdev",
        "Groom", "Texturing", "Environments", "Rendering", "Color Grading", "Art Department", "Previs", "Story"
    ]
    SITES = ["Hyderabad", "London", "Sydney"]

    def __init__(self):
        self.fake = Faker()
        self.logger = get_logger(self.__class__.__name__)
        self.db = DBClient()

    def generate_users(self) -> List[dict]:
        """Generate a list of user dictionaries with realistic fake data."""
        users = []
        for user_index in range(1, 502):
            user = {
                "employee_id": f"E{user_index:03d}",
                "full_name": self.fake.name(),
                "email": self.fake.unique.email(),
                "department": self.fake.random_element(self.DEPARTMENTS),
                "site": self.fake.random_element(self.SITES),
                "active": user_index % 2 == 0,
            }
            users.append(user)
        return users

    def generate_timelogs(self, users: List[dict]) -> List[dict]:
        """Generate a list of time log dictionaries for each user with realistic fake data."""
        timelogs = []
        for user in users:
            for log_index in range(self.TIMELOGS_PER_USER):
                log_date = date(2025, 6, 1) + timedelta(days=log_index)
                login_hour = self.fake.random_int(min=7, max=10)
                logout_hour = login_hour + self.fake.random_int(min=7, max=10)
                login_time = f"{login_hour:02d}:{self.fake.random_int(min=0, max=59):02d}"
                logout_time = f"{logout_hour:02d}:{self.fake.random_int(min=0, max=59):02d}"
                active_hours = round(
                    (logout_hour + self.fake.random_int(min=0, max=59) / 60)
                    - (login_hour + self.fake.random_int(min=0, max=59) / 60),
                    1,
                )
                timelog = {
                    "employee_id": user["employee_id"],
                    "date": str(log_date),  # Ensure date is a string for MongoDB
                    "hostname": self.fake.hostname(),
                    "os": self.fake.random_element(["Linux", "Windows", "macOS"]),
                    "login_time": login_time,
                    "logout_time": logout_time,
                    "active_hours": active_hours,
                }
                timelogs.append(timelog)
        return timelogs

    def seed_users(self, user_rows: List[dict]) -> None:
        """Insert users into the database, ensuring uniqueness and validation."""
        for user_row in user_rows:
            try:
                user = UserModel(**user_row)
                if self.db.find_one("users", {"employee_id": user.employee_id}):
                    self.logger.info(f"User with employee_id {user.employee_id} already exists. Skipping.")
                    continue
                self.db.insert_one("users", user.model_dump())
                self.logger.info(f"Inserted user: {user.employee_id}")
            except ValidationError as validation_exc:
                self.logger.error(f"Validation failed for user {user_row}: {validation_exc}")
            except PyMongoError as mongo_exc:
                self.logger.error(f"MongoDB error inserting user {user_row}: {mongo_exc}")
            except KeyError as key_exc:
                self.logger.error(f"Missing field {key_exc} in user row: {user_row}")

    def seed_timelogs(self, timelog_rows: List[dict]) -> None:
        """Insert time logs into the database, ensuring validation."""
        for timelog_row in timelog_rows:
            try:
                # Convert string date to date for Pydantic model
                if isinstance(timelog_row["date"], str):
                    timelog_row["date"] = date.fromisoformat(timelog_row["date"])
                timelog = TimeLogModel(
                    employee_id=timelog_row["employee_id"],
                    date=timelog_row["date"],
                    hostname=timelog_row["hostname"],
                    os=timelog_row["os"],
                    login_time=timelog_row["login_time"],
                    logout_time=timelog_row["logout_time"],
                    active_hours=float(timelog_row["active_hours"]),
                )
                self.db.insert_one("time_logs", timelog.model_dump(mode="json"))
                self.logger.info(f"Inserted time log for {timelog.employee_id} on {timelog.date}")
            except ValidationError as validation_exc:
                self.logger.error(f"Validation failed for time log {timelog_row}: {validation_exc}")
            except PyMongoError as mongo_exc:
                self.logger.error(f"MongoDB error inserting time log {timelog_row}: {mongo_exc}")
            except KeyError as key_exc:
                self.logger.error(f"Missing field {key_exc} in time log row: {timelog_row}")
            except ValueError as value_exc:
                self.logger.error(f"Value error in time log row {timelog_row}: {value_exc}")

    def run(self) -> None:
        """Generate fake data and seed the MongoDB database with users and time logs."""
        users = self.generate_users()
        timelogs = self.generate_timelogs(users)
        self.seed_users(users)
        self.seed_timelogs(timelogs)
        self.db.close_connection()
        self.logger.info("Database seeding complete.")


def main() -> None:
    seeder = TMSDataGenerator()
    seeder.run()


if __name__ == "__main__":
    main()
