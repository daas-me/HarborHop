document.addEventListener('DOMContentLoaded', function () {
  // ---------- helpers ----------
  function log(...args) { /* console.log('[profile_settings]', ...args); */ }
  function getCookie(name) {
    const cookie = document.cookie.split('; ').find(r => r.trim().startsWith(name + '='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : null;
  }
  function showAlert(msg) {
    // simple alert (keeps behavior consistent). Replace with custom UI if needed.
    alert(msg);
  }

  // ---------- tabs wiring ----------
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

  // ---------- photo upload / remove wiring ----------
  const changeBtn = document.getElementById('changePhotoBtn');
  const removeBtn = document.getElementById('removePhotoBtn');
  const photoInput = document.getElementById('photoInput');
  const photoForm = document.getElementById('photoForm');
  const profilePhotoWrapper = document.getElementById('profilePhotoWrapper');

  // If wrapper not present, create a safe stub to avoid crashes
  if (!profilePhotoWrapper) {
    console.warn('[profile_settings] profilePhotoWrapper not found in DOM');
  }

  // Upload handler (AJAX with fallback)
  if (changeBtn && photoInput && photoForm) {
    changeBtn.addEventListener('click', () => photoInput.click());

    photoInput.addEventListener('change', async () => {
      if (!photoInput.files || photoInput.files.length === 0) return;
      const file = photoInput.files[0];

      // optional client-side size limit
      const maxMB = 8;
      if (file.size > maxMB * 1024 * 1024) {
        showAlert(`File is too large. Max ${maxMB} MB allowed.`);
        photoInput.value = '';
        return;
      }

      const action = photoForm.getAttribute('action');
      if (!action) {
        console.error('[profile_settings] photoForm action attribute missing; falling back to full submit.');
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

        // If response isn't OK, fallback to form submit (handles redirects/login pages)
        if (!resp.ok) {
          console.warn('[profile_settings] upload response not ok (status ' + resp.status + '), falling back to full submit.');
          photoForm.submit();
          return;
        }

        const contentType = resp.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
          // server returned HTML or redirect — fallback to full submit
          photoForm.submit();
          return;
        }

        const data = await resp.json();

        if (data && data.success) {
          // tolerate multiple key names returned by different backends
          const imageUrlRaw = data.image_url || data.photo_url || data.photoUrl || data.url || data.path || null;

          if (imageUrlRaw) {
            // convert relative path ("/media/...") to absolute
            let src = imageUrlRaw;
            if (src.startsWith('/')) {
              src = window.location.origin + src;
            }

            // cache-bust query param to force browser to fetch new image
            const busted = src + (src.includes('?') ? '&' : '?') + 'v=' + Date.now();

            if (profilePhotoWrapper) {
              profilePhotoWrapper.innerHTML = `<img src="${busted}" alt="Profile Photo" id="profilePhoto">`;
              // store initials if dataset not present (used by remove fallback)
              if (!profilePhotoWrapper.dataset.initials) {
                profilePhotoWrapper.dataset.initials = (profilePhotoWrapper.textContent || '').trim().slice(0,4);
              }
            }

            if (removeBtn) removeBtn.disabled = false;
          } else {
            // server returned success but no URL -> reload to let server render
            location.reload();
          }

        } else {
          showAlert(data?.message || 'Upload failed. Please try again.');
        }

      } catch (err) {
        console.error('[profile_settings] upload error', err);
        // final fallback to full form submit
        try { photoForm.submit(); } catch (e) { showAlert('Upload failed.'); }
      } finally {
        // reset input so change event will trigger again for same file
        photoInput.value = '';
      }
    });
  } else {
    // If one of the pieces missing just log; doesn't break other behavior
    log('upload UI not fully present (changeBtn/photoInput/photoForm)');
  }

  // Remove handler (AJAX) — clears server-side and updates UI locally, then reloads
  if (removeBtn) {
    removeBtn.addEventListener('click', async () => {
      if (!confirm('Remove profile photo?')) return;

      const removeUrl = container?.dataset?.removePhotoUrl;
      const initials = profilePhotoWrapper?.dataset?.initials || '';

      if (!removeUrl) {
        // fallback: client-only
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
          // not ok -> show message
          const text = await resp.text().catch(() => '');
          console.warn('[profile_settings] remove returned non-ok', resp.status, text);
          showAlert('Failed to remove photo. Try again.');
          return;
        }

        // try parse JSON
        const data = await resp.json().catch(() => null);
        if (data && data.success) {
          if (profilePhotoWrapper) profilePhotoWrapper.innerHTML = `<span id="profilePhotoPlaceholder">${initials}</span>`;
          removeBtn.disabled = true;
          // reload so server-rendered pages show consistent state
          setTimeout(() => location.reload(), 300);
        } else {
          showAlert(data?.message || 'Failed to remove photo.');
        }
      } catch (err) {
        console.error('[profile_settings] remove error', err);
        showAlert('Error removing photo. Try again.');
      }
    });
  }

  // If no image exists at load, disable remove button
  const profileImgEl = document.getElementById('profilePhoto');
  if (!profileImgEl && removeBtn) removeBtn.disabled = true;

  // hide updateMessage if no content
  const updateMessageEl = document.getElementById('updateMessage');
  if (updateMessageEl) {
    if (!updateMessageEl.textContent || !updateMessageEl.textContent.trim()) {
      updateMessageEl.style.display = 'none';
    } else {
      updateMessageEl.classList.add('success-message');
    }
  }

  // done
  log('profile_settings script loaded');
});
