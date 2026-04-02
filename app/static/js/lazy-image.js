document.addEventListener("DOMContentLoaded", function () {
  const lazyImages = document.querySelectorAll("img.lazy-image");

  if ("IntersectionObserver" in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target;
          const dataSrc = img.getAttribute("data-src");

          if (dataSrc) {
            img.src = dataSrc;
            img.removeAttribute("data-src");
          }

          img.classList.remove("lazy-image");
          observer.unobserve(img);
        }
      });
    });

    lazyImages.forEach((img) => {
      imageObserver.observe(img);
    });
  } else {
    // Fallback: load all images immediately
    lazyImages.forEach((img) => {
      const dataSrc = img.getAttribute("data-src");
      if (dataSrc) {
        img.src = dataSrc;
        img.removeAttribute("data-src");
      }
    });
  }
});