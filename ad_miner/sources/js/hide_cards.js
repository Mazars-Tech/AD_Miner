// var url = new URL(window.location.href);
// var page_type = url.searchParams.get("page");

function switchCards(page_type) {
  Object.values(
    document.getElementsByClassName('col-xl-3 col-md-6 mb-4'),
  ).forEach((card) => {
    if (page_type !== null) {
      if (!card.classList.contains(page_type)) {
        card.classList.add('hidden');
      } else {
        card.classList.remove('hidden');
      }
    }
  });
}
