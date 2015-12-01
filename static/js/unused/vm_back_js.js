 "use strict";

var value=[];
for(var i=0; i<60; i++) value[i] = -1;
  
var cpu_plot = $.plot("#cpu-chart", [], {
  grid: {
    borderColor: "#f3f3f3",
    borderWidth: 1,
    tickColor: "#f3f3f3"
  },
  series: {
    shadowSize: 0, // Drawing is faster without shadows
    color: "#3c8dbc"
  },
  lines: {
    fill: true, //Converts the line chart to area chart
    color: "#3c8dbc"
  },
  yaxis: {
    min: 0,
    max: 100,
    show: true
  },
  xaxis: {
    min: 0,
    max: 60
  }
});

var mem_plot = $.plot("#mem-chart", [], {
  grid: {
      hoverable: true,
      borderColor: "#f3f3f3",
      borderWidth: 1,
      tickColor: "#f3f3f3"
  },
  series: {
    shadowSize: 0,
    lines: {
      show: true
    },
    points: {
      show: true
    }
  },
  lines: {
    fill: true, //Converts the line chart to area chart
    color: "#3c8dbc"
  },
  yaxis: {
    min: 0,
    max: 100,
    show: true
  },
  xaxis: {
    min: 0,
    max: 60,
  }
});

function vessel(interval, caption, plot){

   this.interval = interval;
   this.realtime = 'on';
   this.caption = caption;
   this.total = 60;
   this.plot = plot;
   this.queue = value;
   this.point = [];
}

function filter_cpu(data){
    var l = cpu.queue.push(data.LoadPercentage);
    if(l > 60) l = cpu.queue.shift();
    cpu.point=[];
    for(var i=0; i<60; i++)
      cpu.point.push([i,cpu.queue[i]]);
}

function filter_mem(data){
    var l = mem.queue.push(data.Capacity);
    if(l > 60) l = mem.queue.shift();
    mem.point=[];
    for(var i=0; i<60; i++)
      mem.point.push([i,mem.queue[i]]);
}

function update(v) {
  if (v.caption == 'cpu')
    _ajax('GET', '/VirtualMachineUpdate/', {type:'cpu'}, filter_cpu);
  if (v.caption == 'mem')
    _ajax('GET', '/VirtualMachineUpdate/', {type:'mem'}, filter_mem);
    
  alert(v.caption+v.point)
  v.plot.setData([v.point]);
  v.plot.draw();
  if (v.realtime === "on") setTimeout(update, v.interval, v);
} 
 
var cpu = new vessel(500, 'cpu', cpu_plot);
var mem = new vessel(2000, 'mem', mem_plot);
 
$(function(){
  //mem = new vessel(2000, 'mem', 60, mem_plot);
  //INITIALIZE REALTIME DATA FETCHING
  if (cpu.realtime === "on") update(cpu);
  if (mem.realtime === "on") update(mem);
  //if (net.realtime === "on") update(net);
  
 //REALTIME TOGGLE
 $("#cpu_realtime .btn").click(function () {
   if ($(this).data("toggle") === "on") {
     cpu.realtime = "on";
   }
   else {
     cpu.realtime = "off";
   }
    update(cpu);
 });
 
  $("#mem_realtime .btn").click(function () {
   if ($(this).data("toggle") === "on") {
     mem.realtime = "on";
   }
   else {
     mem.realtime = "off";
   }
    update(mem);
 });
 
  $("#net_realtime .btn").click(function () {
   if ($(this).data("toggle") === "on") {
     net.realtime = "on";
   }
   else {
     net.realtime = "off";
   }
    update(net);
 });

});
