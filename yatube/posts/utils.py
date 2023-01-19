from django.core.paginator import Paginator

NUMBER_OF_OBJECTS = 10


def get_page_context(queryset, request):
    paginator = Paginator(queryset, NUMBER_OF_OBJECTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'page_obj': page_obj,
    }
