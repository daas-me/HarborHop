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

        window.location.href = nextUrl;
    });
});
