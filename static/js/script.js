async function uploadFile() {
    document.getElementById("uploadPopup").style.display = "block";
    document.getElementById("progressContainer").style.display = "block"; // show progress circle
    observeQRDisplay();  // to monitor QR visibility

    const fileInput = document.getElementById("fileInput");
    if (!fileInput.files.length) {
        alert("Please select a file to upload.");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener("progress", function (e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                const offset = 282.6 - (282.6 * percent) / 100;
                document.getElementById("progressBar").style.strokeDashoffset = offset;
                document.getElementById("progressText").textContent = `${percent}%`;
            }
        });

        xhr.onreadystatechange = async function () {
            if (xhr.readyState === 4) {
                document.getElementById("uploadPopup").style.display = "none";

                if (xhr.status === 200) {
                    const data = JSON.parse(xhr.responseText);
                    document.getElementById("transferCode").innerText = data.code;
                    document.getElementById("qrCodeImage").src = data.qr_code_url;
                    startCountdown(600); // Start 10-minute countdown
                    updateHistory();
                    showScanPopup();
                } else {
                    alert("Upload failed: " + xhr.responseText);
                }
            }
        };

        xhr.open("POST", "/upload", true);
        xhr.send(formData);
    } catch (error) {
        alert("Upload failed: " + error);
    }
}

async function downloadFile() {
    const code = document.getElementById("codeInput").value.trim();
    if (!code) {
        alert("Enter the code to download the file.");
        return;
    }

    // Show popup with downloading message
    const popup = document.getElementById("uploadPopup");
    const popupTextNode = popup.querySelector(".popup-message");
    const tickIcon = document.getElementById("successTick");

    if (popupTextNode) {
        popupTextNode.textContent = "Your file is being downloaded...";
    }
    popup.style.display = "block";
    document.getElementById("progressContainer").style.display = "none";
    if (tickIcon) tickIcon.style.display = "none";

    try {
        const response = await fetch(`/download/${code}`);
        if (!response.ok) {
            const errorText = await response.text();
            alert("Error: " + errorText);
            popup.style.display = "none";
            return;
        }

        const blob = await response.blob();
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'downloaded_file';

        if (contentDisposition) {
            const match = contentDisposition.match(/filename="?(.+)"?/);
            if (match && match[1]) {
                filename = match[1];
            }
        }

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

        await updateHistory();

        // Update popup message to show success
        if (popupTextNode) {
            popupTextNode.textContent = "Your file has been downloaded";
        }
        if (tickIcon) {
            tickIcon.style.display = "block";
            tickIcon.classList.add("animate-tick");
        }

        // Auto-close popup after 3 seconds
        setTimeout(() => {
            popup.style.display = "none";
            tickIcon.classList.remove("animate-tick");
        }, 5000);

    } catch (error) {
        alert("Download failed: " + error);
        popup.style.display = "none";
    }
}

//update histroy
async function updateHistory() {
    try {
        const res = await fetch("/get_history");
        const history = await res.json();
        const container = document.getElementById("historyContainer");

        container.innerHTML = ""; // Clear the existing history content

        if (history.length === 0) {
            container.innerHTML = "No history available."; // Show message when there is no history
        }

        history.forEach(entry => {
            const div = document.createElement("div");
            div.className = "history-entry";

            const isSender = entry.sender_ip === currentUserIp;
            const isReceiver = entry.receiver_ip === currentUserIp;

            const senderIp = isSender ? entry.sender_ip : 'Hidden';
            const receiverIp = isReceiver ? entry.receiver_ip : 'Hidden';

            div.innerHTML = `
                <strong>Sender IP:</strong> ${entry.sender_ip}<br>
                <strong>Receiver IP:</strong> ${entry.receiver_ip || 'Pending'}<br>
                <strong>Filename:</strong> ${entry.filename}
            `;
            container.appendChild(div);
        });
    } catch (error) {
        console.error("Failed to update history:", error);
    }
}

// Automatically update history on page load
window.addEventListener("DOMContentLoaded", updateHistory);
//his end
function copyCode() {
    const code = document.getElementById("transferCode").innerText;
    navigator.clipboard.writeText(code);
    const btn = document.getElementById("copyCodeButton");
    btn.classList.add("copied");
    setTimeout(() => btn.classList.remove("copied"), 1000);
}

function showScanPopup() {
    document.getElementById("scan").style.display = "block";
    document.getElementById("overlay").style.display = "block";
}

function hideScanPopup() {
    document.getElementById("scan").style.display = "none";
    document.getElementById("overlay").style.display = "none";
}

// Time countdown function
function startCountdown(durationInSeconds) {
    const expiryTimeElement = document.getElementById("expiryTime");
    let remaining = durationInSeconds;

    const interval = setInterval(() => {
        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;
        expiryTimeElement.textContent = `Expires in: ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

        if (remaining <= 0) {
            clearInterval(interval);
            expiryTimeElement.textContent = "File expired.";
        }

        remaining--;
    }, 1000);
}
//qr
window.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code'); // Get 'code' from the URL parameters
    if (code) {
        const receiveInput = document.getElementById('codeInput'); // Get the input field by id
        if (receiveInput) {
            receiveInput.value = code; // Paste the code into the codeInput field
        }
    }
});
//popup mess
function observeQRDisplay() {
  const scanSection = document.getElementById("scan");
  const popup = document.getElementById("uploadPopup");

  const observer = new MutationObserver(() => {
    const qrImage = document.getElementById("qrCodeImage");
    if (qrImage && qrImage.src && qrImage.src.trim() !== "") {
      popup.style.display = "none";
      observer.disconnect();
    }
  });

  observer.observe(scanSection, { childList: true, subtree: true });
}

//contact


document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('contact-form');

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = {
      name: form.name.value,
      phone: form.phone.value,
      email: form.email.value,
      message: form.message.value
    };

    try {
      const res = await fetch('/submit_contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      const result = await res.json();
      document.getElementById('response-message').innerText = result.message;
      form.reset();
    } catch (err) {
      document.getElementById('response-message').innerText = 'Submission failed.';
    }
  });
});
//share qr
document.getElementById('shareBtn').addEventListener('click', () => {
  const qrImg = document.getElementById('qrCodeImage');
  const dataUrl = qrImg?.src;

  if (!dataUrl) {
    alert("QR Code not found!");
    return;
  }

  fetch(dataUrl)
    .then(res => res.blob())
    .then(blob => {
      const file = new File([blob], 'qr-code.png', { type: 'image/png' });

      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        navigator.share({
          title: 'NowShare QR Code',
          text: 'Scan this to download your file:',
          files: [file],
        }).catch(error => {
          console.error('Sharing failed:', error);
          alert('Sharing canceled or failed.');
        });
      } else {
        alert('Sharing is not supported on this device/browser.');
      }
    });
});

