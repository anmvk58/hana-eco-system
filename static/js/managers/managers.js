$(function() {
    // Daterangepicker
    $("input[name=\"daterange\"]").daterangepicker({
        opens: "left"
    });

    // Reject api
    $("#btn-reject-request").click(function(){
        var input_request_id = $('#request_id').val();
        var input_reason = $('#reason').val();
        var bill_code = $('#bill_code').val();

        $.ajax({
            url: 'http://localhost:8000/managers/reject-request',
            type: 'POST',
            data: JSON.stringify({
                request_id: input_request_id,
                reason: input_reason
            }),
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + getCookie('access_token')
            },
            success: function(response, status, xhr) {
                if (xhr.status === 200) {
                    $('#defaultModalPrimary').modal('hide');
                    rebuildTableRequest()
                    pushNotification('Success', 'Đã từ chối thành công yêu cầu ' + bill_code, 'success')
                }
            },
            error: function(xhr, status, error) {
                console.error("Lỗi khi gọi API:", error);
            }
        });

    })

    // Accept api
    $("#btn-accept-request").click(function(){
        var input_request_id = $('#request_id').val();
        var input_reason = $('#reason').val();
        var bill_code = $('#bill_code').val();

        $.ajax({
            url: 'http://localhost:8000/managers/accept-request',
            type: 'POST',
            data: JSON.stringify({
                request_id: input_request_id,
                reason: input_reason
            }),
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + getCookie('access_token')
            },
            success: function(response, status, xhr) {
                if (xhr.status === 200) {
                    $('#defaultModalPrimary').modal('hide');
                    rebuildTableRequest()
                    pushNotification('Success', 'Đã phê duyệt thành công yêu cầu ' + bill_code, 'success')
                }
            },
            error: function(xhr, status, error) {
                console.error("Lỗi khi gọi API:", error);
            }
        });

    })


    // Search danh sách:
    $("#btn-search-request").click(function(){
        rebuildTableRequest()
    })
});

// Rebuild Table
function rebuildTableRequest(){
    var input_status = $('#input_status').val();
    var input_date = $('#input_date').val();
    var input_from_date = convertDateString(input_date)[0]
    var input_to_date = convertDateString(input_date)[1]

    // call api to get List
    $.ajax({
        url: 'http://localhost:8000/managers/list-all-request',
        type: 'GET',
        data: {
            from_date: input_from_date,
            to_date: input_to_date,
            request_status: input_status
        },
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + getCookie('access_token')
        },
        success: function(response) {
            console.log("Dữ liệu từ API:", response);
            // Xử lý dữ liệu nhận được ở đây
            $("#table-data").empty()
            // Fill data to table
            response.forEach(request => {
               $("#table-data").append(
                '<tr>' +
                    '<td>' + request.request_id + '</td>' +
                    '<td>' + request.bill_code + '</td>' +
                    '<td>' + request.type + '</td>' +
                    '<td>' + request.content + '</td>' +
                    '<td>' + request.status + '</td>' +
                    '<td>' + request.approver + '</td>' +
                    '<td>' + request.reason + '</td>' +
                    '<td>' + request.create_at.replace('T', ' ') + '</td>' +
                    '<td>' + request.approved_at.replace('T', ' ') + '</td>' +
                    '<td>' +
                        '<a href="#"  onclick="get_detail_request(' + request.request_id + ', \'' + request.bill_code + '\', \'' + request.type + '\', \'' + request.content + '\', \'' + request.status + '\')"' +
                        'data-toggle="modal" data-target="#defaultModalPrimary"><i class="far fa-fw fa-eye"></i></a>' +
                    '</td>' +
                '</tr>'
            )
            });
        },
        error: function(xhr, status, error) {
            console.error("Lỗi khi gọi API:", error);
        }
    });
}


// Convert daterange to fromDate and toDate
function convertDateString(dateStr) {
    var dates = dateStr.split(' - ');

    function formatDate(date) {
        var [month, day, year] = date.split('/');
        return Number(year)*10000 + Number(month)*100 + Number(day);
    }

    return dates.map(formatDate)
}

// Helper function to get a cookie by name
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

function get_detail_request(request_id, bill_code, type, content, status){
        // Gán giá trị cho Modal
        $('#request_id').val(request_id);
        $('#bill_code').val(bill_code);
        $('#request_type').val(type);
        $('#content').val(content);

        // Kiểm tra trạng thái của request để disable/ enable nút
        if (status != 'CREATE') {
            $('#btn-reject-request').prop('disabled', true);
            $('#btn-accept-request').prop('disabled', true);
        } else {
            $('#btn-reject-request').prop('disabled', false);
            $('#btn-accept-request').prop('disabled', false);
        }
}

function pushNotification(title, message, type) {
    toastr[type](message, title, {
        positionClass: "toast-bottom-right",
        closeButton: true,
        progressBar: true,
        newestOnTop: true,
        rtl: false,
        timeOut:1500
    });
}