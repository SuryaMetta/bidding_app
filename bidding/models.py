from django.db import models
from django.contrib.auth.models import User 
from django.conf import settings
from .utils import send_auction_closed_notification


class Auction(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    deadline = models.DateTimeField()
    auctioneer = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True) 
    winner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="won_auctions")
    closed = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    receipt_confirmed = models.BooleanField(default=False)

    def close_auction(self, cancel=False):
        """Closes or cancels the auction with email alert logic."""
        if cancel:
            self.is_canceled = True  
        self.closed = True
        self.is_active = False  
        self.save()

        # ✅ Notify the winner (if applicable) and auctioneer
        winning_bid = self.get_winning_bid()
        if winning_bid:
            self.winner = winning_bid.bidder
            self.save()
            send_auction_closed_notification(self)  # Send email alert for winner & auctioneer

    def get_winning_bid(self):
        return self.bids.order_by('-amount').first()

    def __str__(self):
        return self.title


class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="bids")  # Add related_name
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    placed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bidder.username} - {self.amount}"

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    locked_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    def __str__(self):
        return f"{self.user.username}'s Wallet"
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)  # New field

    def __str__(self):
        return self.user.username
