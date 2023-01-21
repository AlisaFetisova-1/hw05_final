from django.core.paginator import Paginator

NUMBER_OF_OBJECTS = 10


def get_page_context(post_list, request):
    paginator = Paginator(post_list, NUMBER_OF_OBJECTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
