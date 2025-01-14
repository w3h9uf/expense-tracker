from fastapi import FastAPI
from app.api.routes import auth, users, transactions


app = FastAPI()

# Include routes
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])

@app.get("/")
def read_root():
    return {"message": "Expense Tracker API is running"}
