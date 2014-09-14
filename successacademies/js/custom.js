function get_plot(id, folder, target) {
    var s = document.createElement("script");
    s.type = "text/javascript";
    s.src = folder.concat(id).concat(".js");
    s.id = id;
    s.async = "true";
    s.setAttribute("data-bokeh-data", "static");
    s.setAttribute("data-bokeh-modelid", id);
    s.setAttribute("data-bokeh-modeltype", "Plot");
    var elem = $('#'+target).find('.plotholder').get(0);
    if (elem.children.length > 0) {
        $(elem).empty();
    }
    elem.appendChild(s);
}

function get_table(id, folder, target) {
    var s = document.createElement("script");
    s.type = "text/javascript";
    s.src = folder.concat(id).concat("_table.js");
    s.id = id+'_table';
    s.async = "true";
    var elem = $('#'+target).find('.tableholder').get(0);
    if (elem.children.length > 0) {
        $(elem).empty();
    }
    elem.appendChild(s);

}

function wait(name, callback) {
    var interval = 10; // ms
    if (typeof name=="string") {
        window.setTimeout(function() {
            if ($(name).length>0) {
                callback();
            } else {
                window.setTimeout(arguments.callee, interval);
            }
        }, interval);
    } else {
        window.setTimeout(function() {
            if (name) {
                callback();
            } else {
                window.setTimeout(arguments.callee, interval);
            }
        }, interval);
    }

}

window.onload = function () {

     $("a[data-file]").on('click', function(){
         var filename = this.getAttribute('data-file');
         var foldername = this.getAttribute('data-folder');
         var targetname = this.getAttribute('data-target');
         get_plot(filename, foldername, targetname)
         wait(".bk-logo", function(){
            $(".bk-logo")[0].setAttribute("href", "http://www.successacademies.org/");
            $(".bk-toolbar-button.help").remove();
            var elements = document.getElementsByTagName('a');
            for (var i = 0, len = elements.length; i < len; i++) {
                elements[i].removeAttribute('title');
            }
        });
        var table = $("#"+targetname+" .tableholder")
        if (table.length>0) {
            get_table(filename, foldername, targetname);
        }
    });

    var anchors = $("a[data-file]");
    var items = {};
    $(anchors).each(function() {
        items[$(this).attr('data-target')] = true;
    });

    for(var target in items) {
        $("a[data-target='"+target+"']")[0].click();
    }

    $('#nav-expander').on('click',function(e){
      e.preventDefault();
      $('body').toggleClass('nav-expanded');
    });

    $('.sub-nav').on('click',function(e){
      e.preventDefault();
      $('body').removeClass('nav-expanded');
    });

    $('.main-nav').on('click',function(e){
      e.preventDefault();
      $(this).siblings().find('.sub-nav').addClass('hide')
      $(this).find('.sub-nav').toggleClass('hide')
    });
    wait(".bk-logo", function(){
            $(".bk-logo")[0].setAttribute("href", "http://www.successacademies.org/");
            $(".bk-toolbar-button.help").remove();
            var elements = document.getElementsByTagName('a');
            for (var i = 0, len = elements.length; i < len; i++) {
                elements[i].removeAttribute('title');
            }
        });
}
