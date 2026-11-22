/* Project specific Javascript goes here. */

// On phones and tablets, a copy button with data-share-label opens the device's share sheet instead.
const canShare = 'share' in navigator && window.matchMedia('(pointer: coarse)').matches;
if (canShare) {
  document.querySelectorAll('[data-share-label]').forEach(function (button) {
    button.querySelector('.copy-label').textContent = button.dataset.shareLabel;
    button.querySelector('.bi').className = 'bi bi-share me-1';
  });
}

// Any button with data-copy="text" copies that text and says "Copied" for a moment.
document.addEventListener('click', function (e) {
  const button = e.target.closest('[data-copy]');
  if (!button || button.dataset.copying) return;
  if (canShare && button.dataset.shareLabel) {
    navigator.share({ title: button.dataset.shareTitle, url: button.dataset.copy }).catch(function () {});
    return;
  }
  button.dataset.copying = 'true';
  const label = button.querySelector('.copy-label') || button;
  const original = label.textContent;
  let finished = false;
  navigator.clipboard.writeText(button.dataset.copy).then(
    function () {
      if (!finished) label.textContent = 'Copied';
    },
    function () {
      if (!finished) label.textContent = 'Copy failed';
    },
  );
  // The clipboard can stall, so the button resets on a timer, not on the promise.
  setTimeout(function () {
    finished = true;
    label.textContent = original;
    delete button.dataset.copying;
  }, 2000);
});

const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
