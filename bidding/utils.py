import os
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)  # For error tracking

def send_auction_closed_notification(auction):
    """Sends email notifications using HTML templates for better presentation."""
    subject = f"Auction Closed: {auction.title}"
    
    try:
        if auction.winner:
            # Winner email
            html_content = render_to_string('bidding/emails/winner_notification.html', {'auction': auction})
            plain_text_content = strip_tags(html_content)
            send_mail(
                subject,
                plain_text_content,
                os.getenv('EMAIL_HOST_USER'),
                [auction.winner.email],
                html_message=html_content
            )
        
        # Auctioneer email
        html_content_auctioneer = render_to_string('bidding/emails/auctioneer_notification.html', {'auction': auction})
        plain_text_content_auctioneer = strip_tags(html_content_auctioneer)
        send_mail(
            subject,
            plain_text_content_auctioneer,
            os.getenv('EMAIL_HOST_USER'),
            [auction.auctioneer.email],
            html_message=html_content_auctioneer
        )

    except Exception as e:
        logger.error(f"Error sending auction closed email for auction {auction.id}: {e}")

def send_bid_notification(auctioneer, bidder, auction):
    """Send email to the auctioneer when a new bid is placed."""
    subject = f"📢 New Bid on Your Auction: {auction.title}"
    
    try:
        html_message = render_to_string('bidding/emails/bid_notification.html', {
            'auctioneer': auctioneer,
            'bidder': bidder,
            'auction': auction
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            os.getenv('EMAIL_HOST_USER'),
            [auctioneer.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Error sending bid notification email for auction {auction.id}: {e}")
