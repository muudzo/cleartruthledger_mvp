from fastapi import APIRouter

# Old transactions router is deprecated.
# Will be replaced by ingestion wiring in Phase 4.
router = APIRouter(prefix="/api/transactions", tags=["transactions"])
