let table;
let isStatsLoading = false;
let searchTimeouts = {};

$(document).ready(function () {
    initDataTable();
    initFilters();
    loadStats();
    initSimpleConfirm();

});


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
function getAllFilterData() {
    return {
        entity_filter: $('#entity-filter').val() || '',
        isin_filter: $('#isin-filter').val() || '',
        scheme_filter: $('#scheme-filter').val() || '',
        month_filter: $('#month-filter').val() || '',

        col_0_search: '',  // S.No (not used for filtering)
        col_1_search: $('.column-search[data-column="1"]').val() || '',   // Entity Name
        col_2_search: $('.column-search[data-column="2"]').val() || '',   // Folio No
        col_3_search: $('.column-search[data-column="3"]').val() || '',   // ISIN
        col_4_search: $('.column-search[data-column="4"]').val() || '',   // Scheme Name
        col_5_search: $('.column-search[data-column="5"]').val() || '',   // Cost Value
        col_6_search: $('.column-search[data-column="6"]').val() || '',   // Unit Balance
        col_7_search: $('.column-search[data-column="7"]').val() || '',   // NAV Date
        col_8_search: $('.column-search[data-column="8"]').val() || '',   // Market Value
        col_9_search: $('.column-search[data-column="9"]').val() || '',   // Updated On
        col_10_search: $('.column-search[data-column="10"]').val() || '', // Updated By

        global_search: table ? table.search() : ''
    };
}

function forceUpdateStats() {
    if (isStatsLoading) return;
    isStatsLoading = true;

    const filterData = getAllFilterData();
    console.log('Updating stats with filter data:', filterData);

    $.ajax({
        url: '/camsapp/api/summary-stats/',
        type: 'GET',
        data: filterData,
        cache: false,
        timeout: 15000,
        beforeSend: function () {
            console.log('Stats request started');
        },
        success: function (response) {
            console.log('Stats response:', response);
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
        error: function (xhr, error, textStatus) {
            console.error('Stats Error:', error, textStatus, xhr.responseText);
            showToast('Error updating statistics: ' + (textStatus || error), 'error');
        },
        complete: function () {
            console.log('Stats request completed');
            isStatsLoading = false;
        }
    });
}

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
//             { data: 0, orderable: false },                      // S.No - not orderable
//             { data: 1, orderable: true },                       // Entity Name (swapped)
//             { data: 2, orderable: true },                       // Folio No (swapped)
//             { data: 3, orderable: true },                       // ISIN
//             { data: 4, orderable: true },                       // Scheme Name
//             { data: 5, orderable: true, className: '' }, // Cost Value
//             { data: 6, orderable: true, className: '' }, // Unit Balance
//             { data: 7, orderable: true },                       // NAV Date
//             { data: 8, orderable: true, className: '' }, // Market Value
//             { data: 9, orderable: true },                       // Updated On
//             { data: 10, orderable: true }                       // Updated By
//         ],
//         pageLength: 10,
//         lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
//         order: [[9, 'desc']],
//         language: {
//             processing: '<div class="d-flex justify-content-center align-items-center py-3"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><span class="ms-2">Loading data...</span></div>',
//             paginate: {
//                 previous: '<i class="bi bi-chevron-left"></i>',
//                 next: '<i class="bi bi-chevron-right"></i>'
//             }
//         },
//         columnDefs: [
//                 {
//                     targets: "_all",
//                     createdCell: function (td) {
//                         $(td).css({
//                             "font-weight": "400",
//                             "font-size": "14px",
//                             "font-family": "'Be Vietnam Pro', sans-serif",
//                             "padding": "10px"
//                         });
//                     }
//                 },
//             ],
//         drawCallback: function (settings) {
//             $('#total-records').text((settings._iRecordsTotal || 0).toLocaleString());
//             initISINEdit();
//             console.log('Table drawn, updating stats...');
//             setTimeout(forceUpdateStats, 200);
//         },
//         initComplete: function () {
//             console.log('DataTable initialization complete');
//             // Initialize column search after table is fully ready
//             initColumnSearch();
//         }
//     });
// }

// FIXED: Completely new column search approach using event delegation
function initDataTable() {
    table = $('#portfolio-table1').DataTable({
        scrollY: "500px",
        scrollCollapse: true,
        paging: true,
        ordering: true,
        searching: true,
        autoWidth: false,
        fixedHeader: true,
        scrollX: true,
        autoWidth: false,
        responsive: false,
        deferRender: true,

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
            { data: 0, orderable: false },
            { data: 1, orderable: true },
            { data: 2, orderable: true },
            { data: 3, orderable: true },
            { data: 4, orderable: true },
            { data: 5, orderable: true },
            { data: 6, orderable: true },
            { data: 7, orderable: true },
            { data: 8, orderable: true },
            { data: 9, orderable: true },
            { data: 10, orderable: true }
        ],
        pageLength: 10,
        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
        order: [[9, 'desc']],

        // 👇 Only one page number between prev and next
        pagingType: "simple_numbers",

        language: {
            processing: `
                <div class="d-flex justify-content-center align-items-center py-3">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <span class="ms-2">Loading data...</span>
                </div>`
        },

        columnDefs: [
            {
                targets: "_all",
                createdCell: function (td) {
                    $(td).css({
                        "font-weight": "400",
                        "font-size": "14px",
                        "font-family": "'Be Vietnam Pro', sans-serif",
                        "padding": "10px",
                        "border": "none" 

                    });
                }
            },
        ],

        drawCallback: function (settings) {
            $('#total-records').text((settings._iRecordsTotal || 0).toLocaleString());
            initISINEdit();
            console.log('Table drawn, updating stats...');
            setTimeout(forceUpdateStats, 200);
        },

        initComplete: function () {
            console.log('DataTable initialization complete');
            initColumnSearch();
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
//             { data: 0, orderable: false },   // Sr No
//             { data: 1, orderable: true },
//             { data: 2, orderable: true },
//             { data: 3, orderable: true },    // Date column → render later in columnDefs
//             { data: 4, orderable: true },    // Amount column
//             { data: 5, orderable: true },    // Amount column
//             { data: 6, orderable: true },    // Amount column
//             { data: 7, orderable: true },    // Amount column
//             { data: 8, orderable: true },    // Amount column
//             { data: 9, orderable: true },    // Amount column
//             { data: 10, orderable: true }    // Amount column
//         ],

//         pageLength: 10,
//         lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
//         order: [[9, 'desc']],  // sort by column 9
//         pagingType: "simple_numbers",

//         language: {
//             processing: `
//                 <div class="d-flex justify-content-center align-items-center py-3">
//                     <div class="spinner-border text-primary" role="status">
//                         <span class="visually-hidden">Loading...</span>
//                     </div>
//                     <span class="ms-2">Loading data...</span>
//                 </div>`
//         },

//         columnDefs: [
//             // Apply styles to all cells
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

//             // Format date column (index 3)
//             {
//                 targets: 3,
//                 render: function (data) {
//                     if (!data) return "";
//                     const d = new Date(data);
//                     return d.toLocaleDateString("en-GB"); // dd-mm-yyyy
//                 }
//             },

//             // Format amount columns (indexes 4 → 10)
//             {
//                 targets: [5, 6, 8, 9],
//                 render: function (data) {
//                     if (data === null || data === undefined || data === "") return "0.00";
//                     return parseFloat(data)
//                         .toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
//                 }
//             }
//         ],

//         drawCallback: function (settings) {
//             $('#total-records').text((settings._iRecordsTotal || 0).toLocaleString());
//             initISINEdit();
//             console.log('Table drawn, updating stats...');
//             setTimeout(forceUpdateStats, 200);
//         },

//         initComplete: function () {
//             console.log('DataTable initialization complete');
//             initColumnSearch();
//         }
//     });
// }




function initColumnSearch() {
    console.log('Initializing column search...');

    // Use event delegation to handle dynamically created elements
    $(document).off('input.columnSearch keyup.columnSearch change.columnSearch paste.columnSearch');
    $(document).on('input.columnSearch keyup.columnSearch change.columnSearch paste.columnSearch', '.column-search', function (e) {
        const $input = $(this);
        const column = $input.data('column');
        const value = $input.val().trim();

        console.log('Column search triggered - Column:', column, 'Value:', value, 'Event:', e.type);

        // Clear existing timeout for this column
        clearTimeout(searchTimeouts['col_' + column]);

        // Set new timeout
        searchTimeouts['col_' + column] = setTimeout(function () {
            console.log('Executing column search for column:', column);

            if (table) {
                // Reload table with new search data
                table.ajax.reload(function () {
                    console.log('Column search complete - updating stats...');
                    forceUpdateStats();
                }, false); // Don't reset paging
            }
        }, 400); // 400ms debounce
    });

    console.log('Column search event delegation set up');
    console.log('Found column search inputs:', $('.column-search').length);
}

function initFilters() {
    // Apply filters button
    $('#apply-filter').click(function () {
        console.log('Apply filters clicked');
        if (table) {
            table.ajax.reload(function () {
                console.log('Apply filters - Table reloaded, updating stats...');
                forceUpdateStats();
            });
        }
        showToast('Filters applied', 'success');
    });

    // Reset filters button
    $('#reset-filter').click(function () {
        console.log('Reset filters clicked');
        $('#entity-filter, #isin-filter, #scheme-filter').val('');
        $('#month-filter').val('');
        $('.column-search').val(''); // Clear all column search inputs

        if (table) {
            table.search('').columns().search('');
            table.ajax.reload(function () {
                console.log('Reset filters - Table reloaded, updating stats...');
                forceUpdateStats();
            });
        }
        showToast('Filters reset', 'info');
    });

    // Global search - use event delegation for DataTable's search input
    $(document).off('input.globalSearch keyup.globalSearch');
    $(document).on('input.globalSearch keyup.globalSearch', '#portfolio-table_filter input', function () {
        const value = $(this).val();
        console.log('Global search triggered, value:', value);

        clearTimeout(searchTimeouts['global']);
        searchTimeouts['global'] = setTimeout(() => {
            console.log('Executing global search stats update');
            forceUpdateStats();
        }, 400);
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
//             title: 'ISIN must be 8 to 20 characters',
//             'data-bs-toggle': 'tooltip'
//         });

//         $this.html('').append($input);
//         $input.focus().select();

//         let tooltip;
//         if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
//             tooltip = new bootstrap.Tooltip($input[0]);
//         }

//         $input.on('blur keypress', function (e) {
//             if (e.type === 'keypress' && e.which !== 13) return;
//             const newValue = $(this).val().trim().toUpperCase();

//             if (tooltip) {
//                 tooltip.dispose();
//             }

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

// function initISINEdit() {
//     $('.editable-isin').off('click').on('click', function () {
//         const $this = $(this);
//         if ($this.find('input').length) return; // Prevent multiple inputs
//         const currentValue = $this.data('value');
//         const id = $this.data('id');
//         const originalHtml = $this.html();

//         const $input = $('<input>', {
//             type: 'text',
//             value: currentValue,
//             class: 'form-control form-control-sm editing',
//             maxlength: 20,
//             title: 'ISIN must be 8 to 20 characters only'
//         });

//         $this.html('').append($input);
//         $input.focus().select();

//         $input.on('blur keypress', function (e) {
//             if (e.type === 'keypress' && e.which !== 13) return;
//             const newValue = $(this).val().trim().toUpperCase();

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
// function initISINEdit() {
//     $('.editable-isin').off('click').on('click', function () {
//         const $this = $(this);
//         if ($this.find('input').length) return; // Prevent multiple inputs

//         const currentValue = $this.data('value') || '';
//         const id = $this.data('id');
//         const originalHtml = $this.html();

//         // Free text input
//         const $input = $('<input>', {
//             type: 'text',
//             value: currentValue,
//             class: ' editing',
//             title: 'Enter any value'
//         });

//         $this.html('').append($input);
//         $input.focus().select();

//         function commitChange() {
//             const newValue = $input.val(); // ✅ accept anything

//             // Restore original if nothing changed
//             if (newValue === currentValue) {
//                 $this.html(originalHtml);
//                 return;
//             }

//             updateISIN(id, newValue, $this, originalHtml);
//         }

//         // Commit on blur
//         $input.on('blur', commitChange);

//         // Commit on Enter
//         $input.on('keydown', function (e) {
//             if (e.key === 'Enter') {
//                 commitChange();
//             }
//         });
//     });
// }


function initISINEdit() {
    // Remove any previous handlers
    $('.editable-isin').off('click');

    $('.editable-isin').on('click', function () {
        const $cell = $(this);

        // Prevent multiple inputs
        if ($cell.find('input').length) return;

        const id = $cell.data('id');
        const currentValue = $cell.data('value') || '';
        const originalHtml = $cell.html();

        // Create free-text input
        const $input = $('<input>', {
            type: 'text',
            value: currentValue,
            class: 'form-control form-control-sm editing',
            title: 'Enter any value',
            autocomplete: 'off'
        });

        $cell.html($input);
        $input.focus().select();

        const commit = () => {
            const newValue = $input.val(); // ✅ accept ANY value
            if (newValue === currentValue) {
                $cell.html(originalHtml);
                return;
            }
            updateISIN(id, newValue, $cell, originalHtml);
        };

        // Commit on blur or Enter
        $input.on('blur', commit);
        $input.on('keydown', function (e) {
            if (e.key === 'Enter') commit();
            if (e.key === 'Escape') $cell.html(originalHtml); // cancel edit
        });
    });
}
function initISINEdit() {
    $('.editable-isin').off('click'); // Remove previous handlers

    $('.editable-isin').on('click', function () {
        const $cell = $(this);
        if ($cell.find('input').length) return;

        const id = $cell.data('id');
        const currentValue = $cell.data('value') || '';
        const originalHtml = $cell.html();

        const $input = $('<input>', {
            type: 'text',
            value: currentValue,
            class: 'form-control form-control-sm editing',
            title: 'Enter any value',
            autocomplete: 'off'
        });

        $cell.html($input);
        $input.focus().select();

        const commit = () => {
            const newValue = $input.val(); // Accept any value

            // Restore original if unchanged
            if (newValue === currentValue) {
                $cell.html(originalHtml);
                return;
            }

            // Directly update value via AJAX
            $.ajax({
                url: '/camsapp/api/update-isin/',
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
                data: JSON.stringify({ id: id, isin: newValue }),
                contentType: 'application/json',
                success: function (res) {
                    if (res.success) {
                        $cell.html(newValue).data('value', newValue);
                        showToast('ISIN updated successfully', 'success');
                        if (table) table.ajax.reload(null, false);
                    } else {
                        showToast(res.error || 'Update failed', 'error');
                        $cell.html(originalHtml);
                    }
                },
                error: function () {
                    showToast('Error updating ISIN', 'error');
                    $cell.html(originalHtml);
                }
            });
        };

        $input.on('blur', commit);
        $input.on('keydown', function (e) {
            if (e.key === 'Enter') commit();
            if (e.key === 'Escape') $cell.html(originalHtml); // Cancel edit
        });
    });
}







// function updateISIN(id, newValue, $element, originalHtml) {
//     $.ajax({
//         url: '/camsapp/api/update-isin/',
//         method: 'POST',
//         headers: { 'X-CSRFToken': getCookie('csrftoken') },
//         data: JSON.stringify({ id: id, isin: newValue }),
//         contentType: 'application/json',
//         success: function (response) {
//             if (response.success) {
//                 $element.html(newValue).data('value', newValue);
//                 showToast('ISIN updated successfully', 'success');
//                 table.ajax.reload(null, false);
//             } else {
//                 showToast(response.error || 'Update failed', 'error');
//                 $element.html(originalHtml);
//             }
//         },
//         error: function () {
//             showToast('Error updating ISIN', 'error');
//             $element.html(originalHtml);
//         }
//     });
// }
function updateISIN(id, newValue, $element, originalHtml) {
    simpleConfirm(`Update ISIN to "${newValue}"?`, function (confirmed) {
        if (!confirmed) {
            // If user cancels, restore original content
            $element.html(originalHtml);
            return;
        }

        // If confirmed, proceed with the AJAX update
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
    });
}

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
    const filterData = getAllFilterData(); // Collect all filter/search parameters
    const params = new URLSearchParams();

    // Append only non-empty filters
    Object.keys(filterData).forEach(key => {
        if (filterData[key]) params.append(key, filterData[key]);
    });

    // Keep the same URL for download
    const downloadUrl = '/camsapp/download/summary/?' + params.toString();

    // Show toast before download
    showToast('Preparing Excel download...', 'info');

    // Trigger download in a new tab
    window.open(downloadUrl, '_blank');

    // Show success toast after a short delay
    setTimeout(() => showToast('Excel summary download started', 'success'), 1000);
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

