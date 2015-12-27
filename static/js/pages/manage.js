 "use strict";
//todo:search \ sort \ splite
function complete(perf){
    var mark = 1;
    var status;
    var item；
    function set_mark(perf_co){
        if (perf_co.is_co) {
            mark = 0;
            status = perf_co.status;
        }
    }
    function fetch_perf(){
        _ajax('GET','/fetchPerf/', {vmName:perf.name}, set_mark);
        if(mark) setTimeout(fetch_perf,2000);
    }
    $("#vmlist tr td:nth-child(2)").each(function(i,element){
        if($(element).text() == perf.name) {item = element.parentElement.children[4];$(item).text("处理中");}
    });
    fetch_perf();
		$(item).text(status);
}


function list_add(list){
    
    var check = "<td ><input id='id_on_line' type='checkbox'/>";
    for(var i in list){
      var uuid_td =  check + "<a href='/VirtualMachine/?uuid=" + list[i].uuid + "'>" + list[i].uuid + "</a></td>";
      var name_td = "<td>" + list[i].mo + "</td>";
      var os_td = "<td>" + list[i].os + "</td>";
      var status_td = "<td>" + list[i].power + "</td>";
      var host_td = "<td>" + list[i].host + "</td>";
      var tr_html = "<tr>" + uuid_td + name_td + os_td + status_td +  host_td +"</tr>";
      var tr = $("#vmlist " + "tr:last");
      tr.after(tr_html);
    }
    list_hide();
}

function list_remove(status){
    $("#vmlist tr td:nth-child(4)").each(function(i,element){
        if($(element).text() == status) element.parentElement.remove();
    });
}

function list_hide(){
     $("#bt_on_line").text("编辑");
     $("#manage1").hide();
        
     $("[id='id_on_line']").each(function(i,element){
        $(element).hide();
     });
}

function list_show(){
    $("#bt_on_line").text("完成");       
    $("#manage1").show();
    $("[id='id_on_line']").each(function(i,element){
        $(element).show();
    });
}
 
$(function () {
    var flag=1;
    list_hide();
    $("#bt_on_line").click(function(){
    if(flag){
        list_show();
        flag=0;
     }
     else
     {
         var rm=[]
         $("[id$='status_vm']").each(function(i,element){
             if (!element.checked) rm.push(element);
         });
         for (var i in rm){
				     list_remove($(rm[i]).text());
         }
         list_hide();
         flag=1;
     }
   });
   
   $("[id$='control_vm']").each(function(i,element){
       $(element).click(function(){
          $("#vmlist tr td:nth-child(1)").each(function(i,item){
           if(item.children[0].checked){
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
           _ajax('GET', '/ManagementUpdate/', {Status:element.className}, list_add);
           //list_hide();       
       }   
       $(element).click(function(){
         if (element.checked){
             _ajax('GET', '/ManagementUpdate/', {Status:element.className}, list_add);
             //list_hide();       
         }
         else{
            list_remove(element.className);
         }
       });
   }); 
});




