from fastapi import APIRouter
from my_auth.models import CustomUser

from example.my_auth.controllers import ProtectedView
from gojira.generics.routes import GenericRouter

router = APIRouter()

routes = GenericRouter(router)
routes.register(ProtectedView)


@router.post("/users", response_model=CustomUser)
async def create_user(user: CustomUser):
    return await user.save()
