    $(document).ready(function(){
    updatePieChart();
    $.notify({
         icon: 'ti-github',
         message: "Join the project on Github and contribute to this open source project !"

            },{
                type: 'success',
                timer: 4000
            });

    	});

    	$('#discover').bind('click', function(event){

          callWhois();

        	$.notify({
            	icon: 'ti-world',
            	message: "Discovering devices"

            },{
                type: 'success',
                timer: 1000
            });

    	});

       var intervalID = setInterval(update_values, 1000);
    	function update_values() {
                $SCRIPT_ROOT = {{ request.script_root|tojson|safe }};
                $.getJSON($SCRIPT_ROOT+"/_dash_live_stats",
                    function(data) {
                        $("#mstpnetworks").text(data.print_mstpnetworks)
                        $("#lastwhoisupdate").text(data.timestamp)
                    });
                $.getJSON($SCRIPT_ROOT+"/_dash_live_data",
                    function(data) {
                        $("#devices").text(data.number_of_devices)
                        $("#trends").text(data.number_of_registered_trends)
                    });
            }
            
        function callWhois() {
                $SCRIPT_ROOT = {{ request.script_root|tojson|safe }};
                $.getJSON($SCRIPT_ROOT+"/_whois");
            }
