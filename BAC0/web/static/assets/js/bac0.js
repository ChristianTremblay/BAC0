type = ['','info','success','warning','danger'];


bac0 = {
    
    initPickColor: function(){
        $('.pick-class-label').click(function(){
            var new_class = $(this).attr('new-class');
            var old_class = $('#display-buttons').attr('data-class');
            var display_div = $('#display-buttons');
            if(display_div.length) {
            var display_buttons = display_div.find('.btn');
            display_buttons.removeClass(old_class);
            display_buttons.addClass(new_class);
            display_div.attr('data-class', new_class);
            }
        });
    },
    
    initChartist: function(){
    
        $SCRIPT_ROOT = {{ request.script_root|tojson|safe }};
        var pie_chart_data = $.getJSON($SCRIPT_ROOT+"/_network_pie_chart");

        var optionsNetworkAndDevices = {
            donut: true,
            donutWidth: 40,
            startAngle: 0,
            total: 100,
            showLabel: false,
            axisX: {
                showGrid: false
            }
        };

        Chartist.Pie('#chartNetworkAndDevices', optionsNetworkAndDevices, {
          labels: pie_chart_data.labels
          series: pie_chart_data.series_pct
        });
    }