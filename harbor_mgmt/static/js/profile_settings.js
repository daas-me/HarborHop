document.addEventListener('DOMContentLoaded', function () {
  //  helpers 
  function getCookie(name) {
    const cookie = document.cookie.split('; ').find(r => r.trim().startsWith(name + '='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : null;
  }
  function showAlert(msg) {
    // using alert for now to match existing behavior
    alert(msg);
  }

  //  tabs wiring (existing) 
  const container = document.querySelector('.container');
  const defaultTab = container?.dataset?.activeTab || 'personal';
  const tabsContainer = document.querySelector('.tabs');
  const tabs = document.querySelectorAll('.tab');
  const sections = document.querySelectorAll('.content-section');

  function setActiveTab(tabName) {
    tabs.forEach(t => {
      const active = t.dataset.tab === tabName;
      t.classList.toggle('active', active);
      t.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    sections.forEach(s => {
      const active = s.id === tabName;
      s.classList.toggle('active', active);
      if (active) s.removeAttribute('hidden'); else s.setAttribute('hidden', 'true');
    });
  }
  setActiveTab(defaultTab);
  if (tabsContainer) {
    tabsContainer.addEventListener('click', (e) => {
      const btn = e.target.closest('.tab');
      if (!btn) return;
      const name = btn.dataset.tab;
      if (!name) return;
      setActiveTab(name);
    });
    tabsContainer.addEventListener('keydown', (e) => {
      const btn = e.target.closest('.tab');
      if (!btn) return;
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        const name = btn.dataset.tab;
        setActiveTab(name);
      }
    });
  }

  //  profile photo upload / remove 
  const changeBtn = document.getElementById('changePhotoBtn');
  const removeBtn = document.getElementById('removePhotoBtn');
  const photoInput = document.getElementById('photoInput');
  const photoForm = document.getElementById('photoForm');
  const profilePhotoWrapper = document.getElementById('profilePhotoWrapper');

  if (changeBtn && photoInput && photoForm) {
    changeBtn.addEventListener('click', () => photoInput.click());

    photoInput.addEventListener('change', async () => {
      if (!photoInput.files || photoInput.files.length === 0) return;
      const file = photoInput.files[0];

      const maxMB = 8;
      if (file.size > maxMB * 1024 * 1024) {
        showAlert(`File is too large. Max ${maxMB} MB allowed.`);
        photoInput.value = '';
        return;
      }

      const action = photoForm.getAttribute('action');
      if (!action) {
        photoForm.submit();
        return;
      }

      const formData = new FormData();
      formData.append('photo', file);

      try {
        const resp = await fetch(action, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: formData
        });

        if (!resp.ok) {
          photoForm.submit();
          return;
        }

        const contentType = resp.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
          photoForm.submit();
          return;
        }

        const data = await resp.json();
        if (data && data.success) {
          const imageUrlRaw = data.image_url || data.photo_url || data.url || null;
          if (imageUrlRaw) {
            let src = imageUrlRaw;
            if (src.startsWith('/')) src = window.location.origin + src;
            const busted = src + (src.includes('?') ? '&' : '?') + 'v=' + Date.now();
            if (profilePhotoWrapper) {
              profilePhotoWrapper.innerHTML = `<img src="${busted}" alt="Profile Photo" id="profilePhoto">`;
            }
            if (removeBtn) removeBtn.disabled = false;
          } else {
            // ensure UI consistent if server doesn't return a URL
            location.reload();
          }
        } else {
          showAlert(data?.message || 'Upload failed. Please try again.');
        }

      } catch (err) {
        console.error('upload error', err);
        try { photoForm.submit(); } catch (e) { showAlert('Upload failed.'); }
      } finally {
        photoInput.value = '';
      }
    });
  }

  if (removeBtn) {
    removeBtn.addEventListener('click', async () => {
      if (!confirm('Remove profile photo?')) return;
      const removeUrl = container?.dataset?.removePhotoUrl;
      const initials = profilePhotoWrapper?.dataset?.initials || '';

      if (!removeUrl) {
        if (profilePhotoWrapper) profilePhotoWrapper.innerHTML = `<span id="profilePhotoPlaceholder">${initials}</span>`;
        removeBtn.disabled = true;
        return;
      }

      try {
        const resp = await fetch(removeUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({ remove: true })
        });

        if (!resp.ok) {
          const text = await resp.text().catch(() => '');
          console.warn('remove non-ok', resp.status, text);
          showAlert('Failed to remove photo. Try again.');
          return;
        }

        const data = await resp.json().catch(() => null);
        if (data && data.success) {
          if (profilePhotoWrapper) profilePhotoWrapper.innerHTML = `<span id="profilePhotoPlaceholder">${initials}</span>`;
          removeBtn.disabled = true;
          setTimeout(() => location.reload(), 300);
        } else {
          showAlert(data?.message || 'Failed to remove photo.');
        }
      } catch (err) {
        console.error('remove error', err);
        showAlert('Error removing photo. Try again.');
      }
    });
  }

  if (!document.getElementById('profilePhoto') && removeBtn) removeBtn.disabled = true;

  //  Delete account wiring 
  const deleteBtn = document.getElementById('deleteAccountBtn');
  const deleteForm = document.getElementById('deleteAccountForm'); // fallback form

  if (deleteBtn) {
    deleteBtn.addEventListener('click', async () => {
      // Strong confirm message
      const confirmText = "Are you sure you want to permanently delete your account? This action cannot be undone. Type 'DELETE' to confirm.";
      // prompt ensures user explicitly types DELETE
      const typed = prompt(confirmText, "");
      if (!typed || typed.trim().toUpperCase() !== 'DELETE') {
        alert('Account deletion cancelled.');
        return;
      }

      // AJAX POST to delete endpoint
      const deleteUrl = "{% url 'delete_account' %}"; // Django will render this in the template
      try {
        const resp = await fetch(deleteUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({ confirm: true })
        });

        // If not JSON (redirect), fall back to form submit
        if (!resp.ok) {
          // fallback: submit the hidden form (non-AJAX) so server can handle redirect
          if (deleteForm) {
            deleteForm.submit();
            return;
          }
          showAlert('Failed to delete account. Please try again.');
          return;
        }

        const data = await resp.json().catch(() => null);
        if (data && data.success) {
          // On success, server logs out user and returns success.
          // Redirect to logout or homepage — server may have already logged out.
          const redirectTo = data.redirect || '{% url "home" %}';
          alert(data.message || 'Your account has been deleted.');
          window.location.href = redirectTo;
        } else {
          showAlert(data?.message || 'Failed to delete account. Please try again.');
        }

      } catch (err) {
        console.error('delete account error', err);
        // fallback to full form submit to let server handle it
        if (deleteForm) deleteForm.submit();
        else showAlert('Failed to delete account. Please try again later.');
      }
    });
  }

  //  hide updateMessage if empty 
  const updateMessageEl = document.getElementById('updateMessage');
  if (updateMessageEl) {
    if (!updateMessageEl.textContent || !updateMessageEl.textContent.trim()) {
      updateMessageEl.style.display = 'none';
    } else {
      updateMessageEl.classList.add('success-message');
    }
  }
});
