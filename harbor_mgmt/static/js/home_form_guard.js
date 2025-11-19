document.addEventListener('DOMContentLoaded', function() {
    // Set min date for all date inputs to today
    var today = new Date();
    var yyyy = today.getFullYear();
    var mm = String(today.getMonth() + 1).padStart(2, '0');
    var dd = String(today.getDate()).padStart(2, '0');
    var minDate = yyyy + '-' + mm + '-' + dd;
    document.querySelectorAll('input[type="date"]').forEach(function(input) {
        input.setAttribute('min', minDate);
    });

    const bookingForm = document.querySelector('.booking-form');
    if (!bookingForm) return;

    bookingForm.addEventListener('submit', function(e) {
        const adults = parseInt(bookingForm.querySelector('input[name="adults"]').value, 10) || 0;
        const children = parseInt(bookingForm.querySelector('input[name="children"]').value, 10) || 0;
        if (adults + children < 1) {
            e.preventDefault();
            alert('Please add at least one passenger.');
        }
    });
});
