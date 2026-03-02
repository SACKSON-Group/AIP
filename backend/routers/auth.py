from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Supabase JWT token and return the user."""
    token = credentials.credentials

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase credentials not configured",
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": SUPABASE_ANON_KEY,
                },
                timeout=10.0,
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to reach Supabase: {str(e)}",
            )

    if response.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return response.json()


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "full_name": user.get("user_metadata", {}).get("full_name"),
        "phone": user.get("user_metadata", {}).get("phone"),
        "created_at": user.get("created_at"),
    }
