from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field, computed_field
from fastapi.responses import JSONResponse
from typing import Annotated, Literal, Any, Dict
import json
import uuid


def load_data() -> Dict[str, dict]:
    try:
        with open("patients.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data(data: Dict[str, dict]) -> None:
    with open("patients.json", "w") as f:
        json.dump(data, f, indent=2)


app = FastAPI(
    title="Patient Management API",
    description="API to manage patient records",
    version="1.0.0"
)

class PatientCreate(BaseModel):
    name: Annotated[str, Field(..., min_length=2, max_length=100, examples=["Aarav Sharma"])]
    city: Annotated[str, Field(..., min_length=2, max_length=100, examples=["Delhi"])]
    age: Annotated[int, Field(..., ge=1, le=120, examples=[28])]
    gender: Annotated[Literal["Male", "Female", "Other"], Field(examples=["Male"])]
    height: Annotated[float, Field(..., gt=0.5, le=2.5, description="in meters", examples=[1.72])]
    weight: Annotated[float, Field(..., gt=10.0, le=300.0, description="in kg", examples=[68.5])]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "underweight"
        elif self.bmi < 25:
            return "normal"
        elif self.bmi < 30:
            return "overweight"
        else:
            return "obese"

class Patient(PatientCreate):
    id: str


@app.get("/")
def root():
    return {"message": "Patient Management API"}


@app.get("/about")
def about():
    return {
        "message": "REST API to manage patient records"
    }


@app.get("/patients")
def get_all_patients():
    data = load_data()
    return {
        "message": "All patients retrieved",
        "count": len(data),
        "patients": list(data.values())
    }


@app.get("/patients/sort")
def sort_patients(
    sort_by: Annotated[
        Literal["age", "height", "weight", "bmi"],
        Query(..., description="Field to sort by")
    ],
    order: Annotated[
        Literal["asc", "desc"],
        Query(description="Sort direction")
    ] = "asc"
):
    patients = load_data()
    patient_list = list(patients.values())

    reverse = order == "desc"

    def sort_key(p: dict) -> Any:
        if sort_by == "bmi":
            h = p.get("height", 0)
            w = p.get("weight", 0)
            return round(w / (h ** 2), 2) if h > 0 else 0
        return p.get(sort_by, 0) or 0

    sorted_patients = sorted(patient_list, key=sort_key, reverse=reverse)

    return {
        "message": f"Sorted by {sort_by} ({order})",
        "patients": sorted_patients
    }


@app.get("/patients/{patient_id}")
def get_patient(patient_id: Annotated[str, Path(examples=["A1B2C3D4"])]):
    data = load_data()
    patient = data.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.post("/patients", status_code=201, response_model=Patient)
def create_patient(patient_in: PatientCreate):
    patients = load_data()

    new_id = uuid.uuid4().hex[:8].upper()

    while new_id in patients:
        new_id = uuid.uuid4().hex[:8].upper()

    patient_dict = patient_in.model_dump()
    patient_dict["id"] = new_id

    patients[new_id] = patient_dict
    save_data(patients)

    return patient_dict


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)