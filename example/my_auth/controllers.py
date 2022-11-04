from my_auth.models import CustomUser

from gojira import permissions
from gojira.generics.mixins import ListMixin
from gojira.generics.routes import GenericController
from gojira.generics.serializers import ModelSerializer


class UserSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = "__all__"


class ProtectedView(ListMixin, GenericController):
    prefix = "users"
    permission_classes = (permissions.IsAuthenticated,)
    model = CustomUser
    serializer_map = {"list": UserSerializer}
