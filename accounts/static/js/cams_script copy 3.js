let table;
let isStatsLoading = false;

$(document).ready(function () {
    initDataTable();
    initFilters();
    loadStats();
});

function getAllFilterData() {
    return {
        entity_filter: $('#entity-filter').val() || '',
        isin_filter: $('#isin-filter').val() || '',
        scheme_filter: $('#scheme-filter').val() || '',
        month_filter: $('#month-filter').val() || '',

        col_0_search: $('.column-search[data-column="0"]').val() || '',
        col_1_search: $('.column-search[data-column="1"]').val() || '',
        col_2_search: $('.column-search[data-column="2"]').val() || '',
        col_3_search: $('.column-search[data-column="3"]').val() || '',
        col_4_search: $('.column-search[data-column="4"]').val() || '',
        col_5_search: $('.column-search[data-column="5"]').val() || '',
        col_6_search: $('.column-search[data-column="6"]').val() || '',
        col_7_search: $('.column-search[data-column="7"]').val() || '',
        col_8_search: $('.column-search[data-column="8"]').val() || '',
        col_9_search: $('.column-search[data-column="9"]').val() || '',

        global_search: table ? table.search() : ''
    };
}

function forceUpdateStats() {
    if (isStatsLoading) return;
    isStatsLoading = true;

    const filterData = getAllFilterData();

    $.ajax({
        url: '/camsapp/api/summary-stats/',
        type: 'GET',
        data: filterData,
        cache: false,
        timeout: 10000,
        success: function (response) {
            $('#card-entities').fadeOut(100, function () {
                $(this).text((response.total_entities || 0).toLocaleString()).fadeIn(100);
            });
            $('#card-folios').fadeOut(100, function () {
                $(this).text((response.total_folios || 0).toLocaleString()).fadeIn(100);
            });
            $('#card-market-value').fadeOut(100, function () {
                $(this).text('₹' + (response.total_market_value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })).fadeIn(100);
            });
            $('#card-cost-value').fadeOut(100, function () {
                $(this).text('₹' + (response.total_cost_value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })).fadeIn(100);
            });
        },
        error: function (xhr, error) {
            console.error('Stats Error:', error, xhr.responseText);
            showToast('Error updating statistics: ' + error, 'error');
        },
        complete: function () {
            isStatsLoading = false;
        }
    });
}

// function initDataTable() {
//     table = $('#portfolio-table').DataTable({
//         processing: true,
//         serverSide: true,
//         ajax: {
//             url: '/camsapp/api/portfolio-data/',
//             type: 'GET',
//             data: function (d) {
//                 Object.assign(d, getAllFilterData());
//                 return d;
//             },
//             error: function (xhr, error) {
//                 console.error('Table AJAX Error:', error);
//                 showToast('Error loading table data', 'error');
//             }
//         },
//         columns: [
//             { data: 0, orderable: true },
//             { data: 1, orderable: true },
//             { data: 2, orderable: true },
//             { data: 3, orderable: true },
//             { data: 4, orderable: true, className: 'text-end' },
//             { data: 5, orderable: true, className: 'text-end' },
//             { data: 6, orderable: true },
//             { data: 7, orderable: true, className: 'text-end' },
//             { data: 8, orderable: true },
//             { data: 9, orderable: true }
//         ],
//         pageLength: 10,
//         lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
//         order: [[8, 'desc']],
//         language: {
//             processing: '<div class="spinner-border text-primary"></div>',
//             paginate: {
//                 previous: '<i class="bi bi-chevron-left"></i>',
//                 next: '<i class="bi bi-chevron-right"></i>'
//             }
//         },
//         drawCallback: function (settings) {
//             $('#total-records').text((settings._iRecordsTotal || 0).toLocaleString());
//             initISINEdit();

//             // Slight delay to avoid race condition
//             setTimeout(forceUpdateStats, 500);
//         }
//     });
// }
// Updated DataTable columns configuration (swap Folio No and Entity Name)
// function initDataTable() {
//     table = $('#portfolio-table').DataTable({
//         processing: true,
//         serverSide: true,
//         ajax: {
//             url: '/camsapp/api/portfolio-data/',
//             type: 'GET',
//             data: function (d) {
//                 Object.assign(d, getAllFilterData());
//                 return d;
//             },
//             error: function (xhr, error) {
//                 console.error('Table AJAX Error:', error);
//                 showToast('Error loading table data', 'error');
//             }
//         },
//         columns: [
//             { data: 0, orderable: false }, // S.No - not orderable
//             { data: 1, orderable: true },  // Entity Name (swapped)
//             { data: 2, orderable: true },  // Folio No (swapped)
//             { data: 3, orderable: true },  // ISIN
//             { data: 4, orderable: true },  // Scheme Name
//             { data: 5, orderable: true, className: 'text-end' }, // Cost Value
//             { data: 6, orderable: true, className: 'text-end' }, // Unit Balance
//             { data: 7, orderable: true },  // NAV Date
//             { data: 8, orderable: true, className: 'text-end' }, // Market Value
//             { data: 9, orderable: true },  // Updated On
//             { data: 10, orderable: true } // Updated By
//         ],
//         pageLength: 10,
//         lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
//         order: [[9, 'desc']], // Updated to column 9 for Updated On
//         language: {
//             processing: '<div class="spinner-border text-primary"></div>',
//             paginate: {
//                 previous: '<i class="bi bi-chevron-left"></i>',
//                 next: '<i class="bi bi-chevron-right"></i>'
//             }
//         },
//         drawCallback: function (settings) {
//             $('#total-records').text((settings._iRecordsTotal || 0).toLocaleString());
//             initISINEdit();
//             setTimeout(forceUpdateStats, 500);
//         }
//     });
// }

// Just update the language.processing in your existing initDataTable function
function initDataTable() {
    table = $('#portfolio-table').DataTable({
        processing: true,
        serverSide: true,
        ajax: {
            url: '/camsapp/api/portfolio-data/',
            type: 'GET',
            data: function (d) {
                Object.assign(d, getAllFilterData());
                return d;
            },
            error: function (xhr, error) {
                console.error('Table AJAX Error:', error);
                showToast('Error loading table data', 'error');
            }
        },
        columns: [
            { data: 0, orderable: false }, // S.No - not orderable
            { data: 1, orderable: true },  // Entity Name (swapped)
            { data: 2, orderable: true },  // Folio No (swapped)
            { data: 3, orderable: true },  // ISIN
            { data: 4, orderable: true },  // Scheme Name
            { data: 5, orderable: true, className: 'text-end' }, // Cost Value
            { data: 6, orderable: true, className: 'text-end' }, // Unit Balance
            { data: 7, orderable: true },  // NAV Date
            { data: 8, orderable: true, className: 'text-end' }, // Market Value
            { data: 9, orderable: true },  // Updated On
            { data: 10, orderable: true } // Updated By
        ],
        pageLength: 10,
        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
        order: [[9, 'desc']],
        language: {
            // FIXED: Better processing indicator
            processing: '<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>',
            paginate: {
                previous: '<i class="bi bi-chevron-left"></i>',
                next: '<i class="bi bi-chevron-right"></i>'
            }
        },
        drawCallback: function (settings) {
            $('#total-records').text((settings._iRecordsTotal || 0).toLocaleString());
            initISINEdit();
            setTimeout(forceUpdateStats, 500);
        }
    });
}

// Add this simple CSS to your stylesheet
/* 
.dataTables_processing {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid #dee2e6 !important;
    border-radius: 0.375rem !important;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075) !important;
    padding: 1rem !important;
    font-weight: 500 !important;
}
*/

function initFilters() {
    // Apply filters button
    $('#apply-filters1').click(function () {
        table.ajax.reload();
        setTimeout(forceUpdateStats, 1000);
        showToast('Filters applied', 'success');
    });

    // Reset filters button
    $('#reset-filters1').click(function () {
        $('#entity-filter, #isin-filter, #scheme-filter').val('');
        $('#month-filter').val('');
        $('.column-search').val('');
        table.search('').columns().search('');
        table.ajax.reload();
        setTimeout(forceUpdateStats, 1000);
        showToast('Filters reset', 'info');
    });

    // Column search with debounce
    let searchTimeouts = {};
    $('.column-search').on('input propertychange change', function () {
        const column = $(this).data('column');
        clearTimeout(searchTimeouts[column]);
        searchTimeouts[column] = setTimeout(() => {
            table.ajax.reload();
            setTimeout(forceUpdateStats, 1000);
        }, 500);
    });

    // Global search debounced
    $('#portfolio-table_filter input').on('input', function () {
        setTimeout(forceUpdateStats, 1000);
    });

    // Download buttons
    $('#download-summary').click(downloadSummary);
    $('#download-detail-previous').click(() => {
        const prev = getPreviousMonth();
        downloadDetail(prev.month, prev.year);
    });
    $('#download-detail-current').click(() => {
        const current = getCurrentMonth();
        downloadDetail(current.month, current.year);
    });
}

function loadStats() {
    forceUpdateStats();
}

// function initISINEdit() {
//     $('.editable-isin').off('click').on('click', function () {
//         const $this = $(this);
//         if ($this.find('input').length) return;
//         const currentValue = $this.data('value');
//         const id = $this.data('id');
//         const originalHtml = $this.html();

//         const $input = $('<input>', {
//             type: 'text',
//             value: currentValue,
//             class: 'form-control form-control-sm editing',
//             maxlength: 20,
//             title: 'ISIN must be 8 to 20 characters', // Tooltip
//             'data-bs-toggle': 'tooltip'
//         });

//         $this.html('').append($input);
//         $input.focus().select();

//         // Initialize Bootstrap tooltip
//         const tooltip = new bootstrap.Tooltip($input[0]);

//         $input.on('blur keypress', function (e) {
//             if (e.type === 'keypress' && e.which !== 13) return;
//             const newValue = $(this).val().trim().toUpperCase();

//             // Dispose tooltip
//             tooltip.dispose();

//             if (newValue === currentValue) {
//                 $this.html(originalHtml);
//                 return;
//             }
//             if (newValue.length < 8 || newValue.length > 20) {
//                 showToast('ISIN must be 8 to 20 characters', 'error');
//                 $this.html(originalHtml);
//                 return;
//             }
//             updateISIN(id, newValue, $this, originalHtml);
//         });
//     });
// }


function updateISIN(id, newValue, $element, originalHtml) {
    $.ajax({
        url: '/camsapp/api/update-isin/',
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        data: JSON.stringify({ id: id, isin: newValue }),
        contentType: 'application/json',
        success: function (response) {
            if (response.success) {
                $element.html(newValue).data('value', newValue);
                showToast('ISIN updated successfully', 'success');
                table.ajax.reload(null, false);
            } else {
                showToast(response.error || 'Update failed', 'error');
                $element.html(originalHtml);
            }
        },
        error: function () {
            showToast('Error updating ISIN', 'error');
            $element.html(originalHtml);
        }
    });
}

// Bootstrap 5 toast with your toast container
function showToast(message, type) {
    const toastEl = $('#toast');
    toastEl.text(message);
    toastEl.removeClass('bg-success bg-danger bg-info bg-warning');

    switch (type) {
        case 'success':
            toastEl.addClass('bg-success');
            break;
        case 'error':
            toastEl.addClass('bg-danger');
            break;
        case 'info':
            toastEl.addClass('bg-info');
            break;
        case 'warning':
            toastEl.addClass('bg-warning');
            break;
        default:
            toastEl.addClass('bg-secondary');
    }
    toastEl.show();

    setTimeout(() => {
        toastEl.fadeOut(400);
    }, 3500);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            if (cookie.trim().startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.trim().substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function downloadSummary() {
    const filterData = getAllFilterData();
    const params = new URLSearchParams();
    Object.keys(filterData).forEach(key => {
        if (filterData[key]) params.append(key, filterData[key]);
    });
    const downloadUrl = '/camsapp/download/summary/?' + params.toString();
    showToast('Preparing download...', 'info');
    window.open(downloadUrl, '_blank');
    setTimeout(() => showToast('Summary download started', 'success'), 1000);
}

function downloadDetail(month, year) {
    const filterData = getAllFilterData();
    const params = new URLSearchParams();
    params.append('month', month);
    params.append('year', year);
    ['entity_filter', 'isin_filter', 'scheme_filter'].forEach(key => {
        if (filterData[key]) params.append(key, filterData[key]);
    });
    const downloadUrl = '/camsapp/download/detail/?' + params.toString();
    showToast(`Preparing ${getMonthName(month)} ${year} detail download...`, 'info');
    window.open(downloadUrl, '_blank');
    setTimeout(() => showToast(`Detail download for ${getMonthName(month)} ${year} started`, 'success'), 1000);
}

function getCurrentMonth() {
    const now = new Date();
    return { month: now.getMonth() + 1, year: now.getFullYear() };
}

function getPreviousMonth() {
    const now = new Date();
    const prev = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    return { month: prev.getMonth() + 1, year: prev.getFullYear() };
}

function getMonthName(monthNumber) {
    return [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ][monthNumber - 1] || 'Unknown';
}

// Setup global ajax csrf for jQuery
$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!(/^(http:|https:).*/.test(settings.url))) {
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});
