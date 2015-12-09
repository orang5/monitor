#tofix:Normalization/unified unit
vc = {
	"name" : "vchart",
	"description" : "define charts in VirtualMachine.html",
	"charts" : [
			{
				"tag" : "cpu",
				"title" : "CPU",
				"realtime" : "cpu_realtime",
				"device" : "cpu_device",
				"chart" : "cpu-chart",
				"points" : [{"lable" : "usage", "value" : ["cpu_LoadPercentage", "cpu_usage"]},
				]	
			},
			{
				"tag" : "mem",
				"title" : "Memory",
				"realtime" : "mem_realtime",
				"device" : "mem_device",
				"chart" : "mem-chart",
				"points" : [{"lable" : "usage", "value" : ["mem_usage","mem_Free"]},#tofix
				            {"lable" : "shared", "value" : ["mem_shared"]},
				            {"lable" : "swaped", "value" : ["mem_swaped"]},
				]
			},
			{
				"tag" : "net",
				"title" : "Network",
				"realtime" : "net_realtime",
				"device" : "net_device",
				"chart" : "net-chart",
				"points" : [{"lable" : "up", "value" : ["net_transmitted", "net_bytes_out_cur"]},
				            {"lable" : "down", "value" : ["net_bytes_in_cur"]},
				            {"lable" : "droppedR", "value" : ["net_droppedRx"]},
				            {"lable" : "droppedT", "value" : ["net_droppedTx"]},
				]
			},
			{
				"tag" : "disk",
				"title" : "Disk",
				"realtime" : "disk_realtime",
				"device" : "disk_device",
				"chart" : "disk-chart",
				"points" : [{"lable" : "read", "value" : ["disk_read","disk_io_stat_read"]},
				            {"lable" : "write", "value" : ["disk_write","disk_io_stat_write"]},
				]
			},
		]
}