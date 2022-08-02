from rest_framework import serializers
from .models import RehagoalUser, Workflow
from .validators import validate_workflow_content_size


class FilterRelatedMixin(object):
    def __init__(self, *args, **kwargs):
        super(FilterRelatedMixin, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field, serializers.RelatedField):
                method_name = 'filter_%s' % name
                try:
                    func = getattr(self, method_name)
                except AttributeError:
                    pass
                else:
                    field.queryset = func(field.queryset)
            if isinstance(field, serializers.ManyRelatedField):
                method_name = 'filter_%s' % name
                try:
                    func = getattr(self, method_name)
                except AttributeError:
                    pass
                else:
                    field.child_relation.queryset = func(field.child_relation.queryset)


class RehagoalUserSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = RehagoalUser
        fields = ('id', 'username')


class WorkflowSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    owner = serializers.HyperlinkedRelatedField(read_only=True, view_name='rehagoaluser-detail')
    content = serializers.FileField(validators=[validate_workflow_content_size])

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(WorkflowSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = Workflow
        fields = ('id', 'owner', 'content')
