from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as T

from rehagoal_server_app.models import RehagoalUser, SimpleUser, Workflow


class RehagoalUserInline(admin.StackedInline):
    model = RehagoalUser
    can_delete = False


class UserAdmin(BaseUserAdmin):
    inlines = (RehagoalUserInline,)


class SimpleUserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (T('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name')
    list_filter = ()

    def get_queryset(self, request):
        qs = super(SimpleUserAdmin, self).get_queryset(request)  # type: QuerySet
        return qs.filter(is_staff=False, is_superuser=False)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(SimpleUser, SimpleUserAdmin)
admin.site.register(RehagoalUser)
admin.site.register(Workflow)
