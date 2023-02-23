from internal.models import Project


def init_project_queryset(model, user):
    """
    Return an initial queryset of the provided `model`.

    If `user.is_staff = True`, returns all objects, otherwise only returns objects with `suppressed = False`.
    """
    if user.is_staff:
        qs = model.objects.all()
    else:
        qs = model.objects.filter(suppressed=False)
    return qs


def init_queryset(model, view_fields):
    qs = model.objects.select_related()

    if "suppressed" not in view_fields:
        qs = qs.filter(suppressed=False)

    return qs


def get_project_and_model(project_code):
    try:
        project = Project.objects.get(code=project_code)
        model = project.content_type.model_class()
        return project, model
    except Project.DoesNotExist:
        return None, None
