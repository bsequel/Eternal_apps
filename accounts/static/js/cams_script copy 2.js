let table;
let isStatsLoading = false;

$(document).ready(function () {
    initDataTable();
    initFilters();
    loadStats();
});

// function getAllFilterData() {
//     return {
//         entity_filter: $('#entity-filter').val() || '',
//         isin_filter: $('#isin-filter').val() || '',
//         scheme_filter: $('#scheme-filter').val() || '',
//         month_filter: $('#month-filter').val() || '',

//         col_0_search: $('.column-search[data-column="0"]').val() || '',
//         col_1_search: $('.column-search[data-column="1"]').val() || '',
//         col_2_search: $('.column-search[data-column="2"]').val() || '',
//         col_3_search: $('.column-search[data-column="3"]').val() || '',
//         col_4_search: $('.column-search[data-column="4"]').val() || '',
//         col_5_search: $('.column-search[data-column="5"]').val() || '',
//         col_6_search: $('.column-search[data-column="6"]').val() || '',
//         col_7_search: $('.column-search[data-column="7"]').val() || '',
//         col_8_search: $('.column-search[data-column="8"]').val() || '',
//         col_9_search: $('.column-search[data-column="9"]').val() || '',

//         global_search: table ? table.search() : ''
//     };
// }

function getAllFilterData() {
    return {
        entity_filter: $('#entity-filter').val() || '',
        isin_filter: $('#isin-filter').val() || '',
        scheme_filter: $('#scheme-filter').val() || '',
        month_filter: $('#month-filter').val() || '',

        // Note: these data-column attributes must match the table column indexes (0..10)
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
        col_10_search: $('.column-search[data-column="10"]').val() || '',

        // global search (DataTables sends search[value] automatically, but include this anyway)
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



function initDataTable() {
    table = $('#portfolio-table').DataTable({
        scrollY: "500px",
        scrollCollapse: true,
        paging: true,
        ordering: true,
        searching: true,
        autoWidth: false,
        fixedHeader: true,
        processing: true,
        serverSide: true,
        ajax: {
            url: '/camsapp/api/portfolio-data/',
            type: 'GET',
            data: function (d) {
                // merge our custom filter params
                Object.assign(d, getAllFilterData());
                return d;
            },
            error: function (xhr, error) {
                console.error('Table AJAX Error:', error);
                showToast('Error loading table data', 'error');
            }
        },
        columns: [
            { data: 0, orderable: true },  // S.No from backend
            { data: 1, orderable: true },  // Entity
            { data: 2, orderable: true },  // Folio
            { data: 3, orderable: true },  // ISIN
            { data: 4, orderable: true },  // Scheme
            { data: 5, orderable: true },  // Cost
            { data: 6, orderable: true },  // Unit Balance
            { data: 7, orderable: true },  // NAV Date
            { data: 8, orderable: true },  // Market Value (with profit/loss class)
            { data: 9, orderable: true },  // Updated At
            { data: 10, orderable: true }  // Updated By
        ],
        pageLength: 10,
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
        ],
        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
        order: [[9, 'desc']], // updated_at desc (index 9)
        language: {
            processing: '<div class="spinner-border text-primary"></div>',
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



// function initDataTable() {
//     table = $('#portfolio-table').DataTable({
//         scrollY: "500px",
//         scrollCollapse: true,
//         paging: true,
//         ordering: true,
//         searching: true,
//         autoWidth: false,
//         fixedHeader: true,
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
//             {   // Serial number column (client side only)
//                 data: null,
//                 orderable: false,
//                 render: function (data, type, row, meta) {
//                     return meta.row + meta.settings._iDisplayStart + 1;
//                 }
//             },
//             { data: 0, orderable: true },  // Entity Name
//             { data: 1, orderable: true },  // Folio No
//             { data: 2, orderable: true },  // ISIN
//             { data: 3, orderable: true },  // Scheme Name
//             { data: 4, orderable: true },  // Cost Value
//             { data: 5, orderable: true },  // Unit Balance
//             { data: 6, orderable: true },  // NAV Date
//             { data: 7, orderable: true },  // Market Value
//             { data: 8, orderable: true },  // Updated At
//             { data: 9, orderable: true }   // Updated By
//         ],
//         pageLength: 10,
//         columnDefs: [
//             {
//                 targets: "_all",
//                 createdCell: function (td) {
//                     $(td).css({
//                         "font-weight": "400",
//                         "font-size": "14px",
//                         "font-family": "'Be Vietnam Pro', sans-serif",
//                         "padding": "10px"
//                     });
//                 }
//             },
            
//         ],
//         lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
//         order: [[9, 'desc']], // Updated At desc (column index shifted)
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


// function initDataTable() {
//     table = $('#portfolio-table').DataTable({
//         scrollY: "500px",        // height of the body
//         scrollCollapse: true,    // collapse when fewer rows
//         paging: true,            // keep pagination
//         ordering: true,
//         searching: true,
//         autoWidth: false,
//         fixedHeader: true,

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
//             { data: 4, orderable: true, className: '' },
//             { data: 5, orderable: true, className: '' },
//             { data: 6, orderable: true },
//             { data: 7, orderable: true, className: '' },
//             { data: 8, orderable: true },
//             { data: 9, orderable: true }
//         ],
//         pageLength: 10,
//         columnDefs: [
//             {
//                 targets: "_all",
//                 createdCell: function (td) {
//                     $(td).css({
//                         "font-weight": "400",
//                         "font-size": "14px",
//                         "font-family": "'Be Vietnam Pro', sans-serif",
//                         "padding": "10px"
//                     });
//                 }
//             },
//         ],
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
// function initDataTable() {
//     table = $('#portfolio-table').DataTable({
//         scrollY: "500px",
//         scrollCollapse: true,
//         paging: true,
//         ordering: true,
//         searching: true,
//         autoWidth: false,
//         fixedHeader: true,
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
//             {   // Serial number column
//                 data: null,
//                 orderable: false,
//                 render: function (data, type, row, meta) {
//                     return meta.row + meta.settings._iDisplayStart + 1;
//                 }
//             },
//             { data: 1, orderable: true },  // previously 2nd column
//             { data: 0, orderable: true },  // previously 1st column
//             { data: 2, orderable: true },
//             { data: 3, orderable: true },
//             { data: 4, orderable: true, className: '' },
//             { data: 5, orderable: true, className: '' },
//             { data: 6, orderable: true },
//             { data: 7, orderable: true, className: '' },
//             { data: 8, orderable: true },
//             { data: 9, orderable: true }
//         ],
//         pageLength: 10,
//         columnDefs: [
//             {
//                 targets: "_all",
//                 createdCell: function (td) {
//                     $(td).css({
//                         "font-weight": "400",
//                         "font-size": "14px",
//                         "font-family": "'Be Vietnam Pro', sans-serif",
//                         "padding": "10px"
//                     });
//                 }
//             },
//         ],
//         lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
//         order: [[9, 'desc']], // shifted since we added serial column
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

function initISINEdit() {
    $('.editable-isin').off('click').on('click', function () {
        const $this = $(this);
        if ($this.find('input').length) return; // Prevent multiple inputs
        const currentValue = $this.data('value');
        const id = $this.data('id');
        const originalHtml = $this.html();

        const $input = $('<input>', {
            type: 'text',
            value: currentValue,
            class: 'form-control form-control-sm editing',
            maxlength: 12
        });

        $this.html('').append($input);
        $input.focus().select();

        $input.on('blur keypress', function (e) {
            if (e.type === 'keypress' && e.which !== 13) return;
            const newValue = $(this).val().trim().toUpperCase();

            if (newValue === currentValue) {
                $this.html(originalHtml);
                return;
            }
            if (newValue.length !== 12) {
                showToast('ISIN must be 12 characters', 'error');
                $this.html(originalHtml);
                return;
            }
            updateISIN(id, newValue, $this, originalHtml);
        });
    });
}

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

// function downloadSummary() {
//     const filterData = getAllFilterData();
//     const params = new URLSearchParams();
//     Object.keys(filterData).forEach(key => {
//         if (filterData[key]) params.append(key, filterData[key]);
//     });
//     const downloadUrl = '/camsapp/download/summary/?' + params.toString();
//     showToast('Preparing download...', 'info');
//     window.open(downloadUrl, '_blank');
//     setTimeout(() => showToast('Summary download started', 'success'), 1000);
// }
// function downloadSummary() {
//     const filterData = getAllFilterData();
//     const params = new URLSearchParams();

//     // Append all non-empty filters
//     Object.keys(filterData).forEach(key => {
//         if (filterData[key]) params.append(key, filterData[key]);
//     });

//     const downloadUrl = '/camsapp/download/summary/?' + params.toString();

//     // Show user feedback
//     showToast('Preparing Excel download...', 'info');

//     // Trigger download by creating a temporary link
//     const link = document.createElement('a');
//     link.href = downloadUrl;
//     link.download = 'cams_summary_filtered.csv'; // Optional: suggest filename
//     document.body.appendChild(link);
//     link.click();
//     document.body.removeChild(link);

//     setTimeout(() => showToast('Excel download started', 'success'), 1000);
// }


function downloadSummary() {
    const filterData = getAllFilterData();
    const params = new URLSearchParams();

    Object.keys(filterData).forEach(key => {
        if (filterData[key]) params.append(key, filterData[key]);

    });
    // Specify type=xlsx
    params.append('type', 'xlsx');

    const downloadUrl = '/camsapp/download/summary/?' + params.toString();

    // Trigger download
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = 'cams_summary_filtered.xlsx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast('Excel download started', 'success');
}

function downloadDetail(month, year) {
    const filterData = getAllFilterData();
    const params = new URLSearchParams();
    params.append('month', month);
    params.append('year', year);
    params.append('type', 'xlsx');

    ['entity_filter', 'isin_filter', 'scheme_filter'].forEach(key => {
        if (filterData[key]) params.append(key, filterData[key]);
    });

    const downloadUrl = '/camsapp/download/detail/?' + params.toString();

    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `cams_detail_${year}_${month}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast(`Excel download for ${getMonthName(month)} ${year} started`, 'success');
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
