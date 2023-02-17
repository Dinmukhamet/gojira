from fastapi import APIRouter

from example.my_auth.controllers import ProtectedView
from gojira.generics.mixins import has_permissions
from gojira.generics.routes import GenericRouter
from gojira.permissions import IsAuthenticated

from .models import CustomUser

router = APIRouter()

routes = GenericRouter(router)
routes.register(ProtectedView)


@router.post("/users", response_model=CustomUser)
@has_permissions(permission_classes=(IsAuthenticated,))
async def create_user(user: CustomUser):
    return await user.save()
