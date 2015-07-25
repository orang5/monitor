 "use strict";
var NetDatasets = [
    {
      lines: {
        fill: true,
        color: "#3c8dbc"
      },
      label: 'UpLoad'
    },
    
    {
      lines: {
        color: "#3b8bba"
      },
      label: 'DownLoad'
    }
  ]

var DiskDatasets = [
    {
      lines: {
        fill: true,
        color: "#3c8dbc"
      },
      label: 'Read'
    },
    
    {
      lines: {
        color: "#3b8bba"
      },
      label: 'Write'
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
    shadowSize: 3,
    lines: {
      show: true
    }
  },
  lines: {
    fill: true, //Converts the line chart to area chart
  },
  yaxis: {
    min: 0,
    max: 4096,
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
    max: 500,
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
    max: 1000,
    show: true
  },
  xaxis: {
    min: 0,
    max: 60
  }
});
  
function vessel(interval, caption, plot, point,device_id){

   this.interval = interval;
    
   this.realtime = 'on';
   this.deviceID = device_id;
   this.caption = caption;
   this.total = 60;
   this.plot = plot;
   this.time = new Date(new Date().getTime() - 3*1000);
   this.queue0 = [];
   this.queue1 = [];
   this.point = point;
   
   this.double_line = (caption==='net'||caption==='disk');
      
   for(var i=0; i<60; i++) {
      this.queue0[i] = -1;
      this.queue1[i] = -1;
   }

   this.refresh = function(id){
      this.time = new Date(new Date().getTime() - 3*1000);
      this.queue0 = [];
      this.queue1 = [];
      this.deviceID = id;
      for(var i=0; i<60; i++) {
        this.queue0[i] = -1;
        this.queue1[i] = -1;
      }
   }  
   
   
   var self = this;
    
   this.fetch = function(res){
      if (res) {
      self.time = new Date(self.time.getTime() + 1000)
      if (self.caption == 'cpu')
      { 
        alert(res.cpu_LoadPercentage.volume)
        self.queue0.push.apply(self.queue0, [res.cpu_LoadPercentage.volume]);
        $("#cpu_speed").html(res.cpu_CurrentClockSpeed.volume+res.cpu_CurrentClockSpeed.unit)
        $("#cpu_Availability").html(res.cpu_LoadPercentage.volume+res.cpu_LoadPercentage.unit)
        $("#cpu_NumberOfCores").html(res.cpu_NumberOfCores)
        $("#cpu_NumberOfLogicalProcessors").html(res.cpu_NumberOfLogicalProcessors)
        $("#cpu_MaxClockSpeed").html(res.cpu_MaxClockSpeed.volume+res.cpu_MaxClockSpeed.unit)
      }
 
      if (self.caption == 'mem')
      {
        alert('mem')
        self.queue0.push.apply(self.queue0, [res.mem_Free.volume]);
        $("#mem_Capacity").html(res.mem_Capacity.volume+res.mem_Capacity.unit)
        $("#mem_SwapTotal").html(res.mem_SwapTotal.volume+res.mem_SwapTotal.unit)
        $("#mem_SwapFree").html(res.mem_SwapFree.volume+res.mem_SwapFree.unit)
        $("#mem_Speed").html(res.mem_Speed.volume+res.mem_Speed.unit)
      }
      
      if (self.caption == 'net')
      { 
        alert('net')
        self.queue0.push.apply(self.queue0, [res.net_bytes_out.volume]);
        self.queue1.push.apply(self.queue1, [res.net_bytes_in.volume]);
        $("#net_MACAddress").html(res.net_MACAddress)
        $("#net_DefaultIPGateway").html(res.net_DefaultIPGateway)
        $("#net_ip_v4").html(res.net_ip_address[0])
        $("#net_ip_v6").html(res.net_ip_address[1])
      }
      if (self.caption == 'disk')
      {
        alert('disk')
        self.queue0.push.apply(self.queue0, [res.io_stat_read.volume]);
        self.queue1.push.apply(self.queue1, [res.io_stat_write.volume]);
        $("#disk_FreeSpace").html(res.disk_FreeSpace.volume+res.disk_FreeSpace.unit)
        $("#disk_capacity").html(res.disk_capacity.volume+res.disk_capacity.unit)
        $("#fstype").html(res.fstype)
      }
      var l = self.queue0.length
      
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
      }
      else
      {
        var d = [];
        for(var i=0; i<self.total; i++)
          d.push([i,self.queue0[i]]);
          self.point = [d];
      }  
    self.plot.setData(self.point);
    self.plot.draw();
    self.plot.setupGrid();
   }
  }
}



 
 
$(function(){
   var uuid = window.location.search;
   function update(v){
    _ajax('GET', '/VirtualMachineUpdate/'+uuid, {Time:v.time.getTime(),DeviceId:v.deviceID}, v.fetch);
    if (v && v.realtime === "on") setTimeout(update, v.interval,v);
  } 
  
  var mem = new vessel(1000, 'mem', mem_plot, null,$("#device_mem li").data("toggle")); 
  var cpu = new vessel(1000, 'cpu', cpu_plot, null,$("#device_cpu li").data("toggle"));
  var net = new vessel(1000, 'net', net_plot, NetDatasets,$("#device_net li").data("toggle")); 
  var disk = new vessel(1000, 'disk', disk_plot, DiskDatasets,$("#device_disk li").data("toggle"));
  
  if (cpu.realtime === "on") update(cpu);
  if (mem.realtime === "on") update(mem);
  if (net.realtime === "on") update(net);
  if (disk.realtime === "on") update(disk);
  
 $("#device_cpu li").click(function () {
      if(cpu.deviceID != $(this).data("toggle"))
      {
        cpu.refresh($(this).data("toggle"))
      }
   });  
  $("#device_mem li").click(function () {
     if(mem.deviceID != $(this).data("toggle"))
     {
        mem.refresh($(this).data("toggle"))
     }
  }); 
  $("#device_disk li").click(function () {
    if(disk.deviceID != $(this).data("toggle"))
    {
      
      disk.refresh($(this).data("toggle"))
    }
  }); 
  $("#device_net li").click(function () {
      if(net.deviceID != $(this).data("toggle"))
      {
        net.refresh($(this).data("toggle"))
      }
   }); 
  
 //REALTIME TOGGLE
 $("#cpu_realtime .btn").click(function () {
   if ($(this).data("toggle") === "on") {
     if (cpu.realtime === "off"){
        cpu.realtime = "on";
        update(cpu);
     }
   }
   else { 
     cpu.realtime = "off";
   }  
 });
 
  $("#mem_realtime .btn").click(function () {
   if ($(this).data("toggle") === "on") {
     if (mem.realtime === "off"){
        mem.realtime = "on";
        update(mem);
     }
   }
   else {
     mem.realtime = "off";
   }
 });
 
  $("#net_realtime .btn").click(function () {
   if ($(this).data("toggle") === "on") {
     if (net.realtime === "off"){
        net.realtime = "on";
        update(net);
     }
   }
   else {
     net.realtime = "off";
   }
 });
 
  $("#disk_realtime .btn").click(function () {
   if ($(this).data("toggle") === "on") {
     if (disk.realtime === "off"){
        disk.realtime = "on";
        update(disk);
     }
   }
   else {
     disk.realtime = "off";
   }
 });

});
