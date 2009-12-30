from webob import Response

def homepage_view(request):
    app_context = request.app_context
    return Response("Hello World!")

