document.addEventListener('DOMContentLoaded', function() {
    if (window.flatpickr) {
        flatpickr("input[type='date']", {
            dateFormat: "Y-m-d",
            maxDate: "today",
            altInput: true,
            altFormat: "F j, Y",
            allowInput: true,
        });
    }
});
