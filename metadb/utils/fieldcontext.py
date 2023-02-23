from django.contrib.contenttypes.models import ContentType


class FieldContext:
    def __init__(self, field, model, content_type):
        self.field = field
        self.model = model
        self.content_type = content_type


def get_field_contexts(model):
    content_type = ContentType.objects.get_for_model(model)
    field_contexts = {
        field.name: FieldContext(
            field=field.name,
            model=model,
            content_type=content_type,
        )
        for field in model._meta.get_fields()
    }
    models = [model] + model._meta.get_parent_list()

    # Starting from the grandest parent model
    # Record which fields belong to which model in the inheritance hierarchy
    for m in reversed(models):
        content_type = ContentType.objects.get_for_model(m)

        for field in m._meta.get_fields(include_parents=False):
            if field.name in field_contexts:
                field_contexts[field.name] = FieldContext(
                    field=field.name,
                    model=m,
                    content_type=content_type,
                )

    return field_contexts
