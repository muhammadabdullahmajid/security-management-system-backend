from rout.client_routs import client
from rout.dashboard_routs import stat
from rout.duty_assignments_routs import dutyassignment
from rout.guard_routs import guard
from rout.inventory_routs import inventory_record
from rout.reports_routs import report
from rout.salary_routs import salaryrecord
from rout.search_routs import search
from rout.user_routs import auth
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import uvicorn

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(client, prefix="/client", tags=["Client"])
app.include_router(stat, prefix="/stat", tags=["stat"])
app.include_router(dutyassignment, prefix="/dutyassignment", tags=["Duty Assignments"])
app.include_router(guard, prefix="/guard", tags=["Guard"])
app.include_router(inventory_record, prefix="/inventory", tags=["Inventory"])
app.include_router(report, prefix="/reports", tags=["Reports"])
app.include_router(salaryrecord, prefix="/salaryrecord", tags=["Salaryrecord"])
app.include_router(search, prefix="/search", tags=["Search"])
app.include_router(auth, prefix="/auth", tags=["Authentication"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
