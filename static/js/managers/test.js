
// init count variable
var count = 0
var total_bill = 0
var list_bill = []

$(document).ready(function () {
    $(document).on("keydown", function (event) {
        if (event.code === "Space") {
            event.preventDefault(); // Ngăn cuộn trang khi nhấn Space
            console.log("Phím Space được nhấn!");

            if (list_bill.length === 0) {
                console.log("Không có bill nào cả")
                pushNotification('Có Lỗi Xảy Ra !!!', 'Không có bill nào cả', 'error')
				$("#bill_input").focus();
            } else {
                var last_bill = list_bill[list_bill.length - 1];
                console.log(last_bill)
                var checkbox = $('[id="ck_' + last_bill + '"]')
                checkbox.prop("checked", !checkbox.prop("checked"));

                var bill_money = $('[id="bill_' + last_bill + '"]').text()

                // fix money add or subtract
                if (checkbox.is(':checked')) {
                    console.log("hello other side")
                    total_bill -= parseInt(bill_money.replace('.', ''))
                    $('#total_bill').val(new Intl.NumberFormat().format(total_bill));
                } else {
                    console.log("hello other side -1")
                    total_bill += parseInt(bill_money.replace('.', ''))
                    $('#total_bill').val(new Intl.NumberFormat().format(total_bill));
                }

            }
        }
    });

    $("#bill_input").focus();

    $('#defaultModalPrimary').on('shown.bs.modal', function () {
        $("#shipper").focus();
    });

});




// function to check bill_code validate first
function check_bill_code(bill_code) {
    if (bill_code === '') {
        pushNotification('Bill Code Error', 'Mã bill trống !!!', 'error')
        return false
    }

    if (!list_bill.includes(bill_code)) {
        return true
    } else {
        pushNotification('Bill Code Exsist', 'Mã bill đã tồn tại !!!', 'error')
        $('#bill_input').val('');
        return false
    }

}


// function to check bill_code correct first
function reset_bill() {
    $("#datatables-basic tbody").empty()
    count = 0
    total_bill = 0
    list_bill = []
    $('#total_bill').val(total_bill)
    pushNotification('Reset new Session', 'Đã reset phiên làm việc mới', 'info')
    $("#bill_input").focus();
}


// function to add new bill to Table
function add_new_bill() {
    // get bill code from input text
    var input_bill = $('#bill_input').val().trim();

    check = check_bill_code(input_bill)

    if (!check) {
        return
    }

    // Call API to kiotviet to get information of this bill_code
    $.ajax({
        url: '/shipper/search-bill/',
        type: 'GET',
        data: {
            'bill': input_bill
        },
        success: function (data_response) {
            // Hiển thị kết quả trả về từ máy chủ
            console.log(data_response)
            // console.log(data_response.error)
            if (data_response.error.length > 0) {
                pushNotification('Có Lỗi Xảy Ra !!!', data_response.error, 'error')
                return
            }

            // Calculate total_bill money:
            total_bill += data_response.bill

            // Fill data to table
            $("#datatables-basic tbody").append(
                '<tr id="' + input_bill + '">' +
                '<td id="' + 'stt_' + input_bill + '">' + ++count + '</td>' +
                '<td>' + input_bill + '</td>' +
                '<td>' + data_response.customer_name + '</td>' +
                '<td>' + data_response.customer_phone + '</td>' +
                '<td>' + data_response.address + '</td>' +
                '<td>' + '<input type="checkbox"  id="' + 'ck_' + input_bill + '" className="form-check-input">' + '</td>' +
                '<td id="' + 'bill_' + input_bill + '">' + new Intl.NumberFormat().format(data_response.bill) + '</td>' +
                '<td class="table-action width-table-action">' +
                '<a href="#"  onclick="delete_one_bill(\'' + input_bill + '\')"><i class="fa-regular fa-trash-can"></i></a>' +
                '</td>' +
                '</tr>'
            )

            // Update total bill
            $('#total_bill').val(new Intl.NumberFormat().format(total_bill));
            // Clear input bill
            $('#bill_input').val('');
            $('#bill_input').focus();

            // Add event on tickbox ck:
            $('[id="ck_' + input_bill + '"]').on('change', function () {
                if (this.checked) {
                    console.log("Checkbox với ID " + this.id + " được tích vào!");
                    total_bill -= data_response.bill
                    $('#total_bill').val(new Intl.NumberFormat().format(total_bill));
                } else {
                    console.log("Checkbox với ID " + this.id + " bị bỏ tích!");
                    total_bill += data_response.bill
                    $('#total_bill').val(new Intl.NumberFormat().format(total_bill));
                }
            });

            pushNotification('Add new bill', 'Thêm bill thành công !', 'success')
            list_bill.push(input_bill)
        },
        error: function (xhr, status, error) {
            console.error('Error:', error);
        }
    });
    // This block should code to complete this feature
}


// function to call add new bill by enter key
$('#bill_input').keypress(function (event) {
    // Kiểm tra nếu phím nhấn là Enter (keyCode 13)
    if (event.which == 13) {
        add_new_bill()
    }
})

// function to delete one row
function delete_one_bill(bill_code) {
    // get money of bill and subtract from total money
    var bill_money = $('[id="bill_' + bill_code + '"]').text()
    total_bill -= parseInt(bill_money.replace('.', ''))
    // Update total bill
    $('#total_bill').val(new Intl.NumberFormat().format(total_bill))

    // remove this row
    $('#' + bill_code).remove()

    // Decrease the counter
    count -= 1

    // get index of element which is going to delete
    index = list_bill.indexOf(bill_code)

    // update STT bigger than item deleted to lower
    for (i = index + 1; i < list_bill.length; i++) {
        $('td[id="stt_' + list_bill[i] + '"]').text(i);
        // console.log(i)
    }

    // actually remove it from array
    list_bill.splice(index, 1)

    pushNotification('Delete Bill', 'Xóa bill thành công !', 'success')
}

// function to sumbit list bill to python server
function confirm_bill() {
    // 1. collect name of shipper:
    var shipper = $("#shipper").val()
    if (shipper === '') {
        pushNotification('Shipper Name Error', 'Vui lòng nhập tên Shipper !!!', 'error')
        return
    }

    if (list_bill.length === 0) {
        pushNotification('Bills Error', 'Chưa nhập danh sách đơn !!!', 'error')
        $("#shipper").val('').blur();
        $("#defaultModalPrimary").modal('hide');
        return
    }


    // collect all array bill_code and send to Django
    // determind that what ck or not
    var result = []
    list_bill.forEach(function(bill) {
//        $('[id="ck_HD020702.01"]').prop('checked')
        var check_ck = $('[id="ck_' + bill + '"]').prop('checked');
        let item = {
            bill_code: bill,
            transfer: check_ck
        }

        result.push(item)
    });

    console.log(JSON.stringify(
            {
                shipper: shipper,
                bills: result
            }
        ))

    // Call api
    $.ajax({
        url: "/shipper/confirm-bill/",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify(
            {
                shipper: shipper,
                bills: result
            }
        ),
        success: function (response) {
            console.log("Success:", response);
        },
        error: function (xhr) {
            console.log("Error:", xhr.responseText);
        }
    });

    // close modal
    $("#shipper").val('').blur();
    $("#defaultModalPrimary").modal('hide');

    // noti success
    pushNotification('Create Successfully', 'Ghi nhận bảng kê thành công !!!', 'success')

    //reset
    reset_bill()
}