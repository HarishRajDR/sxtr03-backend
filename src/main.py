from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
  details = {
    "welcome": "This is SXTR//03",
    "description": "Backend for SXTR//03",
    "website": "https://sxtr03.harishraj.in",
    "author": "Harish Raj D R",
    "author-website": "https://www.harishraj.in",
    "email": "drharishrajdr@gmail.com"
  }
  
  return details
