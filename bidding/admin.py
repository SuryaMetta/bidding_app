from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Auction, Bid, Wallet

admin.site.register(Auction)  # Register the Auction model
admin.site.register(Bid)  # Register the Bid model
admin.site.register(Wallet) 