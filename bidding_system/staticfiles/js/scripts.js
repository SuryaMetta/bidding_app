// scripts.js

document.addEventListener('DOMContentLoaded', function () {
    const navLinks = document.querySelectorAll('nav ul li a');
    const walletContainer = document.querySelector('.wallet-container');

    // Smooth scrolling for links
    navLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                e.preventDefault();
                window.scrollTo({
                    top: targetElement.offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Wallet section animation
    if (walletContainer) {
        walletContainer.style.opacity = '0';
        walletContainer.style.transform = 'translateY(20px)';
        setTimeout(() => {
            walletContainer.style.transition = 'all 0.5s ease';
            walletContainer.style.opacity = '1';
            walletContainer.style.transform = 'translateY(0)';
        }, 300);
    }

    // Interactive auction cards
    const auctionCards = document.querySelectorAll('.auction-card');
    auctionCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'scale(1.05)';
            card.style.boxShadow = '0 4px 15px rgba(179, 136, 255, 0.5)';
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'scale(1)';
            card.style.boxShadow = 'none';
        });
    });

    // Dynamic time greeting
    const greeting = document.createElement('div');
    greeting.textContent = getGreeting();
    greeting.classList.add('greeting-message');
    document.body.insertBefore(greeting, document.body.firstChild);

    function getGreeting() {
        const hour = new Date().getHours();
        if (hour < 12) return 'Good Morning! 🌅';
        if (hour < 18) return 'Good Afternoon! ☀️';
        return 'Good Evening! 🌙';
    }
});
