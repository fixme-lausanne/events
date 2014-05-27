function set_date_picker(){
    var dt_format = 'yy-mm-dd'; // FIXME: add timepicker !
    c_date_from = $.datepicker.formatDate(dt_format, new Date($.now()-86400000*1));
    c_date_to = $.datepicker.formatDate(dt_format, new Date($.now()));
    $('#ev_from').datepicker({
        autoSize: true,
        dateFormat: dt_format,
        onSelect: function(dateText){
            c_date_from = dateText;
            get_data();
        },
    });
    $('#ev_to').datepicker({
        autoSize: true,
        dateFormat: dt_format,
        onSelect: function(dateText){
            c_date_to = dateText;
            get_data();
        },
    });
    $("#ev_from").val(c_date_from);
    $("#ev_to").val(c_date_to);
}

set_date_picker();
