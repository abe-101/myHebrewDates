/* Project specific Javascript goes here. */
function copyUrlToClipboard(url, successMessage, failureMessage) {
  const successText = successMessage || 'URL copied to clipboard.';
  const failureText = failureMessage || 'Failed to copy. Please copy manually.';

  if (!url) {
    alert(failureText);
    return Promise.resolve(false);
  }

  const fallbackCopy = () => {
    const textarea = document.createElement('textarea');
    textarea.value = url;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'absolute';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    textarea.setSelectionRange(0, textarea.value.length);
    const succeeded = document.execCommand('copy');
    document.body.removeChild(textarea);

    if (succeeded) {
      alert(successText);
      return true;
    }

    alert(failureText);
    return false;
  };

  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard
      .writeText(url)
      .then(() => {
        alert(successText);
        return true;
      })
      .catch(() => fallbackCopy());
  }

  return Promise.resolve(fallbackCopy());
}

function shareFile(url, successMessage, failureMessage) {
  const successText = successMessage || 'URL copied to clipboard.';
  const failureText = failureMessage || 'Failed to copy. Please copy manually.';

  if (!url) {
    alert(failureText);
    return;
  }

  if (navigator.share) {
    navigator.share({ url }).catch(() => {
      copyUrlToClipboard(url, successText, failureText);
    });
    return;
  }

  copyUrlToClipboard(url, successText, failureText);
}

document.addEventListener('htmx:confirm', function (e) {
  e.preventDefault();
  if (!e.target.hasAttribute('hx-confirm')) {
    e.detail.issueRequest(true);
    return;
  }
  Swal.fire({
    title: 'Proceed?',
    text: `${e.detail.question}`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonText: 'Yes',
    cancelButtonText: 'No',
    reverseButtons: true,
  }).then(function (result) {
    if (result.isConfirmed) e.detail.issueRequest(true); // use true to skip window.confirm
  });
});

const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl));
