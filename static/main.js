function pad(n){
    return n<10 ? '0'+n : n
}

function set_date_picker(){
    var d = new Date();
    var strDate = d.getFullYear() + "-" + pad(d.getMonth()+1) + "-" + pad(d.getDate());
    $("#ev_date_from").val(strDate);
    $("#ev_date_to").val(strDate);
    $("#ev_time_from").val('19:00');
    $("#ev_time_to").val('22:00');
}

function set_services_btn(){
    $('#services_all').click(function(){
        $('input[name="ev_services"]').each(function(k, elem){
                $(elem).prop('checked', true);
        });
    });
    $('#services_none').click(function(){
        $('input[name="ev_services"]').each(function(k, elem){
                $(elem).prop('checked', false);
        });
    });
}

$(document).ready(function() {
    set_date_picker();
    set_services_btn();
});
