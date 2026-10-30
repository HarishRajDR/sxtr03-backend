from datetime import datetime
from typing import Annotated, Literal

import fastf1
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator
from pydantic_core import PydanticCustomError

load_dotenv()

DRIVERS_KEYS = [
    "DriverNumber",
    "FullName",
    "TeamName",
    "TeamColor",
    "ClassifiedPosition",
]

LAP_KEYS = [
    "DriverNumber",
    "Position",
    "LapNumber",
    "LapTime",
    "Sector1Time",
    "Sector2Time",
    "Sector3Time",
    "Compound",
    "TyreLife",
    "TrackStatus",
    "Deleted",
    "DeletedReason",
]

TELEMETRY_KEYS = [
    "RPM",
    "Speed",
    "nGear",
    "Throttle",
    "Brake",
    "DRS",
    "Distance",
    "Time",
]

origins = [
    "http://sxtr03.harishraj.in",
    "http://localhost:3000",
]

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    details = {
        "welcome": "This is SXTR//03",
        "description": "Backend for SXTR//03",
        "website": "https://sxtr03.harishraj.in",
        "author": "Harish Raj D R",
        "author-website": "https://www.harishraj.in",
        "email": "drharishrajdr@gmail.com",
    }

    return details


# Get the current year
current_year = datetime.now().year


class DriversParams(BaseModel):
    year: int = Field(ge=2018, le=current_year)
    round: str = Field()
    session: Literal[
        "Practice 1",
        "Practice 2",
        "Practice 3",
        "Sprint",
        "Sprint Shootout",
        "Sprint Qualifying",
        "Qualifying",
        "Race",
    ] = Field()


@app.get("/api/drivers")
def drivers(parameters: Annotated[DriversParams, Query()]):
    year = parameters.year
    round = parameters.round
    session = parameters.session

    loaded_session = fastf1.get_session(year, round, session)
    loaded_session.load(
        laps=True,
        telemetry=False,
        weather=False,
    )

    results = loaded_session.results[DRIVERS_KEYS].to_dict("records")

    for idx, driver in enumerate(results):
        driver_number = driver["DriverNumber"]
        laps = loaded_session.laps.pick_drivers(driver_number)[LAP_KEYS]

        # Replace NaT or NaN to null as they are not json compatible
        results[idx]["Laps"] = (
            laps.astype(object).where(pd.notna(laps), None).to_dict("records")
        )

    return {"data": results}


class TelemetryParams(DriversParams):
    driver1: str = Field()
    driver1Lap: int = Field()
    driver2: str | None = None
    driver2Lap: int | None = None

    @model_validator(mode="after")
    def validate_v3_v4(self):
        if self.driver2 is not None and self.driver2Lap is None:
            raise PydanticCustomError(
                "missing",
                "Field required",
            )
        return self


@app.get("/api/telemetry")
def telemetry(parameters: Annotated[TelemetryParams, Query()]):
    year = parameters.year
    round = parameters.round
    session = parameters.session

    driver1_telemetry_result = []
    driver2_telemetry_result = []

    driver1 = parameters.driver1
    driver1_lap = parameters.driver1Lap

    driver2 = parameters.driver2
    driver2_lap = parameters.driver2Lap

    loaded_session = fastf1.get_session(year, round, session)
    loaded_session.load()

    circuit_info = loaded_session.get_circuit_info()
    circuit_data = []

    if circuit_info is not None:
        circuit_data = (
            circuit_info.corners.astype(object)
            .where(pd.notna(circuit_info.corners), None)
            .to_dict("records")
        )

    driver1_lap_data = loaded_session.laps.pick_drivers(driver1).pick_laps(driver1_lap)
    driver1_car_data = driver1_lap_data.get_car_data().add_distance()

    driver1_telemetry_result = (
        driver1_car_data.astype(object)
        .where(pd.notna(driver1_car_data), None)[TELEMETRY_KEYS]
        .to_dict("records")
    )

    if driver2 is not None and driver2_lap is not None:
        driver2_lap_data = loaded_session.laps.pick_drivers(driver2).pick_laps(
            driver2_lap
        )
        driver2_car_data = driver2_lap_data.get_car_data().add_distance()

        driver2_telemetry_result = (
            driver2_car_data.astype(object)
            .where(pd.notna(driver2_car_data), None)[TELEMETRY_KEYS]
            .to_dict("records")
        )

        return {
            "driver1TelemetryData": driver1_telemetry_result,
            "driver2TelemetryData": driver2_telemetry_result,
            "cornerData": circuit_data,
        }

    return {
        "driver1TelemetryData": driver1_telemetry_result,
        "cornerData": circuit_data,
    }
