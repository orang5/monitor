 "use strict";
//todo:search \ sort \ splite
var vm_list = new Array();
var flag=0;
var label = {"poweredOn":"开启", "poweredOff":"关闭", "suspended":"挂起"};
var keys = ["poweredOn", "poweredOff", "suspended"];

function complete(perf){
    var mark = 1;
    var status;
    var item;
    function set_mark(perf_co){
        if (perf_co.is_co) {
            mark = 0;
            status = perf_co.status;
            $(item).text(label[status]);
        }
    }
    function fetch_perf(){
            _ajax('GET','/fetchPerf/', {vmName:perf.name, jid:perf.job_id}, set_mark);
            if(mark) setTimeout(fetch_perf,2000);
    }
    $("#vmlist tr td:nth-child(2)").each(function(i,element){
        if($(element).text() == perf.name) {item = element.parentElement.children[3];$(item).text("处理中");}
    });
    fetch_perf();
}

function display(){
    $("#vmlist tr").empty();
    var check = "<input id='id_on_line' type='checkbox'/>";
    for(var k in keys){
        var list = vm_list[keys[k]];
        for(var i in list){
            var b = (list[i].power == "poweredOn");							  
						var uuid_td =  "<td >" + check + "<a href='/VirtualMachine/?uuid=" + list[i].uuid + "'>" + list[i].uuid + "</a>" + "</td>";
						var name_td = "<td>" + list[i].mo + "</td>";
						var os_td = "<td>" + list[i].os + "</td>";
						var status_td = "<td>" + label[list[i].power] + "</td>";
						var host_td = "<td>" + list[i].host + "</td>";
						var tr_html = "<tr>" + uuid_td + name_td + os_td + status_td +  host_td +"</tr>";
						var tr = $("#vmlist tr:last");
						tr.after(tr_html);
      }
    }
    if(flag) list_show(); else list_hide();
		$("[id$='id_on_line']").each(function(i,element){
				$(element).click(function(){
							if(element.checked) $(element.parentElement.parentElement).css("fontWeight","bold");
							else $(element.parentElement.parentElement).css("fontWeight","normal");
				});
		});
}

function list_add(status){
    return function(list){
        vm_list[status] = list;
        display();
    }
}

function list_remove(status){
    vm_list[status] = [];
    display();
}

function list_hide(){
     $("#bt_on_line").text("编辑");
     $("#manage1").hide();
        
     $("[id$='id_on_line']").each(function(i,element){
        $(element).hide();
     });
}

function list_show(){
    $("#bt_on_line").text("完成");       
    $("#manage1").show();
    $("[id$='id_on_line']").each(function(i,element){
        $(element).show();
    });
}
 
$(function () {
    //list_hide();
    $("#bt_on_line").click(function(){
				if(flag){
						flag = 0;
						vm_list = [];
					 $("[id$='status_vm']").each(function(i,element){
							 if (element.checked){
									 _ajax('GET', '/ManagementUpdate/', {Status:element.className}, list_add(element.className));
							 }   
					 });
				 }
				 else
				 {
				     flag = 1;
             list_show();
				 }
   });
      
   $("[id$='control_vm']").each(function(i,element){
       $(element).click(function(){
          $("#vmlist tr td:nth-child(1)").each(function(i,item){
           if(item.children[0].checked){
               //$(item.parentElement).css("fontWeight","bold");
               var name = $(item.parentElement.children[1]).text();
               _ajax('GET','/VmControl/', {op:element.name, vm_uuid:$(item.children[1]).text(), vmName:name}, complete);
           }
          });  
       
       });
   });
  
   /*
   $("[name$='transform']").click(function(){
       $("#vmlist tr td:nth-child(1)").each(function(i,element){
           if(element.children[0].checked)
               _ajax('GET','/VmControl/', {op:"boot", uuid:$(element.children[1]).text()}, complete);
       });
   });
   */

   $("[id$='status_vm']").each(function(i,element){
       if (element.checked){
           _ajax('GET', '/ManagementUpdate/', {Status:element.className}, list_add(element.className));     
       }   
       $(element).click(function(){
         if (element.checked){
             _ajax('GET', '/ManagementUpdate/', {Status:element.className}, list_add(element.className));       
         }
         else{
            list_remove(element.className);
         }
       });
   }); 
});




