(function () {
  const targets = document.querySelectorAll(
    "#content-main, .module, .inline-group, .submit-row, #changelist, #changelist-filter"
  );

  targets.forEach((item, index) => {
    item.classList.add("fade-admin");
    item.style.animationDelay = `${Math.min(index * 40, 220)}ms`;
  });
})();
