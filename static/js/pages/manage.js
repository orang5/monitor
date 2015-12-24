 "use strict";
//alert("hhe");

function list_add(list){
    
    var check = "<td ><input id='id_on_line' type='checkbox'/>";
    for(var i in list){
      var uuid_td =  check + "<a href='/VirtualMachine/?uuid=" + list[i].uuid + "'>" + list[i].uuid + "</a></td>";
      var name_td = "<td>" + list[i].name + "</td>";
      var os_td = "<td>" + list[i].os + "</td>";
      var status_td = "<td>" + list[i].status + "</td>";
      var tr_html = "<tr>" + uuid_td + name_td + os_td + status_td + "</tr>";
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
        list_hide();
        flag=1;
     }
   });

   $("[id$='status_vm']").each(function(i,element){
       $(element).click(function(){
         if (element.checked){
             _ajax('GET', '/ManagementUpdate/', {Status:element.className}, list_add);       
         }
         else{
            list_remove(element.className);
         }
       });
   }); 
});




