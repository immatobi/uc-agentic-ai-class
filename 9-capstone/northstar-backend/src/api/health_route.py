from fastapi import APIRouter

router = APIRouter()

@router.post("/v1")
def base_health():
    return {
        "error": False,
        "errors": [],
        "data": {
            "name": "Northstar CSA API",
            "version": "1.0.0",
            "status": "OK"
        },
        "message": "successful",
        "status": 200
    }

@router.post("/v1/health")
def health():
    return {
        "error": False,
        "errors": [],
        "data": {
            "name": "Northstar CSA API",
            "version": "1.0.0",
            "status": "OK"
        },
        "message": "successful",
        "status": 200
    }