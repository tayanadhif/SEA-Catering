
// Global variables
let currentSlide = 0;
let selectedRating = 0;

// Smooth scrolling function
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

// Navigation active state handler
function updateActiveNav() {
    const sections = ['home', 'menu', 'subscription', 'testimonials', 'contact'];
    const navLinks = document.querySelectorAll('.nav-link');
    
    sections.forEach((sectionId, index) => {
        const section = document.getElementById(sectionId);
        const rect = section.getBoundingClientRect();
        
        if (rect.top <= 100 && rect.bottom >= 100) {
            navLinks.forEach(link => link.classList.remove('active'));
            navLinks[index].classList.add('active');
        }
    });
}

// Price calculator for subscription
function calculatePrice() {
    const planInputs = document.querySelectorAll('input[name="plan"]');
    const mealTypeInputs = document.querySelectorAll('input[name="mealType"]:checked');
    const deliveryDayInputs = document.querySelectorAll('input[name="deliveryDays"]:checked');
    
    let planPrice = 0;
    planInputs.forEach(input => {
        if (input.checked) {
            planPrice = parseInt(input.dataset.price);
        }
    });
    
    const mealTypeCount = mealTypeInputs.length;
    const deliveryDayCount = deliveryDayInputs.length;
    
    if (planPrice > 0 && mealTypeCount > 0 && deliveryDayCount > 0) {
        const totalPrice = planPrice * mealTypeCount * deliveryDayCount * 4.3;
        document.getElementById('totalPrice').textContent = 
            'Rp' + totalPrice.toLocaleString('id-ID');
    } else {
        document.getElementById('totalPrice').textContent = 'Rp0';
    }
}

// Modal functions
function openPlanModal(planType) {
    const modal = document.getElementById('planModal');
    const modalContent = document.getElementById('modalContent');
    
    const planDetails = {
        diet: {
            title: 'Diet Plan - Rp30.000/meal',
            description: 'Perfect for weight management and healthy living',
            features: [
                'Calorie-controlled portions (300-500 calories per meal)',
                'High fiber vegetables and whole grains',
                'Lean proteins like chicken breast and fish',
                'Fresh fruits and low-fat dairy',
                'Customizable based on dietary restrictions',
                'Nutritionist-approved recipes'
            ],
            image: '🥗'
        },
        protein: {
            title: 'Protein Plan - Rp40.000/meal',
            description: 'Ideal for fitness enthusiasts and muscle building',
            features: [
                'High protein content (25-35g per meal)',
                'Premium lean meats and fish',
                'Post-workout recovery nutrients',
                'Complex carbohydrates for energy',
                'Essential amino acids',
                'Fitness trainer approved meals'
            ],
            image: '🥩'
        },
        royal: {
            title: 'Royal Plan - Rp60.000/meal',
            description: 'Premium dining experience with gourmet ingredients',
            features: [
                'Premium imported ingredients',
                'Chef-crafted gourmet recipes',
                'Larger portion sizes',
                'Exclusive seasonal menus',
                'Fine dining presentation',
                'Luxury packaging and delivery'
            ],
            image: '👑'
        }
    };
    
    const plan = planDetails[planType];
    modalContent.innerHTML = `
        <div style="text-align: center;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">${plan.image}</div>
            <h2 style="color: #2c3e50; margin-bottom: 1rem;">${plan.title}</h2>
            <p style="font-size: 1.1rem; margin-bottom: 2rem; color: #666;">${plan.description}</p>
            <div style="text-align: left;">
                <h3 style="color: #2c3e50; margin-bottom: 1rem;">What's Included:</h3>
                <ul style="list-style: none; padding: 0;">
                    ${plan.features.map(feature => `
                        <li style="padding: 0.5rem 0; color: #555;">
                            <span style="color: #27ae60; margin-right: 0.5rem;">✓</span>
                            ${feature}
                        </li>
                    `).join('')}
                </ul>
            </div>
            <button onclick="scrollToSection('subscription'); closePlanModal();" 
                    style="margin-top: 2rem; background: #3498db; color: white; border: none; padding: 15px 30px; border-radius: 25px; cursor: pointer; font-size: 1rem;">
                Subscribe to This Plan
            </button>
        </div>
    `;
    
    modal.style.display = 'block';
}

function closePlanModal() {
    document.getElementById('planModal').style.display = 'none';
}

// Testimonial carousel
function changeSlide(direction) {
    const slides = document.querySelectorAll('.testimonial-slide');
    slides[currentSlide].classList.remove('active');
    
    currentSlide += direction;
    if (currentSlide >= slides.length) currentSlide = 0;
    if (currentSlide < 0) currentSlide = slides.length - 1;
    
    slides[currentSlide].classList.add('active');
}

// Auto-advance testimonial carousel
function autoAdvanceCarousel() {
    setInterval(() => {
        changeSlide(1);
    }, 5000);
}

// Star rating handler
function handleStarRating() {
    const stars = document.querySelectorAll('.star');
    const ratingInput = document.getElementById('ratingValue');
    
    stars.forEach(star => {
        star.addEventListener('click', () => {
            selectedRating = parseInt(star.dataset.rating);
            ratingInput.value = selectedRating;
            
            stars.forEach((s, index) => {
                if (index < selectedRating) {
                    s.classList.add('active');
                } else {
                    s.classList.remove('active');
                }
            });
        });
        
        star.addEventListener('mouseover', () => {
            const rating = parseInt(star.dataset.rating);
            stars.forEach((s, index) => {
                if (index < rating) {
                    s.style.opacity = '1';
                } else {
                    s.style.opacity = '0.3';
                }
            });
        });
    });
    
    document.querySelector('.star-rating').addEventListener('mouseleave', () => {
        stars.forEach((s, index) => {
            if (index < selectedRating) {
                s.style.opacity = '1';
            } else {
                s.style.opacity = '0.3';
            }
        });
    });
}

// Form validation functions
function validateSubscriptionForm(formData) {
    const name = formData.get('fullName');
    const phone = formData.get('phoneNumber');
    const plan = formData.get('plan');
    const mealTypes = formData.getAll('mealType');
    const deliveryDays = formData.getAll('deliveryDays');
    
    if (!name || !phone || !plan) {
        alert('Please fill in all required fields marked with *');
        return false;
    }
    
    if (mealTypes.length === 0) {
        alert('Please select at least one meal type');
        return false;
    }
    
    if (deliveryDays.length === 0) {
        alert('Please select at least one delivery day');
        return false;
    }
    
    const phoneRegex = /^08[0-9]{8,13}$/;
    if (!phoneRegex.test(phone)) {
        alert('Please enter a valid Indonesian phone number (08xxxxxxxxx)');
        return false;
    }
    
    return true;
}

function validateTestimonialForm(formData) {
    const name = formData.get('customerName');
    const message = formData.get('reviewMessage');
    const rating = formData.get('rating');
    
    if (!name || !message || !rating) {
        alert('Please fill in all fields and select a rating');
        return false;
    }
    
    return true;
}

// Form submission handlers
function handleSubscriptionSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    if (validateSubscriptionForm(formData)) {
        // Simulate successful subscription
        const totalPrice = document.getElementById('totalPrice').textContent;
        alert(`Thank you for subscribing! Your monthly subscription total is ${totalPrice}. We will contact you within 24 hours to confirm your order and arrange payment.`);
        e.target.reset();
        calculatePrice(); // Reset price display
    }
}

function handleTestimonialSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    if (validateTestimonialForm(formData)) {
        alert('Thank you for your review! Your testimonial will be reviewed and published soon.');
        e.target.reset();
        selectedRating = 0;
        document.querySelectorAll('.star').forEach(star => {
            star.classList.remove('active');
            star.style.opacity = '0.3';
        });
        document.getElementById('ratingValue').value = '';
    }
}

function handleContactSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    const name = formData.get('name') || e.target.querySelector('input[type="text"]').value;
    const email = formData.get('email') || e.target.querySelector('input[type="email"]').value;
    const message = formData.get('message') || e.target.querySelector('textarea').value;
    
    if (!name || !email || !message) {
        alert('Please fill in all fields');
        return;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        alert('Please enter a valid email address');
        return;
    }
    
    alert('Thank you for your message! We will get back to you within 24 hours.');
    e.target.reset();
}

// Scroll animations
function addScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe all sections except hero
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(30px)';
        section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(section);
    });
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Navigation functionality
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            scrollToSection(targetId);
        });
    });
    
    // Scroll effects
    window.addEventListener('scroll', function() {
        const nav = document.querySelector('header');
        if (window.scrollY > 100) {
            nav.style.background = 'rgba(255, 255, 255, 0.95)';
        } else {
            nav.style.background = 'rgba(255, 255, 255, 0.95)';
        }
        
        updateActiveNav();
    });
    
    // Price calculator event listeners
    const planInputs = document.querySelectorAll('input[name="plan"]');
    const mealTypeInputs = document.querySelectorAll('input[name="mealType"]');
    const deliveryDayInputs = document.querySelectorAll('input[name="deliveryDays"]');
    
    [...planInputs, ...mealTypeInputs, ...deliveryDayInputs].forEach(input => {
        input.addEventListener('change', calculatePrice);
    });
    
    // Form event listeners
    const subscriptionForm = document.getElementById('subscriptionForm');
    if (subscriptionForm) {
        subscriptionForm.addEventListener('submit', handleSubscriptionSubmit);
    }
    
    const testimonialForm = document.getElementById('testimonialForm');
    if (testimonialForm) {
        testimonialForm.addEventListener('submit', handleTestimonialSubmit);
    }
    
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', handleContactSubmit);
    }
    
    // Initialize star rating
    handleStarRating();
    
    // Initialize carousel auto-advance
    autoAdvanceCarousel();
    
    // Initialize scroll animations
    addScrollAnimations();
    
    // Modal close on outside click
    window.addEventListener('click', function(e) {
        const modal = document.getElementById('planModal');
        if (e.target === modal) {
            closePlanModal();
        }
    });
    
    // Initialize price calculator
    calculatePrice();
});

// Keyboard navigation for modal
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closePlanModal();
    }
});
