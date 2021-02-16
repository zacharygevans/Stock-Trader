from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=1000)


class Stock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    quantity = models.IntegerField()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.quantity == 0:
            self.delete()


class Transaction(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='transactions')
    price = models.DecimalField(max_digits=20, decimal_places=2)
    quantity = models.IntegerField()
    datetime = models.DateTimeField(auto_now_add=True)
