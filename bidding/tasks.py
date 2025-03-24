from celery import shared_task
from django.utils.timezone import now, timedelta
from .models import Auction, Bid, Wallet


@shared_task
def auto_release_funds():
    """Releases funds to the auctioneer if the winner hasn't confirmed receipt within 24 hours."""
    auctions = Auction.objects.filter(is_active=False, winner__isnull=False, closed=False)

    for auction in auctions:
        winner_wallet = Wallet.objects.get(user=auction.winner)
        auctioneer_wallet = Wallet.objects.get(user=auction.auctioneer)

        # Check if 24 hours have passed since auction ended
        if auction.deadline + timedelta(hours=24) < now():
            auctioneer_wallet.balance += winner_wallet.locked_balance  # Transfer funds
            winner_wallet.locked_balance = 0  # Unlock funds from winner’s wallet

            winner_wallet.save()
            auctioneer_wallet.save()

            auction.closed = True  # Mark auction as fully closed
            auction.save()

    return f"Released funds for {auctions.count()} auctions."

@shared_task
def close_expired_auctions():
    expired_auctions = Auction.objects.filter(deadline__lt=now(), is_active=True)

    for auction in expired_auctions:
        highest_bid = auction.bids.order_by('-amount').first()  # Get the highest bid

        if highest_bid:
            auction.winner = highest_bid.bidder  # Assign winner
            winner_wallet = Wallet.objects.get(user=highest_bid.bidder)

            # Lock the bid amount in the winner's wallet
            winner_wallet.balance -= highest_bid.amount
            winner_wallet.locked_balance += highest_bid.amount
            winner_wallet.save()

        auction.is_active = False  # Mark auction as closed
        auction.save()

    return f"Closed {expired_auctions.count()} expired auctions and assigned winners." 

@shared_task
def sample_task():
    return "Celery is working!"
