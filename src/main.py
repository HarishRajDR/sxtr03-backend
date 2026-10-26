from datetime import datetime
from typing import Annotated, Literal

import fastf1
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

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

app = FastAPI()


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
