function switchTab(tabName, event = null) {
    const tabs = document.querySelectorAll('.tab');
    const sections = document.querySelectorAll('.content-section');

    tabs.forEach(tab => tab.classList.remove('active'));
    sections.forEach(section => section.classList.remove('active'));

    const targetTab = event ? event.target : document.querySelector(`.tab[data-tab="${tabName}"]`);
    if (targetTab) {
        targetTab.classList.add('active');
    }

    const targetSection = document.getElementById(tabName);
    if (targetSection) {
        targetSection.classList.add('active');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.container[data-active-tab]');
    const initialTab = container ? container.dataset.activeTab : null;

    if (initialTab) {
        switchTab(initialTab);
    }

    const csrfTokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    const csrfToken = csrfTokenInput ? csrfTokenInput.value : null;

    // ==============================
    //  PROFILE PHOTO UPLOAD / REMOVE
    // ==============================
    attachPhotoEventListeners();

    function attachPhotoEventListeners() {
        const changePhotoBtn = document.getElementById('changePhotoBtn');
        const removePhotoBtn = document.getElementById('removePhotoBtn');
        const photoInput = document.getElementById('photoInput');
        const photoForm = document.getElementById('photoForm');

        // ✅ CHANGE PHOTO
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

        // ✅ REMOVE PHOTO
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

    // ==============================
    //  LOGOUT CONFIRMATION
    // ==============================
    const logoutForm = document.querySelector("form[action$='logout/']");
    if (logoutForm) {
        logoutForm.addEventListener("submit", (e) => {
            if (!confirm("Are you sure you want to log out?")) {
                e.preventDefault();
            }
        });
    }

    // ==============================
    //  BIRTHDATE MAX (CLIENT-SIDE)
    // ==============================
    const dobInput = document.getElementById("date_of_birth");
    if (dobInput) {
        const today = new Date();
        today.setDate(today.getDate() - 1);  // yesterday
        const max = today.toISOString().split("T")[0];
        dobInput.setAttribute("max", max);
    }
});
