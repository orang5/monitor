 "use strict";
/*
var sidebar = [{"name":"host1","uuid":"host_uuid1","vm_list":[{"name":"vm1","uuid":"vm_uuid1"},{"name":"vm2","uuid":"vm_uuid2"}]},{"name":"host2","uuid":"host_uuid2","vm_list":[{"name":"vm1","uuid":"vm_uuid1"},{"name":"vm2","uuid":"vm_uuid2"}]}];
*/
function callback(sidebar){
    for(var item in sidebar){
        var hn = "<a href='/Host_static/?uuid=" + sidebar[item].uuid + "'><i class='fa fa-laptop' />" + sidebar[item].mo +"</a><a href='#'><i class='fa fa-angle-right pull-right' /></a>";
        var l1 = "<li class='treeview active'>" + hn +"</li>";
        $("#platform").append(l1);

        //var ul = "<ul class='treeview-menu' style='display: none;'></ul>";
        var ul = "<ul class='treeview-menu'></ul>";
                          
        $("#platform li:last").append(ul);
        var vm_list = sidebar[item].vm;
        var l2="";
        for(var j in vm_list){
            if (vm_list[j].is_template != "True")
            {
                l2 = l2 + "<li><a href='/VirtualMachine/?uuid=" + vm_list[j].uuid + "'><i class='fa fa-circle-o'></i>" + vm_list[j].mo + "</a></li>";
            }

        }
        $("#platform li:last ul").html(l2);
    }
}



$(document).ready(function(){
  _ajax('GET','/BaseUpdate/',{},callback)
  //callback(sidebar);
});
