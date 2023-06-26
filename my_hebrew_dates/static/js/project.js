/* Project specific Javascript goes here. */
function copyFileUrl(pk) {
  // Get the text field
  var copyText = document.getElementById('calendar_file_url' + pk);

  // Select the text field
  copyText.select();
  copyText.setSelectionRange(0, 99999); // For mobile devices

  // Copy the text inside the text field
  navigator.clipboard.writeText(copyText.value);

  // Alert the copied text
  //createToast({message: "Copied the text:\n" + copyText.value, tags: "text-white bg-success"})
  //alert("Copied the text: " + copyText.value);
}
function shareFile(calendarUuid) {
  const fileUrlInput = document.getElementById(
    `calendar_file_url${calendarUuid}`,
  );
  const fileUrl = fileUrlInput.value;

  if (navigator.share) {
    navigator
      .share({
        url: fileUrl,
      })
      .then(() => {
        console.log('File shared successfully.');
      })
      .catch((error) => {
        console.error('Error sharing file:', error);
        copyFileUrlToClipboard(fileUrl);
        notifyUser('Link copied to clipboard.');
      });
  } else {
    copyFileUrlToClipboard(fileUrl);
    notifyUser('URL copied to clipboard.');
  }
}

function copyFileUrlToClipboard(url) {
  const el = document.createElement('textarea');
  el.value = url;
  document.body.appendChild(el);
  el.select();
  document.execCommand('copy');
  document.body.removeChild(el);
}

function notifyUser(message) {
  alert(message);
}
