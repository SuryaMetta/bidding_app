from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .forms import AuctionForm, BidForm, UserRegistrationForm
from .models import Auction, Bid,Wallet
from django.http import HttpResponse
from django.utils.timezone import now,timedelta
from django.db.models import Max
import sys
from django.db import transaction
import logging
from .models import UserProfile
from .forms import ProfileUpdateForm 
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q 
from .utils import send_auction_closed_notification
from .utils import send_bid_notification
# Home View
def home(request):
    wallet = None  # Default value
    
    if request.user.is_authenticated:  # Check if user is logged in
        wallet = request.user.wallet  # Safe access to wallet

    auctions = Auction.objects.filter(is_active=True)  # ✅ Only active auctions

    return render(request, "bidding/home.html", {"auctions": auctions, "wallet": wallet})  # Include wallet

# User Registration View
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])  
            user.save()
            login(request, user)
            messages.success(request, "Registration successful! You are now logged in.")
            return redirect('home')
        else:
            messages.error(request, "Registration failed. Please check the form.")
    else:
        form = UserRegistrationForm()
    return render(request, 'bidding/register.html', {'form': form})

# User Login View
def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("home")
        else:
            messages.error(request, "Incorrect username or password!")
    return render(request, "bidding/login.html")

# User Logout View
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")

# Auctioneer Dashboard View
@login_required
def auctioneer_dashboard(request):
    user = request.user
    
    # Fetch auctions created by the user
    created_auctions = Auction.objects.filter(auctioneer=user)

    # Fetch auctions where the user has placed a bid
    my_bids = Bid.objects.filter(bidder=user).select_related("auction")

    # Fetch ongoing auctions
    ongoing_auctions = Auction.objects.filter(is_active=True)

    return render(request, "bidding/auctioneer_dashboard.html", {
        "created_auctions": created_auctions,
        "my_bids": my_bids,
        "ongoing_auctions": ongoing_auctions,
    })


# Bidding Dashboard View
def bidding_dashboard(request):
    ongoing_auctions = Auction.objects.filter(is_active=True)  # ✅ Show only active ones
    return render(request, 'bidding/bidding_dashboard.html', {'auctions': ongoing_auctions})

# Auction Creation View
@login_required
def create_auction(request):
    if request.method == 'POST':
        form = AuctionForm(request.POST)
        if form.is_valid():
            auction = form.save(commit=False)
            auction.auctioneer = request.user
            auction.save()
            return redirect('auctioneer_dashboard')
    else:
        form = AuctionForm()
    return render(request, 'bidding/create_auction.html', {'form': form})

# Auction Detail View
@login_required
def auction_detail(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    # Use auction.bids.all() instead of auction.bid_set.all()
    bids = auction.bids.all().order_by('-amount')  
    highest_bid = bids.first()  # Get highest bid
    return render(request, 'bidding/auction_detail.html', {
        'auction': auction,
        'bids': bids,
        'highest_bid': highest_bid,
    })
@login_required
def place_bid(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)

    if not auction.is_active:
        messages.error(request, "This auction has already ended. You cannot place a bid.")
        return redirect('auction_detail', auction_id=auction.id)

    if request.method == "POST":
        form = BidForm(request.POST)
        if form.is_valid():
            bid_amount = form.cleaned_data["amount"]
            user_wallet = Wallet.objects.get(user=request.user)

            highest_bid = Bid.objects.filter(auction=auction).order_by("-amount").first()

            if highest_bid and bid_amount <= highest_bid.amount:
                messages.error(request, "Your bid must be higher than the current highest bid.")
                return redirect('auction_detail', auction_id=auction.id)

            available_balance = user_wallet.balance
            if available_balance < bid_amount:
                messages.error(request, "Insufficient balance to place this bid.")
                return redirect('auction_detail', auction_id=auction.id)

            # ✅ Save the new bid
            bid = form.save(commit=False)
            bid.auction = auction
            bid.bidder = request.user
            bid.save()

            # ✅ Send email notification to the auctioneer
            send_bid_notification(auction.auctioneer, request.user, auction)

            messages.success(request, f"Your bid of ₹{bid_amount} has been placed successfully!")
            return redirect('auction_detail', auction_id=auction.id)

    else:
        form = BidForm()

    return render(request, 'bidding/auction_detail.html', {'form': form, 'auction': auction})

# Dashboard View
@login_required
def dashboard(request):
    return render(request, 'bidding/dashboard.html')

@login_required
def close_auction(request, auction_id):
    """Manually close a specific auction with proper winner handling and email alerts."""
    auction = get_object_or_404(Auction, id=auction_id, is_active=True)
    highest_bid = Bid.objects.filter(auction=auction).order_by("-amount").first()

    if highest_bid:
        winner = highest_bid.bidder
        winning_amount = highest_bid.amount

        # ✅ Get the winner's wallet
        winner_wallet = Wallet.objects.get(user=winner)

        # ✅ Ensure winner has enough balance (including locked balance check)
        available_balance = winner_wallet.balance - winner_wallet.locked_balance
        if available_balance >= winning_amount:
            with transaction.atomic():  # Ensure atomic updates
                # 🔥 Deduct and lock winning amount
                winner_wallet.balance -= winning_amount
                winner_wallet.locked_balance += winning_amount
                winner_wallet.save()

                # ✅ Mark auction as closed and assign winner
                auction.is_active = False
                auction.winner = winner
                auction.save()

            # ✅ Send email notification to the winner & auctioneer
            send_auction_closed_notification(auction)

            messages.success(
                request,
                f"Auction '{auction.title}' closed! {winner.username} won with ₹{winning_amount}."
            )
        else:
            # 🚨 Find the next highest bidder with sufficient balance
            next_highest_bid = (
                Bid.objects.filter(auction=auction, amount__lt=winning_amount)
                .order_by("-amount")
                .first()
            )

            if next_highest_bid:
                next_winner = next_highest_bid.bidder
                next_winning_amount = next_highest_bid.amount

                # ✅ Get the next highest bidder's wallet
                next_winner_wallet = Wallet.objects.get(user=next_winner)
                next_available_balance = next_winner_wallet.balance - next_winner_wallet.locked_balance

                if next_available_balance >= next_winning_amount:
                    with transaction.atomic():
                        # ✅ Deduct balance and lock it for the next winner
                        next_winner_wallet.balance -= next_winning_amount
                        next_winner_wallet.locked_balance += next_winning_amount
                        next_winner_wallet.save()

                        # ✅ Assign the next winner and close auction
                        auction.winner = next_winner
                        auction.is_active = False
                        auction.save()

                    # ✅ Send email to the adjusted winner & auctioneer
                    send_auction_closed_notification(auction)

                    messages.warning(
                        request,
                        f"Auction '{auction.title}' closed! "
                        f"{next_winner.username} won because the top bidder lacked funds."
                    )
                else:
                    # No valid bidders left
                    auction.is_active = False
                    auction.save()
                    messages.error(
                        request,
                        f"Auction '{auction.title}' closed, but the top two bidders lacked sufficient funds."
                    )
            else:
                # No other valid bids
                auction.is_active = False
                auction.save()
                messages.error(
                    request,
                    f"Auction '{auction.title}' closed, but the highest bidder had insufficient funds."
                )

    else:
        # ✅ If no bids, just mark auction as closed
        auction.is_active = False
        auction.save()
        messages.info(request, f"Auction '{auction.title}' closed with no valid bids.")

    return redirect("auctioneer_dashboard")  # Redirect to the auction dashboard
@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=user_profile)  # Correct instance
        password_form = PasswordChangeForm(request.user, request.POST)

        if 'update_profile' in request.POST and profile_form.is_valid():
            profile_form.save()
            return redirect('profile')

        elif 'change_password' in request.POST and password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            return redirect('profile')

    else:
        profile_form = ProfileUpdateForm(instance=user_profile)  # Correct instance
        password_form = PasswordChangeForm(request.user)

    return render(request, 'bidding/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'user_profile': user_profile,
    })



def some_view(request):
    wallet = Wallet.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    return render(request, "bidding/some_template.html", {"wallet": wallet})

@login_required
def my_bids(request):
    bids = Bid.objects.filter(bidder=request.user).select_related('auction')
    return render(request, 'bidding/my_bids.html', {'bids': bids})

def ongoing_auctions(request):
    auctions = Auction.objects.filter(is_active=True)  # Only show active auctions
    return render(request, "bidding/ongoing_auctions.html", {"auctions": auctions})

def close_expired_auctions(request):
    expired_auctions = Auction.objects.filter(is_active=True, deadline__lt=now())

    for auction in expired_auctions:
        highest_bid = Bid.objects.filter(auction=auction).order_by("-amount").first()

        if highest_bid:
            winner = highest_bid.bidder
            winning_amount = highest_bid.amount
            winner_wallet = Wallet.objects.get(user=winner)

            # ✅ Ensure we only close the auction without checking locked balance
            auction.is_active = False
            auction.winner = winner
            auction.save()

            messages.success(
                request,
                f"Auction '{auction.title}' closed! {winner.username} won with ₹{winning_amount}."
            )
        else:
            # ✅ If no valid bids, still close the auction properly
            auction.is_active = False
            auction.save()
            messages.info(request, f"Auction '{auction.title}' closed with no valid bids.")

    return redirect("auctioneer_dashboard")

@login_required
def wallet_view(request):
    wallet = request.user.wallet  # Get the logged-in user's wallet
    return render(request, 'bidding/wallet.html', {'wallet': wallet})

# Set up logging for debugging
logger = logging.getLogger(__name__)

@login_required
def confirm_receipt(request, auction_id):
    """Winner confirms receipt, and payment is released to the auctioneer."""
    auction = get_object_or_404(Auction, id=auction_id, is_active=False)

    # ✅ Prevent duplicate confirmation
    if auction.receipt_confirmed:
        messages.info(request, "Receipt has already been confirmed.")
        return redirect("auction_detail", auction_id=auction.id)

    # ✅ Get the winning bid
    winning_bid = auction.bids.order_by('-amount').first()

    if not winning_bid:
        messages.error(request, "No winning bid found.")
        return redirect("auction_detail", auction_id=auction.id)

    if request.user != winning_bid.bidder:
        messages.error(request, "Only the winning bidder can confirm receipt.")
        return redirect("auction_detail", auction_id=auction.id)

    # ✅ Get wallets
    winner_wallet = request.user.wallet
    auctioneer_wallet = auction.auctioneer.wallet

    # 🚨 Ensure locked balance is available before transferring
    if winner_wallet.locked_balance < winning_bid.amount:
        messages.error(request, "Transaction error: Insufficient locked balance.")
        logger.error(f"Transaction failed for auction {auction_id}: Insufficient locked balance.")
        return redirect("auction_detail", auction_id=auction.id)

    # ✅ Use transaction.atomic() to ensure atomic updates
    try:
        with transaction.atomic():
            winner_wallet.locked_balance -= winning_bid.amount  # Unlock the balance
            auctioneer_wallet.balance += winning_bid.amount  # Transfer to auctioneer

            # Save wallet changes
            winner_wallet.save()
            auctioneer_wallet.save()

            # ✅ Mark auction as completed and confirmed
            auction.receipt_confirmed = True  # New field to track confirmation
            auction.save()

        messages.success(request, "Payment released to the auctioneer!")
        logger.info(f"Auction {auction_id}: Payment successfully transferred to auctioneer.")

    except Exception as e:
        logger.error(f"Error processing receipt confirmation for auction {auction_id}: {e}")
        messages.error(request, "An unexpected error occurred. Please try again.")

    return redirect("auction_detail", auction_id=auction.id)
def auto_release_funds():
    expired_auctions = Auction.objects.filter(is_closed=True, end_time__lt=now() - timedelta(hours=24))

    for auction in expired_auctions:
        if auction.winning_bid and auction.winning_bid.user.wallet.locked_balance > 0:
            winner_wallet = auction.winning_bid.user.wallet
            auctioneer_wallet = auction.user.wallet

            auctioneer_wallet.balance += winner_wallet.locked_balance
            winner_wallet.locked_balance = 0

            auctioneer_wallet.save()
            winner_wallet.save()

@login_required
def cancel_auction(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)

    if request.user != auction.user:
        messages.error(request, "Only the auctioneer can cancel the auction.")
        return redirect("auction_detail", auction_id=auction.id)

    # Refund all bidders
    for bid in auction.bids.all():
        bid.user.wallet.balance += bid.amount
        bid.user.wallet.locked_balance -= bid.amount
        bid.user.wallet.save()

    auction.delete()  # Remove the auction
    messages.success(request, "Auction canceled and all funds refunded.")
    return redirect("home")

@login_required
def add_money(request):
    return render(request, 'bidding/add_money.html')

def auction_detail(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    return render(request, 'bidding/auction_detail.html', {'auction': auction})

def auction_search(request):
    query = request.GET.get('q', '')  # Get search query from URL parameter
    results = Auction.objects.filter(
        Q(title__icontains=query) | 
        Q(description__icontains=query)
    ) if query else Auction.objects.all()

    return render(request, 'bidding/auction_search.html', {'results': results, 'query': query})
