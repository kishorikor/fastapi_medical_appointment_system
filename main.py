from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

app = FastAPI()

# Home endpoint - returns welcome message
@app.get("/")
def home():
    return {"message": "Welcome to MediCare Clinic"}

# Static doctors dataset
doctors = [
    {"id": 1, "name": "Dr. Amit Sharma", "specialization": "Cardiologist", "fee": 800, "experience_years": 10, "is_available": True},
    {"id": 2, "name": "Dr. Priya Mehta", "specialization": "Dermatologist", "fee": 500, "experience_years": 6, "is_available": True},
    {"id": 3, "name": "Dr. Raj Verma", "specialization": "Pediatrician", "fee": 600, "experience_years": 8, "is_available": False},
    {"id": 4, "name": "Dr. Neha Kapoor", "specialization": "General", "fee": 300, "experience_years": 5, "is_available": True},
    {"id": 5, "name": "Dr. Suresh Iyer", "specialization": "Cardiologist", "fee": 900, "experience_years": 15, "is_available": True},
    {"id": 6, "name": "Dr. Anjali Singh", "specialization": "Dermatologist", "fee": 550, "experience_years": 7, "is_available": False}
]

# Appointment storage and counter
appointments = []
appt_counter = 1

# Request model for creating/updating appointment
class AppointmentRequest(BaseModel):
    patient_name: str = Field(..., min_length=2)
    doctor_id: int = Field(..., gt=0)
    date: str = Field(..., min_length=8)
    reason: str = Field(..., min_length=5)
    appointment_type: str = "in-person"
    senior_citizen: bool = False

# Helper function to find doctor by ID
def find_doctor(doctor_id):
    for doctor in doctors:
        if doctor["id"] == doctor_id:
            return doctor
    return None

# Helper function to calculate fee based on type and senior citizen discount
def calculate_fee(base_fee, appointment_type, senior_citizen):
    if appointment_type == "video":
        fee = base_fee * 0.8
    elif appointment_type == "emergency":
        fee = base_fee * 1.5
    else:
        fee = base_fee

    if senior_citizen:
        discounted_fee = fee * 0.85
        return fee, discounted_fee

    return fee, fee

# Helper function to filter doctors based on query params
def filter_doctors_logic(specialization, max_fee, min_experience, is_available):
    result = doctors

    if specialization is not None:
        result = [d for d in result if d["specialization"].lower() == specialization.lower()]

    if max_fee is not None:
        result = [d for d in result if d["fee"] <= max_fee]

    if min_experience is not None:
        result = [d for d in result if d["experience_years"] >= min_experience]

    if is_available is not None:
        result = [d for d in result if d["is_available"] == is_available]

    return result

# Helper function to find appointment by ID
def find_appointment(appointment_id):
    for appt in appointments:
        if appt["appointment_id"] == appointment_id:
            return appt
    return None

# Get all doctors
@app.get("/doctors")
def get_doctors():
    total = len(doctors)
    available_count = len([d for d in doctors if d["is_available"]])

    return {
        "total": total,
        "available_count": available_count,
        "data": doctors
    }

# Doctors summary statistics
@app.get("/doctors/summary")
def doctor_summary():
    total = len(doctors)
    available = len([d for d in doctors if d["is_available"]])

    most_experienced = max(doctors, key=lambda x: x["experience_years"])
    cheapest_fee = min(doctors, key=lambda x: x["fee"])["fee"]

    specialization_count = {}
    for d in doctors:
        spec = d["specialization"]
        specialization_count[spec] = specialization_count.get(spec, 0) + 1

    return {
        "total_doctors": total,
        "available_doctors": available,
        "most_experienced_doctor": most_experienced["name"],
        "cheapest_fee": cheapest_fee,
        "specialization_count": specialization_count
    }

# Filter doctors based on query parameters
@app.get("/doctors/filter")
def filter_doctors(
    specialization: str = Query(None),
    max_fee: int = Query(None),
    min_experience: int = Query(None),
    is_available: bool = Query(None)
):
    filtered = filter_doctors_logic(
        specialization,
        max_fee,
        min_experience,
        is_available
    )

    return {
        "total": len(filtered),
        "data": filtered
    }

# Search doctors by keyword
@app.get("/doctors/search")
def search_doctors(keyword: str):
    result = []

    for d in doctors:
        if keyword.lower() in d["name"].lower() or keyword.lower() in d["specialization"].lower():
            result.append(d)

    if not result:
        return {
            "message": "No doctors found for given keyword",
            "total_found": 0,
            "data": []
        }

    return {
        "total_found": len(result),
        "data": result
    }

# Sort doctors
@app.get("/doctors/sort")
def sort_doctors(sort_by: str = "fee", order: str = "asc"):
    valid_fields = ["fee", "name", "experience_years"]
    valid_orders = ["asc", "desc"]

    if sort_by not in valid_fields:
        return {"error": "Invalid sort_by value"}

    if order not in valid_orders:
        return {"error": "Invalid order value"}

    reverse = True if order == "desc" else False

    sorted_list = sorted(doctors, key=lambda x: x[sort_by], reverse=reverse)

    return {
        "sort_by": sort_by,
        "order": order,
        "total": len(sorted_list),
        "data": sorted_list
    }

# Paginate doctors list
@app.get("/doctors/page")
def paginate_doctors(page: int = 1, limit: int = 3):
    total = len(doctors)
    total_pages = (total + limit - 1) // limit

    if page < 1 or page > total_pages:
        return {"error": "Invalid page number"}

    start = (page - 1) * limit
    end = start + limit

    paginated_data = doctors[start:end]

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "data": paginated_data
    }

# Combined browse: search + sort + pagination
@app.get("/doctors/browse")
def browse_doctors(
    keyword: str = None,
    sort_by: str = "fee",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):
    result = doctors

    if keyword:
        result = [
            d for d in result
            if keyword.lower() in d["name"].lower()
            or keyword.lower() in d["specialization"].lower()
        ]

    reverse = True if order == "desc" else False
    result = sorted(result, key=lambda x: x[sort_by], reverse=reverse)

    total = len(result)
    total_pages = (total + limit - 1) // limit

    if page < 1 or page > total_pages:
        return {"error": "Invalid page number"}

    start = (page - 1) * limit
    end = start + limit

    paginated = result[start:end]

    return {
        "total": total,
        "page": page,
        "total_pages": total_pages,
        "data": paginated
    }

# Get doctor by ID
@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: int):
    for doctor in doctors:
        if doctor["id"] == doctor_id:
            return doctor

    return {"error": "Doctor not found"}

# Get all appointments
@app.get("/appointments")
def get_appointments():
    return {
        "total": len(appointments),
        "data": appointments
    }

# Create new appointment
@app.post("/appointments")
def create_appointment(request: AppointmentRequest):
    global appt_counter

    doctor = find_doctor(request.doctor_id)
    if not doctor:
        return {"error": "Doctor not found"}

    if not doctor["is_available"]:
        return {"error": "Doctor not available"}

    original_fee, final_fee = calculate_fee(
        doctor["fee"],
        request.appointment_type,
        request.senior_citizen
    )

    new_appointment = {
        "appointment_id": appt_counter,
        "patient": request.patient_name,
        "doctor_name": doctor["name"],
        "date": request.date,
        "type": request.appointment_type,
        "original_fee": original_fee,
        "final_fee": final_fee,
        "status": "scheduled"
    }

    appointments.append(new_appointment)
    appt_counter += 1

    return {
        "message": "Appointment booked successfully",
        "data": new_appointment
    }

# Search appointments by patient name
@app.get("/appointments/search")
def search_appointments(patient_name: str):
    result = []

    for appt in appointments:
        if patient_name.lower() in appt["patient"].lower():
            result.append(appt)

    if not result:
        return {
            "message": "No appointments found",
            "total": 0,
            "data": []
        }

    return {
        "total": len(result),
        "data": result
    }

# Sort appointments
@app.get("/appointments/sort")
def sort_appointments(sort_by: str = "final_fee"):
    valid_fields = ["final_fee", "date"]

    if sort_by not in valid_fields:
        return {"error": "Invalid sort field"}

    sorted_list = sorted(appointments, key=lambda x: x[sort_by])

    return {
        "sort_by": sort_by,
        "total": len(sorted_list),
        "data": sorted_list
    }

# Paginate appointments
@app.get("/appointments/page")
def paginate_appointments(page: int = 1, limit: int = 2):
    total = len(appointments)
    total_pages = (total + limit - 1) // limit

    if page < 1 or page > total_pages:
        return {"error": "Invalid page number"}

    start = (page - 1) * limit
    end = start + limit

    data = appointments[start:end]

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "data": data
    }

# Update appointment
@app.put("/appointments/{appointment_id}")
def update_appointment(appointment_id: int, request: AppointmentRequest):
    appt = find_appointment(appointment_id)

    if not appt:
        return {"error": "Appointment not found"}

    doctor = find_doctor(request.doctor_id)
    if not doctor:
        return {"error": "Doctor not found"}

    if not doctor["is_available"]:
        return {"error": "Doctor not available"}

    original_fee, final_fee = calculate_fee(
        doctor["fee"],
        request.appointment_type,
        request.senior_citizen
    )

    appt["patient"] = request.patient_name
    appt["doctor_name"] = doctor["name"]
    appt["date"] = request.date
    appt["type"] = request.appointment_type
    appt["original_fee"] = original_fee
    appt["final_fee"] = final_fee

    return {
        "message": "Appointment updated successfully",
        "data": appt
    }

# Delete appointment
@app.delete("/appointments/{appointment_id}")
def delete_appointment(appointment_id: int):
    for i, appt in enumerate(appointments):
        if appt["appointment_id"] == appointment_id:
            deleted = appointments.pop(i)
            return {
                "message": "Appointment deleted successfully",
                "data": deleted
            }

    return {"error": "Appointment not found"}

# Confirm appointment
@app.put("/appointments/{appointment_id}/confirm")
def confirm_appointment(appointment_id: int):
    appt = find_appointment(appointment_id)

    if not appt:
        return {"error": "Appointment not found"}

    appt["status"] = "confirmed"

    return {
        "message": "Appointment confirmed",
        "data": appt
    }

# Complete appointment
@app.put("/appointments/{appointment_id}/complete")
def complete_appointment(appointment_id: int):
    appt = find_appointment(appointment_id)

    if not appt:
        return {"error": "Appointment not found"}

    appt["status"] = "completed"

    return {
        "message": "Appointment completed",
        "data": appt
    }