function switchTab(tabName, event = null) {
    const tabs = document.querySelectorAll('.tab');
    const sections = document.querySelectorAll('.content-section');

    tabs.forEach(tab => tab.classList.remove('active'));
    sections.forEach(section => section.classList.remove('active'));

    const targetTab = event ? event.target : document.querySelector(`.tab[data-tab="${tabName}"]`);
    if (targetTab) targetTab.classList.add('active');

    const targetSection = document.getElementById(tabName);
    if (targetSection) targetSection.classList.add('active');
}

document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.container[data-active-tab]');
    const initialTab = container ? container.dataset.activeTab : null;
    if (initialTab) switchTab(initialTab);

    const csrfTokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    const csrfToken = csrfTokenInput ? csrfTokenInput.value : null;

    // Photo upload/remove
    attachPhotoEventListeners();
    function attachPhotoEventListeners() {
        const changePhotoBtn = document.getElementById('changePhotoBtn');
        const removePhotoBtn = document.getElementById('removePhotoBtn');
        const photoInput = document.getElementById('photoInput');
        const photoForm = document.getElementById('photoForm');

        if (changePhotoBtn && photoInput && photoForm && csrfToken) {
            changePhotoBtn.addEventListener('click', () => photoInput.click());
            photoInput.addEventListener('change', async () => {
                const file = photoInput.files[0];
                if (!file) return;
                const formData = new FormData(photoForm);
                try {
                    const response = await fetch(photoForm.action, {
                        method: "POST",
                        headers: { "X-CSRFToken": csrfToken },
                        body: formData,
                    });
                    const data = await response.json();
                    if (data.success) {
                        const wrapper = document.getElementById("profilePhotoWrapper");
                        wrapper.innerHTML = `<img src="${data.photo_url}" alt="Profile Photo" id="profilePhoto">`;
                    } else {
                        alert(data.message || "Failed to upload photo.");
                    }
                } catch (err) {
                    console.error("Upload error:", err);
                    alert("Something went wrong while uploading the photo.");
                }
            });
        }

        if (removePhotoBtn && csrfToken) {
            removePhotoBtn.addEventListener('click', async () => {
                if (!confirm("Are you sure you want to remove your profile photo?")) return;
                try {
                    const response = await fetch("/delete-profile-photo/", {
                        method: "POST",
                        headers: { "X-CSRFToken": csrfToken },
                    });
                    const data = await response.json();
                    if (data.success) {
                        const wrapper = document.getElementById("profilePhotoWrapper");
                        const initials = getInitialsFromName();
                        wrapper.innerHTML = `<span id="profilePhotoPlaceholder">${initials}</span>`;
                    } else {
                        alert(data.message || "Failed to remove photo.");
                    }
                } catch (error) {
                    console.error("Error removing photo:", error);
                    alert("Something went wrong while removing the photo.");
                }
            });
        }
    }

    function getInitialsFromName() {
        const nameElement = document.querySelector(".profile-info h1");
        if (!nameElement) return "??";
        const nameParts = nameElement.textContent.trim().split(" ");
        if (nameParts.length === 1) return nameParts[0][0].toUpperCase();
        const first = nameParts[0][0].toUpperCase();
        const last = nameParts[nameParts.length - 1][0].toUpperCase();
        return first + last;
    }

    // Logout confirmation
    const logoutForm = document.querySelector("form[action$='logout/']");
    if (logoutForm) {
        logoutForm.addEventListener("submit", (e) => {
            if (!confirm("Are you sure you want to log out?")) e.preventDefault();
        });
    }

    // Birthdate validation (client-side)
    const dobInput = document.getElementById("date_of_birth");
    const profileForm = document.getElementById("profileForm");
    const updateMessage = document.getElementById("updateMessage");

    function showInlineMessage(text, isError = true) {
        if (!updateMessage) {
            alert(text);
            return;
        }
        updateMessage.textContent = text;
        updateMessage.style.display = "block";
        updateMessage.style.color = isError ? "#d9534f" : "green";
        updateMessage.classList.add("show");
        clearTimeout(showInlineMessage._timer);
        showInlineMessage._timer = setTimeout(() => {
            updateMessage.classList.remove("show");
            updateMessage.style.display = "";
            updateMessage.textContent = "";
        }, 4000);
    }

    if (dobInput) {
        // Allow user to pick recent years (2010-2025 etc). Only disallow future dates.
        const today = new Date();
        const maxDate = new Date(today.getFullYear(), today.getMonth(), today.getDate()); // today
        dobInput.setAttribute("max", maxDate.toISOString().split("T")[0]);
        dobInput.setAttribute("min", "1900-01-01");
        // NOTE: we DO NOT set max to (today - 15 years) so years 2010-2025 remain visible/selectable.
    }

    if (profileForm) {
        profileForm.addEventListener("submit", (e) => {
            if (!dobInput) return;
            const val = dobInput.value;
            if (!val) return; // empty allowed if server accepts empty

            // parse YYYY-MM-DD
            const [y, m, d] = val.split("-");
            if (!y || !m || !d) {
                e.preventDefault();
                showInlineMessage("Invalid birthdate format. Please use YYYY-MM-DD.");
                return;
            }

            const dob = new Date(Number(y), Number(m) - 1, Number(d));
            const today = new Date();
            const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate());

            // reject future/today
            if (dob >= todayOnly) {
                e.preventDefault();
                showInlineMessage("Birthdate cannot be today or in the future.");
                return;
            }

            // compute age
            let age = today.getFullYear() - dob.getFullYear();
            const monthDiff = today.getMonth() - dob.getMonth();
            if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) age--;

            if (age < 15) {
                e.preventDefault();
                showInlineMessage("You must be at least 15 years old to use this service.");
                return;
            }

            // OK — allow submit and show a tiny saving notice
            showInlineMessage("Saving profile...", false);
            // form will submit normally
        });
    }
});
