function switchTab(tabName, event) {
    const tabs = document.querySelectorAll('.tab');
    const sections = document.querySelectorAll('.content-section');

    tabs.forEach(tab => tab.classList.remove('active'));
    sections.forEach(section => section.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById(tabName).classList.add('active');
}
document.addEventListener("DOMContentLoaded", function() {
    const profileForm = document.getElementById("profileForm");
    const updateMessage = document.getElementById("updateMessage");

    profileForm.addEventListener("submit", async function(e) {
        e.preventDefault(); // Stop normal form submit

        const formData = new FormData(profileForm);

        try {
            const response = await fetch("/update-profile-ajax/", {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
                },
            });

            const data = await response.json();

            if (data.success) {
                // ✅ Show success message
                updateMessage.textContent = data.message;
                updateMessage.style.display = "block";
                updateMessage.classList.add("show");
                
                // ✅ Update header info instantly
                document.querySelector(".profile-info h1").textContent =
                    `${data.updated_data.first_name} ${data.updated_data.last_name}`;
                document.querySelector(".profile-info p:nth-of-type(1)").textContent =
                    `📧 ${data.updated_data.email}`;
                document.querySelector(".profile-info p:nth-of-type(2)").textContent =
                    `📱 ${data.updated_data.phone || '+63 000 000 0000'}`;

                // Hide message after 3 seconds
                setTimeout(() => {
                    updateMessage.classList.remove("show");
                }, 3000);
            } else {
                alert("❌ " + data.message);
            }
        } catch (error) {
            console.error("Error:", error);
            alert("Something went wrong while updating your profile.");
        }
    });
});
