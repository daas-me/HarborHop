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
    const profileForm = document.getElementById("profileForm");
    const updateMessage = document.getElementById("updateMessage");
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const container = document.querySelector('.container[data-active-tab]');
    const initialTab = container ? container.dataset.activeTab : null;

    if (initialTab) {
        switchTab(initialTab);
    }

    // ==============================
    //  PROFILE INFO UPDATE (AJAX)
    // ==============================
    if (profileForm) {
        profileForm.addEventListener("submit", async function(e) {
            e.preventDefault();
            const formData = new FormData(profileForm);

            try {
                const response = await fetch("/update-profile-ajax/", {
                    method: "POST",
                    body: formData,
                    headers: { "X-CSRFToken": formData.get("csrfmiddlewaretoken") },
                });

                const data = await response.json();
                if (data.success) {
                    updateMessage.textContent = data.message;
                    updateMessage.style.display = "block";
                    updateMessage.classList.add("show");

                    document.querySelector(".profile-info h1").textContent =
                        `${data.updated_data.first_name} ${data.updated_data.last_name}`;
                    document.querySelector(".profile-info p:nth-of-type(1)").textContent =
                        `📧 ${data.updated_data.email}`;
                    document.querySelector(".profile-info p:nth-of-type(2)").textContent =
                        `📱 ${data.updated_data.phone || '+63 000 000 0000'}`;

                    setTimeout(() => updateMessage.classList.remove("show"), 3000);
                } else {
                    alert("❌ " + data.message);
                }
            } catch (error) {
                console.error("Error:", error);
                alert("Something went wrong while updating your profile.");
            }
        });
    }

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
        if (changePhotoBtn && photoInput) {
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
                }
            });
        }

        // ✅ REMOVE PHOTO
        if (removePhotoBtn) {
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

                        // 🧩 Replace image with initials (no DOM rebuild)
                        wrapper.innerHTML = `<span id="profilePhotoPlaceholder">${initials}</span>`;

                        // ✅ Keep both buttons visible all the time
                        document.getElementById("removePhotoBtn").style.display = "inline-block";
                        document.getElementById("changePhotoBtn").style.display = "inline-block";
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
    
    // ✅ Use only first and last initials
    if (nameParts.length === 1) return nameParts[0][0].toUpperCase();
    const first = nameParts[0][0].toUpperCase();
    const last = nameParts[nameParts.length - 1][0].toUpperCase();
    return first + last;
}
});

document.addEventListener("DOMContentLoaded", () => {
    const logoutForm = document.querySelector("form[action$='logout/']");
    if (logoutForm) {
        logoutForm.addEventListener("submit", (e) => {
            if (!confirm("Are you sure you want to log out?")) {
                e.preventDefault();
            }
        });
    }
});
