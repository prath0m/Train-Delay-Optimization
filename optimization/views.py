from django.shortcuts import render

# Create your views here.


def index(request):
    """View that renders the hello world template"""
    return render(request, 'index.html')
