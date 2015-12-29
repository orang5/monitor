function interactive_chart(pltg, devtg, rttg, tag) {
    /*
     * Flot Interactive Chart
     * -----------------------
     */
    // Data would be fetched from a server
    
		var interactive_plot = $.plot(pltg, [], {
					grid: {
						borderColor: "#f3f3f3",
						borderWidth: 1,
						tickColor: "#f3f3f3"
					},
					series: {
						shadowSize: 0, // Drawing is faster without shadows
						//color: "#3c8dbc"
						
					},
					
					lines: {
						fill: true//Converts the line chart to area chart
						//color:{colors:["#90EE90","#FF0000","#3c8dbc","#3b8bba"]}
					},
					
					
					yaxis: {
						min: 0,
						//max: 100,
						show: true
					},
					xaxis: {
						min: 0,
						max: 60
					},
										
		});

    var uuid = window.location.search;
    var totalPoints = 60;
    var Interval = 2000; //Fetch data ever x milliseconds
    var realtime = "on"; //If == to on then fetch data every x seconds. else stop fetching
    var points = [];
    var mask = [];
    var lable=[];
    for(var i=0; i<10; i++) {
        points[i] = new Array();
        mask[i] = 1;
    }
    /*
    function getDevid(devid){
        for(var i in devid){
            var li = "<li data-toggle=" + devid[i] + "> <a>" +  devid[i] + "</a></li>";
            $(devtg + " ul:last").append(li);
            //$(devtg + " ul:last li").html("<li data-toggle=" + devid[i] + "> <a>" +  devid[i] + "</a></li>");
        }
    }
    _ajax('GET', '/getDeviceId/'+uuid, {Tag:tag}, getDevid);
    */
    var deviceId = $(devtg).data("toggle");

    function refresh(id){
        deviceId = id;
        for(var i=0; i<10; i++){
            for(var j=0; j < totalPoints; j++){
                points[i][j] = -1;
            }
        }
    
    }

	  function fetch() {
			 function update(point) {
			   var sct = "[name=" + tag + "]";
			   $(sct).each(function(i,element){
					   if(element.checked) mask[i]=1;
					   else mask[i]=0;
					   lable[i]=$(element).attr("id");//new
			   });	
			        
			   for(var i=0; i<point.length; i++){
			       while(points[i].unshift(-1) < totalPoints);
			   }

			   for(var i=0; i<point.length; i++)
			       points[i].push(point[i]);
			   
			   for(var i=0; i<point.length; i++){
			       while(points[i].length > totalPoints) points[i].shift();
			   }			   
			   
			   var value = [];
			   
			   for(var i=0; i<point.length; i++){
			       value[i] = new Array();
			       var temp = -1;
			       for(var j=0; j<totalPoints; j++){
			           if(mask[i] == 1) temp = points[i][j];
			           value[i].push([j,temp]);
			       }
			   }
			   //new
			   //add the label
			   var data=[];
			   //var colors=["#FF0000","#3c8dbc","#3b8bba","#90EE90"];//ÑÕÉ«²»·û£¿£¿
			   for(var i=0;i<point.length;i++){
            data[i]={};
            data[i].label=lable[i];
            data[i].data=value[i];
           // data[i].lines={};
           // data[i].lines.color=colors[i];
            }
         interactive_plot.setData(data);
				 interactive_plot.draw();
				 interactive_plot.setupGrid();
			 }
			 _ajax('GET', '/VirtualMachineUpdate/'+uuid, {DeviceId:deviceId,tag:tag}, update);
			 if (realtime=="on")
			     setTimeout(fetch, Interval);
	 }

    //INITIALIZE REALTIME DATA FETCHING
    if (realtime === "on") {
      fetch();
    }
    /*
    $("[name=tag]").click(function(){
			$("[name=tag]").each(function(i,element){
					if(element.checked) mask[i]=1;
					else mask[i]=0;
			});
    });
    */
    $(devtg).click(function(){
		    if(deviceId != $(this).data("toggle")){
		        refresh($(this).data("toggle"));
		    }
    });    
        
        
    //REALTIME TOGGLE
		$(rttg).click(function () {
			 if ($(this).data("toggle") === "on") {
				 if (realtime === "off"){
						realtime = "on";
						fetch();
				 }
			 }
			 else { 
				 realtime = "off";
			 }  
		 });
}