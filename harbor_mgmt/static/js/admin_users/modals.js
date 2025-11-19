import { getCookie, showNotification } from './utils.js';

export function showConfirmModal(username, action) {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.id = `confirm-modal-${Date.now()}`;
        modal.className = 'confirm-modal';
        modal.innerHTML = `
            <div class="confirm-modal-overlay"></div>
            <div class="confirm-modal-content">
                <div class="confirm-modal-header">
                    <h2>Confirm Role Change</h2>
                    <button class="confirm-modal-close">&times;</button>
                </div>
                <div class="confirm-modal-body">
                    <p>${action === 'make_admin'
                        ? `Grant admin privileges to ${username}?`
                        : `Remove admin privileges from ${username}?`}</p>
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

export function showViewUserModal(username, fullName, email) {
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

export function showEditUserModal(userId, firstName, lastName, email, role) {
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

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        if (isSubmitting) {
            console.log('Already submitting...');
            return;
        }

        isSubmitting = true;
        submitBtn.disabled = true;
        const originalText = submitBtn.textContent;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

        const formData = new FormData(event.target);
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

            if (response.redirected && response.url.includes('/login')) {
                console.error('Session expired - redirected to login');
                showNotification('Your session has expired. Please log in again.', 'error');
                setTimeout(() => {
                    window.location.href = '/login/?next=/admin-dashboard/users/';
                }, 2000);
                return;
            }

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
                    window.location.reload();
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
            showNotification(`An error occurred: ${error.message}`, 'error');
            isSubmitting = false;
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    });
}

export function showDeleteUserModal(userId, username, fullName) {
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
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
            });

            const data = await response.json();
            if (data.success) {
                showNotification('User deleted successfully!', 'success');
                setTimeout(() => window.location.reload(), 1500);
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

export function showAddUserModal() {
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

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        if (isSubmitting) {
            console.log('Already submitting...');
            return;
        }

        isSubmitting = true;
        submitBtn.disabled = true;
        const originalText = submitBtn.textContent;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Adding...';

        const formData = new FormData(event.target);
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

            if (response.redirected && response.url.includes('/login')) {
                console.error('Session expired - redirected to login');
                showNotification('Your session has expired. Please log in again.', 'error');
                setTimeout(() => {
                    window.location.href = '/login/?next=/admin-dashboard/users/';
                }, 2000);
                return;
            }

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
                    window.location.reload();
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
            showNotification(`An error occurred: ${error.message}`, 'error');
            isSubmitting = false;
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    });
}

export function showStatusConfirmModal(isActive) {
    return new Promise((resolve) => {
        const previousKeyHandler = document.onkeydown;
        const modal = document.createElement('div');
        modal.className = 'confirm-modal';
        modal.id = `confirm-modal-${Date.now()}`;
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

        const cleanup = (result) => {
            confirmBtn.removeEventListener('click', onConfirm);
            cancelBtn.removeEventListener('click', onCancel);
            closeBtn.removeEventListener('click', onCancel);
            overlay.removeEventListener('click', onCancel);
            document.onkeydown = previousKeyHandler;
            modal.remove();
            resolve(result);
        };

        const onConfirm = () => cleanup(true);
        const onCancel = () => cleanup(false);

        confirmBtn.addEventListener('click', onConfirm);
        cancelBtn.addEventListener('click', onCancel);
        closeBtn.addEventListener('click', onCancel);
        overlay.addEventListener('click', onCancel);

        document.onkeydown = (event) => {
            if (event.key === 'Escape') {
                onCancel();
            }
        };
    });
}
