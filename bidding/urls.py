from django.urls import include,path
from . import views  
from .views import confirm_receipt,place_bid, close_auction, close_expired_auctions, cancel_auction
from .views import profile,add_money
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),  # Home page
    path('login/', views.login_view, name='login'),  
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', profile, name='profile'), 
    # ✅ General Dashboard for Users
    path('dashboard/', views.dashboard, name='dashboard'),
    path('search/', views.auction_search, name='auction_search'),
    path('auction/<int:auction_id>/', views.auction_detail, name='auction_detail'),
    # ✅ Auctioneer Dashboard
    path('auctioneer_dashboard/', views.auctioneer_dashboard, name='auctioneer_dashboard'),

    path('create_auction/', views.create_auction, name='create_auction'),
    path('auction/<int:auction_id>/', views.auction_detail, name='auction_detail'),
    path('place-bid/<int:auction_id>/', place_bid, name='place_bid'),

    # ✅ Manual auction closing (for a specific auction)
    path('auction/<int:auction_id>/close/', close_auction, name='close_auction'),
    path('auction/<int:auction_id>/cancel/', cancel_auction, name='cancel_auction'),  # ✅ Add this

    # ✅ Ongoing Auctions Page
    path('ongoing-auctions/', views.ongoing_auctions, name='ongoing_auctions'),

    # ✅ Automatic closing for expired auctions
    path('close-expired-auctions/', close_expired_auctions, name='close_expired_auctions'),  
    path('confirm-receipt/<int:auction_id>/', confirm_receipt, name='confirm_receipt'),
    path('add-money/', add_money, name='add_money'),

    # ✅ My Bids
    path('my-bids/', views.my_bids, name='my_bids'),
    path('add-money/', add_money, name='add_money'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
