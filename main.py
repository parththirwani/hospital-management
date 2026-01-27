from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional, Dict
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
    description="API for managing patient records with auto-generated UUIDs",
    version="1.0"
)


class PatientCreate(BaseModel):
    name: Annotated[str, Field(..., min_length=2, examples=["Aarav Sharma"])]
    city: Annotated[str, Field(..., min_length=2, examples=["Delhi"])]
    age: Annotated[int, Field(..., ge=1, le=120, examples=[28])]
    gender: Annotated[Literal["male", "female", "others"], Field(..., examples=["male"])]
    height: Annotated[float, Field(..., gt=0.4, le=2.5, description="in meters", examples=[1.72])]
    weight: Annotated[float, Field(..., gt=10.0, le=300.0, description="in kg", examples=[68.5])]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif self.bmi < 25:
            return "Normal"
        elif self.bmi < 30:
            return "Overweight"   # ← fixed: was "Normal" before
        else:
            return "Obese"


class Patient(PatientCreate):
    id: str


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    age: Optional[Annotated[int, Field(ge=1, le=120)]] = None
    gender: Optional[Literal["male", "female", "others"]] = None
    height: Optional[Annotated[float, Field(gt=0.4, le=2.5)]] = None
    weight: Optional[Annotated[float, Field(gt=10.0, le=300.0)]] = None


@app.get("/")
def hello():
    return {"message": "Patient Management System API"}


@app.get("/about")
def about():
    return {"message": "A fully functional API to manage your patient records"}


@app.get("/view")
def view_all():
    data = load_data()
    return {
        "count": len(data),
        "patients": list(data.values())
    }


@app.get("/patient/{patient_id}")
def view_patient(patient_id: Annotated[str, Path(examples=["A1B2C3D4"])]):
    data = load_data()
    patient = data.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.get("/sort")
def sort_patients(
    sort_by: Annotated[
        Literal["height", "weight", "bmi"],
        Query(..., description="Field to sort by")
    ],
    order: Annotated[
        Literal["asc", "desc"],
        Query(description="Sort direction")
    ] = "asc"
):
    data = load_data()
    patients = list(data.values())

    reverse = order == "desc"

    def sort_key(p: dict):
        if sort_by == "bmi":
            h = p.get("height", 0)
            w = p.get("weight", 0)
            return round(w / (h ** 2), 2) if h > 0 else 0
        return p.get(sort_by, 0)

    sorted_patients = sorted(patients, key=sort_key, reverse=reverse)

    return {
        "sorted_by": f"{sort_by} ({order})",
        "patients": sorted_patients
    }


@app.post("/create", status_code=201)
def create_patient(patient: PatientCreate):
    data = load_data()

    new_id = uuid.uuid4().hex[:8].upper()

    while new_id in data:
        new_id = uuid.uuid4().hex[:8].upper()

    patient_dict = patient.model_dump()
    patient_dict["id"] = new_id

    data[new_id] = patient_dict
    save_data(data)

    return JSONResponse(
        status_code=201,
        content={
            "message": "Patient created successfully",
            "patient_id": new_id,
            "patient": patient_dict
        }
    )


@app.put("/edit/{patient_id}")
def update_patient(patient_id: str, patient_update: PatientUpdate):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")

    existing = data[patient_id]

    update_data = patient_update.model_dump(exclude_unset=True)
    existing.update(update_data)

    try:
        full_patient = Patient(**existing)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Validation error after update: {str(e)}")

    data[patient_id] = full_patient.model_dump(exclude={"id"})

    save_data(data)

    return {"message": "Patient updated successfully", "patient_id": patient_id}


@app.delete("/delete/{patient_id}")
def delete_patient(patient_id: str):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")

    del data[patient_id]
    save_data(data)

    return {"message": "Patient deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)