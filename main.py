from fastapi import FastAPI
import json

def load_data():
    with open("patients.json", "r") as f:
        data = json.load(f)
        return data

app = FastAPI()

@app.get("/")
def hello():
    return{"message": "App to store patient data"}

@app.get("/about")
def about():
    return{
        "mesasge": "A fully functional API to manage your patient records"
    }


@app.get("/patients")
def patients():
    data = load_data()
    return{
        "mesasge": "Patient data retrieved sucessfully",
        "data": data
    }


