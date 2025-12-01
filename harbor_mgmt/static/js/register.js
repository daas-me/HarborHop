// static/js/register_dob.js
document.addEventListener('DOMContentLoaded', function () {
  const dobInput = document.getElementById('id_date_of_birth'); // must match forms.py widget id
  const form = document.querySelector('form');

  if (!dobInput || !form) return;

  // set max date = today minus 15 years
  const today = new Date();
  const maxYear = today.getFullYear() - 15;
  const maxDate = new Date(maxYear, today.getMonth(), today.getDate());

  function toIso(d) {
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${d.getFullYear()}-${mm}-${dd}`;
  }

  dobInput.setAttribute('max', toIso(maxDate));

  // find parent form-group to append client-side error message
  const parent = dobInput.closest('.form-group') || dobInput.parentNode;
  let clientErr = parent.querySelector('#dob-client-error');
  if (!clientErr) {
    clientErr = document.createElement('div');
    clientErr.id = 'dob-client-error';
    clientErr.style.color = 'red';
    clientErr.style.marginTop = '6px';
    clientErr.style.display = 'none';
    parent.appendChild(clientErr);
  }

  function calculateAgeFromIso(isoStr) {
    if (!isoStr) return -1;
    const [y, m, d] = isoStr.split('-').map(Number);
    const dob = new Date(y, m - 1, d);
    const now = new Date();
    let age = now.getFullYear() - dob.getFullYear();
    const mDiff = now.getMonth() - dob.getMonth();
    if (mDiff < 0 || (mDiff === 0 && now.getDate() < dob.getDate())) age--;
    return age;
  }

  dobInput.addEventListener('change', function () {
    const age = calculateAgeFromIso(this.value);
    if (age < 15) {
      clientErr.textContent = 'You must be at least 15 years old to register.';
      clientErr.style.display = 'block';
    } else {
      clientErr.textContent = '';
      clientErr.style.display = 'none';
    }
  });

  form.addEventListener('submit', function (e) {
    const age = calculateAgeFromIso(dobInput.value);
    if (age < 15) {
      e.preventDefault();
      clientErr.textContent = 'You must be at least 15 years old to register.';
      clientErr.style.display = 'block';
      dobInput.focus();
    }
  });
});
