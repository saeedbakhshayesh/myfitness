document.addEventListener("DOMContentLoaded", function () {
    const menuToggle = document.getElementById("menuToggle");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");

    function openSidebar() {
        if (sidebar) sidebar.classList.add("open");
        if (overlay) overlay.classList.add("show");
        document.body.style.overflow = "hidden";
    }

    function closeSidebar() {
        if (sidebar) sidebar.classList.remove("open");
        if (overlay) overlay.classList.remove("show");
        document.body.style.overflow = "";
    }

    if (menuToggle && sidebar) {
        menuToggle.addEventListener("click", function (e) {
            e.stopPropagation();
            if (sidebar.classList.contains("open")) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    if (overlay) {
        overlay.addEventListener("click", closeSidebar);
    }

    if (sidebar) {
        sidebar.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", function () {
                if (window.innerWidth <= 768) {
                    closeSidebar();
                }
            });
        });
    }

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeSidebar();
    });

    window.addEventListener("resize", function () {
        if (window.innerWidth > 768) {
            closeSidebar();
        }
    });
});
