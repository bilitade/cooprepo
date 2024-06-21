(function() {
  "use strict";

  var sidebar = document.querySelector('.sidebar');
  var sidebarToggle = document.getElementById('sidebarToggle');

  if (sidebar && sidebarToggle) {
    var collapseElementList = [].slice.call(document.querySelectorAll('.sidebar .collapse'));
    var sidebarCollapseList = collapseElementList.map(function (collapseEl) {
      return new bootstrap.Collapse(collapseEl, { toggle: false });
    });

    // Function to toggle sidebar state
    function toggleSidebar() {
      document.body.classList.toggle('sidebar-toggled');
      sidebar.classList.toggle('toggled');

      if (sidebar.classList.contains('toggled')) {
        for (var bsCollapse of sidebarCollapseList) {
          bsCollapse.hide();
        }
      }

      // Store sidebar state in local storage
      var isSidebarToggled = sidebar.classList.contains('toggled');
      localStorage.setItem('sidebarToggled', isSidebarToggled);
    }

    // Toggle sidebar on button click
    sidebarToggle.addEventListener('click', function(e) {
      toggleSidebar();
    });

    // Initialize sidebar state based on local storage
    var storedSidebarToggled = localStorage.getItem('sidebarToggled');
    if (storedSidebarToggled === 'true') {
      toggleSidebar(); // If toggled, keep it toggled
    }

    // Close any open menu accordions when window is resized below 768px
    window.addEventListener('resize', function() {
      var vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
      if (vw < 768) {
        for (var bsCollapse of sidebarCollapseList) {
          bsCollapse.hide();
        }
      }
    });
  }

  // Prevent the content wrapper from scrolling when the fixed side navigation hovered over
  var fixedNavigation = document.querySelector('body.fixed-nav .sidebar');
  if (fixedNavigation) {
    fixedNavigation.addEventListener('mousewheel DOMMouseScroll wheel', function(e) {
      var vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
      if (vw > 768) {
        var e0 = e.originalEvent,
          delta = e0.wheelDelta || -e0.detail;
        this.scrollTop += (delta < 0 ? 1 : -1) * 30;
        e.preventDefault();
      }
    });
  }

  var scrollToTop = document.querySelector('.scroll-to-top');
  if (scrollToTop) {
    // Scroll to top button appear
    window.addEventListener('scroll', function() {
      var scrollDistance = window.pageYOffset;
      // Check if user is scrolling up
      if (scrollDistance > 100) {
        scrollToTop.style.display = 'block';
      } else {
        scrollToTop.style.display = 'none';
      }
    });
  }

})(); // End of use strict
