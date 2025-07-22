// Toggle user menu
const userMenuButton = document.getElementById('user-menu-button');
const userMenu = userMenuButton.nextElementSibling;

userMenuButton.addEventListener('click', () => {
    userMenu.classList.toggle('hidden');
});

// Close menu when clicking outside
document.addEventListener('click', (e) => {
    if (!userMenuButton.contains(e.target) && !userMenu.contains(e.target)) {
        userMenu.classList.add('hidden');
    }
});

// Toggle property details
const detailButtons = document.querySelectorAll('.property-card .action-btn');
detailButtons.forEach(button => {
    button.addEventListener('click', (e) => {
        e.preventDefault();
        const card = button.closest('.property-card');
        const details = card.querySelector('.property-details');
        details.classList.toggle('hidden');
    });
});

// Add smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

// Add animation on scroll for cards
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-fade-in');
        }
    });
}, {
    threshold: 0.1
});

document.querySelectorAll('.stat-card, .property-card').forEach((card) => {
    observer.observe(card);
});

// Add copy to clipboard functionality for addresses
document.querySelectorAll('.property-card .address').forEach(address => {
    const button = document.createElement('button');
    button.className = 'copy-button';
    button.innerHTML = '<i class="fas fa-copy"></i>';
    button.addEventListener('click', () => {
        navigator.clipboard.writeText(address.textContent);
        button.innerHTML = '<i class="fas fa-check"></i>';
        setTimeout(() => {
            button.innerHTML = '<i class="fas fa-copy"></i>';
        }, 2000);
    });
    address.appendChild(button);
});
