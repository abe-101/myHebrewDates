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
