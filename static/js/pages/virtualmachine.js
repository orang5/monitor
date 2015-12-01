 "use strict"

$(function () {
    var pltg = [];
    var rttg = [];
    var devtg = [];
    var tag = [];
    $("[id$='chart']").each(function(i,element){
        pltg[i] = '#' + element.id;
    });

    $("[id$='realtime']").each(function(i,element){
        rttg[i] = '#' + element.id + ' .btn';
    });

    $("[id$='device']").each(function(i,element){
        devtg[i] = '#' + element.id + ' li';
    });
    
    $("[tag]").each(function(i,element){
        tag[i] = element.getAttribute("tag");
    });
    
    $.each(pltg,function(i){
        interactive_chart(pltg[i], devtg[i], rttg[i], tag[i]);
    });
});


