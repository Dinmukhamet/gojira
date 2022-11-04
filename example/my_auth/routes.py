from fastapi import APIRouter
from my_auth.models import CustomUser

router = APIRouter()


@router.post("/users", response_model=CustomUser)
async def create_user(user: CustomUser):
    return await user.save()
