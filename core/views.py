from django.shortcuts import render
from django.shortcuts import redirect, render
from .models import Ventas
from .forms import VentasForm, DispForm
from datetime import datetime, timedelta, time
import random
import requests
import json

# Create your views here.

def index(request):
    data = {"VentasForm":VentasForm, "DispForm":DispForm}
    return render(request, "core/index.html", data)
