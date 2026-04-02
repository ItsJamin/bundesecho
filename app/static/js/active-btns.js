function showAlert(message, type = "success") {
  const container = document.body;
  const alert = document.createElement("div");
  alert.className = `alert alert-${type} alert-dismissible fade show fixed-alert-item`;
  alert.setAttribute("role", "alert");
  alert.innerText = message;
  container.appendChild(alert);

  setTimeout(() => {
    alert.classList.remove("show");
    setTimeout(() => alert.remove(), 300);
  }, 2000);
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.quote-share-btn').forEach(button => {
    button.addEventListener('click', function() {
      const text = this.dataset.quoteText;
      const person = this.dataset.personName;
      const link = this.dataset.quoteLink;
      const formatted = `"${text}" ~${person} (${link})`;
      navigator.clipboard.writeText(formatted).then(() => {
        showAlert("Zitat in Zwischenablage kopiert!");
      }).catch(err => {
        console.error("Clipboard copy failed:", err);
        showAlert("Fehler beim Kopieren des Zitats!", "danger");
      });
    });
  });

  document.querySelectorAll('.quote-embed-btn').forEach(button => {
    button.addEventListener('click', function() {
      const embedUrl = this.dataset.embedUrl;
      const iframeId = `quote-embed-${Date.now()}`;
      const embedCode = `<iframe id="${iframeId}" src="${embedUrl}" width="100%" frameborder="0" scrolling="no" style="max-width: 600px;"></iframe>
<script>
window.addEventListener('message', function(event) {
  if (event.data.frameUrl === "${embedUrl}") {
    const iframe = document.getElementById('${iframeId}');
    if (iframe) {
      iframe.style.height = event.data.frameHeight + 'px';
    }
  }
});
</script>`;
      navigator.clipboard.writeText(embedCode).then(() => {
        showAlert("Einbettungscode in Zwischenablage kopiert!");
      }).catch(err => {
        console.error("Clipboard copy failed:", err);
        showAlert("Fehler beim Kopieren des Einbettungscodes!", "danger");
      });
    });
  });
});
