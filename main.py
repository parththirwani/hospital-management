from fastapi import FastAPI, HTTPException, Path, Query
import json

def load_data():
    with open("patients.json", "r") as f:
        data = json.load(f)
    return data

app = FastAPI()

@app.get("/")
def hello():
    return {"message": "App to store patient data"}

@app.get("/about")
def about():
    return {"message": "A fully functional API to manage your patient records"}  


@app.get("/patients")
def getPatients():
    data = load_data()
    return {
        "message": "Patient data retrieved successfully",   
        "data": data
    }

@app.get("/patients/sort")
def sortPatients(
    sort_by: str = Query(..., description="Sort on the basis of height, weight, bmi"),
    order: str = Query("asc", description="Sort by asc or desc order")
):
    valid_fields = ["height", "weight", "bmi"]   

    if sort_by not in valid_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid field. Choose one of: {valid_fields}"
        )

    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid order. Use 'asc' or 'desc'"
        )

    data = load_data()
    reverse = order == "desc"

    sorted_data = sorted(
        data.values(),                          
        key=lambda x: x.get(sort_by, 0),
        reverse=reverse
    )

    return {
        "message": "Sorted data fetched successfully",
        "data": sorted_data                      
    }

@app.get("/patients/{patient_id}")
def getPatient(patient_id: str = Path(..., description="ID of the patient in DB", example="P001")):
    data = load_data()
    if patient_id in data:
        return data[patient_id]
    else:
        raise HTTPException(status_code=404, detail="Patient data not found")