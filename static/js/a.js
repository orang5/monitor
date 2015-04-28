'use strict';

function _ajax(method, url, data, callback) {
    $.ajax({
        type: method,
        url: url,
        data: data,
        dataType: 'json'
        
    }).done(function(r) {
        return callback(r)
    })
}

function nice(data){
    
    $('#like_count').html(data.data1[3]);
    $('#likes').hide();
}


$(function(){
    _ajax('GET','index_update/',null,nice)
});