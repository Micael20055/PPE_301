from django.shortcuts import render

def home(request):
    return render(request, 'utilisateur/index.html')
def buy (request):
    return render(request, 'utilisateur/buy.html')
def blog ( request):
    return render(request, 'utilisateur/blog.html')
def contact ( request):
    return render(request, 'utilisateur/contact.html')
def about ( request):
    return render(request, 'utilisateur/about.html')
def index ( request):
    return render(request, 'utilisateur/index-2.html')
def properties ( request):
    return render(request, 'utilisateur/properties.html')
def property_details ( request):
    return render(request, 'utilisateur/property-details.html')
def rent ( request):
    return render(request, 'utilisateur/rent.html')
def view ( request):
    return render(request, 'utilisateur/view-list.html')