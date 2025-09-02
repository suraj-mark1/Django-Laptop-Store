from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from bapp.models import Laptop  # adjust import if Laptop is in another app

def chatbot_response(request):
    query = request.GET.get("q", "").lower()
    laptops = []

    if "business" in query:
        laptops = Laptop.objects.filter(price__gte=60000)
    elif "gaming" in query:
        laptops = Laptop.objects.filter(ram__icontains="16")
    elif "budget" in query:
        laptops = Laptop.objects.filter(price__lte=40000)
    elif "premium" in query:
        laptops = Laptop.objects.filter(price__gte=100000)
    elif "ssd" in query:
        laptops = Laptop.objects.filter(ssd__isnull=False).exclude(ssd="")
    else:
        return JsonResponse({"reply": "Sorry, I couldn’t find anything for that requirement."})

    # prepare response
    results = [
        {
            "name": l.name,
            "price": l.price,
            "url": f"/laptop/{l.id}/"
        }
        for l in laptops[:5]  # show max 5 results
    ]
    return JsonResponse({"reply": "Here are some options:", "laptops": results})
