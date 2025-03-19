from rest_framework import serializers
from .models import MenuItem,Category,Cart,Order,OrderItem
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.utils import timezone

class CategorySerializer(serializers.ModelSerializer):

    def validate(self,attrs):
        attrs["slug"] = slugify(attrs["title"])
        return attrs

    class Meta:
        model = Category
        fields = ['id','title',"slug"]
        extra_kwargs = {
            "slug" : {"read_only":True}
        }


class MenuItemSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = MenuItem
        fields = ["id","title","price","featured","category","category_id"]

class CartSerializer(serializers.ModelSerializer):

    menu_id = serializers.IntegerField(write_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    unit_price=serializers.DecimalField(max_digits=6, decimal_places=2,source='menuitem.price', read_only=True)

    def validate(self,attrs):
        try:
            menu_item = MenuItem.objects.get(id=attrs.get("menu_id"))
        except MenuItem.DoesNotExist:
            raise serializers.ValidationError("Menu item not found")

        attrs["price"] = attrs["quantity"] * menu_item.price
        attrs["user"] = self.context['request'].user
        attrs["unit_price"] = menu_item.price
        attrs["menuitem_id"] = menu_item.id
        attrs.pop('menu_id', None)
        return attrs

    class Meta:
        model = Cart
        fields = ["id","user","menuitem","quantity","unit_price","price","menu_id"]
        extra_kwargs = {
            "price" : {"read_only":True},
            "user" : {"read_only":True}
        }

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id","order","menuitem","quantity","unit_price","price"]

class OrderSerializer(serializers.ModelSerializer):
    orderitem = OrderItemSerializer(many=True,read_only=True,source="orderitem_set")
    
    def validate(self,attrs):

        print(attrs)

        request_method = self.context["request"].method

        if request_method == "POST":
            attrs["date"]=timezone.now().date()
            attrs["status"] = False
            attrs["delivery_crew"] = None
        

        return attrs
    
    class Meta:
        model = Order
        fields = ["id","user","delivery_crew","status","total","date","orderitem"]

    def get_extra_kwargs(self):
        extra_kwargs = super().get_extra_kwargs()
        request_method = self.context["request"].method

        if request_method == "POST":
            extra_kwargs.update({
                "date" : {"read_only" : True},
                "delivery_crew" : {"read_only" : True},
                "status" : {"read_only" : True},
                "user" : {"read_only" : True},
                "total" : {"read_only" : True},
            })

        return extra_kwargs



class UserSerilializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','email']