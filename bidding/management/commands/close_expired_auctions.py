from django.core.management.base import BaseCommand
from django.utils import timezone
from bidding.models import Auction, Bid

class Command(BaseCommand):
    help = "Closes auctions that have reached their deadline and declares a winner."

    def handle(self, *args, **kwargs):
        now = timezone.now()
        expired_auctions = Auction.objects.filter(is_active=True, deadline__lt=now)

        for auction in expired_auctions:
            highest_bid = auction.bids.order_by('-amount').first()  # Get highest bid

            if highest_bid:
                auction.winner = highest_bid.bidder  # Assign winner
            auction.is_active = False  # Mark auction as closed
            auction.save()

            self.stdout.write(self.style.SUCCESS(f"Auction '{auction.title}' closed."))

        if not expired_auctions:
            self.stdout.write("No expired auctions found.")
