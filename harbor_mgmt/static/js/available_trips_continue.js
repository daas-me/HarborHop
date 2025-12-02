document.addEventListener('DOMContentLoaded', function() {
    const continueBtn = document.querySelector('.continue-btn');
    if (!continueBtn) return;

    continueBtn.addEventListener('click', function(e) {
        if (continueBtn.disabled) {
            return;
        }

        e.preventDefault();

        const nextUrl = '/passenger-info/';
        const isAuthenticated = document.body.dataset.isAuthenticated === 'true';

        if (!isAuthenticated) {
            window.location.href = '/login/?next=' + encodeURIComponent(nextUrl);
            return;
        }

        // Store a flag that we're coming from available_trips
        sessionStorage.setItem('from_available_trips', 'true');
        
        window.location.href = nextUrl;
    });
});