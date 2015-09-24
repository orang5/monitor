 "use strict";

var sidebar = [{"name":"host1","uuid":"host_uuid1","vm_list":[{"name":"vm1","uuid":"vm_uuid1"},{"name":"vm2","uuid":"vm_uuid2"}]},{"name":"host2","uuid":"host_uuid2","vm_list":[{"name":"vm1","uuid":"vm_uuid1"},{"name":"vm2","uuid":"vm_uuid2"}]}];

function callback(sidebar){
    for(var i in sidebar){
        var hn = "<a href='#'><i class='fa fa-laptop'></i>" + sidebar[i].name +"<i class='fa fa-angle-left pull-right'></i></a>";
        var l1 = "<li class='treeview active'>" + hn +"</li>";
        $("#plantform").append(l1);

        //var ul = "<ul class='treeview-menu' style='display: none;'></ul>";
        var ul = "<ul class='treeview-menu'></ul>";
                          
        $("#plantform li:last").append(ul);
        var vm_list = sidebar[i].vm_list;
        var l2="";
        for(var j in vm_list){
            l2 = l2 + "<li><a href='/VirtualMachine_static/?uuid=a41f724e5fb8'><i class='fa fa-circle-o'></i>" + j + "</a></li>";

            //$("#plantform li:last ul").append(l2);
            
        }
        $("#plantform li:last ul").html(l2);
    }
}




$(function(){
  //_ajax('GET','/BaseUpdate/',{},callback)
  callback(sidebar);
});
