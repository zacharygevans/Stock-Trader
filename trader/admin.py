from django.contrib import admin
from trader.models import User
from trader.models import Stock
from trader.models import Transaction

# Register your models here.
admin.site.register(User)
admin.site.register(Stock)
admin.site.register(Transaction)