from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from .permissions import IsOwnerOrReadOnly, IsAdminOrDenyList
from .models import RehagoalUser, Workflow
from .serializers import RehagoalUserSerializer, WorkflowSerializer


class RehagoalUserViewSet(ReadOnlyModelViewSet):
    """
    retrieve:
    Return the given user.

    list:
    Return a list of all registered users.

    create:
    Create a new user.

    update:
    Update the given user.

    delete:
    Delete a registered user.
    """
    queryset = RehagoalUser.objects.all().order_by('-user__date_joined')
    serializer_class = RehagoalUserSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly, IsAdminOrDenyList)


class WorkflowViewSet(ModelViewSet):
    """
    retrieve:
    Return the given RehaGoal workflow.

    list:
    Return a list of all RehaGoal workflows visible to the authenticated user.

    create:
    Create a new RehaGoal workflow.

    update:
    Update the given RehaGoal workflow.

    partial_update:
    Update the given RehaGoal workflow (subset of available fields).

    delete:
    Delete an existing RehaGoal workflow.
    """
    serializer_class = WorkflowSerializer
    queryset = Workflow.objects.all()
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or self.action == "retrieve":
            return Workflow.objects.all()
        return Workflow.objects.filter(owner=user.rehagoal_user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user.rehagoal_user)
