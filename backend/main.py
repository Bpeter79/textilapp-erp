from fastapi import FastAPI
# 1. Be kell importálni a CORS middleware-t:
from fastapi.middleware.cors import CORSMiddleware
from routers import companies, projects, patterns, settlements

app = FastAPI(title="Optitex Textil ERP API")

# 2. Meg kell mondani a FastAPI-nak, hogy engedje be a frontendet:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Minden honlapot engedélyez (így a localhost:5173-at is)
    allow_credentials=True,
    allow_methods=["*"],  # Engedélyezi a GET, POST, PUT, DELETE parancsokat
    allow_headers=["*"],
)

# A többi kódod (app.include_router...) változatlanul marad alatta:
app.include_router(companies.router)
# ... a többi routered ...