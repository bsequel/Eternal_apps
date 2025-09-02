$(document).ready(function () {

    // Global variables
    let allCases = [];
    let table;
    let userTable;
    let etlAutoInterval = null;
    // Global variable to track CAMS auto ETL interval
    let camsEtlAutoInterval = null;
    const body = document.body;
    const username = body.dataset.username;
    const email1 = body.dataset.email;
    const role = body.dataset.role;
    const defaultSection = $('.nav-link1.active').data('section');
    $('#activeSection').text(defaultSection);

    // Initialize functions
    initSimpleConfirm();
    initUserInfo();
    initSidebarToggle();
    initNavigation();
    if (role === 'viewer') {
        initCaseTable_viewer();
    } else {
        initCaseTable();
    }
    initUserTable();
    bindFilterEvents();
    fetchCases();

    initetl();
    initCamsEtl();

    initRefreshFunctionality();






    // Simple confirmation popup - add this CSS and HTML once
    function initSimpleConfirm() {
        if ($('#simpleConfirmPopup').length === 0) {
            $('body').append(`
            <style>
                #simpleConfirmPopup {
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.5);
                    z-index: 9999;
                }
                .simple-confirm-box {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    min-width: 300px;
                    text-align: center;
                }
                .simple-confirm-message {
                    margin-bottom: 20px;
                    font-size: 16px;
                    color: #333;
                }
                .simple-confirm-buttons {
                    display: flex;
                    gap: 10px;
                    justify-content: center;
                }
                .simple-confirm-btn {
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                }
                .simple-confirm-yes {
                    background: #007bff;
                    color: white;
                }
                .simple-confirm-no {
                    background: #6c757d;
                    color: white;
                }
            </style>
            <div id="simpleConfirmPopup">
                <div class="simple-confirm-box">
                    <div class="simple-confirm-message" id="simpleConfirmMessage">Are you sure?</div>
                    <div class="simple-confirm-buttons">
                        <button class="simple-confirm-btn simple-confirm-no" id="simpleConfirmNo">Cancel</button>
                        <button class="simple-confirm-btn simple-confirm-yes" id="simpleConfirmYes">Confirm</button>
                    </div>
                </div>
            </div>
        `);
        }
    }

    // Simple confirm function
    function simpleConfirm(message, callback) {
        $('#simpleConfirmMessage').text(message);
        $('#simpleConfirmPopup').show();

        $('#simpleConfirmYes').off('click').on('click', function () {
            $('#simpleConfirmPopup').hide();
            callback(true);
        });

        $('#simpleConfirmNo').off('click').on('click', function () {
            $('#simpleConfirmPopup').hide();
            callback(false);
        });

        // Close on background click
        $('#simpleConfirmPopup').off('click').on('click', function (e) {
            if (e.target === this) {
                $('#simpleConfirmPopup').hide();
                callback(false);
            }
        });
    }



    // Format functions
    function formatDate(date) {
        if (!date) return '';

        try {
            let d;

            if (date instanceof Date) {
                d = date;
            } else if (typeof date === 'string') {
                let cleanDate = date.trim();

                // Case 1: "28/01/2025 03:52:AM" or "28-01-2025 03:52:AM"
                if (/^\d{2}[\/-]\d{2}[\/-]\d{4}\s+\d{2}:\d{2}:(AM|PM)$/i.test(cleanDate)) {
                    let parts = cleanDate.replace(/\//g, '-').split(/[\s:]+/);
                    let [day, month, year] = parts[0].split('-');
                    let hours = parseInt(parts[1], 10);
                    let minutes = parts[2];
                    let meridian = parts[3].toUpperCase();

                    if (meridian === "PM" && hours < 12) hours += 12;
                    if (meridian === "AM" && hours === 12) hours = 0;

                    d = new Date(year, month - 1, day, hours, minutes);
                }
                // Case 2: "28/01/2025 14:35:22" or "28-01-2025 14:35:22"
                else if (/^\d{2}[\/-]\d{2}[\/-]\d{4}\s+\d{2}:\d{2}(:\d{2})?$/.test(cleanDate)) {
                    let [datePart, timePart] = cleanDate.replace(/\//g, '-').split(' ');
                    let [day, month, year] = datePart.split('-');
                    let [hours, minutes, seconds = "00"] = timePart.split(':');
                    d = new Date(year, month - 1, day, hours, minutes, seconds);
                }
                // Case 3: "28/01/2025" or "28-01-2025"
                else if (/^\d{2}[\/-]\d{2}[\/-]\d{4}$/.test(cleanDate)) {
                    let [day, month, year] = cleanDate.replace(/\//g, '-').split('-');
                    d = new Date(year, month - 1, day);
                }
                // ✅ Case 4: "2025-03-20" or "2025-03-20 14:35:22"
                else if (/^\d{4}-\d{2}-\d{2}(\s+\d{2}:\d{2}(:\d{2})?)?$/.test(cleanDate)) {
                    let [datePart, timePart = "00:00:00"] = cleanDate.split(' ');
                    let [year, month, day] = datePart.split('-');
                    let [hours, minutes, seconds = "00"] = timePart.split(':');
                    d = new Date(year, month - 1, day, hours, minutes, seconds);
                }
                else {
                    return date; // do not attempt other conversions
                }
            } else {
                return date;
            }

            if (isNaN(d)) return date;

            // Format output into: DD-MM-YYYY hh:mm AM/PM
            let day = d.getDate().toString().padStart(2, '0');
            let month = (d.getMonth() + 1).toString().padStart(2, '0');
            let year = d.getFullYear();
            let hours = d.getHours();
            let minutes = d.getMinutes().toString().padStart(2, '0');
            let ampm = hours >= 12 ? 'PM' : 'AM';
            hours = hours % 12 || 12;

            // If input was just a date (no time)
            if (/^\d{2}[\/-]\d{2}[\/-]\d{4}$/.test(date.trim()) || /^\d{4}-\d{2}-\d{2}$/.test(date.trim())) {
                return `${day}-${month}-${year}`;
            }

            return `${day}-${month}-${year} ${hours.toString().padStart(2, '0')}:${minutes} ${ampm}`;
        } catch {
            return date;
        }
    }

    // Format Currency
    function formatCurrency(amount) {
        if (!amount) return '₹0';
        const num = parseFloat(String(amount).replace(/[₹,]/g, ''));
        if (isNaN(num)) return amount;
        return `₹${num.toLocaleString('en-IN')}`;
    }

    function formatINR(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2
        }).format(amount);
    }

    function formatToCrore(amountInRupees) {
        let croreValue = amountInRupees / 10000000;
        return `₹${croreValue.toFixed(2)} Cr`;
    }

    function getInitials(name) {
        const parts = name.trim().split(" ");
        let initials = parts[0].charAt(0).toUpperCase();
        if (parts.length > 1) {
            initials += parts[parts.length - 1].charAt(0).toUpperCase();
        }
        return initials;
    }

    function initUserInfo() {
        $('#username').text(username);
        $('#profileToggle').text(getInitials(username));
        $('#user-email').text(email1);
        $('#user-role').text(role);

        const accessLevelElement = $('.alert-card-access .alert-card-content');
        if (accessLevelElement.length) {
            if (role === 'admin') {
                accessLevelElement
                    .removeClass('text-danger')
                    .addClass('text-success')
                    .text('Admin');
            } else {
                accessLevelElement
                    .removeClass('text-success')
                    .addClass('text-danger')
                    .text('Viewer');
            }
        }

        if (role === 'admin') {
            $('#adminSection').show();
            $('#roleMessage').removeClass('alert-secondary').addClass('alert-info')
                .html(`
                <div>
                    Access level: <strong>Admin</strong>
                </div>
            `);
        }
    }


    function initetl() {
        if (role === 'admin') {
            const etlContainer = $('#etl1');
            if (!etlContainer.length) {
                console.error('❌ #etl1 container not found in DOM.');
                return;
            }

            etlContainer.html(`
            <div class="etl-controls p-3">
                <span>
                    <button id="runEtlBtn" class="btn btn-gradient-primary btn-sm shadow-lg position-relative overflow-hidden me-2">
                        <span class="btn-text d-flex align-items-center justify-content-center">
                            <i class="bi bi-database-gear me-2"></i>
                            <span>Run ETL Process</span>
                        </span>
                        <span class="btn-loader d-none">
                            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                            <span>Processing...</span>
                        </span>
                        <span class="btn-ripple position-absolute top-0 start-0 w-100 h-100"></span>
                    </button>
                     </span>
                    <span>
                    <button id="toggleAutoEtl" class="btn btn-outline-secondary btn-sm">
                        <span class="auto-status">Auto: OFF</span>
                    </button>
                    </span>
                    
                    <div id="etlCountdown" class="d-none mt-2">
                        <small class="text-muted">Next ETL in: <span class="countdown-timer">00:00</span></small>
                    </div>
                </div>
            `);

            $(document).off('click', '#runEtlBtn').on('click', '#runEtlBtn', function (e) {
                e.preventDefault();
                executeEtl();
            });

            // $(document).off('click', '#toggleAutoEtl').on('click', '#toggleAutoEtl', function (e) {
            //     e.preventDefault();

            //     // Check the current state (you can use the button's class OR text)
            //     const isAutoOn = $(this).hasClass('auto-active');
            //     const message = isAutoOn
            //         ? 'Are you sure you want to turn OFF Auto ETL?'
            //         : 'Are you sure you want to turn ON Auto ETL?';

            //     if (confirm(message)) {
            //         toggleAutoEtl();
            //     }
            // });

            // Replace your existing toggle auto ETL code with this:
            $(document).off('click', '#toggleAutoEtl').on('click', '#toggleAutoEtl', function (e) {
                e.preventDefault();

                const isAutoOn = $(this).hasClass('auto-active');
                const message = isAutoOn
                    ? 'Are you sure you want to turn OFF Auto ETL?'
                    : 'Are you sure you want to turn ON Auto ETL?';

                simpleConfirm(message, function (confirmed) {
                    if (confirmed) {
                        toggleAutoEtl();
                    }
                });
            });


            // ---- Check auto-etl state on page load ----
            if (localStorage.getItem('autoEtlOn') === 'true') {
                startAutoEtl();
                $('#toggleAutoEtl').addClass('auto-active');
                $('#toggleAutoEtl .auto-status').text('Auto: ON');
                $('#etlCountdown').removeClass('d-none');
            }
        }
    }


    function executeEtl() {
        console.log('ETL button clicked');

        const button = $('#runEtlBtn');
        const btnText = button.find('.btn-text');
        const btnLoader = button.find('.btn-loader');

        console.log('Button elements found:', btnText.length, btnLoader.length);

        btnText.addClass('d-none');
        btnLoader.removeClass('d-none');
        button.prop('disabled', true).addClass('processing');

        showToast('Running ETL process...', 'success');

        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrfToken = csrfInput ? csrfInput.value : null;

        if (!csrfToken) {
            btnText.removeClass('d-none');
            btnLoader.addClass('d-none');
            button.prop('disabled', false).removeClass('processing');
            showToast('Missing CSRF token.', 'error');
            return;
        }

        fetch('/cyberapp/run-etl/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP error! status: ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                if (data.message) {
                    showToast(data.message + (data.task_id ? ' (Task ID: ' + data.task_id + ')' : ''), 'success');
                    setTimeout(() => {
                        refreshTableData();
                    }, 2000);
                } else {
                    showToast('ETL could not be started.', 'error');
                }
            })
            .catch(err => {
                console.error('❌ ETL Error:', err);
                showToast('ETL trigger failed: ' + err.message, 'error');
            })
            .finally(() => {
                console.log('Resetting button state');
                btnText.removeClass('d-none');
                btnLoader.addClass('d-none');
                button.prop('disabled', false).removeClass('processing');
            });
    }

    function toggleAutoEtl() {
        const toggleBtn = $('#toggleAutoEtl');
        const statusSpan = toggleBtn.find('.auto-status');
        const countdownDiv = $('#etlCountdown');

        if (etlAutoInterval) {
            clearInterval(etlAutoInterval);
            etlAutoInterval = null;
            toggleBtn.removeClass('auto-active');
            statusSpan.text('Auto: OFF');
            countdownDiv.addClass('d-none');
            // Save state
            localStorage.setItem('autoEtlOn', 'false');
            showToast('Auto ETL disabled', 'info');
        } else {
            startAutoEtl();
            toggleBtn.addClass('auto-active');
            statusSpan.text('Auto: ON');
            countdownDiv.removeClass('d-none');
            // Save state
            localStorage.setItem('autoEtlOn', 'true');
            showToast('Auto ETL enabled - Running every 2 minute', 'success');
        }
    }


    function startAutoEtl() {
        let timeLeft = 120;

        function updateCountdown() {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            const display = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            $('.countdown-timer').text(display);

            if (timeLeft <= 0) {
                executeEtl();
                timeLeft = 120;
                showToast('Auto ETL executed', 'info');
            } else {
                timeLeft--;
            }
        }

        updateCountdown();
        etlAutoInterval = setInterval(updateCountdown, 1000);
    }

    function initCamsEtl() {
        if (role === 'admin') {
            const camsEtlContainer = $('#camsEtl1');
            if (!camsEtlContainer.length) {
                console.error('❌ #camsEtl1 container not found in DOM.');
                return;
            }

            camsEtlContainer.html(`
            <div class="etl-controls p-3">
                <span>
                    <button id="runCamsEtlBtn" class="btn btn-gradient-primary btn-sm shadow-lg position-relative overflow-hidden me-2">
                        <span class="cams-btn-text d-flex align-items-center justify-content-center">
                            <i class="bi bi-bank2 me-2"></i>
                            <span>Run CAMS ETL Process</span>
                        </span>
                        <span class="cams-btn-loader d-none">
                            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                            <span>Processing CAMS Data...</span>
                        </span>
                        <span class="cams-btn-ripple position-absolute top-0 start-0 w-100 h-100"></span>
                    </button>
                     </span>
                    <span>
                    <button id="toggleCamsAutoEtl" class="btn btn-outline-secondary btn-sm mt-2">
                        <span class="cams-auto-status">CAMS Auto: OFF</span>
                    </button>
                    </span>
                    
                    <div id="camsEtlCountdown" class="d-none mt-2">
                        <small class="text-muted">Next CAMS ETL in: <span class="cams-countdown-timer">00:00</span></small>
                    </div>
                </div>
            `);

            $(document).off('click', '#runCamsEtlBtn').on('click', '#runCamsEtlBtn', function (e) {
                e.preventDefault();
                executeCamsEtl();
            });

            $(document).off('click', '#toggleCamsAutoEtl').on('click', '#toggleCamsAutoEtl', function (e) {
                e.preventDefault();

                // Check the current state (you can use the button's class OR text)
                const isCamsAutoOn = $(this).hasClass('cams-auto-active');
                const message = isCamsAutoOn
                    ? 'Are you sure you want to turn OFF CAMS Auto ETL?'
                    : 'Are you sure you want to turn ON CAMS Auto ETL?';

                simpleConfirm(message, function (confirmed) {
                    if (confirmed) {
                        toggleCamsAutoEtl();
                    }
                });
            });


            // ---- Check CAMS auto-etl state on page load ----
            if (localStorage.getItem('camsAutoEtlOn') === 'true') {
                startCamsAutoEtl();
                $('#toggleCamsAutoEtl').addClass('cams-auto-active');
                $('#toggleCamsAutoEtl .cams-auto-status').text('CAMS Auto: ON');
                $('#camsEtlCountdown').removeClass('d-none');
            }
        }
    }


    function executeCamsEtl() {
        console.log('CAMS ETL button clicked');

        const camsButton = $('#runCamsEtlBtn');
        const camsBtnText = camsButton.find('.cams-btn-text');
        const camsBtnLoader = camsButton.find('.cams-btn-loader');

        console.log('CAMS Button elements found:', camsBtnText.length, camsBtnLoader.length);

        camsBtnText.addClass('d-none');
        camsBtnLoader.removeClass('d-none');
        camsButton.prop('disabled', true).addClass('cams-processing');

        showToast('Running CAMS ETL process...', 'success');

        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrfToken = csrfInput ? csrfInput.value : null;

        if (!csrfToken) {
            camsBtnText.removeClass('d-none');
            camsBtnLoader.addClass('d-none');
            camsButton.prop('disabled', false).removeClass('cams-processing');
            showToast('Missing CSRF token for CAMS ETL.', 'error');
            return;
        }

        fetch('/camsapp/run-cams-etl/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP error! status: ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                if (data.message) {
                    showToast(data.message + (data.cams_task_id ? ' (CAMS Task ID: ' + data.cams_task_id + ')' : ''), 'success');
                    setTimeout(() => {
                        refreshCamsTableData();
                    }, 2000);
                } else {
                    showToast('CAMS ETL could not be started.', 'error');
                }
            })
            .catch(err => {
                console.error('❌ CAMS ETL Error:', err);
                showToast('CAMS ETL trigger failed: ' + err.message, 'error');
            })
            .finally(() => {
                console.log('Resetting CAMS button state');
                camsBtnText.removeClass('d-none');
                camsBtnLoader.addClass('d-none');
                camsButton.prop('disabled', false).removeClass('cams-processing');
            });
    }

    function toggleCamsAutoEtl() {
        const camsToggleBtn = $('#toggleCamsAutoEtl');
        const camsStatusSpan = camsToggleBtn.find('.cams-auto-status');
        const camsCountdownDiv = $('#camsEtlCountdown');

        if (camsEtlAutoInterval) {
            clearInterval(camsEtlAutoInterval);
            camsEtlAutoInterval = null;
            camsToggleBtn.removeClass('cams-auto-active');
            camsStatusSpan.text('CAMS Auto: OFF');
            camsCountdownDiv.addClass('d-none');
            // Save state
            localStorage.setItem('camsAutoEtlOn', 'false');
            showToast('CAMS Auto ETL disabled', 'info');
        } else {
            startCamsAutoEtl();
            camsToggleBtn.addClass('cams-auto-active');
            camsStatusSpan.text('CAMS Auto: ON');
            camsCountdownDiv.removeClass('d-none');
            // Save state
            localStorage.setItem('camsAutoEtlOn', 'true');
            showToast('CAMS Auto ETL enabled - Running every 2 minutes', 'success');
        }
    }


    function startCamsAutoEtl() {
        let camsTimeLeft = 120;

        function updateCamsCountdown() {
            const camsMinutes = Math.floor(camsTimeLeft / 60);
            const camsSeconds = camsTimeLeft % 60;
            const camsDisplay = `${camsMinutes.toString().padStart(2, '0')}:${camsSeconds.toString().padStart(2, '0')}`;
            $('.cams-countdown-timer').text(camsDisplay);

            if (camsTimeLeft <= 0) {
                executeCamsEtl();
                camsTimeLeft = 120;
                showToast('CAMS Auto ETL executed', 'info');
            } else {
                camsTimeLeft--;
            }
        }

        updateCamsCountdown();
        camsEtlAutoInterval = setInterval(updateCamsCountdown, 1000);
    }

    function refreshCamsTableData() {
        console.log('Refreshing CAMS table data...');
        // Add your CAMS table refresh logic here
        // This might involve reloading a DataTable or fetching new data

        // Example:
        if (typeof camsDataTable !== 'undefined' && camsDataTable) {
            camsDataTable.ajax.reload();
        }

        // Or if you have a custom refresh function for CAMS data:
        // loadCamsData();
    }






    function initSidebarToggle() {
        let hoverTimeout;
        let isHoverEnabled = true;

        $('#toggleSidebar').on('click', function () {
            const isMobile = window.innerWidth <= 768;

            if (isMobile) {
                $('#sidebar').toggleClass('show');
                $('#overlay').toggleClass('active');
            } else {
                $('#sidebar').toggleClass('collapsed');
                $('#mainContent').toggleClass('expanded');
                $('#toggleIcon').toggleClass('bi-chevron-double-left bi-chevron-double-right');

                isHoverEnabled = false;
                setTimeout(() => {
                    isHoverEnabled = true;
                }, 300);
            }
        });

        function initHoverBehavior() {
            const sidebar = $('#sidebar');
            const mainContent = $('#mainContent');
            const toggleIcon = $('#toggleIcon');

            sidebar.on('mouseenter', function () {
                if (!isHoverEnabled || window.innerWidth <= 768) return;

                clearTimeout(hoverTimeout);

                if (sidebar.hasClass('collapsed')) {
                    sidebar.removeClass('collapsed').addClass('hover-expanded');
                    mainContent.removeClass('expanded').addClass('hover-contracted');
                    toggleIcon.removeClass('bi-chevron-double-right').addClass('bi-chevron-double-left');
                }
            });

            sidebar.on('mouseleave', function () {
                if (!isHoverEnabled || window.innerWidth <= 768) return;

                clearTimeout(hoverTimeout);

                hoverTimeout = setTimeout(() => {
                    if (sidebar.hasClass('hover-expanded')) {
                        sidebar.removeClass('hover-expanded').addClass('collapsed');
                        mainContent.removeClass('hover-contracted').addClass('expanded');
                        toggleIcon.removeClass('bi-chevron-double-left').addClass('bi-chevron-double-right');
                    }
                }, 300);
            });
        }

        initHoverBehavior();

        $(window).on('resize', function () {
            const isMobile = window.innerWidth <= 768;

            if (isMobile) {
                $('#sidebar').removeClass('collapsed hover-expanded');
                $('#mainContent').removeClass('expanded hover-contracted');
                isHoverEnabled = false;
            } else {
                isHoverEnabled = true;
                if (!$('#sidebar').hasClass('collapsed') && !$('#sidebar').hasClass('hover-expanded')) {
                    $('#sidebar').addClass('collapsed');
                    $('#mainContent').addClass('expanded');
                    $('#toggleIcon').removeClass('bi-chevron-double-left').addClass('bi-chevron-double-right');
                }
            }
        });

        $('#overlay').on('click', function () {
            $('#sidebar').removeClass('show');
            $('#overlay').removeClass('active');
        });

        addHoverAnimations();
    }

    function addHoverAnimations() {
        if ($('#sidebar-hover-styles').length > 0) return;

        const hoverStyles = `
        <style id="sidebar-hover-styles">
            #sidebar {
                transition: width 0.3s ease, margin-left 0.3s ease;
            }
            
            #mainContent {
                transition: margin-left 0.3s ease, width 0.3s ease;
            }
            
            #sidebar:not(.collapsed):hover {
                box-shadow: 2px 0 10px rgba(0,0,0,0.1);
            }
            
            #sidebar.collapsed:hover {
                box-shadow: 2px 0 15px rgba(0,0,0,0.15);
            }
            
            #sidebar.collapsed:hover .nav-link1 {
                background-color: rgba(255,255,255,0.05);
                border-radius: 8px;
                margin: 2px 8px;
            }
            
            #toggleIcon {
                transition: transform 0.3s ease;
            }
            
            #sidebar * {
                user-select: none;
            }
            
            @media (max-width: 768px) {
                #sidebar {
                    transition: transform 0.3s ease !important;
                }
                
                #sidebar:hover {
                    box-shadow: none !important;
                }
            }
        </style>
    `;

        $('head').append(hoverStyles);
    }

    function initNavigation() {
        $('.nav-link1').on('click', function (e) {
            e.preventDefault();

            const section = $(this).data('section');

            $('.nav-link1').removeClass('active');
            $(this).addClass('active');

            $('.content-section').removeClass('active');
            $(`#${section}-content`).addClass('active');

            $('#activeSection').text(section.charAt(0).toUpperCase() + section.slice(1).toLowerCase());

            $('.navbar .nav-link').removeClass('active');
            $(`.navbar .nav-link[href*="section=${section}"]`).addClass('active');

            const url = new URL(window.location);
            url.searchParams.set("section", section);
            window.history.pushState({}, "", url);
        });

        $('.navbar .nav-link').on('click', function (e) {
            const url = new URL($(this).attr('href'), window.location.origin);
            const section = url.searchParams.get("section");

            if (section) {
                e.preventDefault();

                $('.navbar .nav-link').removeClass('active');
                $(this).addClass('active');

                $('.nav-link1').removeClass('active');
                $(`.nav-link1[data-section="${section}"]`).addClass('active');

                $('.content-section').removeClass('active');
                $(`#${section}-content`).addClass('active');

                $('#activeSection').text(section.charAt(0).toUpperCase() + section.slice(1).toLowerCase());

                window.history.pushState({}, "", url);
            }
        });

        const params = new URLSearchParams(window.location.search);
        const section = params.get("section") || "cyber-cell";

        $('.nav-link1').removeClass('active');
        $(`.nav-link1[data-section="${section}"]`).addClass('active');

        $('.navbar .nav-link').removeClass('active');
        $(`.navbar .nav-link[href*="section=${section}"]`).addClass('active');

        $('.content-section').removeClass('active');
        $(`#${section}-content`).addClass('active');

        $('#activeSection').text(section.charAt(0).toUpperCase() + section.slice(1).toLowerCase());
    }

    function initCaseTable() {
        if ($.fn.DataTable.isDataTable('#casesTable')) {
            $('#casesTable').DataTable().clear().destroy();
        }



        const columnHeaders = [
            'S.No', 'Complaint Date', 'Mail Date', 'Mail Month', 'Amount',
            'Reference Number', 'Police Station Address', 'Account Number',
            'Name', 'Mobile Number', 'Email ID', 'Status', 'Ageing Days',
            'Debit from Bank', 'Region', 'UTR Number', 'UTR Amount',
            'Transaction DateTime', 'Total Fraudulent Amount', 'Updated On',
            'Updated By', 'PDF URL',
            'Lien Amount',   // 🆕
            'Remarks'        // 🆕
        ];


        $('#casesTable thead tr.filter-row th').each(function (i) {
            if (i !== 11 && i !== 13) {
                $('input', this).off().on('keyup change clear', function () {
                    if (table.column(i).search() !== this.value) {
                        table.column(i).search(this.value).draw();
                    }
                });
            }
        });

        table = $('#casesTable').DataTable({
            scrollY: "500px",        // height of the body
            scrollCollapse: true,    // collapse when fewer rows
            paging: true,            // keep pagination
            ordering: true,
            searching: true,
            autoWidth: false,
            fixedHeader: true,

            scrollX: true,
            autoWidth: false,
            dom: 'Bfrtip',
            pageLength: 50,
            lengthMenu: [1, 5, 10, 25, 50, 100],
            buttons: [{ extend: 'pageLength' }],
            columnDefs: [
                {
                    targets: "_all",
                    createdCell: function (td) {
                        $(td).css({
                            "font-weight": "400",
                            "font-size": "14px",
                            "font-family": "'Be Vietnam Pro', sans-serif",
                            "padding": "10px"
                        });
                    }
                },
                // Dates: Complaint Date, Mail Date, Transaction DateTime, Updated On  
                { targets: [1, 2, 17, 19], render: (data) => formatDate(data) },
                // Currency: Amount, UTR Amount, Total Fraudulent Amount
                { targets: [4, 16, 18], render: (data) => formatCurrency(data) },
                {
                    targets: 11,
                    render: function (data, type, row) {
                        const statusMap = {
                            "Pending": { bg: "#f8d7da", color: "#721c24", emoji: "⏳" },
                            "Picked": { bg: "#fff8b4", color: "#c29606ff", emoji: "📌" },
                            "Closed": { bg: "#d4edda", color: "#155724", emoji: "✅" }
                        };
                        return `<select class="form-select form-select-sm status-dropdown ${data.toLowerCase()}-status" style="font-weight:500; font-family:'Be Vietnam Pro', sans-serif; border-radius:50px; background-color:${statusMap[data].bg}; color:${statusMap[data].color};" data-case-id="${row[0]}">
                        <option value="Pending" ${data === "Pending" ? "selected" : ""}>${statusMap["Pending"].emoji} Pending</option>
                        <option value="Picked" ${data === "Picked" ? "selected" : ""}>${statusMap["Picked"].emoji} Picked</option>
                        <option value="Closed" ${data === "Closed" ? "selected" : ""}>${statusMap["Closed"].emoji} Closed</option>
                    </select>`;
                    }
                },
                {
                    targets: 13,
                    render: function (data, type, row) {
                        const debitMap = {
                            "Yes": { bg: "#d4edda", color: "#155724", emoji: "✅" },
                            "No": { bg: "#f8d7da", color: "#721c24", emoji: "❌" }
                        };
                        return `<select class="form-select form-select-sm debit-dropdown ${data.toLowerCase()}-debit" style="font-weight:500; font-family:'Be Vietnam Pro', sans-serif; border-radius:50px; background-color:${debitMap[data].bg}; color:${debitMap[data].color};" data-case-id="${row[0]}">
                        <option value="Yes" ${data === "Yes" ? "selected" : ""}>${debitMap["Yes"].emoji} Yes</option>
                        <option value="No" ${data === "No" ? "selected" : ""}>${debitMap["No"].emoji} No</option>
                    </select>`;
                    }
                },
                {
                    targets: 15, // UTR Number column index
                    render: function (data, type, row) {
                        if (data === "ReferRemarks") {
                            return `<input type="text" placeholder="ReferRemarks" class="form-control form-control-sm utr-input"
                        data-case-id="${row[0]}"
                        value=""
                        placeholder="Enter UTR Number" />`;
                        } else {
                            return data || '';
                        }
                    }
                },

                {
                    targets: 21,
                    render: function (data) {
                        if (!data) return `<span class="text-muted">No PDF</span>`;
                        return `<a href="${data}" target="_blank" class="btn btn-sm btn-outline-dark">
                            <i class="bi bi-file-earmark-pdf"></i> View PDF
                        </a>`;
                    }
                },
                {
                    targets: 22, // lien_amount column index
                    render: function (data, type, row) {
                        const debitFromBank = row[13]; // column index for Debit from Bank
                        const readonly = debitFromBank === "Yes" ? "" : "readonly";
                        const style = debitFromBank === "Yes" ? "" : "background-color:#f0f0f0; color:#888;";

                        return `<input type="text" class="form-control form-control-sm lien-input"
            data-case-id="${row[0]}" 
            value="${data || ''}" 
            ${readonly} 
            style="${style}" 
            title="Only numbers allowed" />`; // ✅ tooltip placeholder
                    }
                },
                {
                    targets: 23, // remarks column index
                    render: function (data, type, row) {
                        return `<input type="text" class="form-control form-control-sm remarks-input"
                       data-case-id="${row[0]}" value="${data || ''}" />`;
                    }
                }

            ]
        });

        function cleanCellData(data, column) {
            if (typeof data === 'string') {
                var temp = document.createElement('div');
                temp.innerHTML = data;
                var cleanText = temp.textContent || temp.innerText || '';

                if (column === 11 || column === 13) {
                    var select = temp.querySelector('select');
                    if (select) {
                        var selectedOption = select.querySelector('option[selected]');
                        return selectedOption ? selectedOption.value : select.value;
                    }
                }

                if (column === 21) {
                    var link = temp.querySelector('a');
                    if (link && link.href) {
                        return link.href;
                    }
                    return cleanText === 'No PDF' ? 'No PDF' : cleanText;
                }

                data = cleanText;
            }

            // Apply same formatting for export
            if ([1, 2, 17, 19].includes(column)) {
                return formatDate(data);
            }
            if ([4, 16, 18].includes(column)) {
                return formatCurrency(data);
            }

            return data || '';
        }

        const csrftoken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];

        function sendCaseUpdate(caseId, data) {
            $.ajax({
                url: `/cyberapp/cases/${caseId}/update/`,
                type: 'POST',
                data: JSON.stringify(data),
                contentType: 'application/json',
                headers: { 'X-CSRFToken': csrftoken },
                success: function (res) {
                    console.log('Case updated:', res);
                    showToast('Case updated successfully', 'success');
                    refreshTableData();
                },
                error: function (xhr) {
                    console.error('Update failed:', xhr.responseText);
                    showToast('Error updating case: ' + xhr.responseText, 'error');
                }
            });
        }

        $(document).on('change', '.status-dropdown', function () {
            const caseId = $(this).data('case-id');
            const newStatus = $(this).val();
            const dropdown = $(this);

            // if (confirm(`Are you sure you want to change status to "${newStatus}"?`)) {
            //     sendCaseUpdate(caseId, { status: newStatus.toLowerCase() });
            // } else {
            //     dropdown.val(dropdown.find('option[selected]').val());
            // }
            simpleConfirm(`Are you sure you want to change status to "${newStatus}"?`, function (confirmed) {
                if (confirmed) {
                    sendCaseUpdate(caseId, { status: newStatus.toLowerCase() });
                } else {
                    dropdown.val(dropdown.find('option[selected]').val());
                }
            });
        });

        // $(document).on('change', '.debit-dropdown', function () {
        //     const caseId = $(this).data('case-id');
        //     const newDebit = $(this).val();
        //     const dropdown = $(this);

        //     if (confirm(`Are you sure you want to change debit to "${newDebit}"?`)) {
        //         sendCaseUpdate(caseId, { debit_from_bank: newDebit.toLowerCase() });
        //     } else {
        //         dropdown.val(dropdown.find('option[selected]').val());
        //     }
        // });
        // --- Handle lien_amount update ---
        $(document).on('change', '.debit-dropdown', function () {
            const caseId = $(this).data('case-id');
            const newDebit = $(this).val();
            const dropdown = $(this);

            // if (confirm(`Are you sure you want to change debit to "${newDebit}"?`)) {
            //     // Send update to backend
            //     sendCaseUpdate(caseId, { debit_from_bank: newDebit.toLowerCase() });

            //     // --- Enable/disable lien input in the same row ---
            //     const row = dropdown.closest('tr');
            //     const lienInput = row.find('.lien-input');

            //     if (newDebit === "Yes") {
            //         lienInput.prop("readonly", false).css({ "background-color": "", "color": "" });
            //     } else {
            //         lienInput.prop("readonly", true).css({ "background-color": "#f0f0f0", "color": "#888" });
            //         lienInput.val(""); // optional: clear lien amount if "No"
            //     }

            // } else {
            //     // Rollback dropdown selection if user cancels
            //     dropdown.val(dropdown.find('option[selected]').val());
            // }
            simpleConfirm(`Are you sure you want to change debit to "${newDebit}"?`, function (confirmed) {
                if (confirmed) {
                    // Send update to backend
                    sendCaseUpdate(caseId, { debit_from_bank: newDebit.toLowerCase() });

                    // --- Enable/disable lien input in the same row ---
                    const row = dropdown.closest('tr');
                    const lienInput = row.find('.lien-input');

                    if (newDebit === "Yes") {
                        lienInput.prop("readonly", false).css({ "background-color": "", "color": "" });
                    } else {
                        lienInput.prop("readonly", true).css({ "background-color": "#f0f0f0", "color": "#888" });
                        lienInput.val(""); // optional: clear lien amount if "No"
                    }
                } else {
                    // Rollback dropdown selection if user cancels
                    dropdown.val(dropdown.find('option[selected]').val());
                }
            });
        });

        $(document).on('change', '.lien-input', function () {
            const caseId = $(this).data('case-id');
            const newValue = $(this).val().trim();
            const input = $(this);

            // ✅ Regex: allow integers or floats like 123 or 123.45
            const floatRegex = /^[0-9]+(\.[0-9]+)?$/;

            if (!floatRegex.test(newValue)) {
                // Invalid input -> show tooltip
                input.attr("data-bs-toggle", "tooltip")
                    .attr("data-bs-placement", "top")
                    .attr("title", "Only numbers allowed (e.g. 100 or 100.50)");

                // initialize and show tooltip
                new bootstrap.Tooltip(input[0]).show();

                // reset value after 2 seconds
                setTimeout(() => {
                    input.val('');
                    input.tooltip('dispose'); // remove tooltip
                }, 2000);

                return; // stop update
            }

            // ✅ Valid value -> continue update
            if (confirm(`Update lien amount to "${newValue}"?`)) {
                sendCaseUpdate(caseId, { lien_amount: newValue });
            } else {
                refreshTableData();
            }
        });

        // --- Handle remarks update ---
        $(document).on('change', '.remarks-input', function () {
            const caseId = $(this).data('case-id');
            const newValue = $(this).val();

            if (confirm(`Update remarks to "${newValue}"?`)) {
                sendCaseUpdate(caseId, { remarks: newValue });
            } else {
                $('#casesTable').DataTable().ajax.reload(null, false);
            }
        });

        // Assuming "Transaction DateTime" is column index 18
        $('#col-transaction-search').on('keyup change', function () {
            $('#casesTable').DataTable()
                .column(17)   // adjust index if needed
                .search(this.value)
                .draw();
        });

        // --- Handle UTR Number update ---
        // --- Handle UTR Number update ---
        $(document).on('change', '.utr-input', function () {
            const caseId = $(this).data('case-id');
            const inputField = $(this);
            const newValue = inputField.val().trim();

            // ✅ Regex: exactly 16 alphanumeric characters (letters + numbers only)
            const utrRegex = /^[A-Za-z0-9]{16}$/;

            if (newValue === "") {
                showTooltip(inputField, "UTR Number cannot be empty!");
                return;
            }

            if (!utrRegex.test(newValue)) {
                showTooltip(inputField, "Must be exactly 16 alphanumeric characters.");
                inputField.val(""); // clear invalid input
                return;
            }

            if (confirm(`Update UTR Number to "${newValue}"?`)) {
                sendCaseUpdate(caseId, { utr_number: newValue });
            } else {
                refreshTableData();
            }
        });

        // ✅ Helper function to show tooltip
        function showTooltip(element, message) {
            element.attr("data-bs-toggle", "tooltip")
                .attr("data-bs-placement", "top")
                .attr("title", message)
                .tooltip({ trigger: "manual" })
                .tooltip("show");

            // Auto-hide tooltip after 2s
            setTimeout(() => {
                element.tooltip("dispose");
            }, 2000);
        }




        table.on('draw', updateCardsFromTable);

        function createCustomExportWithHeaders(format) {
            const filteredData = table.rows({ search: 'applied' }).data().toArray();
            const visibleColumns = table.columns(':visible').indexes().toArray();
            filteredData.sort((a, b) => parseInt(a) - parseInt(b));
            const exportHeaders = visibleColumns.map(index => columnHeaders[index] || `Column_${index}`);

            let exportData = [exportHeaders];
            filteredData.forEach(row => {
                let cleanRow = [];
                visibleColumns.forEach(colIndex => {
                    cleanRow.push(cleanCellData(row[colIndex], colIndex));
                });
                exportData.push(cleanRow);
            });

            if (format === 'csv') {
                downloadCSV(exportData, 'cyber_cases_with_headers');
            } else if (format === 'excel') {
                downloadExcel(exportData, 'cyber_cases_with_headers');
            }
        }

        function downloadCSV(data, filename) {
            const csv = data.map(row =>
                row.map(cell => {
                    const cellStr = String(cell || '');
                    if (cellStr.includes(',') || cellStr.includes('\n') || cellStr.includes('"')) {
                        return `"${cellStr.replace(/"/g, '""')}"`;
                    }
                    return cellStr;
                }).join(',')
            ).join('\n');

            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = (filename || 'export') + '_' + new Date().toISOString().slice(0, 10) + '.csv';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }

        function downloadExcel(data, filename) {
            const ws = XLSX.utils.aoa_to_sheet(data);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, "Sheet1");
            XLSX.writeFile(wb, (filename || 'export') + '_' + new Date().toISOString().slice(0, 10) + '.xlsx');
        }

        setTimeout(() => {
            const casesTableButtons = $('#casesTable_wrapper .dt-buttons');
            if (casesTableButtons.length > 0 && $('#customExcelExportWithHeaders').length === 0) {
                casesTableButtons.append(`
                <button id="customExcelExportWithHeaders" class="btn btn-dark btn-sm ms-1">
                    <i class="bi bi-file-earmark-excel"></i> Excel with Headers
                </button>
            `);
                $('#customExcelExportWithHeaders').on('click', function () {
                    createCustomExportWithHeaders('excel');
                });
            }
        }, 100);
    }

    function initCaseTable_viewer() {
        if ($.fn.DataTable.isDataTable('#casesTable1')) {
            $('#casesTable1').DataTable().clear().destroy();
        }



        const columnHeaders = [
            'S.No', 'Complaint Date', 'Mail Date', 'Mail Month', 'Amount',
            'Reference Number', 'Police Station Address', 'Account Number',
            'Name', 'Mobile Number', 'Email ID', 'Status', 'Ageing Days',
            'Debit from Bank', 'Region', 'UTR Number', 'UTR Amount',
            'Transaction DateTime', 'Total Fraudulent Amount', 'Updated On',
            'Updated By', 'PDF URL'
        ];

        $('#casesTable1 thead tr.filter-row th').each(function (i) {
            $('input', this).off().on('keyup change clear', function () {
                if (table.column(i).search() !== this.value) {
                    table.column(i).search(this.value).draw();
                }
            });
        });

        table = $('#casesTable1').DataTable({
            scrollX: true,
            autoWidth: false,
            dom: 'Bfrtip', // B=buttons, l=length menu, f=filter, r=processing, t=table, i=info, p=pagination
            pageLength: 50,
            lengthMenu: [5, 10, 25, 50, 100],
            buttons: [
                {
                    extend: 'pageLength',
                    text: 'Show Entries', // Custom text for the button
                }
            ],
            columnDefs: [
                {
                    targets: "_all", // apply to ALL columns
                    createdCell: function (td) {
                        $(td).css({
                            "font-weight": "300",
                            "font-size": "14px",
                            "font-family": "'Be Vietnam Pro', sans-serif",
                            "padding": "10px"
                        });
                    }
                },
                // Dates: Complaint Date, Mail Date, Transaction DateTime, Updated On  
                { targets: [1, 2, 17, 19], render: (data) => formatDate(data) },
                // Currency: Amount, UTR Amount, Total Fraudulent Amount
                { targets: [4, 16, 18], render: (data) => formatCurrency(data) },
                {
                    targets: 11,
                    render: function (data, type, row) {
                        let bgColor = "";
                        let textColor = "";
                        let content = "";

                        if (data === "Pending") {
                            bgColor = "#ffe5b4";  // light orange
                            textColor = "#b86f00";
                            content = "⏳ Pending";
                        } else if (data === "Picked") {
                            bgColor = "#fff8b4";  // pale yellow
                            textColor = "#c3b600";
                            content = "📌 Picked";
                        } else if (data === "Closed") {
                            bgColor = "#d4edda";  // light green
                            textColor = "#155724";
                            content = "✅ Closed";
                        }

                        return `
                    <span style="display:inline-block; width:100%; padding:4px 0; text-align:center; 
                                background:${bgColor}; color:${textColor}; border-radius:30px; font-weight:600;">
                        ${content}
                    </span>
                `;
                    }
                },
                {
                    targets: 13,
                    createdCell: function (td, cellData, rowData, row, col) {
                        // Clear existing classes/styles if needed
                        td.className = "";

                        if (cellData === "Yes") {
                            td.style.backgroundColor = "#d4edda";  // light green background
                            td.style.color = "#155724";             // dark green text
                            td.style.fontWeight = "600";
                            td.style.borderRadius = "15px";         // rounded corners
                            td.style.textAlign = "center";
                        } else if (cellData === "No") {
                            td.style.backgroundColor = "#f8d7da";  // light red background
                            td.style.color = "#721c24";             // dark red text
                            td.style.fontWeight = "600";
                            td.style.borderRadius = "15px";
                            td.style.textAlign = "center";
                        }
                    },
                    render: function (data, type, row) {
                        let bgColor = "";
                        let textColor = "";
                        let content = "";

                        if (data === "Yes") {
                            bgColor = "#d4edda";   // light green background
                            textColor = "#155724";  // dark green text
                            content = "✅ Yes";
                        } else if (data === "No") {
                            bgColor = "#f8d7da";   // light red background
                            textColor = "#721c24";  // dark red text
                            content = "❌ No";
                        } else {
                            bgColor = "#f0f0f0";   // default light grey background
                            textColor = "#000000";  // black text
                            content = data;
                        }

                        return `
                            <span style="
                            display: inline-block;
                            width: 100%;
                            padding: 4px 6px;
                            border-radius: 15px;
                            font-weight: 600;
                            text-align: center;
                            background-color: ${bgColor};
                            color: ${textColor};
                            ">
                            ${content}
                            </span>
                        `;
                    }

                },
                {
                    targets: 21,
                    render: function (data) {
                        if (!data) return `<span class="text-muted">No PDF</span>`;
                        return `<a href="${data}" target="_blank" class="btn btn-sm btn-outline-dark">
                        <i class="bi bi-file-earmark-pdf"></i> View PDF
                    </a>`;
                    }
                }
            ]
        });

        function cleanCellData(data, column) {
            if (typeof data === 'string') {
                var temp = document.createElement('div');
                temp.innerHTML = data;
                var cleanText = temp.textContent || temp.innerText || '';

                if (column === 21) {
                    var link = temp.querySelector('a');
                    if (link && link.href) {
                        return link.href;
                    }
                    return cleanText === 'No PDF' ? 'No PDF' : cleanText;
                }

                return cleanText;
            }
            return data || '';
        }

        table.on('draw', updateCardsFromTable);

        function createCustomExportWithHeaders(format) {
            const filteredData = table.rows({ search: 'applied' }).data().toArray();
            const visibleColumns = table.columns(':visible').indexes().toArray();

            const exportHeaders = visibleColumns.map(index => columnHeaders[index] || `Column_${index}`);

            let exportData = [exportHeaders];

            filteredData.forEach(row => {
                let cleanRow = [];
                visibleColumns.forEach(colIndex => {
                    const cellData = row[colIndex];
                    cleanRow.push(cleanCellData(cellData, colIndex));
                });
                exportData.push(cleanRow);
            });

            if (format === 'csv') {
                downloadCSV(exportData, 'cyber_cases_with_headers');
            } else if (format === 'excel') {
                downloadExcel(exportData, 'cyber_cases_with_headers');
            }
        }

        function downloadCSV(data, filename) {
            const csv = data.map(row =>
                row.map(cell => {
                    const cellStr = String(cell || '');
                    if (cellStr.includes(',') || cellStr.includes('\n') || cellStr.includes('"')) {
                        return `"${cellStr.replace(/"/g, '""')}"`;
                    }
                    return cellStr;
                }).join(',')
            ).join('\n');

            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = (filename || 'export') + '_' + new Date().toISOString().slice(0, 10) + '.csv';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }

        function downloadExcel(data, filename) {
            const ws = XLSX.utils.aoa_to_sheet(data);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, "Sheet1");
            XLSX.writeFile(wb, (filename || 'export') + '_' +
                new Date().toISOString().slice(0, 10) + '.xlsx');
        }

        setTimeout(() => {
            const casesTableButtons = $('#casesTable1_wrapper .dt-buttons');

            if (casesTableButtons.length > 0 && $('#customExcelExportWithHeadersViewer').length === 0) {
                casesTableButtons.append(`
                    <button id="customExcelExportWithHeadersViewer" class="btn btn-dark btn-sm ms-1">
                        <i class="bi bi-file-earmark-excel"></i> Excel with Headers
                    </button>
                `);

                $('#customExcelExportWithHeadersViewer').on('click', function () {
                    createCustomExportWithHeaders('excel');
                });
            }
        }, 100);
    }

    // function initUserTable() {
    //     if ($('#userTable').length === 0) return;

    //     userTable = $('#userTable').DataTable({
    //         pageLength: 5,
    //         lengthMenu: [5, 10, 25, 50],
    //         ordering: true,
    //         searching: true,
    //         dom: 'Bfrtip',
    //         buttons: [
    //             {
    //                 extend: 'excelHtml5',
    //                 text: 'Download Excel',
    //                 className: 'd-none',
    //                 exportOptions: { columns: [0, 1, 2] }
    //             }
    //         ]
    //     });

    //     $('#downloadExcelBtn').on('click', function () {
    //         userTable.button('.buttons-excel').trigger();
    //     });

    //     $('#create-user-form').on('submit', function (e) {
    //         e.preventDefault();
    //         const form = this;
    //         const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

    //         fetch("/create-user/", {
    //             method: 'POST',
    //             headers: { 'X-CSRFToken': csrfToken },
    //             body: new FormData(form)
    //         })
    //             .then(res => res.json())
    //             .then(data => {
    //                 if (data.success) {
    //                     showToast(data.message, 'success');
    //                     setTimeout(() => form.reset(), 0);
    //                     if (userTable && userTable.ajax) {
    //                         userTable.ajax.reload(null, false);
    //                     }
    //                 } else {
    //                     let errors = "";
    //                     for (let field in data.errors) {
    //                         errors += `${field}: ${data.errors[field].join(', ')}\n`;
    //                     }
    //                     showToast(errors, 'error');
    //                 }
    //             })
    //             .catch(() => showToast('Server error.', 'error'));
    //     });
    // }

    //     function initUserTable() {
    //     if ($('#userTable').length === 0) return;

    //     userTable = $('#userTable').DataTable({
    //         ajax: {
    //             url: "/users-json/",
    //             type: "GET",
    //             dataSrc: ""   // because we return a plain list []
    //         },
    //         columns: [
    //             { data: "username" },
    //             { data: "email" },
    //             {
    //                 data: "role",
    //                 render: function (role) {
    //                     const badgeClass = role === "admin" ? "badge-admin" : "badge-viewer";
    //                     return `<span class="badge ${badgeClass}">${role.charAt(0).toUpperCase() + role.slice(1)}</span>`;
    //                 }
    //             },
    //             {
    //                 data: "id",
    //                 render: function (id, type, row) {
    //                     return `
    //                         <select class="form-select form-select-sm"
    //                                 onchange="updateUserRole('${id}', this.value)">
    //                             <option value="viewer" ${row.role === "viewer" ? "selected" : ""}>Viewer</option>
    //                             <option value="admin" ${row.role === "admin" ? "selected" : ""}>Admin</option>
    //                         </select>
    //                     `;
    //                 }
    //             }
    //         ],
    //         pageLength: 5,
    //         lengthMenu: [5, 10, 25, 50],
    //         ordering: true,
    //         searching: true,
    //         dom: 'Bfrtip',
    //         buttons: [
    //             {
    //                 extend: 'excelHtml5',
    //                 text: 'Download Excel',
    //                 className: 'd-none',
    //                 exportOptions: { columns: [0, 1, 2] }
    //             }
    //         ]
    //     });

    //     $('#downloadExcelBtn').on('click', function () {
    //         userTable.button('.buttons-excel').trigger();
    //     });

    //     $('#create-user-form').on('submit', function (e) {
    //         e.preventDefault();
    //         const form = this;
    //         const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

    //         fetch("/create-user/", {
    //             method: 'POST',
    //             headers: { 'X-CSRFToken': csrfToken },
    //             body: new FormData(form)
    //         })
    //             .then(res => res.json())
    //             .then(data => {
    //                 if (data.success) {
    //                     showToast(data.message, 'success');
    //                     setTimeout(() => form.reset(), 0);

    //                     // 🔄 reload new data
    //                     userTable.ajax.reload(null, false);
    //                 } else {
    //                     let errors = "";
    //                     if (data.errors) {
    //                         for (let field in data.errors) {
    //                             const fieldErrors = data.errors[field]
    //                                 .map(e => e.message)
    //                                 .join(', ');
    //                             errors += `${field}: ${fieldErrors}\n`;
    //                         }
    //                     } else if (data.error) {
    //                         errors = data.error;
    //                     }
    //                     showToast(errors, 'error');
    //                 }
    //             })
    //             .catch(() => showToast('Server error.', 'error'));
    //     });
    // }


    // window.updateUserRole = function (userId, newRole) {
    //     if (!confirm(`Change role to "${newRole}"?`)) return;

    //     const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
    //         document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    //     if (!csrfToken) {
    //         showToast('CSRF token not found.', 'error');
    //         return;
    //     }

    //     const data = new URLSearchParams();
    //     data.append('user_id', userId);
    //     data.append('role', newRole);

    //     fetch('/update-role/', {
    //         method: 'POST',
    //         headers: {
    //             'X-CSRFToken': csrfToken,
    //         },
    //         body: data
    //     })
    //         .then(res => {
    //             if (!res.ok) throw new Error(`Network response was not ok: ${res.status}`);
    //             return res.json();
    //         })
    //         .then(data => {
    //             if (data.success) {
    //                 const badge = document.getElementById(`role-badge-${userId}`);
    //                 if (badge) {
    //                     badge.textContent = newRole.charAt(0).toUpperCase() + newRole.slice(1);
    //                     badge.className = "badge " + (newRole === "admin" ? "badge-admin" : "badge-viewer");
    //                 }
    //                 showToast(data.message, 'success');
    //             } else {
    //                 showToast(data.error || 'Failed to update role', 'error');
    //             }
    //         })
    //         .catch(err => {
    //             console.error('Fetch error:', err);
    //             showToast('Error updating role: ' + err.message, 'error');
    //         });
    // };

    // window.updateUserRole = function (userId, newRole) {
    //     if (!confirm(`Change role to "${newRole}"?`)) return;

    //     const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
    //         document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    //     if (!csrfToken) {
    //         showToast('CSRF token not found.', 'error');
    //         return;
    //     }

    //     const data = new URLSearchParams();
    //     data.append('user_id', userId);
    //     data.append('role', newRole);

    //     fetch('/update-role/', {
    //         method: 'POST',
    //         headers: {
    //             'X-CSRFToken': csrfToken,
    //         },
    //         body: data
    //     })
    //         .then(res => {
    //             if (!res.ok) throw new Error(`Network response was not ok: ${res.status}`);
    //             return res.json();
    //         })
    //         .then(data => {
    //             if (data.success) {
    //                 const badge = document.getElementById(`role-badge-${userId}`);
    //                 if (badge) {
    //                     badge.textContent = newRole.charAt(0).toUpperCase() + newRole.slice(1);
    //                     badge.className = "badge " + (newRole === "admin" ? "badge-admin" : "badge-viewer");
    //                 }
    //                 showToast(data.message, 'success');
    //             } else {
    //                 showToast(data.error || 'Failed to update role', 'error');
    //             }
    //         })
    //         .catch(err => {
    //             console.error('Fetch error:', err);
    //             showToast('Error updating role: ' + err.message, 'error');
    //         });
    // };


    // function initUserTable() {
    //     if ($('#userTable').length === 0) return;

    //     userTable = $('#userTable').DataTable({
    //         processing: true,
    //         serverSide: true,
    //         ajax: { url: "/users-json/", type: "GET" },
    //         columns: [
    //             { data: "id" },
    //             { data: "username" },
    //             { data: "email" },
    //             {
    //                 data: "role",
    //                 render: function (role) {
    //                     const badgeClass = role === "admin" ? "badge-admin" : "badge-viewer";
    //                     return `<span class="badge ${badgeClass}">${role.charAt(0).toUpperCase() + role.slice(1)}</span>`;
    //                 }
    //             },
    //             {
    //                 data: "id",
    //                 render: function (id, type, row) {
    //                     return `
    //                 <span class="m-5">
    //                 <select class="form-select form-select-sm role-selector shadow-sm rounded-pill px-2 py-1" 
    //                         style="width: 120px; font-size: 0.85rem;"
    //                         data-user-id="${id}">
    //                     <option value="viewer" ${row.role === "viewer" ? "selected" : ""}>
    //                         👀 Viewer
    //                     </option>
    //                     <option value="admin" ${row.role === "admin" ? "selected" : ""}>
    //                         🔑 Admin
    //                     </option>
    //                 </select>

    //                 </span>    
    //                 <span class="">
    //                 <button class="btn btn-sm btn-danger delete-user-btn" data-user-id="${id}">Delete</button>
    //                 </span>

    //                 `;
    //                 },
    //                 orderable: false,
    //                 searchable: false
    //             }
    //         ],
    //         pageLength: 5,
    //         lengthMenu: [5, 10, 25, 50],
    //         dom: 'Bfrtip',
    //         buttons: [
    //             { extend: 'excelHtml5', text: 'Download Excel', className: 'd-none', exportOptions: { columns: [0, 1, 2, 3] } }
    //         ]
    //     });

    //     $('#downloadExcelBtn').on('click', function () {
    //         userTable.button('.buttons-excel').trigger();
    //     });

    //     // Role change
    //     $('#userTable').on('change', '.role-selector', function () {
    //         const userId = $(this).data('user-id');
    //         const newRole = $(this).val();
    //         const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    //         fetch(`/update-user-role/${userId}/`, {
    //             method: 'POST',
    //             headers: { 'X-CSRFToken': csrfToken },
    //             body: new URLSearchParams({ role: newRole })
    //         })
    //             .then(res => res.json())
    //             .then(data => {
    //                 if (data.success) {
    //                     showToast("Role updated", "success");
    //                     const row = userTable.row($(this).closest('tr'));
    //                     const rowData = row.data();
    //                     rowData.role = newRole;
    //                     row.data(rowData).draw(false);
    //                 } else {
    //                     showToast(data.error || "Failed to update role", "error");
    //                 }
    //             });
    //     });

    //     // Delete user
    //     $('#userTable').on('click', '.delete-user-btn', function () {
    //         const userId = $(this).data('user-id');
    //         const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    //         if (!confirm("Are you sure you want to delete this user?")) return;

    //         fetch(`/delete-user/${userId}/`, {
    //             method: 'POST',
    //             headers: { 'X-CSRFToken': csrfToken },
    //         })
    //             .then(res => res.json())
    //             .then(data => {
    //                 if (data.success) {
    //                     showToast("User deleted", "success");
    //                     userTable.ajax.reload(null, false); // reload table
    //                 } else {
    //                     showToast(data.error || "Failed to delete user", "error");
    //                 }
    //             });
    //     });

    //     // Create user
    //     $('#create-user-form').on('submit', function (e) {
    //         e.preventDefault();
    //         const form = this;
    //         const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

    //         fetch("/create-user/", {
    //             method: 'POST',
    //             headers: { 'X-CSRFToken': csrfToken },
    //             body: new FormData(form)
    //         })
    //             .then(res => res.json())
    //             .then(data => {
    //                 if (data.success) {
    //                     showToast(data.message, 'success');
    //                     setTimeout(() => form.reset(), 0);
    //                     userTable.ajax.reload(null, false);
    //                 } else {
    //                     let errors = "";
    //                     if (data.errors) {
    //                         for (let field in data.errors) {
    //                             errors += `${field}: ${data.errors[field].join(', ')}\n`;
    //                         }
    //                     } else if (data.error) {
    //                         errors = data.error;
    //                     }
    //                     showToast(errors, 'error');
    //                 }
    //             })
    //             .catch(() => showToast('Server error.', 'error'));
    //     });
    // }

    function initUserTable() {
        if ($('#userTable').length === 0) return;

        const userTable = $('#userTable').DataTable({
            processing: true,
            serverSide: true,
            ajax: { url: "/users-json/", type: "GET" },
            columns: [
                {
                    data: null,
                    render: function (data, type, row, meta) {
                        return meta.row + meta.settings._iDisplayStart + 1;
                    },
                    orderable: false,
                    searchable: false
                },
                { data: "username" },
                { data: "email" },
                {
                    data: "role",
                    render: function (role) {
                        const badgeClass = role === "admin" ? "badge-admin" : "badge-viewer";
                        return `<span class="badge ${badgeClass}">
                                ${role.charAt(0).toUpperCase() + role.slice(1)}
                            </span>`;
                    }
                },
                {
                    data: "id",
                    render: function (id, type, row) {
                        return `
                        <span class="me-2">
                            <select class="form-select-sm role-selector shadow-sm rounded-pill px-2 py-1" 
                                    style="width: 120px; font-size: 0.85rem;"
                                    data-user-id="${id}">
                                <option value="viewer" ${row.role === "viewer" ? "selected" : ""}>👀 Viewer</option>
                                <option value="admin" ${row.role === "admin" ? "selected" : ""}>🔑 Admin</option>
                            </select>
                        </span>
                        <span>
                            <button class="btn btn-sm btn-danger delete-user-btn" data-user-id="${id}">
                                Delete
                            </button>
                        </span>
                    `;
                    },
                    orderable: false,
                    searchable: false
                }
            ],
            pageLength: 5,
            lengthMenu: [5, 10, 25, 50],
            dom: '<"row mb-3"<"col-md-6 d-flex align-items-center"l><"col-md-6 d-flex justify-content-end"f>>' +
                'rt' +
                '<"row mt-3"<"col-md-6"i><"col-md-6 d-flex justify-content-end"p>>B',
            buttons: [
                {
                    extend: 'excelHtml5',
                    text: 'Download Excel',
                    className: 'd-none',
                    exportOptions: { columns: [0, 1, 2, 3] }
                }
            ]
        });

        // Download Excel
        $('#downloadExcelBtn').on('click', function () {
            userTable.button('.buttons-excel').trigger();
        });

        // Role change
        // Role change with confirmation
        $('#userTable').on('change', '.role-selector', function () {
            const userId = $(this).data('user-id');
            const newRole = $(this).val();
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            // Confirm before sending request
            if (!confirm(`Are you sure you want to change this user's role to "${newRole}"?`)) {
                // ❌ If user cancels, reset select to previous value
                userTable.ajax.reload(null, false);
                return;
            }

            fetch(`/update-user-role/${userId}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
                body: new URLSearchParams({ role: newRole })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showToast(`✅ Role updated to ${newRole.charAt(0).toUpperCase() + newRole.slice(1)} successfully.`, "success");

                        // update row instantly
                        const row = userTable.row($(this).closest('tr'));
                        const rowData = row.data();
                        rowData.role = newRole;
                        row.data(rowData).draw(false);

                    } else {
                        showToast(`❌ ${data.error || "Failed to update role"}`, "danger");
                        userTable.ajax.reload(null, false);
                    }
                })
                .catch(() => {
                    showToast("⚠️ Server error while updating role.", "danger");
                    userTable.ajax.reload(null, false);
                });
        });



        // Delete user
        // $('#userTable').on('click', '.delete-user-btn', function () {
        //     const userId = $(this).data('user-id');
        //     const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        //     if (!confirm("Are you sure you want to delete this user?")) return;

        //     fetch(`/delete-user/${userId}/`, {
        //         method: 'POST',
        //         headers: { 'X-CSRFToken': csrfToken },
        //     })
        //         .then(res => res.json())
        //         .then(data => {
        //             if (data.success) {
        //                 showToast("User deleted", "success");
        //                 userTable.ajax.reload(null, false);
        //             } else {
        //                 showToast(data.error || "Failed to delete user", "danger");
        //             }
        //         })
        //         .catch(() => showToast("Server error while deleting user.", "danger"));
        // });

        // Updated delete user code
        $('#userTable').on('click', '.delete-user-btn', function () {
            const userId = $(this).data('user-id');
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            // Replace this line:
            // if (!confirm("Are you sure you want to delete this user?")) return;

            // With this:
            simpleConfirm("Are you sure you want to delete this user?", function (confirmed) {
                if (!confirmed) return;

                // Move the fetch request inside the callback
                fetch(`/delete-user/${userId}/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken },
                })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            showToast("User deleted", "success");
                            userTable.ajax.reload(null, false);
                        } else {
                            showToast(data.error || "Failed to delete user", "danger");
                        }
                    })
                    .catch(() => showToast("Server error while deleting user.", "danger"));
            });
        });

        // Create user with inline validation
        // Create user with single error at a time
        // Create user with single error at a time
        // Create user with inline validation + success message at top
        $('#create-user-form').on('submit', function (e) {
            e.preventDefault();
            const form = this;
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

            // clear old errors + alerts
            $(form).find('.invalid-feedback').remove();
            $(form).find('.is-invalid').removeClass('is-invalid');
            $(form).find('.alert').remove();

            fetch("/create-user/", {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
                body: new FormData(form)
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        // ✅ Success alert at top of form
                        $(form).prepend(`
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        ${data.message || "User created successfully!"}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                `);

                        setTimeout(() => form.reset(), 0);
                        userTable.ajax.reload(null, false);
                    } else {
                        if (data.errors) {
                            if (data.errors.__all__) {
                                // Handle non-field error (like password mismatch)
                                const firstError = data.errors.__all__[0].message || data.errors.__all__[0];
                                const pwdField = $(form).find('[name="password2"]');
                                pwdField.addClass('is-invalid');
                                pwdField.after(`<div class="invalid-feedback">${firstError}</div>`);
                            } else {
                                // Handle first field error
                                let firstField = Object.keys(data.errors)[0];
                                let firstErrorMsg = data.errors[firstField][0].message || data.errors[firstField][0];

                                let input = $(form).find(`[name=${firstField}]`);
                                input.addClass('is-invalid');
                                input.after(`<div class="invalid-feedback">${firstErrorMsg}</div>`);
                            }
                        } else if (data.error) {
                            // General error fallback at top
                            $(form).prepend(`
                        <div class="alert alert-danger alert-dismissible fade show" role="alert">
                            ${data.error}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    `);
                        } else {
                            showToast("Something went wrong. Please try again.", 'danger');
                        }
                    }
                })
                .catch(() => showToast('Server error while creating user.', 'danger'));
        });




        // Auto reload if parent div is visible
        setInterval(() => {
            const container = document.getElementById("userTableContainer"); // wrap div id
            if (container && container.offsetParent !== null) {
                userTable.ajax.reload(null, false);
            }
        }, 30000); // every 30s
    }

    function bindFilterEvents() {
        $('#apply-filters').on('click', function (e) {
            e.preventDefault();
            applyFilters();
        });

        $('#reset-filters').on('click', function (e) {
            e.preventDefault();
            resetFilters();
        });
    }

    function fetchCases() {
        fetch('/cyberapp/cases/')
            .then(res => {
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                return res.json();
            })
            .then(data => {
                allCases = data.cases || [];
                renderTable(allCases);
            })
            .catch(err => {
                console.error('Error loading data:', err);
                showToast('Failed to load cases data', 'error');
            });
    }

    function renderTable(data) {
        table.clear();

        data.forEach(c => {
            table.row.add([
                c.sno,
                c.complaint_date,
                c.mail_date,
                c.mail_month,
                c.amount,
                c.reference_number,
                c.police_station_address,
                c.account_number,
                c.name,
                c.mobile_number,
                c.email_id,
                c.status,
                c.ageing_days,
                c.debit_from_bank,
                c.region,
                c.utr_number,
                c.utr_amount,
                c.transaction_datetime,
                c.total_fraudulent_amount,
                c.updated_on,
                c.updated_by,
                c.pdf_url,
                c.lien_amount,
                c.remarks,
            ]);
        });

        table.draw(false);
        updateDashboardCards(data);
    }

    function applyFilters() {
        const filterType = $('#date-filter-type').val();
        const startDate = $('#start-date').val();
        const endDate = $('#end-date').val();
        const status = $('#status-filter').val().toLowerCase();
        const account = $('#account-filter').val().toLowerCase();
        const reference = $('#reference-filter').val().toLowerCase();
        const month = $('#month-filter').val().toLowerCase();

        const filtered = allCases.filter(c => {
            let valid = true;
            if (startDate) valid = valid && c[filterType] >= startDate;
            if (endDate) valid = valid && c[filterType] <= endDate;
            if (status) valid = valid && String(c.status).toLowerCase() === status;
            if (account) valid = valid && String(c.account_number || '').toLowerCase().includes(account);
            if (reference) valid = valid && String(c.reference_number || '').toLowerCase().includes(reference);
            if (month) valid = valid && String(c.mail_month || '').toLowerCase() === month;
            return valid;
        });

        renderTable(filtered);
    }

    function resetFilters() {
        $('#date-filter-type').val('mail_date');
        $('#start-date').val('');
        $('#end-date').val('');
        $('#status-filter').val('');
        $('#account-filter').val('');
        $('#reference-filter').val('');
        $('#month-filter').val('');
        renderTable(allCases);
    }
    function updateDashboardCards(data) {
        let total = data.length;
        let pending = 0, picked = 0, closed = 0;
        let totalFraud = 0;
        let totalLien = 0;
        let totalAmount = 0;

        data.forEach(c => {
            const status = c.status;
            const fraudAmount = parseFloat(String(c.total_fraudulent_amount || '0').replace(/[₹,]/g, '')) || 0;
            const lienAmount = parseFloat(String(c.lien_amount || '0').replace(/[₹,]/g, '')) || 0;
            const caseAmount = parseFloat(String(c.amount || '0').replace(/[₹,]/g, '')) || 0;

            if (status === 'Pending') pending++;
            else if (status === 'Picked') picked++;
            else if (status === 'Closed') closed++;

            totalFraud += fraudAmount;
            totalLien += lienAmount;
            totalAmount += caseAmount;
        });

        // Existing cards
        $('#card-total-cases').text(total);
        $('#card-pending').text(pending);
        $('#card-picked').text(picked);
        $('#card-closed').text(closed);

        // Fraud amount formatting
        if (totalFraud >= 10000000) {
            $('#card-fraud-amount').text(formatToCrore(totalFraud));
        } else {
            $('#card-fraud-amount').text(formatINR(totalFraud));
        }

        // New cards
        $('#card-lien-amount').text(formatINR(totalLien));
        $('#card-total-amount').text(formatINR(totalAmount));
    }

    function updateCardsFromTable() {
        const filteredData = table.rows({ search: 'applied' }).data().toArray();

        let total = filteredData.length;
        let pending = 0, picked = 0, closed = 0;
        let totalFraud = 0;
        let totalLien = 0;
        let totalAmount = 0;

        filteredData.forEach(row => {
            const status = row[11]?.toString().trim();
            const fraudAmount = parseFloat(String(row[18] || '0').replace(/[₹,]/g, '')) || 0;
            const lienAmount = parseFloat(String(row[22] || '0').replace(/[₹,]/g, '')) || 0; // ✅ new col
            const caseAmount = parseFloat(String(row[4] || '0').replace(/[₹,]/g, '')) || 0;  // ✅ amount col

            if (status === 'Pending') pending++;
            else if (status === 'Picked') picked++;
            else if (status === 'Closed') closed++;

            totalFraud += fraudAmount;
            totalLien += lienAmount;
            totalAmount += caseAmount;
        });

        $('#card-total-cases').text(total);
        $('#card-pending').text(pending);
        $('#card-picked').text(picked);
        $('#card-closed').text(closed);

        if (totalFraud >= 10000000) {
            $('#card-fraud-amount').text(formatToCrore(totalFraud));
        } else {
            $('#card-fraud-amount').text(formatINR(totalFraud));
        }

        $('#card-lien-amount').text(formatINR(totalLien));
        $('#card-total-amount').text(formatINR(totalAmount));
    }

    function refreshTableData() {
        console.log('🔄 Refreshing table data...');

        fetch('/cyberapp/cases/')
            .then(res => {
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                return res.json();
            })
            .then(data => {
                allCases = data.cases || [];

                const currentSearch = table.search();
                const currentPage = table.page();

                table.clear();

                allCases.forEach(c => {
                    table.row.add([
                        c.sno,
                        c.complaint_date,
                        c.mail_date,
                        c.mail_month,
                        c.amount,
                        c.reference_number,
                        c.police_station_address,
                        c.account_number,
                        c.name,
                        c.mobile_number,
                        c.email_id,
                        c.status,
                        c.ageing_days,
                        c.debit_from_bank,
                        c.region,
                        c.utr_number,
                        c.utr_amount,
                        c.transaction_datetime,
                        c.total_fraudulent_amount,
                        c.updated_on,
                        c.updated_by,
                        c.pdf_url,
                        c.lien_amount,
                        c.remarks,
                    ]);
                });

                table.search(currentSearch);
                table.draw(false);

                if (currentPage < table.page.info().pages) {
                    table.page(currentPage).draw(false);
                }

                updateDashboardCards(allCases);

                console.log('✅ Table refreshed successfully');
            })
            .catch(err => {
                console.error('❌ Error refreshing data:', err);
                showToast('Failed to refresh table data', 'error');
            });
    }

    function initRefreshFunctionality() {
        setTimeout(() => {
            let targetTableWrapper;

            if (role === 'viewer') {
                targetTableWrapper = $('#casesTable1_wrapper .dt-buttons');
            } else {
                targetTableWrapper = $('#casesTable_wrapper .dt-buttons');
            }

            if (targetTableWrapper.length > 0 && $('#manualRefreshBtn').length === 0) {
                targetTableWrapper.append(`
                    <button id="manualRefreshBtn" class="btn btn-dark btn-sm ms-2" title="Refresh Data">
                        <i class="bi bi-arrow-clockwise"></i> Refresh
                    </button>
                `);

                $('#manualRefreshBtn').on('click', function () {
                    const btn = $(this);
                    btn.prop('disabled', true).html('<i class="bi bi-arrow-clockwise"></i> Refreshing...');

                    refreshTableData();

                    setTimeout(() => {
                        btn.prop('disabled', false).html('<i class="bi bi-arrow-clockwise"></i> Refresh');
                    }, 1000);
                });
            }
        }, 500);

        console.log('✅ Refresh functionality initialized');
    }

    function showToast(message, type = 'success') {
        const toastId = 'toast-' + Date.now();
        const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';

        const toastHtml = `
            <div class="toast align-items-center text-white ${bgClass} border-0 mb-2" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        $('#toastContainer').append(toastHtml);

        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            new bootstrap.Toast(document.getElementById(toastId), { delay: 3000 }).show();
        } else {
            setTimeout(() => {
                $('#' + toastId).fadeOut(() => $('#' + toastId).remove());
            }, 3000);
        }
    }


    // ===========================   cams  =============================
});