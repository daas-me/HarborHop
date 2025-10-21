// Utility function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    if (!cookieValue) {
        const tokenInput = document.querySelector('[name="csrfmiddlewaretoken"]');
        if (tokenInput) cookieValue = tokenInput.value;
    }
    return cookieValue;
}

// Show notification
function showNotification(message, type = 'info') {
    const notif = document.createElement('div');
    notif.textContent = message;
    notif.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        font-weight: 500;
        z-index: 3000;
        animation: slideIn 0.3s ease-out;
        ${type === 'success' ? 'background: #10b981; color: white;' : type === 'error' ? 'background: #ef4444; color: white;' : 'background: #3b82f6; color: white;'}
    `;
    document.body.appendChild(notif);
    setTimeout(() => notif.remove(), 3000);
}

// Show confirm modal
function showConfirmModal(username, action) {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.id = 'confirm-modal-' + Date.now();
        modal.className = 'confirm-modal';
        modal.innerHTML = `
            <div class="confirm-modal-overlay"></div>
            <div class="confirm-modal-content">
                <div class="confirm-modal-header">
                    <h2>Confirm Role Change</h2>
                    <button class="confirm-modal-close">&times;</button>
                </div>
                <div class="confirm-modal-body">
                    <p>${action === "make_admin" ? `Grant admin privileges to ${username}?` : `Remove admin privileges from ${username}?`}</p>
                </div>
                <div class="confirm-modal-footer">
                    <button class="confirm-modal-btn cancel">Cancel</button>
                    <button class="confirm-modal-btn confirm">Confirm</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        const confirmBtn = modal.querySelector('.confirm-modal-btn.confirm');
        const cancelBtn = modal.querySelector('.confirm-modal-btn.cancel');
        const closeBtn = modal.querySelector('.confirm-modal-close');
        const overlay = modal.querySelector('.confirm-modal-overlay');

        const cleanup = () => {
            confirmBtn.removeEventListener('click', onConfirm);
            cancelBtn.removeEventListener('click', onCancel);
            closeBtn.removeEventListener('click', onCancel);
            overlay.removeEventListener('click', onCancel);
            modal.remove();
        };

        const onConfirm = () => {
            cleanup();
            resolve(true);
        };

        const onCancel = () => {
            cleanup();
            resolve(false);
        };

        confirmBtn.addEventListener('click', onConfirm);
        cancelBtn.addEventListener('click', onCancel);
        closeBtn.addEventListener('click', onCancel);
        overlay.addEventListener('click', onCancel);

        modal.style.display = 'flex';
    });
}

// Show view user modal
function showViewUserModal(username, fullName, email) {
    const modal = document.createElement('div');
    modal.className = 'view-user-modal';
    modal.innerHTML = `
        <div class="modal-overlay"></div>
        <div class="modal-content">
            <div class="modal-header"><h2>User Details</h2><button class="modal-close">&times;</button></div>
            <div class="modal-body">
                <div class="detail-group"><label>Username:</label><p>${username}</p></div>
                <div class="detail-group"><label>Full Name:</label><p>${fullName}</p></div>
                <div class="detail-group"><label>Email:</label><p>${email}</p></div>
            </div>
            <div class="modal-footer"><button class="btn-close">Close</button></div>
        </div>
    `;
    document.body.appendChild(modal);
    const closeModal = () => modal.remove();
    modal.querySelector('.modal-close').addEventListener('click', closeModal);
    modal.querySelector('.btn-close').addEventListener('click', closeModal);
    modal.querySelector('.modal-overlay').addEventListener('click', closeModal);
}

// Show edit user modal
function showEditUserModal(userId, firstName, lastName, email, role) {
    const modal = document.createElement('div');
    modal.className = 'edit-user-modal';
    modal.innerHTML = `
        <div class="modal-overlay"></div>
        <div class="modal-content">
            <div class="modal-header">
                <h2>Edit User</h2>
                <button class="modal-close">&times;</button>
            </div>
            <form class="edit-user-form">
                <div class="form-group">
                    <label>First Name</label>
                    <input type="text" name="first_name" value="${firstName}" autocomplete="off">
                </div>
                <div class="form-group">
                    <label>Last Name</label>
                    <input type="text" name="last_name" value="${lastName}" autocomplete="off">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" value="${email}" required autocomplete="off">
                </div>
                <div class="form-group checkbox-group">
                    <label>
                        <input type="checkbox" name="is_admin" ${role === 'admin' ? 'checked' : ''}>
                        <span>Make Admin</span>
                    </label>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn-cancel">Cancel</button>
                    <button type="submit" class="btn-submit">Save Changes</button>
                </div>
            </form>
        </div>
    `;
    document.body.appendChild(modal);
    
    const closeModal = () => modal.remove();
    const form = modal.querySelector('.edit-user-form');
    const submitBtn = modal.querySelector('.btn-submit');
    
    modal.querySelector('.modal-close').addEventListener('click', closeModal);
    modal.querySelector('.btn-cancel').addEventListener('click', closeModal);
    modal.querySelector('.modal-overlay').addEventListener('click', closeModal);
    
    let isSubmitting = false;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (isSubmitting) {
            console.log('Already submitting...');
            return;
        }
        
        isSubmitting = true;
        submitBtn.disabled = true;
        const originalText = submitBtn.textContent;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
        
        const formData = new FormData(e.target);
        const csrfToken = getCookie('csrftoken');
        
        console.log('=== EDIT USER REQUEST ===');
        console.log('User ID:', userId);
        console.log('First Name:', formData.get('first_name'));
        console.log('Last Name:', formData.get('last_name'));
        console.log('Email:', formData.get('email'));
        console.log('Is Admin:', formData.get('is_admin') === 'on');
        console.log('CSRF Token:', csrfToken ? 'Present' : 'MISSING!');
        
        if (!csrfToken) {
            console.error('CSRF token not found!');
            showNotification('Security token missing. Please refresh the page.', 'error');
            isSubmitting = false;
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
            return;
        }
        
        try {
            console.log(`Sending request to /edit-user/${userId}/...`);
            
            const response = await fetch(`/edit-user/${userId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
                credentials: 'include',
            });
            
            console.log('Response status:', response.status);
            console.log('Response ok:', response.ok);
            console.log('Response URL:', response.url);
            console.log('Response redirected:', response.redirected);
            
            // Check for redirect to login
            if (response.redirected && response.url.includes('/login')) {
                console.error('Session expired - redirected to login');
                showNotification('Your session has expired. Please log in again.', 'error');
                setTimeout(() => {
                    window.location.href = '/login/?next=/admin-dashboard/users/';
                }, 2000);
                return;
            }
            
            // Parse JSON response
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Server did not return JSON. Content-Type:', contentType);
                const text = await response.text();
                console.error('Response text (first 500 chars):', text.substring(0, 500));
                throw new Error('Server returned invalid response format');
            }
            
            const data = await response.json();
            console.log('Response data:', data);
            
            if (response.ok && data.success) {
                console.log('✓ User updated successfully!');
                showNotification('User updated successfully!', 'success');
                closeModal();
                
                setTimeout(() => {
                    console.log('Reloading page...');
                    location.reload();
                }, 1500);
            } else {
                console.error('Server error:', data.message);
                showNotification(data.message || 'Error updating user', 'error');
                isSubmitting = false;
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
            
        } catch (error) {
            console.error('Fetch error:', error);
            showNotification('An error occurred: ' + error.message, 'error');
            isSubmitting = false;
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    });
}

// Show delete user modal
function showDeleteUserModal(userId, username, fullName) {
    const modal = document.createElement('div');
    modal.className = 'delete-user-modal';
    modal.innerHTML = `
        <div class="modal-overlay"></div>
        <div class="modal-content">
            <div class="modal-header">
                <h2>Delete User</h2>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="delete-warning">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <p><strong>Warning:</strong> This action cannot be undone.</p>
                </div>
                <p>Are you sure you want to delete <strong>${fullName}</strong> (${username})?</p>
                <p>All associated data will be permanently removed from the system.</p>
            </div>
            <div class="modal-footer">
                <button class="btn-cancel">Cancel</button>
                <button class="btn-delete">Delete User</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    const closeModal = () => modal.remove();
    const cancelBtn = modal.querySelector('.btn-cancel');
    const deleteBtn = modal.querySelector('.btn-delete');
    const closeBtn = modal.querySelector('.modal-close');
    const overlay = modal.querySelector('.modal-overlay');

    cancelBtn.addEventListener('click', closeModal);
    closeBtn.addEventListener('click', closeModal);
    overlay.addEventListener('click', closeModal);

    deleteBtn.addEventListener('click', async () => {
        deleteBtn.disabled = true;
        deleteBtn.textContent = 'Deleting...';

        try {
            const response = await fetch(`/delete-user/${userId}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            });

            const data = await response.json();
            if (data.success) {
                showNotification('User deleted successfully!', 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                showNotification(data.message || 'Error deleting user', 'error');
                deleteBtn.disabled = false;
                deleteBtn.textContent = 'Delete User';
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('An error occurred', 'error');
            deleteBtn.disabled = false;
            deleteBtn.textContent = 'Delete User';
        }
    });
}

// Show add user modal
function showAddUserModal() {
    const modal = document.createElement('div');
    modal.className = 'add-user-modal';
    modal.innerHTML = `
        <div class="modal-overlay"></div>
        <div class="modal-content">
            <div class="modal-header">
                <h2>Add New User</h2>
                <button class="modal-close">&times;</button>
            </div>
            <form class="add-user-form">
                <div class="form-group">
                    <label for="username">Username *</label>
                    <input type="text" id="username" name="username" required autocomplete="off">
                </div>
                <div class="form-group">
                    <label for="email">Email *</label>
                    <input type="email" id="email" name="email" required autocomplete="off">
                </div>
                <div class="form-group">
                    <label for="first_name">First Name</label>
                    <input type="text" id="first_name" name="first_name" autocomplete="off">
                </div>
                <div class="form-group">
                    <label for="last_name">Last Name</label>
                    <input type="text" id="last_name" name="last_name" autocomplete="off">
                </div>
                <div class="form-group">
                    <label for="password">Password *</label>
                    <input type="password" id="password" name="password" required autocomplete="new-password">
                </div>
                <div class="form-group checkbox-group">
                    <label>
                        <input type="checkbox" name="is_admin">
                        <span>Make Admin</span>
                    </label>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn-cancel">Cancel</button>
                    <button type="submit" class="btn-submit">Add User</button>
                </div>
            </form>
        </div>
    `;
    document.body.appendChild(modal);

    const closeModal = () => modal.remove();
    const form = modal.querySelector('.add-user-form');
    const submitBtn = modal.querySelector('.btn-submit');
    
    modal.querySelector('.modal-close').addEventListener('click', closeModal);
    modal.querySelector('.btn-cancel').addEventListener('click', closeModal);
    modal.querySelector('.modal-overlay').addEventListener('click', closeModal);

    let isSubmitting = false;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (isSubmitting) {
            console.log('Already submitting...');
            return;
        }
        
        isSubmitting = true;
        submitBtn.disabled = true;
        const originalText = submitBtn.textContent;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Adding...';
        
        const formData = new FormData(e.target);
        const csrfToken = getCookie('csrftoken');
        
        console.log('=== ADD USER REQUEST ===');
        console.log('Username:', formData.get('username'));
        console.log('Email:', formData.get('email'));
        console.log('CSRF Token:', csrfToken ? 'Present' : 'MISSING!');
        
        if (!csrfToken) {
            console.error('CSRF token not found!');
            showNotification('Security token missing. Please refresh the page.', 'error');
            isSubmitting = false;
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            return;
        }
        
        try {
            console.log('Sending request to /add-user/...');
            
            // FIXED: Correct URL without /admin/ prefix
            const response = await fetch('/add-user/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
                credentials: 'include', 
            });
            
            console.log('Response status:', response.status);
            console.log('Response ok:', response.ok);
            console.log('Response URL:', response.url);
            console.log('Response redirected:', response.redirected);
            
            // Check for redirect to login (session expired)
            if (response.redirected && response.url.includes('/login')) {
                console.error('Session expired - redirected to login');
                showNotification('Your session has expired. Please log in again.', 'error');
                setTimeout(() => {
                    window.location.href = '/login/?next=/admin-dashboard/users/';
                }, 2000);
                return;
            }
            
            // Parse JSON response
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Server did not return JSON. Content-Type:', contentType);
                const text = await response.text();
                console.error('Response text (first 500 chars):', text.substring(0, 500));
                throw new Error('Server returned invalid response format');
            }
            
            const data = await response.json();
            console.log('Response data:', data);
            
            if (response.ok && data.success) {
                console.log('✓ User added successfully!');
                showNotification('User added successfully!', 'success');
                closeModal();
                
                setTimeout(() => {
                    console.log('Reloading page...');
                    location.reload();
                }, 1500);
            } else {
                console.error('Server error:', data.message);
                showNotification(data.message || 'Error adding user', 'error');
                isSubmitting = false;
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
            
        } catch (error) {
            console.error('Fetch error:', error);
            showNotification('An error occurred: ' + error.message, 'error');
            isSubmitting = false;
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    });
}

// Custom status confirmation modal
function showStatusConfirmModal(isActive) {
  return new Promise((resolve) => {
    const modal = document.createElement('div');
    modal.className = 'confirm-modal';
    modal.id = 'confirm-modal-' + Date.now();
    modal.style.display = 'flex';
    modal.innerHTML = `
      <div class="confirm-modal-overlay"></div>
      <div class="confirm-modal-content">
        <div class="confirm-modal-header">
          <h2>Confirm Status Change</h2>
          <button class="confirm-modal-close">&times;</button>
        </div>
        <div class="confirm-modal-body">
          <p>Are you sure you want to ${isActive ? 'deactivate' : 'activate'} this user?</p>
        </div>
        <div class="confirm-modal-footer">
          <button class="confirm-modal-btn cancel">Cancel</button>
          <button class="confirm-modal-btn confirm">Confirm</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
    const confirmBtn = modal.querySelector('.confirm-modal-btn.confirm');
    const cancelBtn = modal.querySelector('.confirm-modal-btn.cancel');
    const closeBtn = modal.querySelector('.confirm-modal-close');
    const overlay = modal.querySelector('.confirm-modal-overlay');
    const cleanup = () => modal.remove();
    confirmBtn.addEventListener('click', () => { cleanup(); resolve(true); });
    cancelBtn.addEventListener('click', () => { cleanup(); resolve(false); });
    closeBtn.addEventListener('click', () => { cleanup(); resolve(false); });
    overlay.addEventListener('click', () => { cleanup(); resolve(false); });
    document.onkeydown = (e) => { if (e.key === 'Escape') { cleanup(); resolve(false); } };
  });
}


// Main initialization
function initializeAdminUsers() {
    const searchInput = document.querySelector(".search-input");
    const filterButtons = document.querySelectorAll(".filter-btn");
    const addUserBtn = document.querySelector('.add-user-btn');

    // Filter table functionality
    function filterTable() {
        const searchValue = searchInput.value.toLowerCase();
        const activeFilter = document.querySelector(".filter-btn.active")?.textContent.trim() || "All Users";

        document.querySelectorAll(".users-table tbody tr").forEach(row => {
            if (row.textContent.includes("No users found")) return;

            const name = row.querySelector(".user-name-text")?.textContent.toLowerCase() || "";
            const username = row.querySelector(".user-username")?.textContent.toLowerCase() || "";
            const email = row.querySelector("td:nth-child(3)")?.textContent.toLowerCase() || "";
            
            let roleText = row.querySelector(".role-badge")?.textContent.trim().toLowerCase() || 
                          row.querySelector(".role-badge-btn")?.textContent.toLowerCase() || "";
            roleText = roleText.split("(")[0].trim();

            const matchesSearch = name.includes(searchValue) || username.includes(searchValue) || email.includes(searchValue);

            let matchesFilter = true;
            if (activeFilter === "Admins") matchesFilter = roleText.includes("admin");
            else if (activeFilter === "Regular") matchesFilter = roleText.includes("user") && !roleText.includes("admin");
            else if (activeFilter === "Recent") {
                const joinedText = row.querySelector("td:nth-child(6)")?.textContent.trim();
                const joinedDate = new Date(joinedText);
                const now = new Date();
                const diffDays = (now - joinedDate) / (1000 * 60 * 60 * 24);
                matchesFilter = diffDays <= 30;
            }

            row.style.display = (matchesSearch && matchesFilter) ? "" : "none";
        });
    }

    // Search event
    if (searchInput) {
        searchInput.addEventListener("keyup", filterTable);
    }

    // Filter buttons event
    filterButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            filterButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            filterTable();
        });
    });

    // Add User button
    if (addUserBtn) {
        addUserBtn.addEventListener('click', showAddUserModal);
    }

    // Role change handler - UPDATED VERSION
    document.addEventListener('click', async (e) => {
        // Check if the clicked element or its parent is a role badge button
        let btn = null;
        if (e.target.classList.contains('role-badge-btn')) {
            btn = e.target;
        } else if (e.target.closest('.role-badge-btn')) {
            btn = e.target.closest('.role-badge-btn');
        }
        
        if (!btn) return;
        
        console.log('Role button clicked:', btn);
        
        e.preventDefault();
        e.stopPropagation();

        const form = btn.closest("form");
        console.log('Form found:', form);
        
        if (!form) {
            console.error("Form not found for role button");
            showNotification('Error: Form not found', 'error');
            return;
        }

        const userId = form.querySelector('input[name="user_id"]')?.value;
        const action = form.querySelector('input[name="action"]')?.value;
        const username = btn.closest("tr")?.querySelector(".user-username")?.textContent.replace("@", "").trim() || "user";

        console.log('Role change details:', {userId, action, username});

        if (!userId || !action) {
            console.error("Missing userId or action", {userId, action});
            showNotification('Error: Missing user information', 'error');
            return;
        }

        console.log('Showing confirm modal...');
        const confirmed = await showConfirmModal(username, action);
        console.log('Modal result:', confirmed);
        
        if (!confirmed) {
            console.log('User cancelled the action');
            return;
        }

        // Disable button during request
        btn.disabled = true;
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Updating...';

        try {
            const csrfToken = getCookie('csrftoken');
            console.log('CSRF Token:', csrfToken ? 'Found' : 'Not found');
            
            if (!csrfToken) {
                throw new Error('CSRF token not found');
            }
            
            const response = await fetch('/change-user-role/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ 
                    user_id: parseInt(userId), 
                    action: action 
                })
            });

            console.log('Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.success) {
                showNotification(data.message, 'success');
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                showNotification(data.message || 'Error updating role', 'error');
                btn.disabled = false;
                btn.innerHTML = originalHTML;
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showNotification('An error occurred: ' + error.message, 'error');
            btn.disabled = false;
            btn.innerHTML = originalHTML;
        }
    });

    // Action buttons handler
    document.addEventListener('click', (e) => {
    if (!e.target.closest('.action-icon-btn')) return;

    const btn = e.target.closest('.action-icon-btn');
    e.preventDefault();
    e.stopPropagation(); // Prevent event bubbling
    
    const row = btn.closest('tr');
    const username = row.querySelector('.user-username')?.textContent.replace('@', '') || 'user';
    const userFullName = row.querySelector('.user-name-text')?.textContent || username;
    const userEmail = row.querySelector('td:nth-child(3)')?.textContent || '';

    if (btn.title === 'View') {
        showViewUserModal(username, userFullName, userEmail);
    } else if (btn.classList.contains('edit-btn')) {
                const userId = btn.dataset.userId;
                const firstName = btn.dataset.firstName;
                const lastName = btn.dataset.lastName;
                const email = btn.dataset.email;
                const role = btn.dataset.role;
                showEditUserModal(userId, firstName, lastName, email, role);
    } else if (btn.classList.contains('delete')) {
        const userId = btn.dataset.userId || btn.getAttribute('data-user-id');
        const deleteUsername = btn.dataset.username || btn.getAttribute('data-username');
        const deleteFullName = btn.dataset.fullname || btn.getAttribute('data-fullname');
        showDeleteUserModal(userId, deleteUsername, deleteFullName);
    }
});
}

// Run when DOM is ready
if (document.readyState === 'loading') {
}


// Run when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAdminUsers);
} else {
    initializeAdminUsers();
}

// ✅ Manage Active/Inactive user toggle
document.addEventListener('click', async function (e) {
  const badge = e.target.closest('.toggle-status');
  if (!badge) return;

  const userId = badge.dataset.userId;
  const isActive = badge.dataset.active === 'true';

  // Prevent toggling your own status
  if (badge.closest('tr')?.querySelector('.role-badge')?.textContent.includes('(You)')) {
    showNotification("You can't change your own status.", 'error');
    return;
  }

  // Confirmation modal
  const confirmed = await showStatusConfirmModal(isActive);
  if (!confirmed) return;

  // 🔄 Create spinner badge
  const originalHTML = badge.outerHTML;
  const spinnerBadge = document.createElement('span');
  spinnerBadge.className = 'status-badge updating';
  spinnerBadge.innerHTML = `<i class="fa-solid fa-spinner custom-spin"></i> Updating...`;

  // Optional: control spinner speed via JS
  spinnerBadge.querySelector('.custom-spin').style.animationDuration = '8s';

  badge.replaceWith(spinnerBadge);

  try {
    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) throw new Error('CSRF token not found');

    const resp = await fetch(`/toggle-user-active-ajax/${userId}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    const data = await resp.json();

    if (data.success) {
      // CASE 1: Full row HTML returned
      if (data.row_html) {
        const row = spinnerBadge.closest('tr');
        const tempDiv = document.createElement('tbody');
        tempDiv.innerHTML = data.row_html.trim();
        const newRow = tempDiv.firstElementChild;
        if (row && newRow) row.replaceWith(newRow);
      }
      // CASE 2: Only badge HTML returned
      else if (data.badge_html) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = data.badge_html.trim();
        const newBadge = tempDiv.firstElementChild;
        newBadge.classList.add('toggle-status');
        newBadge.dataset.userId = userId;
        newBadge.dataset.active = data.is_active ? 'true' : 'false';
        spinnerBadge.replaceWith(newBadge);
      }

      showNotification('User status updated!', 'success');
    } else {
      showNotification(data.message || 'Error updating status', 'error');
      spinnerBadge.outerHTML = originalHTML;
    }
  } catch (error) {
    console.error(error);
    showNotification('An error occurred.', 'error');
    spinnerBadge.outerHTML = originalHTML;
  }
});
