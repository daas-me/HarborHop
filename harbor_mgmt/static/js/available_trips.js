document.addEventListener('DOMContentLoaded', () => {
    const scheduleCards = Array.from(document.querySelectorAll('.schedule-card'));

    if (!scheduleCards.length) {
        return;
    }

    const tripType = document.body.dataset.tripType || 'one_way';
    const summaryCard = document.querySelector('.summary-card');
    const summarySections = {};
    let totalAmountEl = null;
    let continueBtn = null;
    const bookingMeta = {
        tripType,
        adults: Number(document.body.dataset.adults || 0),
        children: Number(document.body.dataset.children || 0),
        originName: document.body.dataset.originName || '',
        destinationName: document.body.dataset.destinationName || '',
        departureDate: document.body.dataset.departureDate || '',
        returnDate: document.body.dataset.returnDate || '',
    };
    let currentTotal = 0;
    let persistTimeout = null;

    if (summaryCard) {
        totalAmountEl = summaryCard.querySelector('.summary-total-amount');
        continueBtn = summaryCard.querySelector('.continue-btn');

        summaryCard.querySelectorAll('.summary-section').forEach((section) => {
            const key = section.dataset.summary;
            const content = section.querySelector('.summary-content');

            if (!key || !content) {
                return;
            }

            summarySections[key] = {
                section,
                content,
                defaultHtml: content.innerHTML,
            };
        });
    }

    const selections = {
        outbound: null,
        return: null,
    };

    const currencyFormatter = new Intl.NumberFormat('en-PH', {
        style: 'currency',
        currency: 'PHP',
        minimumFractionDigits: 2,
    });

    scheduleCards.forEach((card) => {
        const seatSelect = card.querySelector('.seat-type-select');
        const selectBtn = card.querySelector('.select-btn');

        if (seatSelect) {
            updateCardPricing(card, seatSelect);

            seatSelect.addEventListener('change', () => {
                updateCardPricing(card, seatSelect);

                if (card.classList.contains('selected')) {
                    const direction = card.dataset.direction;
                    selections[direction] = buildSelection(card);
                    updateSummary(direction);
                    updateTotalAndButton();
                    schedulePersist();
                }
            });
        }

        if (selectBtn && !selectBtn.disabled) {
            selectBtn.addEventListener('click', () => {
                if (card.classList.contains('selected')) {
                    // Unselect
                    card.classList.remove('selected');
                    selectBtn.textContent = 'Select';
                    const direction = card.dataset.direction;
                    selections[direction] = null;
                    resetSummary(direction);
                    updateTotalAndButton();
                    schedulePersist();
                } else {
                    handleCardSelection(card);
                }
            });
        }
    });

    updateTotalAndButton();

    function handleCardSelection(card) {
        const direction = card.dataset.direction;

        if (!direction) {
            return;
        }

        const seatSelect = card.querySelector('.seat-type-select');
        if (seatSelect && seatSelect.options.length === 0) {
            return;
        }

        // Deselect other cards for the same direction
        scheduleCards
            .filter((otherCard) => otherCard !== card && otherCard.dataset.direction === direction)
            .forEach((otherCard) => {
                otherCard.classList.remove('selected');
                const otherBtn = otherCard.querySelector('.select-btn');
                if (otherBtn) {
                    otherBtn.textContent = 'Select';
                }
            });

        // Mark this card as selected
        card.classList.add('selected');
        const button = card.querySelector('.select-btn');
        if (button) {
            button.textContent = 'Selected';
        }

        selections[direction] = buildSelection(card);
        updateSummary(direction);
        updateTotalAndButton();
        schedulePersist();
    }

    function buildSelection(card) {
        const direction = card.dataset.direction;
        const seatSelect = card.querySelector('.seat-type-select');
        const option = seatSelect ? seatSelect.options[seatSelect.selectedIndex] : null;
        const price = option ? parseFloat(option.dataset.price || '0') : 0;

        return {
            direction,
            vessel: card.dataset.vessel || '',
            company: card.dataset.company || '',
            departureDateTime: card.dataset.departureDatetime || '',
            departureDate: card.dataset.departureDate || '',
            departureTime: card.dataset.departureTime || '',
            originName: card.dataset.originName || '',
            destinationName: card.dataset.destinationName || '',
            accommodationName: option ? option.dataset.name || option.textContent.trim() : '',
            seatType: option ? option.dataset.seatType || option.textContent.trim() : '',
            aircon: option ? option.dataset.aircon === 'true' : false,
            remaining: option ? option.dataset.remaining || '' : '',
            price: Number.isFinite(price) ? price : 0,
        };
    }

    function updateCardPricing(card, seatSelect) {
        const option = seatSelect.options[seatSelect.selectedIndex];
        const priceBox = card.querySelector('.price');
        const seatTypeDisplay = card.querySelector('.seat-type-display');
        const seatRemainingDisplay = card.querySelector('.seat-remaining');

        if (priceBox && option) {
            const priceValue = parseFloat(option.dataset.price || '0');
            priceBox.textContent = Number.isFinite(priceValue)
                ? formatCurrency(priceValue)
                : '--';
        }

        if (seatTypeDisplay && option) {
            const seatText = option.dataset.seatType || option.dataset.name || option.textContent.trim();
            seatTypeDisplay.textContent = seatText || '--';
        }

        if (seatRemainingDisplay && option) {
            const remainingRaw = option.dataset.remaining;
            seatRemainingDisplay.textContent = remainingRaw !== undefined && remainingRaw !== ''
                ? `${remainingRaw} left`
                : '--';
        }
    }

    function updateSummary(direction) {
        const summaryData = summarySections[direction];
        const selection = selections[direction];

        if (!summaryData) {
            return;
        }

        if (!selection) {
            resetSummary(direction);
            return;
        }

        const { content } = summaryData;
        content.classList.remove('empty');
        content.innerHTML = `
            <div class="summary-line">
                <span class="summary-label">Company</span>
                <span class="summary-value">${escapeHtml(selection.company)}</span>
            </div>
            <div class="summary-line">
                <span class="summary-label">Vessel</span>
                <span class="summary-value">${escapeHtml(selection.vessel) || '—'}</span>
            </div>
            <div class="summary-line">
                <span class="summary-label">Route</span>
                <span class="summary-value">${escapeHtml(selection.originName)} → ${escapeHtml(selection.destinationName)}</span>
            </div>
            <div class="summary-line">
                <span class="summary-label">Departure Date</span>
                <span class="summary-value">${escapeHtml(selection.departureDate) || '—'}</span>
            </div>
            <div class="summary-line">
                <span class="summary-label">Departure Time</span>
                <span class="summary-value">${escapeHtml(selection.departureTime) || '—'}</span>
            </div>
            <div class="summary-line">
                <span class="summary-label">Accommodation</span>
                <span class="summary-value">${escapeHtml(selection.accommodationName) || '—'}</span>
            </div>
            <div class="summary-line">
                <span class="summary-label">Seat Type</span>
                <span class="summary-value">${escapeHtml(selection.seatType) || '—'}</span>
            </div>
            <div class="summary-line">
                <span class="summary-label">Aircon</span>
                <span class="summary-value">${selection.aircon ? 'YES' : 'NO'}</span>
            </div>
            <div class="summary-line">
                <span class="summary-label">Price</span>
                <span class="summary-value">${formatCurrency(selection.price)}</span>
            </div>
        `;
    }

    function resetSummary(direction) {
        const summaryData = summarySections[direction];
        if (!summaryData) {
            return;
        }

        const { content, defaultHtml } = summaryData;
        content.innerHTML = defaultHtml;
        content.classList.add('empty');
    }

    function updateTotalAndButton() {
        const needsReturn = tripType === 'round_trip';
        const outboundSelected = Boolean(selections.outbound);
        const returnSelected = Boolean(selections.return);

        currentTotal = [selections.outbound, selections.return]
            .filter((item) => item && Number.isFinite(item.price))
            .reduce((acc, item) => acc + item.price, 0);

        if (totalAmountEl) {
            totalAmountEl.textContent = currentTotal > 0 ? formatCurrency(currentTotal) : '₱0.00';
        }

        if (continueBtn) {
            const ready = outboundSelected && (!needsReturn || returnSelected);
            continueBtn.disabled = !ready;
            continueBtn.classList.toggle('disabled', !ready);
        }
    }

    function formatCurrency(value) {
        if (!Number.isFinite(value)) {
            return '₱0.00';
        }

        return currencyFormatter.format(value);
    }

    function escapeHtml(value) {
        if (!value) {
            return '';
        }

        return value
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function schedulePersist() {
        if (persistTimeout) {
            clearTimeout(persistTimeout);
        }
        persistTimeout = setTimeout(() => {
            persistSelectionsToServer();
        }, 200);
    }

    function getCsrfToken() {
        const name = 'csrftoken=';
        const decodedCookie = decodeURIComponent(document.cookie || '');
        const cookies = decodedCookie.split(';');
        for (const cookie of cookies) {
            const trimmed = cookie.trim();
            if (trimmed.startsWith(name)) {
                return trimmed.substring(name.length);
            }
        }
        return '';
    }

    async function persistSelectionsToServer() {
        const payload = {
            selections: {
                outbound: selections.outbound ? { ...selections.outbound } : null,
                return: selections.return ? { ...selections.return } : null,
            },
            meta: { ...bookingMeta },
            total_price: currentTotal,
        };

        try {
            await fetch('/api/store-booking-selection/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify(payload),
                credentials: 'same-origin',
            });
        } catch (err) {
            console.warn('Unable to persist booking selection', err);
        }
    }

    window.harborBooking = {
        persist: persistSelectionsToServer,
        hasCompleteSelection: () => {
            const needsReturn = tripType === 'round_trip';
            return Boolean(selections.outbound) && (!needsReturn || Boolean(selections.return));
        },
        getSelections: () => ({
            outbound: selections.outbound ? { ...selections.outbound } : null,
            return_leg: selections.return ? { ...selections.return } : null,
        }),
        getMeta: () => ({ ...bookingMeta }),
        getTotal: () => currentTotal,
    };
});
