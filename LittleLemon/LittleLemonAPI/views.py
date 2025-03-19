from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status,generics
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from .models import *
from .serializers import *
from .permissions import IsManager,IsEmployee
from django.shortcuts import  get_object_or_404
from django.contrib.auth.models import Group, User
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


# Create your views here.

class CategoriesView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        permission_clases = []
        if self.request.method != "GET":
            permission_clases = [IsAuthenticated]

        return [permission() for permission in permission_clases]

class MenuItemsView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    search_fields = ['category__title']
    ordering_fields = ['price', 'inventory']


    def get_permissions(self):
        permission_clases = []
        if self.request.method != "GET":
            permission_clases = [IsAuthenticated,IsManager]

        return [permission() for permission in permission_clases]
    
class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        permission_clases = []
        if self.request.method != "GET":
            permission_clases = [IsAuthenticated,IsManager]

        return [permission() for permission in permission_clases]
    
class GroupsManagerView(APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    def get_permissions(self):
        permission_clases = [IsAuthenticated,IsManager]
        return [permission() for permission in permission_clases]

    def post(self,request):
        user = get_object_or_404(User,username=request.data["username"])
        username=request.data["username"]
        if user.groups.filter(name="Manager").exists():
                return Response({"message": f"User {username} is already in the Managers group."},
                                status=status.HTTP_200_OK)
        managers = Group.objects.get(name="Manager")
        managers.user_set.add(user)
        return Response({"message": f"user {username} added to Manager group"},status=status.HTTP_200_OK)
    
    def get(self,request):
        users = User.objects.all().filter(groups__name="Manager")
        items = UserSerilializer(users,many=True)
        return Response(items.data)
    
    def delete(self,request,pk):
        user = get_object_or_404(User,id=pk)
        username=user.username
        if not user.groups.filter(name="Manager").exists():
                return Response({"message": f"User {username} does not exist in the Managers group."},
                                status=status.HTTP_200_OK)
        managers = Group.objects.get(name="Manager")
        managers.user_set.remove(user)
        return Response({"message": f"user {username} removed from Manager group"},status=status.HTTP_200_OK)

class GroupsDeliveryCrewView(APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    def get_permissions(self):
        permission_clases = [IsAuthenticated,IsManager]
        return [permission() for permission in permission_clases]

    def post(self,request):
        user = get_object_or_404(User,username=request.data["username"])
        username=request.data["username"]
        if user.groups.filter(name="Delivery crew").exists():
                return Response({"message": f"User {username} is already in the Delivery crew group."},
                                status=status.HTTP_200_OK)
        dcs = Group.objects.get(name="Delivery crew")
        dcs.user_set.add(user)
        return Response({"message": f"user {username} added to Delivery crew group"},status=status.HTTP_200_OK)
    
    def get(self,request):
        users = User.objects.all().filter(groups__name="Delivery crew")
        items = UserSerilializer(users,many=True)
        return Response(items.data)
    
    def delete(self,request,pk):
        user = get_object_or_404(User,id=pk)
        username=user.username
        if not user.groups.filter(name="Delivery crew").exists():
                return Response({"message": f"User {username} does not exist in the Delivery crew group."},
                                status=status.HTTP_200_OK)
        dcs = Group.objects.get(name="Delivery crew")
        dcs.user_set.remove(user)
        return Response({"message": f"user {username} removed from Delivery crew group"},status=status.HTTP_200_OK)
    
class CartView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    def get_permissions(self):
        permission_clases = [IsAuthenticated]
        return [permission() for permission in permission_clases]
    
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def get_queryset(self):
         return Cart.objects.all().filter(user=self.request.user)
    
    def delete(self,request, *args, **kwargs):
         Cart.objects.all().filter(user=self.request.user).delete()
         return Response({"message": "All elements deleted from cart"},status=status.HTTP_200_OK)
         
class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_permissions(self):
        permission_clases = [IsAuthenticated]
        if self.request.method != "GET":
            permission_clases.append(IsEmployee)
        if self.request.method == "DELETE" or self.request.method == "PUT":
            permission_clases.append(IsManager)
        return [permission() for permission in permission_clases]
    
    def update(self, request, *args, **kwargs):
        if request.user.groups.filter(name="Manager").exists() or args[0] == True:
            return super().update(request, *args, **kwargs)
        else:
            return Response({"message": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        
    def partial_update(self, request, pk, *args, **kwargs):
        order = get_object_or_404(Order,id=pk)
        if request.user.groups.filter(name="Delivery crew").exists() and order.delivery_crew == request.user:
            updated_fields = request.data.keys()
            if any(field != 'status' for field in updated_fields):
                return Response({"message": "You can only update the 'status' field."}, status=status.HTTP_400_BAD_REQUEST)
            if "status" not in request.data:
                return Response({"message": "You can only update the 'status' field."}, status=status.HTTP_400_BAD_REQUEST)
            return super().partial_update(request, True)
            
        elif request.user.groups.filter(name="Manager").exists():
            return super().partial_update(request, *args, **kwargs)
        else:
            return Response({"message": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)

    def get(self, request,pk):
        order = get_object_or_404(Order,id=pk)

        if order.user != self.request.user and not self.request.user.groups.filter(name="Manager").exists():
            return Response({"message": "You do not have permission to access this order."}, status=status.HTTP_403_FORBIDDEN)
        
        order_items = OrderItem.objects.filter(order=order)
        serializer = OrderItemSerializer(order_items, many=True)
        return Response(serializer.data)
    

class OrderView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    
    search_fields = ['delivery_crew__id']
    ordering_fields = ['total', 'date']


    def get_permissions(self):
        permission_clases = [IsAuthenticated]
        return [permission() for permission in permission_clases]

    def get_queryset(self):
        user = self.request.user
        if user.groups.count() == 0:
            return Order.objects.all().filter(user = user)
        elif user.is_superuser or user.groups.filter(name="Manager").exists():
            return Order.objects.all()
        elif user.groups.filter(name="Delivery crew").exists():
            return Order.objects.all().filter(delivery_crew = user)
            
    def create(self, request, *args, **kwargs):

        def get_total_price(user):
            total = 0
            items = Cart.objects.all().filter(user=user)
            for item in items.values():
                total += item["price"]
            return total

        menuitem_count = Cart.objects.all().filter(user=self.request.user).count()
        if menuitem_count == 0:
            return Response({"message":"no items in cart"})
        
        data = request.data.copy()
        total = get_total_price(self.request.user)
        data["total"] = total
        data["user"] = self.request.user.id
        order_serializer = OrderSerializer(context={'request':request},data=data)

        print(order_serializer.is_valid())

        if order_serializer.is_valid():

            order = order_serializer.save(user = self.request.user, 
                                          total = total)

            items = Cart.objects.all().filter(user = self.request.user)

            for item in items.values():
                orderitem = OrderItem(
                    order = order,
                    menuitem_id = item["menuitem_id"],
                    quantity = item["quantity"],
                    price = item["price"],
                    unit_price = item["unit_price"]
                )
                orderitem.save()

            Cart.objects.all().filter(user = self.request.user).delete()

            return Response(order_serializer.data)
        
        print(order_serializer.errors)
        
        return Response({"message":"something failed"})
