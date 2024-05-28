from django.http import  JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from razorpay import Customer
from fari_project import settings
from shop.form import CustomUserForm
from . models import *
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.views import LoginView, LogoutView
import json
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from .models import Cart, Order



def order_success(request):
    return render(request, 'shop/order_success.html')

def home(request):
  products=Product.objects.filter(trending=1)
  return render(request,"shop/index.html",{"products":products})
 
def favviewpage(request):
  if request.user.is_authenticated:
    fav=Favourite.objects.filter(user=request.user)
    return render(request,"shop/fav.html",{"fav":fav})
  else:
    return render(request,"shop/fav.html")
 
def remove_fav(request,fid):
  item=Favourite.objects.get(id=fid)
  item.delete()
  return redirect("/favviewpage")
 
 
 
 
def cart_page(request):
  if request.user.is_authenticated:
    cart=Cart.objects.filter(user=request.user)
    return render(request,"shop/cart.html",{"cart":cart})
  else:
    return render(request,"shop/cart.html")
 
def remove_cart(request,cid):
  cartitem=Cart.objects.get(id=cid)
  cartitem.delete()
  return redirect("/cart")
 
 
def fav_page(request):
   if request.headers.get('x-requested-with')=='XMLHttpRequest':
    if request.user.is_authenticated:
      data=json.load(request)
      product_id=data['pid']
      product_status=Product.objects.get(id=product_id)
      if product_status:
         if Favourite.objects.filter(user=request.user.id,product_id=product_id):
          return JsonResponse({'status':'Product Already in Favourite'}, status=200)
         else:
          Favourite.objects.create(user=request.user,product_id=product_id)
          return JsonResponse({'status':'Product Added to Favourite'}, status=200)
    else:
      return JsonResponse({'status':'Login to Add Favourite'}, status=200)
   else:
    return JsonResponse({'status':'Invalid Access'}, status=200)
 
 
def add_to_cart(request):
   if request.headers.get('x-requested-with')=='XMLHttpRequest':
    if request.user.is_authenticated:
      data=json.load(request)
      product_qty=data['product_qty']
      product_id=data['pid']
      #print(request.user.id)
      product_status=Product.objects.get(id=product_id)
      if product_status:
        if Cart.objects.filter(user=request.user.id,product_id=product_id):
          return JsonResponse({'status':'Product Already in Cart'}, status=200)
        else:
          if product_status.quantity>=product_qty:
            Cart.objects.create(user=request.user,product_id=product_id,product_qty=product_qty)
            return JsonResponse({'status':'Product Added to Cart'}, status=200)
          else:
            return JsonResponse({'status':'Product Stock Not Available'}, status=200)
    else:
      return JsonResponse({'status':'Login to Add Cart'}, status=200)
   else:
    return JsonResponse({'status':'Invalid Access'}, status=200)
 
def logout_page(request):
  if request.user.is_authenticated:
    logout(request)
    messages.success(request,"Logged out Successfully")
  return redirect("/")
 
 
def login_page(request):
  if request.user.is_authenticated:
    return redirect("/")
  else:
    if request.method=='POST':
      name=request.POST.get('username')
      pwd=request.POST.get('password')
      user=authenticate(request,username=name,password=pwd)
      if user is not None:
        login(request,user)
        messages.success(request,"Logged in Successfully")
        return redirect("/")
      else:
        messages.error(request,"Invalid User Name or Password")
        return redirect("/login")
    return render(request,"shop/login.html")
 
def register(request):
  form=CustomUserForm()
  if request.method=='POST':
    form=CustomUserForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request,"Registration Success You can Login Now..!")
      return redirect('/login')
  return render(request,"shop/register.html",{'form':form})
 
 
def collections(request):
  catagory=Catagory.objects.filter(status=0)
  return render(request,"shop/collections.html",{"catagory":catagory})
 
def collectionsview(request,name):
  if(Catagory.objects.filter(name=name,status=0)):
      products=Product.objects.filter(category__name=name)
      return render(request,"shop/products/index.html",{"products":products,"category_name":name})
  else:
    messages.warning(request,"No Such Catagory Found")
    return redirect('collections')
 
@login_required
def product_details(request,cname,pname):
    if(Catagory.objects.filter(name=cname,status=0)):
      if(Product.objects.filter(name=pname,status=0)):
        products=Product.objects.filter(name=pname,status=0).first()
        return render(request,"shop/products/product_details.html",{"products":products})
      else:
        messages.error(request,"No Such Produtct Found")
        return redirect('collections')
    else:
      messages.error(request,"No Such Catagory Found")
      return redirect('collections') 


def checkout(request):
    # Retrieve the items from the cart
    cart_items = Cart.objects.filter(user=request.user)
    total_amount = sum(item.total_cost for item in cart_items)
    
    if request.method == 'POST':
        # Process the checkout form and create the order
        order = Order.objects.create(user=request.user, total_amount=total_amount)
        for item in cart_items:
            order.order_items.create(product=item.product, quantity=item.product_qty, amount=item.total_cost)
        
        # Clear the cart after successful checkout
        cart_items.delete()
        
        return redirect('order_success')  # Redirect to the order success page

    return render(request, 'shop/checkout.html', {'cart_items': cart_items, 'total_amount': total_amount})

@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'shop/profile.html', {'orders': orders})

def place_order(request):
    if request.method == 'POST':
        # Process the order
        # Save order to database

        # Redirect to the confirmation page
        return redirect('payment')

def confirm_order(request):
    # Retrieve data from session or database to display in confirmation page
    # For example, you can retrieve order details here

    if request.method == 'POST':
        # If user confirms the order, proceed to payment page
        return redirect('order_success')

    return render(request, 'shop/payment.html')

def payment(request):
    if 'id' in request.session:
        session_id = request.session['id']
        user = Customer.objects.get(id=session_id)
        cart = Cart.objects.filter(UserID=user)
        result = sum(item.Price for item in cart)  # Use sum() to calculate result

        if request.method == 'POST':
            cardnum = request.POST.get('CardNumber')  # Use get() to safely get form data
            expiry = request.POST.get('expirydate')
            cvv = request.POST.get('cvv')
            Payment.objects.create(CardNumber=cardnum, cvv=cvv, expiry=expiry, PaidUser=user.UserName)

            # Redirect to order_success page after processing the payment
            return redirect('order_success')

        return render(request, "shop/payment.html", {'result': result, 'user': user})

    return render(request, "shop/payment.html")