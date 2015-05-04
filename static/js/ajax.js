function _ajax(method, url, data, callback) {
    $.ajax({
        type: method,
        url: url,
        data: data,
        dataType: 'json'
    }).done(function(r) {
        if(r) return  callback && callback(r);
        
        return callback && callback(null, r);
        
    }).fail(function(r){alert('fail')})
}