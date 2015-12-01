 "use strict";
var ChartDatasets = [
    {
      lines: {
        fill: true,
        color: "#3c8dbc"
      },
    },
    
    {
      lines: {
        color: "#3b8bba"
        
      },
    }
  ]

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

var net_plot = $.plot("#net-chart", [], {
  grid: {
      hoverable: true,
      borderColor: "#f3f3f3",
      borderWidth: 1,
      tickColor: "#f3f3f3"
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

var disk_plot = $.plot("#disk-chart", [], {
  grid: {
      hoverable: true,
      borderColor: "#f3f3f3",
      borderWidth: 1,
      tickColor: "#f3f3f3"
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
  
function vessel(interval, caption, plot){

   this.interval = interval;
    
   this.realtime = 'on';
   this.caption = caption;
   this.total = 60;
   this.plot = plot;
   this.queue0 = [];
   this.queue1 = [];
   this.point = [];
   
   this.double_line = (caption==='net'||caption==='disk');
   if(this.double_line) this.point = ChartDatasets;
   
   if(caption == 'net')
      {
        this.point[0].label = "Upload";
        this.point[1].label = "DownLoad";
      }
      
   if(caption == 'disk')
      {
        this.point[0].label = "Read";
        this.point[1].label = "Write";
      }   
      
   
   for(var i=0; i<60; i++) {
      this.queue0[i] = -1;
      this.queue1[i] = -1;
   }

   
   var self = this;

   this.fetch = function(res){

      if (self.caption == 'cpu')
        var l = self.queue0.push(res.LoadPercentage);
 
      if (self.caption == 'mem')
        var l = self.queue0.push(res.Capacity);

      if (self.caption == 'net')
      {        
        self.queue0.push(res.UpLoad);
        var l = self.queue1.push(res.DownLoad);
      }
      if (self.caption == 'disk')
      {
        self.queue0.push(res.Read);
        var l = self.queue1.push(res.Write);
      }

      if(l > self.total) {
        self.queue0.shift();
        if(self.double_line)
          self.queue1.shift();
      }

      if(self.double_line)
      {

        self.point[0].data = [];
        self.point[1].data = [];
        for(var i=0; i<self.total; i++)
        {
          self.point[0].data.push([i,self.queue0[i]]);
          self.point[1].data.push([i,self.queue1[i]]);
        }
        //alert('fetch: ' + self.caption + ": " + self.point[0].data)
       
      }
      else
      {
        //alert('asdf')
        var d = [];
        for(var i=0; i<self.total; i++)
          d.push([i,self.queue0[i]]);
          self.point = [data];
      }

   }
    
   this.update = function(){
      _ajax('GET', '/VirtualMachineUpdate/', {type:self.caption}, self.fetch);
    //if(self.double_line)
      //alert('update: '+self.caption + ": " + self.point[0].data)
    alert(self.point)
    self.plot.setData(self.point);
    self.plot.draw();
    if (self.realtime === "on") setTimeout(self.update, self.interval);
  }    
   
}



 
 
$(function(){

  var mem = new vessel(500, 'mem', mem_plot); 
  var cpu = new vessel(500, 'cpu', cpu_plot);
  var net = new vessel(1000, 'net', net_plot); 
  var disk = new vessel(1000, 'disk', disk_plot);
  
  if (cpu.realtime === "on") cpu.update();
  if (mem.realtime === "on") mem.update();
  if (net.realtime === "on") net.update();
  if (disk.realtime === "on") disk.update();
  
 //REALTIME TOGGLE
 $("#cpu_realtime .btn").click(function () {
   if ($(this).data("toggle") === "on") {
     cpu.realtime = "on";
   }
   else {
     cpu.realtime = "off";
   }
    cpu.update();
 });
 
  $("#mem_realtime .btn").click(function () {
   if ($(this).data("toggle") === "on") {
     mem.realtime = "on";
   }
   else {
     mem.realtime = "off";
   }
    mem.update();
 });
 
  $("#net_realtime .btn").click(function () {
   if ($(this).data("toggle") === "on") {
     net.realtime = "on";
   }
   else {
     net.realtime = "off";
   }
    net.update();
 });
 
  $("#disk_realtime .btn").click(function () {
   if ($(this).data("toggle") === "on") {
     disk.realtime = "on";
   }
   else {
     disk.realtime = "off";
   }
    disk.update();
 });

});
